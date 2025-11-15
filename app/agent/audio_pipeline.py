"""Audio pipeline wrapper around AgentSession with Live Video input."""

import asyncio
import atexit
import os
from pathlib import Path
from typing import Optional

import livekit.rtc as rtc
from google.genai.types import Modality
from livekit.agents import AgentSession, RoomInputOptions, mcp
from livekit.agents.log import logger
from livekit.plugins import google, silero

from app.core.config import settings
from app.services.elevenlabs import create_tts
from app.services.voxstral import create_stt


class AudioPipeline:
    """
    Audio pipeline wrapper around LiveKit AgentSession with Live Video input.
    
    This pipeline uses Gemini Live Realtime with native video input enabled,
    allowing the model to see and understand video frames automatically.
    
    The pipeline is configured to use Gemini Live for text generation only,
    with ElevenLabs TTS handling all audio output for natural voice synthesis.
    """

    def __init__(self, room: rtc.Room):
        """
        Initialize the audio pipeline.

        Args:
            room: LiveKit room instance
        """
        self._room = room
        self._session: Optional[AgentSession] = None
        self._whatsapp_server_process: Optional[asyncio.subprocess.Process] = None

    async def start(self) -> None:
        """Start the audio pipeline with Live Video input enabled."""
        if self._session is not None:
            logger.warning("Audio pipeline is already started")
            return

        try:
            # Start WhatsApp MCP server wrapper if enabled
            await self._start_whatsapp_mcp_server()

            # Create MCP server configurations
            mcp_servers = self._create_mcp_servers()

            # Create STT instance
            stt = create_stt()

            # Create VAD instance for streaming STT support
            # Mistral STT doesn't support streaming, so we need VAD
            vad_instance = silero.VAD.load()

            # Create LLM instance (Gemini Live Realtime with video support)
            # Configure to output text only so ElevenLabs TTS handles audio output
            llm = google.realtime.RealtimeModel(
                model=settings.gemini_model,
                modalities=[Modality.TEXT],  # Text-only output, ElevenLabs TTS handles audio
                instructions=self._get_agent_instructions(),
            )

            # Create TTS instance
            tts = create_tts()

            # Create Agent (tools come from MCP servers automatically)
            from livekit.agents import Agent
            agent = Agent(
                instructions=self._get_agent_instructions(),
            )

            # Create AgentSession with VAD for streaming STT support
            self._session = AgentSession(
                llm=llm,
                stt=stt,
                vad=vad_instance,  # Add VAD for streaming STT support
                tts=tts,
                mcp_servers=mcp_servers if mcp_servers else None,
            )

            # Start the session with Live Video input enabled
            # This allows Gemini Live to automatically receive and process video frames
            await self._session.start(
                agent=agent,
                room=self._room,
                room_input_options=RoomInputOptions(
                    video_enabled=True,  # Enable native video input for Gemini Live
                    # Video frames are automatically sampled:
                    # - 1 frame/second while user speaks
                    # - 1 frame every 3 seconds otherwise
                    # - Frames are fit into 1024x1024 and encoded to JPEG
                ),
            )

            logger.info("Audio pipeline started with Live Video input enabled")

        except Exception as e:
            logger.error(f"Error starting audio pipeline: {e}", exc_info=True)
            raise

    async def stop(self) -> None:
        """Stop the audio pipeline."""
        if self._session is None:
            return

        try:
            await self._session.aclose()
            self._session = None
            logger.info("Audio pipeline stopped")

            # Stop WhatsApp MCP server wrapper
            await self._stop_whatsapp_mcp_server()

        except Exception as e:
            logger.error(f"Error stopping audio pipeline: {e}", exc_info=True)

    async def _start_whatsapp_mcp_server(self) -> None:
        """
        Start local WhatsApp MCP server wrapper if enabled.

        The wrapper implements MCP protocol and translates calls to the REST API.
        """
        if not settings.whatsapp_mcp_server_enabled:
            logger.debug("WhatsApp MCP server wrapper is disabled")
            return

        try:
            import sys

            # Get path to WhatsApp MCP server run script
            script_path = Path(__file__).parent.parent / "scripts" / "run_whatsapp_mcp.py"
            if not script_path.exists():
                logger.warning(f"WhatsApp MCP server script not found: {script_path}")
                return

            # Start FastMCP server in background using streamable-http transport
            # Use the run script to start the server
            port = settings.whatsapp_mcp_server_port
            
            env = os.environ.copy()
            env["WHATSAPP_MCP_SERVER_PORT"] = str(port)
            env["WHATSAPP_MCP_SERVER_HOST"] = "127.0.0.1"
            
            logger.info(f"Starting WhatsApp MCP server on port {port}...")
            self._whatsapp_server_process = await asyncio.create_subprocess_exec(
                sys.executable,
                str(script_path),
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Wait for server to start and verify it's running
            max_wait_time = 10  # Wait up to 10 seconds
            check_interval = 0.5  # Check every 0.5 seconds
            waited = 0
            
            while waited < max_wait_time:
                await asyncio.sleep(check_interval)
                waited += check_interval
                
                # Check if process crashed
                if self._whatsapp_server_process.returncode is not None:
                    # Read stderr to see what went wrong
                    stderr_output = await self._whatsapp_server_process.stderr.read()
                    error_msg = stderr_output.decode() if stderr_output else "Unknown error"
                    logger.error(
                        f"WhatsApp MCP server failed to start (exit code: {self._whatsapp_server_process.returncode})\n"
                        f"Error output: {error_msg}"
                    )
                    self._whatsapp_server_process = None
                    return
                
                # Try to connect to verify server is ready
                try:
                    import httpx
                    async with httpx.AsyncClient(timeout=1.0) as client:
                        # FastMCP streamable-http exposes /mcp endpoint
                        response = await client.get(f"http://127.0.0.1:{port}/mcp")
                        if response.status_code in (200, 405):  # 405 Method Not Allowed is OK for GET
                            logger.info(
                                f"WhatsApp MCP server wrapper started successfully on http://127.0.0.1:{port}/mcp"
                            )
                            # Register cleanup on exit
                            atexit.register(self._cleanup_whatsapp_server)
                            return
                except (httpx.ConnectError, httpx.TimeoutException):
                    # Server not ready yet, continue waiting
                    continue
                except Exception as e:
                    logger.debug(f"Health check error (server may still be starting): {e}")
                    continue
            
            # If we get here, server didn't start in time
            logger.error(
                f"WhatsApp MCP server did not become ready within {max_wait_time} seconds"
            )
            if self._whatsapp_server_process:
                self._whatsapp_server_process.terminate()
                self._whatsapp_server_process = None

        except Exception as e:
            logger.error(
                f"Failed to start WhatsApp MCP server wrapper: {e}",
                exc_info=True,
            )

    async def _stop_whatsapp_mcp_server(self) -> None:
        """Stop the WhatsApp MCP server wrapper."""
        if self._whatsapp_server_process:
            try:
                self._whatsapp_server_process.terminate()
                await asyncio.wait_for(self._whatsapp_server_process.wait(), timeout=5.0)
                logger.info("WhatsApp MCP server wrapper stopped")
            except asyncio.TimeoutError:
                logger.warning("WhatsApp MCP server wrapper did not stop gracefully, killing")
                self._whatsapp_server_process.kill()
                await self._whatsapp_server_process.wait()
            except Exception as e:
                logger.error(f"Error stopping WhatsApp MCP server: {e}", exc_info=True)
            finally:
                self._whatsapp_server_process = None

    def _cleanup_whatsapp_server(self) -> None:
        """Cleanup function for atexit."""
        if self._whatsapp_server_process:
            try:
                self._whatsapp_server_process.terminate()
            except Exception:
                pass

    def _create_mcp_servers(self) -> list[mcp.MCPServerHTTP]:
        """
        Create MCP server instances from settings.

        Includes local WhatsApp MCP server wrapper if enabled, following the recommended MCP integration pattern.
        MCP servers are automatically loaded and tools are made available to the agent.

        Returns:
            List of MCP server instances
        """
        servers = []
        urls = settings.get_mcp_server_urls()
        headers_map = settings.get_mcp_server_headers()

        # Add configured MCP servers from MCP_SERVER_URLS
        for url in urls:
            if not url or url.strip() == "":
                continue
            try:
                headers = headers_map.get(url, {})
                servers.append(mcp.MCPServerHTTP(url, headers=headers))
                logger.debug(f"Added MCP server: {url}")
            except Exception as e:
                logger.warning(
                    f"Failed to create MCP server for {url}: {e}",
                    exc_info=True,
                )

        # Add local WhatsApp MCP server wrapper if enabled
        # FastMCP uses streamable-http transport, so URL should end with /mcp
        if settings.whatsapp_mcp_server_enabled:
            whatsapp_mcp_url = f"http://127.0.0.1:{settings.whatsapp_mcp_server_port}/mcp"
            try:
                servers.append(mcp.MCPServerHTTP(whatsapp_mcp_url))
                logger.info(
                    f"Added WhatsApp MCP server wrapper: {whatsapp_mcp_url}"
                )
            except Exception as e:
                logger.warning(
                    f"Failed to add WhatsApp MCP server wrapper: {e}",
                    exc_info=True,
                )

        logger.info(
            f"Created {len(servers)} MCP server connection(s)",
            extra={"mcp_server_count": len(servers)},
        )

        return servers

    def _get_agent_instructions(self) -> str:
        """
        Get agent instructions for Gemini Live.

        Returns:
            Agent instructions string
        """
        return """You are a helpful assistant for visually impaired users. Your role is to:

1. Help users identify obstacles and navigate safely
2. Find nearby places using Google Maps (via MCP tools)
3. Get directions to locations (via MCP tools)
4. Search and book accommodations (via MCP tools)
5. Manage WhatsApp communications (search contacts, read messages, send messages)

WhatsApp Capabilities:
- Search for contacts by name or phone number using search_contacts
- List and browse WhatsApp chats using list_chats (check for unread messages)
- Read messages from chats using list_messages or get_chat
- Send text messages using send_message
- Send files using send_file
- Send audio messages using send_audio
- Get message context using get_message_context
- Download media from messages using download_media

IMPORTANT WhatsApp Behavior:
- When the user starts a conversation or asks about messages, ALWAYS proactively check for unread messages by calling list_chats first
- Look for chats with unread_count > 0 or unread indicators in the response
- When you see unread messages, immediately inform the user and offer to read them
- Use list_messages with chat_jid to read messages from specific chats
- Always confirm before sending messages
- Read messages clearly and provide full context
- Help users find contacts by name or phone number
- Summarize conversations when asked
- Be careful with sensitive information

When user asks about messages or WhatsApp:
1. First call list_chats to see all chats and check for unread messages
2. If there are unread messages, inform the user immediately
3. Ask if they want to read the unread messages
4. Use list_messages with the chat_jid to read messages from specific chats

Always:
- Speak clearly and provide detailed descriptions
- Describe distances and directions in a way that's easy to understand
- Confirm important actions before executing them
- Provide step-by-step guidance for navigation
- Be patient and supportive

You have access to live video input from the user's camera. When users ask you to:
- "What obstacles do you see?" - Analyze the current video frame and describe any obstacles
- "What's in front of me?" - Describe what you see in the camera view
- "Is it safe to walk?" - Assess the path ahead for obstacles or hazards
- "Describe the environment" - Provide a detailed description of the surroundings

Use the visual information from the camera to:
- Identify obstacles and hazards in real-time
- Describe the environment and surroundings
- Provide detailed spatial awareness
- Guide navigation based on what you see

Always combine visual understanding with voice interaction to provide the most helpful assistance. Users can ask you to analyze obstacles at any time by simply asking you to look at what's in front of them."""

