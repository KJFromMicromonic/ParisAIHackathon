"""MCP protocol schemas for tool definitions and requests."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MCPToolInputSchema(BaseModel):
    """MCP tool input schema definition."""

    type: str = Field(default="object", description="Schema type")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Schema properties")
    required: List[str] = Field(default_factory=list, description="Required properties")


class MCPTool(BaseModel):
    """MCP tool definition."""

    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    inputSchema: MCPToolInputSchema = Field(..., description="Input schema")


class MCPToolsResponse(BaseModel):
    """Response from MCP server listing tools."""

    tools: List[MCPTool] = Field(default_factory=list, description="List of available tools")


class MCPToolCallRequest(BaseModel):
    """Request to call an MCP tool."""

    name: str = Field(..., description="Tool name to call")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Tool arguments")


class MCPToolCallResponse(BaseModel):
    """Response from MCP tool call."""

    content: List[Dict[str, Any]] = Field(
        default_factory=list, description="Tool call response content"
    )
    isError: bool = Field(default=False, description="Whether the response is an error")


class MCPServerConfig(BaseModel):
    """Configuration for an MCP server."""

    url: str = Field(..., description="MCP server URL")
    headers: Dict[str, str] = Field(default_factory=dict, description="HTTP headers for requests")

