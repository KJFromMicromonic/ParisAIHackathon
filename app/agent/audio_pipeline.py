"""Audio pipeline wrapper around AgentSession with Live Video input."""

from typing import Optional

import livekit.rtc as rtc
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
    """

    def __init__(self, room: rtc.Room):
        """
        Initialize the audio pipeline.

        Args:
            room: LiveKit room instance
        """
        self._room = room
        self._session: Optional[AgentSession] = None

    async def start(self) -> None:
        """Start the audio pipeline with Live Video input enabled."""
        if self._session is not None:
            logger.warning("Audio pipeline is already started")
            return

        try:
            # Create MCP server configurations
            mcp_servers = self._create_mcp_servers()

            # Create STT instance
            stt = create_stt()

            # Create VAD instance for streaming STT support
            # Mistral STT doesn't support streaming, so we need VAD
            vad_instance = silero.VAD.load()

            # Create LLM instance (Gemini Live Realtime with video support)
            llm = google.realtime.RealtimeModel(
                model=settings.gemini_model,
                voice=settings.gemini_voice,
                instructions=self._get_agent_instructions(),
            )

            # Create TTS instance
            tts = create_tts()

            # Create simple Agent (Gemini Live Realtime handles vision natively)
            from livekit.agents import Agent
            agent = Agent(instructions=self._get_agent_instructions())

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

        except Exception as e:
            logger.error(f"Error stopping audio pipeline: {e}", exc_info=True)

    def _create_mcp_servers(self) -> list[mcp.MCPServerHTTP]:
        """
        Create MCP server instances from settings.

        Returns:
            List of MCP server instances
        """
        servers = []
        urls = settings.get_mcp_server_urls()
        headers_map = settings.get_mcp_server_headers()

        for url in urls:
            headers = headers_map.get(url, {})
            servers.append(mcp.MCPServerHTTP(url, headers=headers))

        logger.debug(
            f"Created {len(servers)} MCP server connections",
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

