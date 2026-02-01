"""
MCP (Model Context Protocol) Client Integration

This module provides a client for connecting to MCP servers and calling tools.
MCP enables agents to interact with external systems like browsers, databases, etc.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MCPClient:
    """
    Client for interacting with MCP (Model Context Protocol) servers.

    Supports connecting to MCP servers via stdio and calling tools.
    """

    def __init__(
        self,
        command: str,
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize MCP client.

        Args:
            command: Command to launch MCP server (e.g., "mcp-server-browsermcp")
            args: Optional command-line arguments
            env: Optional environment variables
        """
        self.command = command
        self.args = args or []
        self.env = env or {}
        self._tools_cache: Optional[List[Dict[str, Any]]] = None
        logger.info(f"Initialized MCP client for command: {command}")

    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        List available tools from the MCP server.

        Returns:
            List of tool definitions with name, description, and input schema
        """
        if self._tools_cache is not None:
            return self._tools_cache

        try:
            # Import MCP libraries dynamically to avoid hard dependency
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client

            server_params = StdioServerParameters(
                command=self.command, args=self.args, env=self.env
            )

            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()

                    # List tools from server
                    tools_result = await session.list_tools()

                    # Convert to standard format
                    tools = []
                    for tool in tools_result.tools:
                        tools.append(
                            {
                                "name": tool.name,
                                "description": tool.description,
                                "input_schema": (
                                    tool.inputSchema
                                    if hasattr(tool, "inputSchema")
                                    else {}
                                ),
                            }
                        )

                    self._tools_cache = tools
                    logger.info(f"Listed {len(tools)} tools from MCP server")
                    return tools

        except ImportError:
            logger.error("MCP library not installed. Install with: pip install mcp")
            return []
        except Exception as e:
            logger.error(f"Failed to list MCP tools: {e}")
            return []

    async def call_tool(
        self, name: str, arguments: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Call a tool on the MCP server.

        Args:
            name: Tool name to call
            arguments: Tool arguments as a dictionary

        Returns:
            Tool execution result
        """
        try:
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client

            server_params = StdioServerParameters(
                command=self.command, args=self.args, env=self.env
            )

            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()

                    # Call the tool
                    result = await session.call_tool(name, arguments=arguments or {})

                    logger.info(f"Called MCP tool '{name}' successfully")
                    return result

        except ImportError:
            logger.error("MCP library not installed. Install with: pip install mcp")
            return {"error": "MCP library not installed"}
        except Exception as e:
            logger.error(f"Failed to call MCP tool '{name}': {e}")
            return {"error": str(e)}

    def to_openai_tool_schema(self, tool: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert MCP tool definition to OpenAI tool schema format.

        Args:
            tool: MCP tool definition

        Returns:
            OpenAI-compatible tool schema
        """
        return {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool.get("description", ""),
                "parameters": tool.get(
                    "input_schema",
                    {
                        "type": "object",
                        "properties": {},
                    },
                ),
            },
        }

    async def get_openai_tools(
        self, allowed_tools: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get tools in OpenAI schema format, optionally filtered by allowed list.

        Args:
            allowed_tools: List of tool names to include (None = all tools)

        Returns:
            List of OpenAI-compatible tool schemas
        """
        tools = await self.list_tools()

        # Filter by allowed tools if specified
        if allowed_tools:
            tools = [t for t in tools if t["name"] in allowed_tools]

        # Convert to OpenAI format
        return [self.to_openai_tool_schema(tool) for tool in tools]


# Convenience function to run async code from sync context
def sync_call_tool(
    client: MCPClient, name: str, arguments: Optional[Dict[str, Any]] = None
) -> Any:
    """
    Synchronous wrapper for calling MCP tools.

    Args:
        client: MCPClient instance
        name: Tool name
        arguments: Tool arguments

    Returns:
        Tool result
    """
    return asyncio.run(client.call_tool(name, arguments))


def sync_list_tools(client: MCPClient) -> List[Dict[str, Any]]:
    """
    Synchronous wrapper for listing MCP tools.

    Args:
        client: MCPClient instance

    Returns:
        List of tool definitions
    """
    return asyncio.run(client.list_tools())
