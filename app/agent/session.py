"""Session manager for coordinating audio pipeline with integrated video processing."""

import asyncio
from typing import Optional

import livekit.rtc as rtc
from livekit.agents.log import logger

from app.agent.audio_pipeline import AudioPipeline


class AgentSessionManager:
    """
    Manages per-room session state and coordinates audio pipeline.
    
    Video processing is now integrated into the AudioPipeline via:
    - Native Live Video input for Gemini Live (via RoomInputOptions)
    - VisionAgent hooks for obstacle detection and DataChannel publishing
    """

    def __init__(self, room: rtc.Room):
        """
        Initialize the session manager.

        Args:
            room: LiveKit room instance
        """
        self._room = room
        self._audio_pipeline: Optional[AudioPipeline] = None
        self._running = False

    async def start(self) -> None:
        """
        Start the audio pipeline with integrated video processing.
        
        The AudioPipeline now handles both:
        - Audio processing (STT → Gemini Live → TTS)
        - Video processing (Live Video input for Gemini Live + obstacle detection)
        """
        if self._running:
            logger.warning("Session manager is already running")
            return

        try:
            self._running = True

            # Initialize audio pipeline (which includes video processing)
            self._audio_pipeline = AudioPipeline(self._room)

            # Start the pipeline
            await self._audio_pipeline.start()

            logger.info(
                "Session manager started",
                extra={"room_name": self._room.name},
            )

        except Exception as e:
            logger.error(f"Error starting session manager: {e}", exc_info=True)
            await self.stop()
            raise

    async def stop(self) -> None:
        """Stop both video and audio pipelines."""
        if not self._running:
            return

        self._running = False

        try:
            # Stop the audio pipeline (which includes video processing)
            if self._audio_pipeline:
                await self._audio_pipeline.stop()

            self._audio_pipeline = None

            logger.info(
                "Session manager stopped",
                extra={"room_name": self._room.name},
            )

        except Exception as e:
            logger.error(f"Error stopping session manager: {e}", exc_info=True)

    @property
    def room(self) -> rtc.Room:
        """Get the LiveKit room instance."""
        return self._room

    @property
    def room_name(self) -> str:
        """Get the room name."""
        return self._room.name

    @property
    def is_running(self) -> bool:
        """Check if the session is running."""
        return self._running

