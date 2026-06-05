"""API route definitions for the CodeSuite Diagnostics Demo.

Fetches live pipeline state from AWS CodePipeline instead of using hardcoded data.
"""

from __future__ import annotations

import boto3
from fastapi import APIRouter, HTTPException

from agent import diagnose_pipeline_failure
from models import DiagnosisResponse

router = APIRouter()

# Pipeline names we care about for the demo
DEMO_PIPELINE_NAMES = [
    "codesuite-diag-scenario1-pipeline",
    "codesuite-diag-scenario2-pipeline",
    "codesuite-diag-scenario3-pipeline",
]


def _get_codepipeline_client():
    return boto3.client("codepipeline", region_name="us-east-1")


def _get_codedeploy_client():
    return boto3.client("codedeploy", region_name="us-east-1")


def _get_codebuild_client():
    return boto3.client("codebuild", region_name="us-east-1")


def _fetch_pipeline_state(pipeline_name: str) -> dict:
    """Fetch live pipeline state from AWS."""
    client = _get_codepipeline_client()

    try:
        state = client.get_pipeline_state(name=pipeline_name)
    except client.exceptions.PipelineNotFoundException:
        raise HTTPException(status_code=404, detail=f"Pipeline '{pipeline_name}' not found")

    stages = []
    for stage in state.get("stageStates", []):
        actions = []
        for action in stage.get("actionStates", []):
            latest = action.get("latestExecution", {})
            action_data = {
                "name": action.get("actionName", "Unknown"),
                "status": latest.get("status", "Unknown"),
            }
            error_details = latest.get("errorDetails")
            if error_details:
                action_data["errorMessage"] = error_details.get("message", "")
            actions.append(action_data)

        stages.append({
            "name": stage.get("stageName", "Unknown"),
            "status": stage.get("latestExecution", {}).get("status", "Unknown"),
            "actions": actions,
        })

    # Get recent executions
    try:
        exec_response = client.list_pipeline_executions(
            pipelineName=pipeline_name, maxResults=5
        )
    except Exception:
        exec_response = {"pipelineExecutionSummaries": []}

    executions = []
    for ex in exec_response.get("pipelineExecutionSummaries", []):
        executions.append({
            "executionId": ex.get("pipelineExecutionId", ""),
            "status": ex.get("status", "Unknown"),
            "startTime": str(ex.get("startTime", "")),
            "lastUpdateTime": str(ex.get("lastUpdateTime", "")),
            "trigger": ex.get("trigger", {}).get("triggerType", ""),
        })

    # Determine overall latest execution
    latest_execution = None
    if executions:
        latest_execution = executions[0]

    return {
        "name": pipeline_name,
        "stages": stages,
        "executions": executions,
        "latestExecution": latest_execution,
    }


