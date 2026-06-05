"""MCP Client module using the official MCP SDK client.

This module manages MCP server subprocesses and provides a unified interface
for invoking tools across multiple MCP servers via the SDK's stdio transport.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server."""
    name: str
    command: str
    args: List[str] = field(default_factory=list)
    env: Optional[Dict[str, str]] = None


@dataclass
class MCPTool:
    """Represents a tool exposed by an MCP server."""
    name: str
    description: str
    input_schema: dict
    server_name: str


class MCPClient:
    """Client for managing and communicating with MCP servers."""

    def __init__(self):
        self._servers: Dict[str, MCPServerConfig] = {}
        self._tools: Dict[str, MCPTool] = {}
        self._sessions: Dict[str, Any] = {}
        self._contexts: Dict[str, Any] = {}

    def register_server(self, config: MCPServerConfig):
        """Register an MCP server configuration."""
        self._servers[config.name] = config

    async def start_server(self, server_name: str):
        """Start an MCP server and discover its tools."""
        config = self._servers[server_name]

        server_params = StdioServerParameters(
            command=config.command,
            args=config.args,
            env=config.env,
        )

        # Create the stdio client context
        ctx = stdio_client(server_params)
        streams = await ctx.__aenter__()
        self._contexts[server_name] = ctx

        # Create a session
        session = ClientSession(*streams)
        await session.__aenter__()
        self._sessions[server_name] = session

        # Initialize the session
        await session.initialize()

        # Discover tools
        tools_result = await session.list_tools()
        for tool in tools_result.tools:
            self._tools[tool.name] = MCPTool(
                name=tool.name,
                description=tool.description or "",
                input_schema=tool.inputSchema if tool.inputSchema else {},
                server_name=server_name,
            )

    async def start_all(self):
        """Start all registered MCP servers."""
        for server_name in self._servers:
            try:
                await self.start_server(server_name)
            except Exception as e:
                print(f"Warning: Failed to start MCP server '{server_name}': {e}")

    async def stop_all(self):
        """Stop all running MCP server sessions."""
        for name, session in self._sessions.items():
            try:
                await session.__aexit__(None, None, None)
            except Exception:
                pass
        for name, ctx in self._contexts.items():
            try:
                await ctx.__aexit__(None, None, None)
            except Exception:
                pass
        self._sessions.clear()
        self._contexts.clear()

    def get_all_tools(self) -> List[MCPTool]:
        """Get all tools from all registered servers."""
        return list(self._tools.values())

    def get_tool_schemas_for_bedrock(self) -> List[dict]:
        """Get tool schemas formatted for Bedrock Converse API."""
        tools = []
        for tool in self._tools.values():
            tools.append({
                "toolSpec": {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": {
                        "json": tool.input_schema,
                    },
                }
            })
        return tools

    async def call_tool(self, tool_name: str, arguments: dict) -> dict:
        """Call a tool on the appropriate MCP server."""
        if tool_name not in self._tools:
            return {"error": f"Tool '{tool_name}' not found"}

        tool = self._tools[tool_name]
        server_name = tool.server_name
        session = self._sessions.get(server_name)

        if not session:
            return {"error": f"Server '{server_name}' is not connected"}

        try:
            result = await session.call_tool(tool_name, arguments)

            # Extract text content from MCP response
            if result.content:
                for content_item in result.content:
                    if content_item.type == "text":
                        try:
                            return json.loads(content_item.text)
                        except json.JSONDecodeError:
                            return {"text": content_item.text}

            return {"error": "Empty response from tool"}
        except Exception as e:
            return {"error": str(e)}


def get_default_mcp_client() -> MCPClient:
    """Create an MCP client with default server configurations."""
    import shutil
    import sys

    client = MCPClient()

    # Find the python3 executable
    python_cmd = shutil.which("python3") or sys.executable

    # Custom MCP servers
    mcp_servers_dir = Path(__file__).parent.parent / "mcp-servers"

    client.register_server(MCPServerConfig(
        name="codecommit",
        command=python_cmd,
        args=[str(mcp_servers_dir / "codecommit" / "server.py")],
    ))

    client.register_server(MCPServerConfig(
        name="codepipeline",
        command=python_cmd,
        args=[str(mcp_servers_dir / "codepipeline" / "server.py")],
    ))

    # AWS Labs MCP servers (uncomment when installed via uvx)
    # client.register_server(MCPServerConfig(
    #     name="aws-iam",
    #     command="uvx",
    #     args=["awslabs.aws-iam-mcp-server@latest"],
    #     env={"FASTMCP_LOG_LEVEL": "ERROR"},
    # ))
    #
    # client.register_server(MCPServerConfig(
    #     name="aws-cloudwatch",
    #     command="uvx",
    #     args=["awslabs.amazon-cloudwatch-mcp-server@latest"],
    #     env={"FASTMCP_LOG_LEVEL": "ERROR"},
    # ))

    return client
