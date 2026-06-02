"""Unit tests for CodePipeline MCP Server handlers using mocked boto3 responses."""

import sys
import os
import importlib
import pytest
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError

# Import codepipeline handlers using importlib to avoid path conflicts
_codepipeline_path = os.path.join(
    os.path.dirname(__file__), "..", "mcp-servers", "codepipeline"
)
spec = importlib.util.spec_from_file_location(
    "codepipeline_handlers",
    os.path.join(_codepipeline_path, "handlers.py"),
)
codepipeline_handlers = importlib.util.module_from_spec(spec)
sys.modules["codepipeline_handlers"] = codepipeline_handlers
spec.loader.exec_module(codepipeline_handlers)

get_pipeline_state = codepipeline_handlers.get_pipeline_state
get_pipeline_execution = codepipeline_handlers.get_pipeline_execution
get_action_execution_details = codepipeline_handlers.get_action_execution_details
list_pipeline_executions = codepipeline_handlers.list_pipeline_executions

# Patch target is the module we loaded
PATCH_TARGET = "codepipeline_handlers._get_client"


def make_client_error(code: str, message: str = "Error") -> ClientError:
    """Helper to create a ClientError with a specific error code."""
    return ClientError(
        {"Error": {"Code": code, "Message": message}},
        "operation_name",
    )


class TestGetPipelineState:
    """Tests for the get_pipeline_state handler."""

    @pytest.mark.asyncio
    async def test_get_pipeline_state_success(self):
        """Should return pipeline state with stages and actions."""
        mock_response = {
            "stageStates": [
                {
                    "stageName": "Source",
                    "latestExecution": {"status": "Succeeded"},
                    "actionStates": [
                        {
                            "actionName": "CodeCommit_Source",
                            "latestExecution": {
                                "status": "Succeeded",
                                "lastStatusChange": "2024-01-01T00:00:00Z",
                            },
                        }
                    ],
                },
                {
                    "stageName": "Deploy",
                    "latestExecution": {"status": "Failed"},
                    "actionStates": [
                        {
                            "actionName": "CodeDeploy_Deploy",
                            "latestExecution": {
                                "status": "Failed",
                                "lastStatusChange": "2024-01-01T00:01:00Z",
                                "errorDetails": {
                                    "code": "DeploymentFailed",
                                    "message": "appspec.yml not found",
                                },
                            },
                        }
                    ],
                },
            ]
        }

        with patch(PATCH_TARGET) as mock_get_client:
            mock_client = MagicMock()
            mock_client.get_pipeline_state.return_value = mock_response
            mock_get_client.return_value = mock_client

            result = await get_pipeline_state("my-pipeline")

            assert result["pipeline_name"] == "my-pipeline"
            assert len(result["stages"]) == 2
            assert result["stages"][0]["stage_name"] == "Source"
            assert result["stages"][0]["status"] == "Succeeded"
            assert result["stages"][1]["stage_name"] == "Deploy"
            assert result["stages"][1]["status"] == "Failed"
            assert result["stages"][1]["actions"][0]["action_name"] == "CodeDeploy_Deploy"

    @pytest.mark.asyncio
    async def test_get_pipeline_state_not_found(self):
        """Should raise ValueError for non-existent pipeline."""
        with patch(PATCH_TARGET) as mock_get_client:
            mock_client = MagicMock()
            mock_client.get_pipeline_state.side_effect = make_client_error(
                "PipelineNotFoundException"
            )
            mock_get_client.return_value = mock_client

            with pytest.raises(ValueError, match="does not exist"):
                await get_pipeline_state("nonexistent-pipeline")


class TestGetPipelineExecution:
    """Tests for the get_pipeline_execution handler."""

    @pytest.mark.asyncio
    async def test_get_pipeline_execution_success(self):
        """Should return execution details."""
        mock_response = {
            "pipelineExecution": {
                "pipelineExecutionId": "exec-123",
                "status": "Failed",
                "statusSummary": "Deploy stage failed",
                "trigger": {"triggerType": "PollForSourceChanges"},
            }
        }

        with patch(PATCH_TARGET) as mock_get_client:
            mock_client = MagicMock()
            mock_client.get_pipeline_execution.return_value = mock_response
            mock_get_client.return_value = mock_client

            result = await get_pipeline_execution("my-pipeline", "exec-123")

            assert result["pipeline_name"] == "my-pipeline"
            assert result["execution_id"] == "exec-123"
            assert result["status"] == "Failed"
            assert result["status_summary"] == "Deploy stage failed"

    @pytest.mark.asyncio
    async def test_get_pipeline_execution_not_found(self):
        """Should raise ValueError for non-existent execution."""
        with patch(PATCH_TARGET) as mock_get_client:
            mock_client = MagicMock()
            mock_client.get_pipeline_execution.side_effect = make_client_error(
                "PipelineExecutionNotFoundException"
            )
            mock_get_client.return_value = mock_client

            with pytest.raises(ValueError, match="Execution.*not found"):
                await get_pipeline_execution("my-pipeline", "bad-exec-id")

    @pytest.mark.asyncio
    async def test_get_pipeline_execution_pipeline_not_found(self):
        """Should raise ValueError for non-existent pipeline."""
        with patch(PATCH_TARGET) as mock_get_client:
            mock_client = MagicMock()
            mock_client.get_pipeline_execution.side_effect = make_client_error(
                "PipelineNotFoundException"
            )
            mock_get_client.return_value = mock_client

            with pytest.raises(ValueError, match="does not exist"):
                await get_pipeline_execution("nonexistent", "exec-123")


