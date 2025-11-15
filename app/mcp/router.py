"""MCP (Model Context Protocol) router for tool call routing."""

import json
from typing import Any, Dict, List, Optional

import httpx
from livekit.agents.log import logger

from app.core.config import settings
from app.mcp.schemas import (
    MCPServerConfig,
    MCPTool,
    MCPToolCallRequest,
    MCPToolCallResponse,
    MCPToolsResponse,
)


class MCPRouter:
    """Router for calling MCP servers and managing tool calls."""

    def __init__(self, server_configs: Optional[List[MCPServerConfig]] = None):
        """
        Initialize the MCP router.

        Args:
            server_configs: List of MCP server configurations. If None, loads from settings.
        """
        if server_configs is None:
            server_configs = self._load_configs_from_settings()

        self._server_configs = {config.url: config for config in server_configs}
        self._http_client = httpx.AsyncClient(timeout=30.0)
        self._tools_cache: Dict[str, List[MCPTool]] = {}

    def _load_configs_from_settings(self) -> List[MCPServerConfig]:
        """
        Load MCP server configurations from settings.

        Returns:
            List of MCP server configurations
        """
        configs = []
        urls = settings.get_mcp_server_urls()
        headers_map = settings.get_mcp_server_headers()

        for url in urls:
            headers = headers_map.get(url, {})
            configs.append(MCPServerConfig(url=url, headers=headers))

        return configs

    async def list_tools(self, server_url: Optional[str] = None) -> List[MCPTool]:
        """
        List available tools from MCP server(s).

        Args:
            server_url: Specific server URL to query. If None, queries all servers.

        Returns:
            List of available tools
        """
        if server_url:
            servers = [server_url] if server_url in self._server_configs else []
        else:
            servers = list(self._server_configs.keys())

        all_tools = []
        for url in servers:
            try:
                # Check cache first
                if url in self._tools_cache:
                    all_tools.extend(self._tools_cache[url])
                    continue

                # Fetch tools from server
                config = self._server_configs[url]
                response = await self._http_client.get(
                    f"{url}/tools",
                    headers=config.headers,
                )
                response.raise_for_status()

                data = response.json()
                tools_response = MCPToolsResponse(**data)
                self._tools_cache[url] = tools_response.tools
                all_tools.extend(tools_response.tools)

                logger.debug(
                    f"Loaded {len(tools_response.tools)} tools from {url}",
                    extra={"server_url": url, "tool_count": len(tools_response.tools)},
                )

            except Exception as e:
                logger.error(
                    f"Error listing tools from {url}: {e}",
                    exc_info=True,
                    extra={"server_url": url},
                )

        return all_tools

    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        server_url: Optional[str] = None,
    ) -> MCPToolCallResponse:
        """
        Call an MCP tool.

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            server_url: Specific server URL to call. If None, tries all servers.

        Returns:
            Tool call response

        Raises:
            ValueError: If tool is not found or call fails
        """
        if server_url:
            servers = [server_url] if server_url in self._server_configs else []
        else:
            servers = list(self._server_configs.keys())

        # Try each server until we find the tool
        for url in servers:
            try:
                config = self._server_configs[url]
                request_data = MCPToolCallRequest(name=tool_name, arguments=arguments)

                response = await self._http_client.post(
                    f"{url}/tools/{tool_name}",
                    json=request_data.dict(),
                    headers={**config.headers, "Content-Type": "application/json"},
                )
                response.raise_for_status()

                data = response.json()
                tool_response = MCPToolCallResponse(**data)

                logger.debug(
                    f"Successfully called tool {tool_name} on {url}",
                    extra={"tool_name": tool_name, "server_url": url},
                )

                return tool_response

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    # Tool not found on this server, try next
                    continue
                raise ValueError(f"HTTP error calling tool {tool_name}: {e}")

            except Exception as e:
                logger.error(
                    f"Error calling tool {tool_name} on {url}: {e}",
                    exc_info=True,
                    extra={"tool_name": tool_name, "server_url": url},
                )
                # Continue to next server
                continue

        raise ValueError(f"Tool {tool_name} not found on any MCP server")

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._http_client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# Global router instance
_router: Optional[MCPRouter] = None


def get_mcp_router() -> MCPRouter:
    """
    Get or create the global MCP router instance.

    Returns:
        MCPRouter instance
    """
    global _router
    if _router is None:
        _router = MCPRouter()
    return _router

