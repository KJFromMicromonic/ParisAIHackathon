"""WhatsApp API function tools for LiveKit agents."""

import json
from typing import Any, Dict, List, Optional

import httpx
from livekit.agents import llm
from livekit.agents.log import logger
from pydantic import BaseModel, Field

from app.core.config import settings


class SearchContactsRequest(BaseModel):
    """Request model for searching contacts."""

    query: str = Field(..., description="Search term to match against contact names or phone numbers")


class ListChatsRequest(BaseModel):
    """Request model for listing chats."""

    query: Optional[str] = Field(None, description="Search term to filter chats by name or JID")
    limit: int = Field(20, description="Maximum number of chats to return")
    page: int = Field(0, description="Page number for pagination")
    include_last_message: bool = Field(True, description="Whether to include the last message in each chat")
    sort_by: str = Field("last_active", description="Field to sort results by (last_active or name)")


class GetChatRequest(BaseModel):
    """Request model for getting a chat."""

    chat_jid: str = Field(..., description="The JID of the chat to retrieve")
    include_last_message: bool = Field(True, description="Whether to include the last message")


class GetDirectChatByContactRequest(BaseModel):
    """Request model for getting direct chat by contact."""

    sender_phone_number: str = Field(..., description="The phone number to search for")


class GetContactChatsRequest(BaseModel):
    """Request model for getting contact chats."""

    jid: str = Field(..., description="The contact's JID to search for")
    limit: int = Field(20, description="Maximum number of chats to return")
    page: int = Field(0, description="Page number for pagination")


class ListMessagesRequest(BaseModel):
    """Request model for listing messages."""

    after: Optional[str] = Field(None, description="ISO-8601 date string to only return messages after this date")
    before: Optional[str] = Field(None, description="ISO-8601 date string to only return messages before this date")
    sender_phone_number: Optional[str] = Field(None, description="Phone number to filter messages by sender")
    chat_jid: Optional[str] = Field(None, description="Chat JID to filter messages by chat")
    query: Optional[str] = Field(None, description="Search term to filter messages by content")
    limit: int = Field(20, description="Maximum number of messages to return")
    page: int = Field(0, description="Page number for pagination")
    include_context: bool = Field(True, description="Whether to include messages before and after matches")
    context_before: int = Field(1, description="Number of messages to include before each match")
    context_after: int = Field(1, description="Number of messages to include after each match")


class GetLastInteractionRequest(BaseModel):
    """Request model for getting last interaction."""

    jid: str = Field(..., description="The JID of the contact to search for")


class GetMessageContextRequest(BaseModel):
    """Request model for getting message context."""

    message_id: str = Field(..., description="The ID of the message to get context for")
    before: int = Field(5, description="Number of messages to include before the target message")
    after: int = Field(5, description="Number of messages to include after the target message")


class SendMessageRequest(BaseModel):
    """Request model for sending a message."""

    recipient: str = Field(
        ...,
        description="Phone number (with country code, no +) or JID (e.g., 123456789@s.whatsapp.net or 123456789@g.us for groups)",
    )
    message: str = Field(..., description="The message text to send")


class SendFileRequest(BaseModel):
    """Request model for sending a file."""

    recipient: str = Field(..., description="Phone number or JID")
    media_path: str = Field(..., description="Absolute path to the media file to send")


class SendAudioRequest(BaseModel):
    """Request model for sending an audio message."""

    recipient: str = Field(..., description="Phone number or JID")
    media_path: str = Field(..., description="Absolute path to the audio file to send")


class DownloadMediaRequest(BaseModel):
    """Request model for downloading media."""

    message_id: str = Field(..., description="The ID of the message containing the media")
    chat_jid: str = Field(..., description="The JID of the chat containing the message")


