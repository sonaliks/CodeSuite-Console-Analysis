"""MCP Client module for spawning and communicating with MCP servers.

This module manages MCP server subprocesses and provides a unified interface
for invoking tools across multiple MCP servers via stdio JSON-RPC.
"""

import asyncio
import json
import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server."""
    name: str
    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)


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
        self._servers: dict[str, MCPServerConfig] = {}
        self._processes: dict[str, asyncio.subprocess.Process] = {}
        self._tools: dict[str, MCPTool] = {}
        self._request_id = 0

    def register_server(self, config: MCPServerConfig):
        """Register an MCP server configuration."""
        self._servers[config.name] = config

    async def start_server(self, server_name: str):
        """Start an MCP server subprocess."""
        config = self._servers[server_name]

        env = os.environ.copy()
        env.update(config.env)

        process = await asyncio.create_subprocess_exec(
            config.command,
            *config.args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )

        self._processes[server_name] = process

        # Initialize the MCP connection
        await self._initialize(server_name)

        # Discover tools
        await self._discover_tools(server_name)

    async def start_all(self):
        """Start all registered MCP servers."""
        for server_name in self._servers:
            await self.start_server(server_name)

    async def stop_all(self):
        """Stop all running MCP server processes."""
        for name, process in self._processes.items():
            if process.returncode is None:
                process.terminate()
                await process.wait()
        self._processes.clear()

    def get_all_tools(self) -> list[MCPTool]:
        """Get all tools from all registered servers."""
        return list(self._tools.values())

    def get_tool_schemas_for_bedrock(self) -> list[dict]:
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

        response = await self._send_request(
            server_name,
            "tools/call",
            {"name": tool_name, "arguments": arguments},
        )

        # Extract text content from MCP response
        if "result" in response:
            content = response["result"].get("content", [])
            if content and content[0].get("type") == "text":
                try:
                    return json.loads(content[0]["text"])
                except json.JSONDecodeError:
                    return {"text": content[0]["text"]}
        elif "error" in response:
            return {"error": response["error"].get("message", "Unknown error")}

        return {"error": "Unexpected response format"}

    async def _initialize(self, server_name: str):
        """Send initialize request to MCP server."""
        await self._send_request(
            server_name,
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "codesuite-diagnostics", "version": "0.1.0"},
            },
        )
        # Send initialized notification
        await self._send_notification(server_name, "notifications/initialized", {})

    async def _discover_tools(self, server_name: str):
        """Discover tools from an MCP server."""
        response = await self._send_request(server_name, "tools/list", {})

        if "result" in response:
            for tool_data in response["result"].get("tools", []):
                tool = MCPTool(
                    name=tool_data["name"],
                    description=tool_data.get("description", ""),
                    input_schema=tool_data.get("inputSchema", {}),
                    server_name=server_name,
                )
                self._tools[tool.name] = tool

    async def _send_request(self, server_name: str, method: str, params: dict) -> dict:
        """Send a JSON-RPC request to an MCP server and return the response."""
        process = self._processes.get(server_name)
        if not process or process.returncode is not None:
            return {"error": {"message": f"Server '{server_name}' is not running"}}

        self._request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
            "params": params,
        }

        request_bytes = json.dumps(request).encode() + b"\n"
        process.stdin.write(request_bytes)
        await process.stdin.drain()

        # Read response line
        response_line = await process.stdout.readline()
        if not response_line:
            return {"error": {"message": "No response from server"}}

        return json.loads(response_line.decode())

    async def _send_notification(self, server_name: str, method: str, params: dict):
        """Send a JSON-RPC notification (no response expected)."""
        process = self._processes.get(server_name)
        if not process or process.returncode is not None:
            return

        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        }

        notification_bytes = json.dumps(notification).encode() + b"\n"
        process.stdin.write(notification_bytes)
        await process.stdin.drain()


def get_default_mcp_client() -> MCPClient:
    """Create an MCP client with default server configurations."""
    client = MCPClient()

    # Custom MCP servers
    mcp_servers_dir = Path(__file__).parent.parent / "mcp-servers"

    client.register_server(MCPServerConfig(
        name="codecommit",
        command="python",
        args=[str(mcp_servers_dir / "codecommit" / "server.py")],
    ))

    client.register_server(MCPServerConfig(
        name="codepipeline",
        command="python",
        args=[str(mcp_servers_dir / "codepipeline" / "server.py")],
    ))

    # AWS Labs MCP servers (installed via uvx)
    client.register_server(MCPServerConfig(
        name="aws-iam",
        command="uvx",
        args=["awslabs.aws-iam-mcp-server@latest"],
        env={"FASTMCP_LOG_LEVEL": "ERROR"},
    ))

    client.register_server(MCPServerConfig(
        name="aws-cloudwatch",
        command="uvx",
        args=["awslabs.amazon-cloudwatch-mcp-server@latest"],
        env={"FASTMCP_LOG_LEVEL": "ERROR"},
    ))

    return client
