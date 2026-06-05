"""CodePipeline MCP Server - Entry point and tool registration."""

import json
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from handlers import (
    get_pipeline_state,
    get_pipeline_execution,
    get_action_execution_details,
    list_pipeline_executions,
    get_pipeline_configuration,
    get_deployment_info,
    get_deployment_targets,
    list_deployments_for_group,
    get_build_info,
    get_build_logs,
    list_builds_for_project,
)


server = Server("codepipeline-mcp-server")


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """Return the list of tools exposed by this MCP server."""
    return [
        Tool(
            name="get_pipeline_state",
            description=(
                "Get the current state of a CodePipeline including all stage "
                "and action statuses. Shows which stages succeeded or failed."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "pipeline_name": {
                        "type": "string",
                        "description": "The name of the CodePipeline",
                    },
                },
                "required": ["pipeline_name"],
            },
        ),
        Tool(
            name="get_pipeline_execution",
            description=(
                "Get details of a specific pipeline execution including status, "
                "start time, and trigger information."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "pipeline_name": {
                        "type": "string",
                        "description": "The name of the CodePipeline",
                    },
                    "execution_id": {
                        "type": "string",
                        "description": "The execution ID to retrieve details for",
                    },
                },
                "required": ["pipeline_name", "execution_id"],
            },
        ),
        Tool(
            name="get_action_execution_details",
            description=(
                "Get detailed error messages and output for a specific failed action "
                "within a pipeline execution. Useful for diagnosing why a stage failed."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "pipeline_name": {
                        "type": "string",
                        "description": "The name of the CodePipeline",
                    },
                    "execution_id": {
                        "type": "string",
                        "description": "The pipeline execution ID",
                    },
                    "stage_name": {
                        "type": "string",
                        "description": "The name of the stage containing the action",
                    },
                    "action_name": {
                        "type": "string",
                        "description": "The name of the action to get details for",
                    },
                },
                "required": ["pipeline_name", "execution_id", "stage_name", "action_name"],
            },
        ),
        Tool(
            name="list_pipeline_executions",
            description=(
                "List recent executions for a pipeline with their statuses. "
                "Returns the most recent executions ordered by start time."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "pipeline_name": {
                        "type": "string",
                        "description": "The name of the CodePipeline",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of executions to return (default: 5)",
                        "default": 5,
                    },
                },
                "required": ["pipeline_name"],
            },
        ),
        Tool(
            name="get_pipeline_configuration",
            description=(
                "Get the pipeline definition including source repository names, "
                "action configurations, build project names, deploy targets, and "
                "the pipeline's IAM role ARN. Use this to find repository names, "
                "service roles, and action-specific configurations."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "pipeline_name": {
                        "type": "string",
                        "description": "The name of the CodePipeline",
                    },
                },
                "required": ["pipeline_name"],
            },
        ),
        Tool(
            name="get_deployment_info",
            description=(
                "Get detailed information about a CodeDeploy deployment including "
                "status, error information, deployment overview, revision details, "
                "and compute platform."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "deployment_id": {
                        "type": "string",
                        "description": "The CodeDeploy deployment ID (e.g., d-XXXXXXXXX)",
                    },
                },
                "required": ["deployment_id"],
            },
        ),
        Tool(
            name="get_deployment_targets",
            description=(
                "Get the targets (EC2 instances or ECS tasks) for a CodeDeploy deployment "
                "with their lifecycle event statuses, error diagnostics, log tails, "
                "and script names. Use this to find why specific instances failed."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "deployment_id": {
                        "type": "string",
                        "description": "The CodeDeploy deployment ID",
                    },
                },
                "required": ["deployment_id"],
            },
        ),
        Tool(
            name="list_deployments_for_group",
            description=(
                "List recent deployments for a specific CodeDeploy application and "
                "deployment group, including their statuses and error information."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "application_name": {
                        "type": "string",
                        "description": "The CodeDeploy application name",
                    },
                    "deployment_group_name": {
                        "type": "string",
                        "description": "The deployment group name",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum results to return (default: 5)",
                        "default": 5,
                    },
                },
                "required": ["application_name", "deployment_group_name"],
            },
        ),
        Tool(
            name="get_build_info",
            description=(
                "Get detailed information about a CodeBuild build including status, "
                "build phases with error messages, environment configuration, "
                "service role, and log locations."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "build_id": {
                        "type": "string",
                        "description": "The full CodeBuild build ID (e.g., project-name:build-uuid)",
                    },
                },
                "required": ["build_id"],
            },
        ),
        Tool(
            name="get_build_logs",
            description=(
                "Get the CloudWatch build logs for a CodeBuild build. "
                "Returns the last N lines of build output. Use this to read "
                "error messages, test failures, and build commands that failed."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "build_id": {
                        "type": "string",
                        "description": "The full CodeBuild build ID",
                    },
                    "max_lines": {
                        "type": "integer",
                        "description": "Maximum number of log lines to return (default: 100)",
                        "default": 100,
                    },
                },
                "required": ["build_id"],
            },
        ),
        Tool(
            name="list_builds_for_project",
            description=(
                "List recent builds for a CodeBuild project with their statuses and initiators."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "The CodeBuild project name",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum results to return (default: 5)",
                        "default": 5,
                    },
                },
                "required": ["project_name"],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Route tool calls to the appropriate handler."""
    try:
        if name == "get_pipeline_state":
            result = await get_pipeline_state(
                pipeline_name=arguments["pipeline_name"],
            )
        elif name == "get_pipeline_execution":
            result = await get_pipeline_execution(
                pipeline_name=arguments["pipeline_name"],
                execution_id=arguments["execution_id"],
            )
        elif name == "get_action_execution_details":
            result = await get_action_execution_details(
                pipeline_name=arguments["pipeline_name"],
                execution_id=arguments["execution_id"],
                stage_name=arguments["stage_name"],
                action_name=arguments["action_name"],
            )
        elif name == "list_pipeline_executions":
            result = await list_pipeline_executions(
                pipeline_name=arguments["pipeline_name"],
                max_results=arguments.get("max_results", 5),
            )
        elif name == "get_pipeline_configuration":
            result = await get_pipeline_configuration(
                pipeline_name=arguments["pipeline_name"],
            )
        elif name == "get_deployment_info":
            result = await get_deployment_info(
                deployment_id=arguments["deployment_id"],
            )
        elif name == "get_deployment_targets":
            result = await get_deployment_targets(
                deployment_id=arguments["deployment_id"],
            )
        elif name == "list_deployments_for_group":
            result = await list_deployments_for_group(
                application_name=arguments["application_name"],
                deployment_group_name=arguments["deployment_group_name"],
                max_results=arguments.get("max_results", 5),
            )
        elif name == "get_build_info":
            result = await get_build_info(
                build_id=arguments["build_id"],
            )
        elif name == "get_build_logs":
            result = await get_build_logs(
                build_id=arguments["build_id"],
                max_lines=arguments.get("max_lines", 100),
            )
        elif name == "list_builds_for_project":
            result = await list_builds_for_project(
                project_name=arguments["project_name"],
                max_results=arguments.get("max_results", 5),
            )
        else:
            result = {"error": f"Unknown tool: {name}"}

        return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}, indent=2))]


async def main():
    """Run the CodePipeline MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
