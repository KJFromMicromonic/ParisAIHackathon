"""WhatsApp MCP Server implementation that wraps the REST API using FastMCP."""

import json
from typing import Any, Optional

import httpx
from mcp.server.fastmcp import FastMCP

from app.core.config import settings

# Create FastMCP server instance
mcp = FastMCP(
    name="WhatsApp MCP Server",
    instructions="WhatsApp API integration for voice assistants. Provides tools to search contacts, list chats, read messages, and send messages via WhatsApp.",
)

# Initialize HTTP client for WhatsApp API
_whatsapp_client: Optional[httpx.AsyncClient] = None


def get_whatsapp_client() -> httpx.AsyncClient:
    """
    Get or create WhatsApp API HTTP client instance.

    Returns:
        HTTP client instance configured for WhatsApp API
    """
    global _whatsapp_client
    if _whatsapp_client is None:
        base_url = settings.whatsapp_api_url
        headers = settings.get_whatsapp_api_headers()
        _whatsapp_client = httpx.AsyncClient(
            base_url=base_url,
            headers=headers,
            timeout=30.0,
        )
    return _whatsapp_client


# Map MCP tool names to REST API endpoints
ENDPOINT_MAP = {
    "search_contacts": "/api/contacts/search",
    "list_chats": "/api/chats/list",
    "get_chat": "/api/chats/get",
    "get_direct_chat_by_contact": "/api/chats/get_by_contact",
    "get_contact_chats": "/api/chats/by_contact",
    "list_messages": "/api/messages/list",
    "get_last_interaction": "/api/messages/last_interaction",
    "get_message_context": "/api/messages/context",
    "send_message": "/api/send/message",
    "send_file": "/api/send/file",
    "send_audio": "/api/send/audio",
    "download_media": "/api/media/download",
}


async def _call_whatsapp_api(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """
    Call WhatsApp REST API endpoint.

    Args:
        tool_name: Name of the tool/endpoint
        arguments: Request arguments

    Returns:
        API response data
    """
    client = get_whatsapp_client()
    endpoint = ENDPOINT_MAP.get(tool_name)
    if not endpoint:
        raise ValueError(f"Unknown tool: {tool_name}")

    response = await client.post(endpoint, json=arguments)
    response.raise_for_status()
    return response.json()


# Define MCP tools using FastMCP decorators
@mcp.tool()
async def search_contacts(query: str) -> str:
    """
    Search WhatsApp contacts by name or phone number.

    Returns a list of matching contacts with their phone numbers, names, and JIDs.

    Args:
        query: Search term to match against contact names or phone numbers

    Returns:
        JSON string containing list of matching contacts
    """
    try:
        result = await _call_whatsapp_api("search_contacts", {"query": query})
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "success": False})


@mcp.tool()
async def list_chats(
    query: Optional[str] = None,
    limit: int = 20,
    page: int = 0,
    include_last_message: bool = True,
    sort_by: str = "last_active",
) -> str:
    """
    Get WhatsApp chats matching specified criteria.

    Returns a paginated list of chats with metadata and optional last message.
    Use this to check for unread messages.

    Args:
        query: Search term to filter chats by name or JID (optional)
        limit: Maximum number of chats to return (default: 20)
        page: Page number for pagination (default: 0)
        include_last_message: Whether to include the last message in each chat (default: True)
        sort_by: Field to sort results by - 'last_active' or 'name' (default: 'last_active')

    Returns:
        JSON string containing paginated list of chats. Look for unread_count fields to identify unread messages.
    """
    try:
        args = {
            "limit": limit,
            "page": page,
            "include_last_message": include_last_message,
            "sort_by": sort_by,
        }
        if query:
            args["query"] = query
        result = await _call_whatsapp_api("list_chats", args)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "success": False})


@mcp.tool()
async def get_chat(chat_jid: str, include_last_message: bool = True) -> str:
    """
    Get WhatsApp chat metadata by JID.

    Returns detailed information about a specific chat.

    Args:
        chat_jid: The JID of the chat to retrieve (e.g., 123456789@s.whatsapp.net or 123456789@g.us)
        include_last_message: Whether to include the last message (default: True)

    Returns:
        JSON string containing chat metadata
    """
    try:
        result = await _call_whatsapp_api(
            "get_chat", {"chat_jid": chat_jid, "include_last_message": include_last_message}
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "success": False})


@mcp.tool()
async def get_direct_chat_by_contact(sender_phone_number: str) -> str:
    """
    Get WhatsApp chat by contact phone number.

    Finds the direct chat with a specific contact using their phone number.

    Args:
        sender_phone_number: The phone number to search for (with country code, no + or symbols)

    Returns:
        JSON string containing chat information
    """
    try:
        result = await _call_whatsapp_api(
            "get_direct_chat_by_contact", {"sender_phone_number": sender_phone_number}
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "success": False})


