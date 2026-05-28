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