@router.get("/pipelines")
async def list_pipelines():
    """List all pipelines that have a recent failed execution."""
    client = _get_codepipeline_client()
    pipelines = []

    try:
        all_pipeline_names = []
        paginator = client.get_paginator("list_pipelines")
        for page in paginator.paginate():
            for p in page.get("pipelines", []):
                all_pipeline_names.append(p["name"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list pipelines: {str(e)}")

    for name in all_pipeline_names:
        try:
            # Check if the pipeline has any failed executions
            exec_response = client.list_pipeline_executions(
                pipelineName=name, maxResults=1
            )
            summaries = exec_response.get("pipelineExecutionSummaries", [])
            if not summaries:
                continue

            latest_status = summaries[0].get("status", "")
            if latest_status == "Failed":
                pipeline_data = _fetch_pipeline_state(name)
                pipelines.append(pipeline_data)
        except Exception:
            pass

    return pipelines


@router.get("/pipelines/{pipeline_name}")
async def get_pipeline(pipeline_name: str):
    """Get live pipeline detail with stages and execution history."""
    return _fetch_pipeline_state(pipeline_name)


@router.get("/pipelines/{pipeline_name}/executions/{execution_id}")
async def get_pipeline_execution(pipeline_name: str, execution_id: str):
    """Get details for a specific pipeline execution."""
    pipeline_data = _fetch_pipeline_state(pipeline_name)
    for ex in pipeline_data.get("executions", []):
        if ex["executionId"] == execution_id:
            return ex
    # If "latest" was requested, return the first execution
    if execution_id == "latest" and pipeline_data.get("executions"):
        return pipeline_data["executions"][0]
    return {"executionId": execution_id, "status": "Unknown", "startTime": "", "lastUpdateTime": ""}


@router.post("/pipelines/{pipeline_name}/executions/{execution_id}/diagnose")
async def diagnose_execution(pipeline_name: str, execution_id: str) -> DiagnosisResponse:
    """Trigger diagnosis of a failed pipeline execution."""
    # Verify pipeline exists
    _fetch_pipeline_state(pipeline_name)

    try:
        diagnosis = await diagnose_pipeline_failure(pipeline_name, execution_id)
        return diagnosis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Diagnosis failed: {str(e)}")


# ─── CodeDeploy Endpoints ───────────────────────────────────────────────────────


@router.get("/deployments")
async def list_deployments():
    """List recent CodeDeploy deployments."""
    client = _get_codedeploy_client()

    try:
        response = client.list_deployments(
            includeOnlyStatuses=["Failed", "Succeeded", "InProgress", "Stopped"],
        )
        deployment_ids = response.get("deployments", [])[:20]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list deployments: {str(e)}")

    if not deployment_ids:
        return []

    try:
        batch_response = client.batch_get_deployments(deploymentIds=deployment_ids)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get deployment details: {str(e)}")

    deployments = []
    for dep in batch_response.get("deploymentsInfo", []):
        deployments.append({
            "deploymentId": dep.get("deploymentId", ""),
            "applicationName": dep.get("applicationName", ""),
            "deploymentGroupName": dep.get("deploymentGroupName", ""),
            "status": dep.get("status", "Unknown"),
            "createTime": str(dep.get("createTime", "")),
            "completeTime": str(dep.get("completeTime", "")),
            "description": dep.get("description", ""),
            "errorInformation": dep.get("errorInformation", {}),
        })

    return deployments


# ─── CodeBuild Endpoints ────────────────────────────────────────────────────────


@router.get("/build-projects")
async def list_build_projects():
    """List CodeBuild projects with their latest build status."""
    client = _get_codebuild_client()

    try:
        response = client.list_projects(sortBy="NAME", sortOrder="ASCENDING")
        project_names = response.get("projects", [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list build projects: {str(e)}")

    if not project_names:
        return []

    try:
        batch_response = client.batch_get_projects(names=project_names)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get project details: {str(e)}")

    projects = []
    for proj in batch_response.get("projects", []):
        latest_build = None
        # Get the latest build for this project
        try:
            builds_response = client.list_builds_for_project(
                projectName=proj["name"], sortOrder="DESCENDING"
            )
            build_ids = builds_response.get("ids", [])[:1]
            if build_ids:
                build_detail = client.batch_get_builds(ids=build_ids)
                builds = build_detail.get("builds", [])
                if builds:
                    b = builds[0]
                    latest_build = {
                        "buildId": b.get("id", ""),
                        "status": b.get("buildStatus", "Unknown"),
                        "startTime": str(b.get("startTime", "")),
                        "endTime": str(b.get("endTime", "")),
                        "duration": str(b.get("endTime", 0)),
                    }
        except Exception:
            pass

        projects.append({
            "name": proj.get("name", ""),
            "arn": proj.get("arn", ""),
            "description": proj.get("description", ""),
            "source": proj.get("source", {}).get("type", ""),
            "lastModified": str(proj.get("lastModified", "")),
            "latestBuild": latest_build,
        })

    return projects


@router.get("/deployments/{deployment_id}")
async def get_deployment(deployment_id: str):
    """Get detailed information about a specific deployment."""
    client = _get_codedeploy_client()

    try:
        response = client.get_deployment(deploymentId=deployment_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Deployment not found: {str(e)}")

    dep = response.get("deploymentInfo", {})

    # Get deployment target instances
    instances = []
    try:
        targets_response = client.list_deployment_targets(deploymentId=deployment_id)
        target_ids = targets_response.get("targetIds", [])
        if target_ids:
            targets_detail = client.batch_get_deployment_targets(
                deploymentId=deployment_id, targetIds=target_ids[:10]
            )
            for target in targets_detail.get("deploymentTargets", []):
                instance_target = target.get("instanceTarget") or target.get("ecsTarget") or {}
                lifecycle_events = instance_target.get("lifecycleEvents", [])
                instances.append({
                    "targetId": target.get("deploymentTargetType", "Unknown"),
                    "status": instance_target.get("status", "Unknown"),
                    "lifecycleEvents": [
                        {
                            "name": evt.get("lifecycleEventName", ""),
                            "status": evt.get("status", "Unknown"),
                            "startTime": str(evt.get("startTime", "")),
                            "endTime": str(evt.get("endTime", "")),
                            "diagnostics": evt.get("diagnostics", {}),
                        }
                        for evt in lifecycle_events
                    ],
                })
    except Exception:
        pass

    return {
        "deploymentId": dep.get("deploymentId", ""),
        "applicationName": dep.get("applicationName", ""),
        "deploymentGroupName": dep.get("deploymentGroupName", ""),
        "status": dep.get("status", "Unknown"),
        "createTime": str(dep.get("createTime", "")),
        "completeTime": str(dep.get("completeTime", "")),
        "description": dep.get("description", ""),
        "revision": dep.get("revision", {}),
        "errorInformation": dep.get("errorInformation", {}),
        "deploymentOverview": dep.get("deploymentOverview", {}),
        "computePlatform": dep.get("computePlatform", ""),
        "creator": dep.get("creator", ""),
        "targets": instances,
    }


@router.get("/build-projects/{project_name}")
async def get_build_project(project_name: str):
    """Get detailed information about a specific build project and its recent builds."""
    client = _get_codebuild_client()

    try:
        response = client.batch_get_projects(names=[project_name])
        projects = response.get("projects", [])
        if not projects:
            raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found")
        proj = projects[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get project: {str(e)}")

    # Get recent builds
    builds = []
    try:
        builds_response = client.list_builds_for_project(
            projectName=project_name, sortOrder="DESCENDING"
        )
        build_ids = builds_response.get("ids", [])[:10]
        if build_ids:
            builds_detail = client.batch_get_builds(ids=build_ids)
            for b in builds_detail.get("builds", []):
                phases = [
                    {
                        "name": phase.get("phaseType", ""),
                        "status": phase.get("phaseStatus", ""),
                        "duration": phase.get("durationInSeconds", 0),
                    }
                    for phase in b.get("phases", [])
                ]
                builds.append({
                    "buildId": b.get("id", ""),
                    "buildNumber": b.get("buildNumber", 0),
                    "status": b.get("buildStatus", "Unknown"),
                    "startTime": str(b.get("startTime", "")),
                    "endTime": str(b.get("endTime", "")),
                    "sourceVersion": b.get("sourceVersion", ""),
                    "initiator": b.get("initiator", ""),
                    "phases": phases,
                    "logs": {
                        "groupName": b.get("logs", {}).get("groupName", ""),
                        "streamName": b.get("logs", {}).get("streamName", ""),
                        "deepLink": b.get("logs", {}).get("deepLink", ""),
                    },
                })
    except Exception:
        pass

    return {
        "name": proj.get("name", ""),
        "arn": proj.get("arn", ""),
        "description": proj.get("description", ""),
        "source": {
            "type": proj.get("source", {}).get("type", ""),
            "location": proj.get("source", {}).get("location", ""),
            "buildspec": proj.get("source", {}).get("buildspec", ""),
        },
        "environment": {
            "type": proj.get("environment", {}).get("type", ""),
            "computeType": proj.get("environment", {}).get("computeType", ""),
            "image": proj.get("environment", {}).get("image", ""),
        },
        "serviceRole": proj.get("serviceRole", ""),
        "lastModified": str(proj.get("lastModified", "")),
        "created": str(proj.get("created", "")),
        "builds": builds,
    }


# ─── CodeDeploy Diagnosis ───────────────────────────────────────────────────────


@router.post("/deployments/{deployment_id}/diagnose")
async def diagnose_deployment(deployment_id: str) -> DiagnosisResponse:
    """Trigger diagnosis of a failed CodeDeploy deployment."""
    from agent import diagnose_deployment_failure

    client = _get_codedeploy_client()
    try:
        response = client.get_deployment(deploymentId=deployment_id)
        dep = response.get("deploymentInfo", {})
    except Exception:
        raise HTTPException(status_code=404, detail=f"Deployment '{deployment_id}' not found")

    try:
        diagnosis = await diagnose_deployment_failure(
            deployment_id=deployment_id,
            application_name=dep.get("applicationName", ""),
            deployment_group=dep.get("deploymentGroupName", ""),
            status=dep.get("status", ""),
            error_info=dep.get("errorInformation", {}),
        )
        return diagnosis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Diagnosis failed: {str(e)}")


# ─── CodeBuild Diagnosis ────────────────────────────────────────────────────────


@router.post("/build-projects/{project_name}/builds/{build_id}/diagnose")
async def diagnose_build(project_name: str, build_id: str) -> DiagnosisResponse:
    """Trigger diagnosis of a failed CodeBuild build."""
    from agent import diagnose_build_failure

    client = _get_codebuild_client()
    try:
        response = client.batch_get_builds(ids=[build_id])
        builds = response.get("builds", [])
        if not builds:
            raise HTTPException(status_code=404, detail=f"Build '{build_id}' not found")
        build = builds[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get build: {str(e)}")

    try:
        diagnosis = await diagnose_build_failure(
            project_name=project_name,
            build_id=build_id,
            status=build.get("buildStatus", ""),
            phases=build.get("phases", []),
            logs=build.get("logs", {}),
        )
        return diagnosis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Diagnosis failed: {str(e)}")