@mcp.tool()
async def get_contact_chats(jid: str, limit: int = 20, page: int = 0) -> str:
    """
    Get all chats involving a specific contact.

    Returns both direct chats and group chats where the contact is a member.

    Args:
        jid: The contact's JID to search for
        limit: Maximum number of chats to return (default: 20)
        page: Page number for pagination (default: 0)

    Returns:
        JSON string containing list of chats
    """
    try:
        result = await _call_whatsapp_api(
            "get_contact_chats", {"jid": jid, "limit": limit, "page": page}
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "success": False})


@mcp.tool()
async def list_messages(
    chat_jid: str,
    after: Optional[str] = None,
    before: Optional[str] = None,
    sender_phone_number: Optional[str] = None,
    query: Optional[str] = None,
    limit: int = 20,
    page: int = 0,
    include_context: bool = True,
    context_before: int = 1,
    context_after: int = 1,
) -> str:
    """
    Get WhatsApp messages from a specific chat.

    Supports filtering by date, sender, chat, and content search.
    Returns paginated results with optional surrounding message context.
    IMPORTANT: Use chat_jid parameter to read messages from a specific chat.

    Args:
        chat_jid: REQUIRED - Chat JID to filter messages by chat (e.g., 123456789@s.whatsapp.net)
        after: ISO-8601 date string to only return messages after this date (optional)
        before: ISO-8601 date string to only return messages before this date (optional)
        sender_phone_number: Phone number to filter messages by sender (optional)
        query: Search term to filter messages by content (optional)
        limit: Maximum number of messages to return (default: 20)
        page: Page number for pagination (default: 0)
        include_context: Whether to include messages before and after matches (default: True)
        context_before: Number of messages to include before each match (default: 1)
        context_after: Number of messages to include after each match (default: 1)

    Returns:
        JSON string containing paginated results with optional surrounding message context
    """
    try:
        args = {
            "chat_jid": chat_jid,
            "limit": limit,
            "page": page,
            "include_context": include_context,
            "context_before": context_before,
            "context_after": context_after,
        }
        if after:
            args["after"] = after
        if before:
            args["before"] = before
        if sender_phone_number:
            args["sender_phone_number"] = sender_phone_number
        if query:
            args["query"] = query
        result = await _call_whatsapp_api("list_messages", args)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "success": False})


@mcp.tool()
async def get_last_interaction(jid: str) -> str:
    """
    Get most recent message with a contact.

    Returns the latest message in the conversation with the specified contact.

    Args:
        jid: The JID of the contact to search for

    Returns:
        JSON string containing the last interaction
    """
    try:
        result = await _call_whatsapp_api("get_last_interaction", {"jid": jid})
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "success": False})


@mcp.tool()
async def get_message_context(message_id: str, before: int = 5, after: int = 5) -> str:
    """
    Get context around a specific message.

    Returns the target message along with surrounding messages for context.

    Args:
        message_id: The ID of the message to get context for
        before: Number of messages to include before the target message (default: 5)
        after: Number of messages to include after the target message (default: 5)

    Returns:
        JSON string containing message context
    """
    try:
        result = await _call_whatsapp_api(
            "get_message_context", {"message_id": message_id, "before": before, "after": after}
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "success": False})


@mcp.tool()
async def send_message(recipient: str, message: str) -> str:
    """
    Send a WhatsApp message to a person or group.

    Supports sending to phone numbers (with country code, no +) or JIDs
    (e.g., 123456789@s.whatsapp.net or 123456789@g.us for groups).

    Args:
        recipient: Phone number or JID
        message: The message text to send

    Returns:
        JSON string containing send result
    """
    try:
        result = await _call_whatsapp_api("send_message", {"recipient": recipient, "message": message})
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "success": False})


@mcp.tool()
async def send_file(recipient: str, media_path: str) -> str:
    """
    Send a file (image, video, raw audio, document) via WhatsApp.

    The file must exist at the specified absolute path.

    Args:
        recipient: Phone number or JID
        media_path: Absolute path to the media file to send

    Returns:
        JSON string containing send result
    """
    try:
        result = await _call_whatsapp_api("send_file", {"recipient": recipient, "media_path": media_path})
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "success": False})


@mcp.tool()
async def send_audio(recipient: str, media_path: str) -> str:
    """
    Send an audio file as a WhatsApp voice message.

    Audio files should be in .ogg Opus format for best compatibility.
    If FFmpeg is installed, other formats will be automatically converted.

    Args:
        recipient: Phone number or JID
        media_path: Absolute path to the audio file to send

    Returns:
        JSON string containing send result
    """
    try:
        result = await _call_whatsapp_api("send_audio", {"recipient": recipient, "media_path": media_path})
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "success": False})


@mcp.tool()
async def download_media(message_id: str, chat_jid: str) -> str:
    """
    Download media from a WhatsApp message.

    Returns the local file path where the media was saved.

    Args:
        message_id: The ID of the message containing the media
        chat_jid: The JID of the chat containing the message

    Returns:
        JSON string containing download result with file path
    """
    try:
        result = await _call_whatsapp_api(
            "download_media", {"message_id": message_id, "chat_jid": chat_jid}
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "success": False})


# Export ASGI app for uvicorn
# FastMCP provides streamable_http_app() method for streamable-http transport
app = mcp.streamable_http_app()
