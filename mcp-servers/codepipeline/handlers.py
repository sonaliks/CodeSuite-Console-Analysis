"""CodePipeline MCP Server - Tool handler implementations."""

import boto3
from botocore.exceptions import ClientError


def _get_client():
    """Create a boto3 CodePipeline client."""
    return boto3.client("codepipeline")


async def get_pipeline_state(pipeline_name: str) -> dict:
    """
    Get the current state of a CodePipeline.

    Args:
        pipeline_name: The name of the CodePipeline.

    Returns:
        Dictionary with pipeline state including stage and action statuses.
    """
    client = _get_client()

    try:
        response = client.get_pipeline_state(name=pipeline_name)

        stages = []
        for stage in response.get("stageStates", []):
            actions = []
            for action in stage.get("actionStates", []):
                action_info = {
                    "action_name": action.get("actionName"),
                    "status": action.get("latestExecution", {}).get("status", "Unknown"),
                    "last_status_change": action.get("latestExecution", {}).get(
                        "lastStatusChange"
                    ),
                    "error_details": action.get("latestExecution", {}).get("errorDetails"),
                }
                actions.append(action_info)

            stages.append({
                "stage_name": stage.get("stageName"),
                "status": stage.get("latestExecution", {}).get("status", "Unknown"),
                "actions": actions,
            })

        return {
            "pipeline_name": pipeline_name,
            "stages": stages,
        }

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "PipelineNotFoundException":
            raise ValueError(
                f"Pipeline '{pipeline_name}' does not exist. "
                "Please verify the pipeline name and try again."
            )
        else:
            raise ValueError(f"AWS CodePipeline error: {e.response['Error']['Message']}")


async def get_pipeline_execution(pipeline_name: str, execution_id: str) -> dict:
    """
    Get details of a specific pipeline execution.

    Args:
        pipeline_name: The name of the CodePipeline.
        execution_id: The execution ID to retrieve details for.

    Returns:
        Dictionary with execution details.
    """
    client = _get_client()

    try:
        response = client.get_pipeline_execution(
            pipelineName=pipeline_name,
            pipelineExecutionId=execution_id,
        )

        execution = response.get("pipelineExecution", {})

        return {
            "pipeline_name": pipeline_name,
            "execution_id": execution.get("pipelineExecutionId"),
            "status": execution.get("status"),
            "status_summary": execution.get("statusSummary", ""),
            "trigger": execution.get("trigger", {}),
        }

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "PipelineNotFoundException":
            raise ValueError(
                f"Pipeline '{pipeline_name}' does not exist. "
                "Please verify the pipeline name and try again."
            )
        elif error_code == "PipelineExecutionNotFoundException":
            raise ValueError(
                f"Execution '{execution_id}' not found for pipeline '{pipeline_name}'. "
                "Please verify the execution ID and try again."
            )
        else:
            raise ValueError(f"AWS CodePipeline error: {e.response['Error']['Message']}")


async def get_action_execution_details(
    pipeline_name: str, execution_id: str, stage_name: str, action_name: str
) -> dict:
    """
    Get detailed error messages for a specific action in a pipeline execution.

    Args:
        pipeline_name: The name of the CodePipeline.
        execution_id: The pipeline execution ID.
        stage_name: The name of the stage containing the action.
        action_name: The name of the action to get details for.

    Returns:
        Dictionary with action execution details including error messages.
    """
    client = _get_client()

    try:
        response = client.list_action_executions(
            pipelineName=pipeline_name,
            filter={
                "pipelineExecutionId": execution_id,
            },
        )

        # Find the specific action in the results
        for detail in response.get("actionExecutionDetails", []):
            if (
                detail.get("stageName") == stage_name
                and detail.get("actionName") == action_name
            ):
                output = detail.get("output", {})
                execution_result = output.get("executionResult", {})

                return {
                    "pipeline_name": pipeline_name,
                    "execution_id": execution_id,
                    "stage_name": stage_name,
                    "action_name": action_name,
                    "status": detail.get("status", "Unknown"),
                    "error_message": execution_result.get("externalExecutionSummary", ""),
                    "external_execution_id": execution_result.get("externalExecutionId", ""),
                    "external_execution_url": execution_result.get("externalExecutionUrl", ""),
                    "input_artifacts": [
                        a.get("name") for a in detail.get("input", {}).get("inputArtifacts", [])
                    ],
                    "output_artifacts": [
                        a.get("name") for a in output.get("outputArtifacts", [])
                    ],
                }

        return {
            "pipeline_name": pipeline_name,
            "execution_id": execution_id,
            "stage_name": stage_name,
            "action_name": action_name,
            "error": (
                f"Action '{action_name}' in stage '{stage_name}' not found "
                f"for execution '{execution_id}'."
            ),
        }

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "PipelineNotFoundException":
            raise ValueError(
                f"Pipeline '{pipeline_name}' does not exist. "
                "Please verify the pipeline name and try again."
            )
        else:
            raise ValueError(f"AWS CodePipeline error: {e.response['Error']['Message']}")


async def list_pipeline_executions(pipeline_name: str, max_results: int = 5) -> dict:
    """
    List recent executions for a pipeline.

    Args:
        pipeline_name: The name of the CodePipeline.
        max_results: Maximum number of executions to return (default: 5).

    Returns:
        Dictionary with list of recent executions.
    """
    client = _get_client()

    try:
        response = client.list_pipeline_executions(
            pipelineName=pipeline_name,
            maxResults=max_results,
        )

        executions = []
        for execution in response.get("pipelineExecutionSummaries", []):
            executions.append({
                "execution_id": execution.get("pipelineExecutionId"),
                "status": execution.get("status"),
                "start_time": execution.get("startTime"),
                "last_update_time": execution.get("lastUpdateTime"),
                "trigger": execution.get("trigger", {}),
                "source_revisions": execution.get("sourceRevisions", []),
            })

        return {
            "pipeline_name": pipeline_name,
            "executions": executions,
        }

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "PipelineNotFoundException":
            raise ValueError(
                f"Pipeline '{pipeline_name}' does not exist. "
                "Please verify the pipeline name and try again."
            )
        else:
            raise ValueError(f"AWS CodePipeline error: {e.response['Error']['Message']}")


async def get_pipeline_configuration(pipeline_name: str) -> dict:
    """
    Get the pipeline definition/configuration including source repository names,
    action configurations, and role ARNs.

    Args:
        pipeline_name: The name of the CodePipeline.

    Returns:
        Dictionary with pipeline configuration details including stages,
        actions, and their configurations (source repos, build projects, etc).
    """
    client = _get_client()

    try:
        response = client.get_pipeline(name=pipeline_name)
        pipeline = response.get("pipeline", {})

        stages = []
        for stage in pipeline.get("stages", []):
            actions = []
            for action in stage.get("actions", []):
                actions.append({
                    "action_name": action.get("name"),
                    "category": action.get("actionTypeId", {}).get("category"),
                    "provider": action.get("actionTypeId", {}).get("provider"),
                    "configuration": action.get("configuration", {}),
                })
            stages.append({
                "stage_name": stage.get("name"),
                "actions": actions,
            })

        return {
            "pipeline_name": pipeline_name,
            "role_arn": pipeline.get("roleArn", ""),
            "artifact_store": pipeline.get("artifactStore", {}),
            "stages": stages,
        }

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "PipelineNotFoundException":
            raise ValueError(
                f"Pipeline '{pipeline_name}' does not exist. "
                "Please verify the pipeline name and try again."
            )
        else:
            raise ValueError(f"AWS CodePipeline error: {e.response['Error']['Message']}")
