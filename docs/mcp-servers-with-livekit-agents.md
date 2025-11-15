# Using MCP Servers with LiveKit Agents

## Overview

LiveKit Agents has full support for [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) servers to load tools from external sources. MCP is an open standard for integrating AI systems with external tools and data sources, allowing your agents to access and interact with various external services.

This is particularly useful for building applications that need to:
- Access external APIs (like Google Maps, Airbnb, etc.)
- Integrate with databases or other data sources
- Use tools provided by third-party services
- Build modular, extensible agent systems

## Installation

To use MCP servers with LiveKit Agents, first install the `mcp` optional dependencies:

```shell
uv add livekit-agents[mcp]~=1.2
```

## Basic Usage

### Using MCP Servers with AgentSession

Pass the MCP server URL to the `AgentSession` constructor. The tools will be automatically loaded like any other tool:

```python
from livekit.agents import AgentSession, mcp

session = AgentSession(
    llm="openai/gpt-4o",
    tts="elevenlabs/eleven_multilingual_v2",
    stt="deepgram/nova-2",
    mcp_servers=[
        mcp.MCPServerHTTP("https://your-mcp-server.com")
    ]
)
```

### Using MCP Servers with Agent Class

You can also pass MCP servers directly to the `Agent` class:

```python
from livekit.agents import Agent, mcp

agent = Agent(
    instructions="You are a helpful assistant that can access external services.",
    llm="openai/gpt-4o",
    tts="elevenlabs/eleven_multilingual_v2",
    stt="deepgram/nova-2",
    mcp_servers=[
        mcp.MCPServerHTTP("https://your-mcp-server.com")
    ]
)
```

## Setting Up Your Own MCP Server

### MCP Server Requirements

Your MCP server must:
1. Be accessible via HTTP/HTTPS
2. Implement the MCP protocol specification
3. Expose tools that follow the MCP tool schema
4. Handle authentication if required

### Example: Google Maps MCP Server

For your use case of helping blind/visually impaired users find places, you might create a Google Maps MCP server that exposes tools like:

- `search_nearby_places`: Search for places near a location
- `get_directions`: Get directions between two points
- `get_place_details`: Get detailed information about a place

### Example: Airbnb MCP Server

For booking Airbnb properties, your MCP server might expose:

- `search_properties`: Search for available properties
- `get_property_details`: Get details about a specific property
- `book_property`: Book a property (with proper authentication)

## Integration with Gemini Live Realtime Models

When using Gemini Live realtime models with MCP servers, the tools are automatically available to the model:

```python
from livekit.agents import AgentSession, mcp
from livekit.plugins import google

session = AgentSession(
    llm=google.realtime.RealtimeModel(
        model="gemini-2.0-flash-exp",
        voice="Puck",
        instructions="You are a helpful assistant for visually impaired users. You can help them find places, get directions, and book accommodations."
    ),
    mcp_servers=[
        mcp.MCPServerHTTP("https://your-google-maps-mcp-server.com"),
        mcp.MCPServerHTTP("https://your-airbnb-mcp-server.com")
    ]
)
```

The Gemini Live model will automatically have access to all tools exposed by your MCP servers and can call them during conversations.

## Tool Definition in MCP Servers

Your MCP server should expose tools following this schema:

```json
{
  "name": "tool_name",
  "description": "What the tool does",
  "inputSchema": {
    "type": "object",
    "properties": {
      "param1": {
        "type": "string",
        "description": "Description of param1"
      },
      "param2": {
        "type": "number",
        "description": "Description of param2"
      }
    },
    "required": ["param1"]
  }
}
```

## Error Handling

When MCP tools are called, errors should be handled gracefully:

```python
from livekit.agents import ToolError

# In your MCP server tool implementation
try:
    result = perform_action()
    return result
except Exception as e:
    raise ToolError(f"Failed to perform action: {str(e)}")
```

## Authentication

If your MCP servers require authentication, you can pass credentials:

```python
mcp_servers=[
    mcp.MCPServerHTTP(
        "https://your-mcp-server.com",
        headers={
            "Authorization": "Bearer YOUR_API_KEY"
        }
    )
]
```

## Best Practices

1. **Tool Descriptions**: Write clear, specific descriptions for each tool. The LLM uses these to decide when to call tools.

2. **Error Messages**: Provide helpful error messages that guide the LLM (and ultimately the user) on how to recover.

3. **Response Format**: Return structured data that the LLM can easily interpret and communicate to users.

4. **Rate Limiting**: Implement rate limiting in your MCP servers to prevent abuse.

5. **Caching**: Consider caching frequently accessed data to reduce API calls.

6. **User Feedback**: For long-running operations, provide feedback to users through the agent's speech capabilities.

## Example: Complete Agent with MCP Servers

```python
from livekit import agents
from livekit.agents import AgentSession, mcp
from livekit.plugins import google

async def entrypoint(ctx: agents.JobContext):
    await ctx.connect()
    
    session = AgentSession(
        llm=google.realtime.RealtimeModel(
            model="gemini-2.0-flash-exp",
            voice="Puck",
            instructions="""You are a helpful assistant for visually impaired users. 
            You can help them:
            - Find nearby places using Google Maps
            - Get directions to locations
            - Search and book Airbnb properties
            Always speak clearly and provide detailed descriptions."""
        ),
        mcp_servers=[
            mcp.MCPServerHTTP(
                "https://your-google-maps-mcp-server.com",
                headers={"Authorization": f"Bearer {GOOGLE_MAPS_API_KEY}"}
            ),
            mcp.MCPServerHTTP(
                "https://your-airbnb-mcp-server.com",
                headers={"Authorization": f"Bearer {AIRBNB_API_KEY}"}
            )
        ]
    )
    
    await session.start(ctx.room)

if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
```

## MCP Server Transport Types

LiveKit Agents supports two types of MCP server transports:

### HTTP/SSE Transport

For HTTP-based MCP servers using Server-Sent Events (SSE):

```python
mcp.MCPServerHTTP("https://your-mcp-server.com/sse")
```

### Stdio Transport

For stdio-based MCP servers (useful for local development):

```python
mcp.MCPServerStdio(
    command="npx",
    args=["-y", "your-mcp-server"],
    cwd="/path/to/working/directory"
)
```

## Additional Resources

- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [LiveKit Agents Tools Documentation](https://docs.livekit.io/agents/build/tools/)
- [MCP Agent Example](https://github.com/livekit-examples/python-agents-examples/tree/main/mcp)
- [Voice MCP Agent Example](https://github.com/den-vasyliev/voice-mcp-agent)
- [Using MCP with LiveKit Agents (KB Article)](https://kb.livekit.io/articles/2746379221-using-mcp-with-livekit-agents)

## Notes

- MCP server support is currently only available in Python
- Tools from MCP servers are loaded automatically and work alongside any tools defined directly in your agent
- The LLM will automatically decide when to call MCP tools based on the conversation context
- You can use multiple MCP servers simultaneously
- For HTTP/SSE servers, ensure your server supports CORS if accessing from web clients
