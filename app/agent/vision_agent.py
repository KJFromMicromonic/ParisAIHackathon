"""Custom Agent class with video frame processing for obstacle detection."""

import asyncio
import json
from typing import Optional

import livekit.rtc as rtc
from livekit.agents import Agent
from livekit.agents.log import logger
from livekit.agents.utils.images import EncodeOptions, encode

from app.core.config import settings
from app.services.gemini import get_vision_service


class VisionAgent(Agent):
    """
    Custom Agent that processes video frames for obstacle detection.
    
    This agent hooks into video frames from the room and processes them
    for obstacle detection while Gemini Live handles video input natively.
    """

    def __init__(self, instructions: str):
        """
        Initialize the Vision Agent.

        Args:
            instructions: Agent instructions for the LLM
        """
        super().__init__(instructions=instructions)
        self._tasks: list[asyncio.Task] = []
        self._video_stream: Optional[rtc.VideoStream] = None
        self._latest_frame: Optional[rtc.VideoFrame] = None
        self._vision_service = get_vision_service()
        self._last_processed_time = 0.0
        self._frame_interval = 1.0 / settings.video_processing_fps
        self._room: Optional[rtc.Room] = None

    async def on_enter(self) -> None:
        """Called when the agent enters the room."""
        from livekit.agents import get_job_context

        self._room = get_job_context().room

        # Set up video stream handler
        self._room.on("track_subscribed", self._on_track_subscribed)

        # Check for existing video tracks
        await self._check_existing_video_tracks()

        logger.info("Vision agent entered room, video processing enabled")

    async def on_exit(self) -> None:
        """Called when the agent exits the room."""
        # Clean up video stream
        if self._video_stream:
            await self._video_stream.aclose()
            self._video_stream = None

        # Cancel all tasks
        for task in self._tasks:
            if not task.done():
                task.cancel()

        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()

        if self._room:
            self._room.off("track_subscribed", self._on_track_subscribed)

        logger.info("Vision agent exited room")

    async def _check_existing_video_tracks(self) -> None:
        """Check for existing video tracks from remote participants."""
        if not self._room:
            return

        for participant in self._room.remote_participants.values():
            for publication in participant.track_publications.values():
                if (
                    publication.kind == rtc.TrackKind.KIND_VIDEO
                    and publication.source == rtc.TrackSource.SOURCE_CAMERA
                    and publication.subscribed
                    and publication.track
                ):
                    await self._create_video_stream(publication.track)
                    return

    def _on_track_subscribed(
        self,
        track: rtc.RemoteTrack,
        publication: rtc.RemoteTrackPublication,
        participant: rtc.RemoteParticipant,
    ) -> None:
        """Handle new video track subscription."""
        if (
            track.kind == rtc.TrackKind.KIND_VIDEO
            and publication.source == rtc.TrackSource.SOURCE_CAMERA
        ):
            asyncio.create_task(self._create_video_stream(track))

    async def _create_video_stream(self, track: rtc.RemoteTrack) -> None:
        """
        Create a video stream to process frames for obstacle detection.

        Args:
            track: Video track to process
        """
        # Close existing stream if any
        if self._video_stream:
            await self._video_stream.aclose()

        # Create new video stream
        self._video_stream = rtc.VideoStream(track)

        # Start processing frames
        task = asyncio.create_task(self._process_video_stream())
        self._tasks.append(task)
        task.add_done_callback(lambda t: self._tasks.remove(t) if t in self._tasks else None)

        logger.debug("Created video stream for obstacle detection")

    async def _process_video_stream(self) -> None:
        """Process video frames from the stream for obstacle detection."""
        import time

        try:
            async for event in self._video_stream:
                frame = event.frame

                # Throttle processing to avoid overwhelming the API
                current_time = time.time()
                if current_time - self._last_processed_time < self._frame_interval:
                    continue

                self._last_processed_time = current_time

                # Process frame asynchronously
                asyncio.create_task(self._detect_obstacles(frame))

        except asyncio.CancelledError:
            logger.debug("Video stream processing cancelled")
        except Exception as e:
            logger.error(f"Error processing video stream: {e}", exc_info=True)

    async def _detect_obstacles(self, frame: rtc.VideoFrame) -> None:
        """
        Detect obstacles in a video frame and publish results.

        Args:
            frame: Video frame to process
        """
        if not self._room:
            return

        try:
            # Convert frame to JPEG
            jpeg_bytes = encode(
                frame,
                EncodeOptions(
                    format="jpeg",
                    quality=settings.video_jpeg_quality,
                ),
            )

            # Detect obstacles using Gemini Vision (async call)
            detection_result = await self._vision_service.detect_obstacles(jpeg_bytes)

            # Publish results via DataChannel
            await self._publish_detection_result(detection_result)

        except Exception as e:
            logger.error(f"Error detecting obstacles: {e}", exc_info=True)

    async def _publish_detection_result(self, result: dict) -> None:
        """
        Publish obstacle detection result via DataChannel.

        Args:
            result: Detection result dictionary
        """
        if not self._room:
            return

        try:
            payload = json.dumps(result).encode("utf-8")
            await self._room.local_participant.publish_data(
                payload,
                topic=settings.obstacle_detection_topic,
                reliable=True,
            )

            obstacle_count = len(result.get("obstacles", []))
            logger.debug(
                f"Published obstacle detection result: {obstacle_count} obstacles",
                extra={"obstacle_count": obstacle_count},
            )

        except Exception as e:
            logger.error(f"Error publishing detection result: {e}", exc_info=True)

