"""CodeCommit MCP Server - Entry point and tool registration."""

import json
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from handlers import list_files, get_file_content, get_repository_metadata


server = Server("codecommit-mcp-server")


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """Return the list of tools exposed by this MCP server."""
    return [
        Tool(
            name="list_files",
            description=(
                "List files at the root of a CodeCommit repository. "
                "Returns an array of file and folder names at the specified path."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "repository_name": {
                        "type": "string",
                        "description": "The name of the CodeCommit repository",
                    },
                    "branch": {
                        "type": "string",
                        "description": "The branch name (defaults to 'main')",
                        "default": "main",
                    },
                },
                "required": ["repository_name"],
            },
        ),
        Tool(
            name="get_file_content",
            description=(
                "Get the content of a specific file from a CodeCommit repository. "
                "Returns the file content as a string."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "repository_name": {
                        "type": "string",
                        "description": "The name of the CodeCommit repository",
                    },
                    "file_path": {
                        "type": "string",
                        "description": "The path to the file within the repository",
                    },
                    "branch": {
                        "type": "string",
                        "description": "The branch name (defaults to 'main')",
                        "default": "main",
                    },
                },
                "required": ["repository_name", "file_path"],
            },
        ),
        Tool(
            name="get_repository_metadata",
            description=(
                "Get metadata about a CodeCommit repository including "
                "repository name, default branch, and clone URLs."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "repository_name": {
                        "type": "string",
                        "description": "The name of the CodeCommit repository",
                    },
                },
                "required": ["repository_name"],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Route tool calls to the appropriate handler."""
    try:
        if name == "list_files":
            result = await list_files(
                repository_name=arguments["repository_name"],
                branch=arguments.get("branch", "main"),
            )
        elif name == "get_file_content":
            result = await get_file_content(
                repository_name=arguments["repository_name"],
                file_path=arguments["file_path"],
                branch=arguments.get("branch", "main"),
            )
        elif name == "get_repository_metadata":
            result = await get_repository_metadata(
                repository_name=arguments["repository_name"],
            )
        else:
            result = {"error": f"Unknown tool: {name}"}

        return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}, indent=2))]


async def main():
    """Run the CodeCommit MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