class TestGetActionExecutionDetails:
    """Tests for the get_action_execution_details handler."""

    @pytest.mark.asyncio
    async def test_get_action_execution_details_success(self):
        """Should return action error details."""
        mock_response = {
            "actionExecutionDetails": [
                {
                    "stageName": "Deploy",
                    "actionName": "CodeDeploy_Deploy",
                    "status": "Failed",
                    "input": {
                        "inputArtifacts": [{"name": "SourceOutput"}],
                    },
                    "output": {
                        "executionResult": {
                            "externalExecutionSummary": "The AppSpec file cannot be located",
                            "externalExecutionId": "d-ABC123",
                            "externalExecutionUrl": "https://console.aws.amazon.com/...",
                        },
                        "outputArtifacts": [],
                    },
                }
            ]
        }

        with patch(PATCH_TARGET) as mock_get_client:
            mock_client = MagicMock()
            mock_client.list_action_executions.return_value = mock_response
            mock_get_client.return_value = mock_client

            result = await get_action_execution_details(
                "my-pipeline", "exec-123", "Deploy", "CodeDeploy_Deploy"
            )

            assert result["status"] == "Failed"
            assert "AppSpec file cannot be located" in result["error_message"]
            assert result["input_artifacts"] == ["SourceOutput"]

    @pytest.mark.asyncio
    async def test_get_action_execution_details_action_not_found(self):
        """Should return error dict when action is not found in results."""
        mock_response = {"actionExecutionDetails": []}

        with patch(PATCH_TARGET) as mock_get_client:
            mock_client = MagicMock()
            mock_client.list_action_executions.return_value = mock_response
            mock_get_client.return_value = mock_client

            result = await get_action_execution_details(
                "my-pipeline", "exec-123", "Deploy", "MissingAction"
            )

            assert "error" in result
            assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_get_action_execution_details_pipeline_not_found(self):
        """Should raise ValueError for non-existent pipeline."""
        with patch(PATCH_TARGET) as mock_get_client:
            mock_client = MagicMock()
            mock_client.list_action_executions.side_effect = make_client_error(
                "PipelineNotFoundException"
            )
            mock_get_client.return_value = mock_client

            with pytest.raises(ValueError, match="does not exist"):
                await get_action_execution_details(
                    "nonexistent", "exec-123", "Deploy", "Action"
                )


class TestListPipelineExecutions:
    """Tests for the list_pipeline_executions handler."""

    @pytest.mark.asyncio
    async def test_list_pipeline_executions_success(self):
        """Should return list of recent executions."""
        mock_response = {
            "pipelineExecutionSummaries": [
                {
                    "pipelineExecutionId": "exec-1",
                    "status": "Failed",
                    "startTime": "2024-01-01T00:00:00Z",
                    "lastUpdateTime": "2024-01-01T00:05:00Z",
                    "trigger": {"triggerType": "PollForSourceChanges"},
                    "sourceRevisions": [],
                },
                {
                    "pipelineExecutionId": "exec-2",
                    "status": "Succeeded",
                    "startTime": "2024-01-02T00:00:00Z",
                    "lastUpdateTime": "2024-01-02T00:03:00Z",
                    "trigger": {"triggerType": "Manual"},
                    "sourceRevisions": [],
                },
            ]
        }

        with patch(PATCH_TARGET) as mock_get_client:
            mock_client = MagicMock()
            mock_client.list_pipeline_executions.return_value = mock_response
            mock_get_client.return_value = mock_client

            result = await list_pipeline_executions("my-pipeline", max_results=5)

            assert result["pipeline_name"] == "my-pipeline"
            assert len(result["executions"]) == 2
            assert result["executions"][0]["execution_id"] == "exec-1"
            assert result["executions"][0]["status"] == "Failed"
            assert result["executions"][1]["status"] == "Succeeded"

    @pytest.mark.asyncio
    async def test_list_pipeline_executions_not_found(self):
        """Should raise ValueError for non-existent pipeline."""
        with patch(PATCH_TARGET) as mock_get_client:
            mock_client = MagicMock()
            mock_client.list_pipeline_executions.side_effect = make_client_error(
                "PipelineNotFoundException"
            )
            mock_get_client.return_value = mock_client

            with pytest.raises(ValueError, match="does not exist"):
                await list_pipeline_executions("nonexistent")

    @pytest.mark.asyncio
    async def test_list_pipeline_executions_empty(self):
        """Should return empty list for pipeline with no executions."""
        mock_response = {"pipelineExecutionSummaries": []}

        with patch(PATCH_TARGET) as mock_get_client:
            mock_client = MagicMock()
            mock_client.list_pipeline_executions.return_value = mock_response
            mock_get_client.return_value = mock_client

            result = await list_pipeline_executions("my-pipeline")

            assert result["executions"] == []
