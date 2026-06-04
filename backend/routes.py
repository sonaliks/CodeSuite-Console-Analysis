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