class WhatsAppAPIClient:
    """Client for interacting with the WhatsApp API."""

    def __init__(self, base_url: str, headers: Optional[Dict[str, str]] = None):
        """
        Initialize the WhatsApp API client.

        Args:
            base_url: Base URL of the WhatsApp API
            headers: Optional headers to include in requests
        """
        self._base_url = base_url.rstrip("/")
        self._headers = headers or {}
        self._http_client = httpx.AsyncClient(timeout=30.0, headers=self._headers)

    async def _make_request(
        self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            data: Request body data

        Returns:
            Response JSON data

        Raises:
            httpx.HTTPError: If the request fails
        """
        url = f"{self._base_url}{endpoint}"
        try:
            logger.debug(f"Making {method} request to {url} with data: {data}")
            if method == "GET":
                response = await self._http_client.get(url)
            elif method == "POST":
                response = await self._http_client.post(url, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            result = response.json()
            logger.debug(f"Response from {endpoint}: {result}")
            return result

        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error calling {endpoint}: {e.response.status_code} - {e.response.text}",
                exc_info=True,
            )
            raise
        except Exception as e:
            logger.error(f"Error calling {endpoint}: {e}", exc_info=True)
            raise

    async def search_contacts(self, query: str) -> Dict[str, Any]:
        """
        Search WhatsApp contacts by name or phone number.

        Args:
            query: Search term to match against contact names or phone numbers

        Returns:
            Response containing matching contacts
        """
        request_data = SearchContactsRequest(query=query)
        response = await self._make_request("POST", "/api/contacts/search", request_data.dict())
        return response

    async def list_chats(
        self,
        query: Optional[str] = None,
        limit: int = 20,
        page: int = 0,
        include_last_message: bool = True,
        sort_by: str = "last_active",
    ) -> Dict[str, Any]:
        """
        Get WhatsApp chats matching specified criteria.

        Args:
            query: Search term to filter chats by name or JID
            limit: Maximum number of chats to return
            page: Page number for pagination
            include_last_message: Whether to include the last message in each chat
            sort_by: Field to sort results by (last_active or name)

        Returns:
            Response containing paginated list of chats
        """
        request_data = ListChatsRequest(
            query=query,
            limit=limit,
            page=page,
            include_last_message=include_last_message,
            sort_by=sort_by,
        )
        response = await self._make_request("POST", "/api/chats/list", request_data.dict())
        return response

    async def get_chat(self, chat_jid: str, include_last_message: bool = True) -> Dict[str, Any]:
        """
        Get WhatsApp chat metadata by JID.

        Args:
            chat_jid: The JID of the chat to retrieve
            include_last_message: Whether to include the last message

        Returns:
            Response containing chat information
        """
        request_data = GetChatRequest(chat_jid=chat_jid, include_last_message=include_last_message)
        response = await self._make_request("POST", "/api/chats/get", request_data.dict())
        return response

    async def get_direct_chat_by_contact(self, sender_phone_number: str) -> Dict[str, Any]:
        """
        Get WhatsApp chat by contact phone number.

        Args:
            sender_phone_number: The phone number to search for

        Returns:
            Response containing chat information
        """
        request_data = GetDirectChatByContactRequest(sender_phone_number=sender_phone_number)
        response = await self._make_request("POST", "/api/chats/get_by_contact", request_data.dict())
        return response

    async def get_contact_chats(self, jid: str, limit: int = 20, page: int = 0) -> Dict[str, Any]:
        """
        Get all chats involving a specific contact.

        Args:
            jid: The contact's JID to search for
            limit: Maximum number of chats to return
            page: Page number for pagination

        Returns:
            Response containing both direct chats and group chats
        """
        request_data = GetContactChatsRequest(jid=jid, limit=limit, page=page)
        response = await self._make_request("POST", "/api/chats/by_contact", request_data.dict())
        return response

    async def list_messages(
        self,
        after: Optional[str] = None,
        before: Optional[str] = None,
        sender_phone_number: Optional[str] = None,
        chat_jid: Optional[str] = None,
        query: Optional[str] = None,
        limit: int = 20,
        page: int = 0,
        include_context: bool = True,
        context_before: int = 1,
        context_after: int = 1,
    ) -> Dict[str, Any]:
        """
        Get WhatsApp messages matching specified criteria with optional context.

        Args:
            after: ISO-8601 date string to only return messages after this date
            before: ISO-8601 date string to only return messages before this date
            sender_phone_number: Phone number to filter messages by sender
            chat_jid: Chat JID to filter messages by chat
            query: Search term to filter messages by content
            limit: Maximum number of messages to return
            page: Page number for pagination
            include_context: Whether to include messages before and after matches
            context_before: Number of messages to include before each match
            context_after: Number of messages to include after each match

        Returns:
            Response containing paginated results with optional surrounding message context
        """
        request_data = ListMessagesRequest(
            after=after,
            before=before,
            sender_phone_number=sender_phone_number,
            chat_jid=chat_jid,
            query=query,
            limit=limit,
            page=page,
            include_context=include_context,
            context_before=context_before,
            context_after=context_after,
        )
        response = await self._make_request("POST", "/api/messages/list", request_data.dict())
        return response

    async def get_last_interaction(self, jid: str) -> Dict[str, Any]:
        """
        Get most recent message with a contact.

        Args:
            jid: The JID of the contact to search for

        Returns:
            Response containing the latest message
        """
        request_data = GetLastInteractionRequest(jid=jid)
        response = await self._make_request("POST", "/api/messages/last_interaction", request_data.dict())
        return response

    async def get_message_context(
        self, message_id: str, before: int = 5, after: int = 5
    ) -> Dict[str, Any]:
        """
        Get context around a specific message.

        Args:
            message_id: The ID of the message to get context for
            before: Number of messages to include before the target message
            after: Number of messages to include after the target message

        Returns:
            Response containing the target message along with surrounding messages
        """
        request_data = GetMessageContextRequest(message_id=message_id, before=before, after=after)
        response = await self._make_request("POST", "/api/messages/context", request_data.dict())
        return response

    async def send_message(self, recipient: str, message: str) -> Dict[str, Any]:
        """
        Send a WhatsApp message to a person or group.

        Args:
            recipient: Phone number (with country code, no +) or JID
            message: The message text to send

        Returns:
            Response indicating success or failure
        """
        request_data = SendMessageRequest(recipient=recipient, message=message)
        response = await self._make_request("POST", "/api/send/message", request_data.dict())
        return response

    async def send_file(self, recipient: str, media_path: str) -> Dict[str, Any]:
        """
        Send a file (image, video, raw audio, document) via WhatsApp.

        Args:
            recipient: Phone number or JID
            media_path: Absolute path to the media file to send

        Returns:
            Response indicating success or failure
        """
        request_data = SendFileRequest(recipient=recipient, media_path=media_path)
        response = await self._make_request("POST", "/api/send/file", request_data.dict())
        return response

    async def send_audio(self, recipient: str, media_path: str) -> Dict[str, Any]:
        """
        Send an audio file as a WhatsApp voice message.

        Args:
            recipient: Phone number or JID
            media_path: Absolute path to the audio file to send (should be .ogg Opus format)

        Returns:
            Response indicating success or failure
        """
        request_data = SendAudioRequest(recipient=recipient, media_path=media_path)
        response = await self._make_request("POST", "/api/send/audio", request_data.dict())
        return response

    async def download_media(self, message_id: str, chat_jid: str) -> Dict[str, Any]:
        """
        Download media from a WhatsApp message.

        Args:
            message_id: The ID of the message containing the media
            chat_jid: The JID of the chat containing the message

        Returns:
            Response containing the local file path where the media was saved
        """
        request_data = DownloadMediaRequest(message_id=message_id, chat_jid=chat_jid)
        response = await self._make_request("POST", "/api/media/download", request_data.dict())
        return response

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._http_client.aclose()


# Global WhatsApp API client instance
_whatsapp_client: Optional[WhatsAppAPIClient] = None


def get_whatsapp_client() -> WhatsAppAPIClient:
    """
    Get or create the global WhatsApp API client instance.

    Returns:
        WhatsAppAPIClient instance
    """
    global _whatsapp_client
    if _whatsapp_client is None:
        base_url = settings.whatsapp_api_url
        headers = settings.get_whatsapp_api_headers()
        _whatsapp_client = WhatsAppAPIClient(base_url, headers)
    return _whatsapp_client


# Create function tools
def create_whatsapp_tools() -> List[llm.FunctionTool]:
    """
    Create LiveKit function tools for WhatsApp API.

    Returns:
        List of function tools for WhatsApp operations
    """
    logger.info("Creating WhatsApp function tools...")
    client = get_whatsapp_client()
    logger.info(f"WhatsApp API client initialized with base URL: {client._base_url}")

    @llm.function_tool()
    async def search_contacts(query: str) -> str:
        """
        Search WhatsApp contacts by name or phone number.

        Returns a list of matching contacts with their phone numbers, names, and JIDs.

        Args:
            query: Search term to match against contact names or phone numbers

        Returns:
            JSON string containing matching contacts
        """
        try:
            logger.info(f"Searching contacts with query: {query}")
            result = await client.search_contacts(query)
            logger.info(f"Search contacts result: {result}")
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"Error searching contacts: {e}", exc_info=True)
            return json.dumps({"error": str(e), "success": False})

    @llm.function_tool()
    async def list_chats(
        query: Optional[str] = None,
        limit: int = 20,
        page: int = 0,
        include_last_message: bool = True,
        sort_by: str = "last_active",
    ) -> str:
        """
        Get WhatsApp chats matching specified criteria. Use this to check for unread messages.

        Returns a paginated list of chats with metadata and optional last message.
        IMPORTANT: Check the response for unread_count or unread indicators to find new messages.

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
            result = await client.list_chats(query, limit, page, include_last_message, sort_by)
            # Handle both dict and list responses
            data = result.get('data', {})
            if isinstance(data, dict):
                chats = data.get('chats', [])
            elif isinstance(data, list):
                chats = data
            else:
                chats = []
            logger.info(f"Listed chats: {len(chats)} chats found")
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"Error listing chats: {e}", exc_info=True)
            return json.dumps({"error": str(e), "success": False})

    @llm.function_tool()
    async def get_chat(chat_jid: str, include_last_message: bool = True) -> str:
        """
        Get WhatsApp chat metadata by JID.

        Returns detailed information about a specific chat.

        Args:
            chat_jid: The JID of the chat to retrieve (e.g., 123456789@s.whatsapp.net or 123456789@g.us)
            include_last_message: Whether to include the last message (default: True)

        Returns:
            JSON string containing chat information
        """
        try:
            result = await client.get_chat(chat_jid, include_last_message)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"Error getting chat: {e}", exc_info=True)
            return json.dumps({"error": str(e), "success": False})

    @llm.function_tool()
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
            result = await client.get_direct_chat_by_contact(sender_phone_number)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"Error getting direct chat by contact: {e}", exc_info=True)
            return json.dumps({"error": str(e), "success": False})

    @llm.function_tool()
    async def get_contact_chats(jid: str, limit: int = 20, page: int = 0) -> str:
        """
        Get all chats involving a specific contact.

        Returns both direct chats and group chats where the contact is a member.

        Args:
            jid: The contact's JID to search for
            limit: Maximum number of chats to return (default: 20)
            page: Page number for pagination (default: 0)

        Returns:
            JSON string containing both direct chats and group chats
        """
        try:
            result = await client.get_contact_chats(jid, limit, page)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"Error getting contact chats: {e}", exc_info=True)
            return json.dumps({"error": str(e), "success": False})

    @llm.function_tool()
    async def list_messages(
        after: Optional[str] = None,
        before: Optional[str] = None,
        sender_phone_number: Optional[str] = None,
        chat_jid: Optional[str] = None,
        query: Optional[str] = None,
        limit: int = 20,
        page: int = 0,
        include_context: bool = True,
        context_before: int = 1,
        context_after: int = 1,
    ) -> str:
        """
        Get WhatsApp messages from a specific chat. Use this to read messages after finding chats with list_chats.

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
            if not chat_jid:
                return json.dumps({
                    "error": "chat_jid is required. First call list_chats to get chat_jid values.",
                    "success": False
                })
            result = await client.list_messages(
                after,
                before,
                sender_phone_number,
                chat_jid,
                query,
                limit,
                page,
                include_context,
                context_before,
                context_after,
            )
            # Handle both dict and list responses
            data = result.get('data', {})
            if isinstance(data, dict):
                messages = data.get('messages', [])
            elif isinstance(data, list):
                messages = data
            else:
                messages = []
            logger.info(f"Listed messages for chat {chat_jid}: {len(messages)} messages found")
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"Error listing messages: {e}", exc_info=True)
            return json.dumps({"error": str(e), "success": False})

    @llm.function_tool()
    async def get_last_interaction(jid: str) -> str:
        """
        Get most recent message with a contact.

        Returns the latest message in the conversation with the specified contact.

        Args:
            jid: The JID of the contact to search for

        Returns:
            JSON string containing the latest message
        """
        try:
            result = await client.get_last_interaction(jid)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"Error getting last interaction: {e}", exc_info=True)
            return json.dumps({"error": str(e), "success": False})

    @llm.function_tool()
    async def get_message_context(message_id: str, before: int = 5, after: int = 5) -> str:
        """
        Get context around a specific message.

        Returns the target message along with surrounding messages for context.

        Args:
            message_id: The ID of the message to get context for
            before: Number of messages to include before the target message (default: 5)
            after: Number of messages to include after the target message (default: 5)

        Returns:
            JSON string containing the target message along with surrounding messages
        """
        try:
            result = await client.get_message_context(message_id, before, after)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"Error getting message context: {e}", exc_info=True)
            return json.dumps({"error": str(e), "success": False})

    @llm.function_tool()
    async def send_message(recipient: str, message: str) -> str:
        """
        Send a WhatsApp message to a person or group.

        Supports sending to:
        - Phone numbers (with country code, no + or symbols)
        - Direct chat JIDs (e.g., 123456789@s.whatsapp.net)
        - Group JIDs (e.g., 123456789@g.us)

        Args:
            recipient: Phone number or JID
            message: The message text to send

        Returns:
            JSON string indicating success or failure
        """
        try:
            result = await client.send_message(recipient, message)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"Error sending message: {e}", exc_info=True)
            return json.dumps({"error": str(e), "success": False})

    @llm.function_tool()
    async def send_file(recipient: str, media_path: str) -> str:
        """
        Send a file (image, video, raw audio, document) via WhatsApp.

        The file must exist at the specified absolute path.

        Args:
            recipient: Phone number or JID
            media_path: Absolute path to the media file to send

        Returns:
            JSON string indicating success or failure
        """
        try:
            result = await client.send_file(recipient, media_path)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"Error sending file: {e}", exc_info=True)
            return json.dumps({"error": str(e), "success": False})

    @llm.function_tool()
    async def send_audio(recipient: str, media_path: str) -> str:
        """
        Send an audio file as a WhatsApp voice message.

        Audio files should be in .ogg Opus format for best compatibility.
        If FFmpeg is installed, other formats will be automatically converted.

        Args:
            recipient: Phone number or JID
            media_path: Absolute path to the audio file to send

        Returns:
            JSON string indicating success or failure
        """
        try:
            result = await client.send_audio(recipient, media_path)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"Error sending audio: {e}", exc_info=True)
            return json.dumps({"error": str(e), "success": False})

    @llm.function_tool()
    async def download_media(message_id: str, chat_jid: str) -> str:
        """
        Download media from a WhatsApp message.

        Returns the local file path where the media was saved.

        Args:
            message_id: The ID of the message containing the media
            chat_jid: The JID of the chat containing the message

        Returns:
            JSON string containing the local file path where the media was saved
        """
        try:
            result = await client.download_media(message_id, chat_jid)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"Error downloading media: {e}", exc_info=True)
            return json.dumps({"error": str(e), "success": False})

    tools = [
        search_contacts,
        list_chats,
        get_chat,
        get_direct_chat_by_contact,
        get_contact_chats,
        list_messages,
        get_last_interaction,
        get_message_context,
        send_message,
        send_file,
        send_audio,
        download_media,
    ]
    
    logger.info(f"Created {len(tools)} WhatsApp function tools: {[tool.__name__ for tool in tools]}")
    return tools

