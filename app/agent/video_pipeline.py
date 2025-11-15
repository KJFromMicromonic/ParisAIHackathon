"""Video pipeline for processing video frames and detecting obstacles."""

import asyncio
import json
import time
from typing import Optional

import livekit.rtc as rtc
from livekit.agents.log import logger
from livekit.agents.utils.images import EncodeOptions, encode

from app.core.config import settings
from app.services.gemini import get_vision_service


class VideoPipeline:
    """Pipeline for processing video frames and detecting obstacles."""

    def __init__(self, room: rtc.Room):
        """
        Initialize the video pipeline.

        Args:
            room: LiveKit room instance
        """
        self._room = room
        self._vision_service = get_vision_service()
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._last_frame_time = 0.0
        self._frame_interval = 1.0 / settings.video_processing_fps

    async def start(self) -> None:
        """Start the video pipeline."""
        if self._running:
            logger.warning("Video pipeline is already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run())

        logger.info("Video pipeline started")

    async def stop(self) -> None:
        """Stop the video pipeline."""
        if not self._running:
            return

        self._running = False
        if self._task:
            await asyncio.wait_for(self._task, timeout=5.0)
            self._task = None

        logger.info("Video pipeline stopped")

    async def _run(self) -> None:
        """Main video processing loop."""
        try:
            # Wait for a participant with video to join
            participant = await self._wait_for_video_participant()
            if not participant:
                logger.warning("No video participant found, stopping video pipeline")
                return

            # Subscribe to video track
            video_stream = await self._subscribe_to_video(participant)
            if not video_stream:
                logger.warning("Could not subscribe to video track")
                return

            logger.info(
                f"Subscribed to video from participant {participant.identity}",
                extra={"participant_identity": participant.identity},
            )

            # Process video frames
            async for frame_event in video_stream:
                if not self._running:
                    break

                # Throttle frame processing
                current_time = time.time()
                if current_time - self._last_frame_time < self._frame_interval:
                    continue

                self._last_frame_time = current_time

                # Process frame asynchronously (don't await to avoid blocking)
                asyncio.create_task(self._process_frame(frame_event.frame))

        except asyncio.CancelledError:
            logger.info("Video pipeline task cancelled")
        except Exception as e:
            logger.error(f"Error in video pipeline: {e}", exc_info=True)
        finally:
            self._running = False

    async def _wait_for_video_participant(self, timeout: float = 30.0) -> Optional[rtc.RemoteParticipant]:
        """
        Wait for a remote participant with video to join.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            Remote participant with video, or None if timeout
        """
        start_time = time.time()

        # Check existing participants
        for participant in self._room.remote_participants.values():
            if self._has_video_track(participant):
                return participant

        # Wait for new participant with video
        event = asyncio.Event()

        def on_track_subscribed(
            track: rtc.RemoteTrack,
            publication: rtc.RemoteTrackPublication,
            participant: rtc.RemoteParticipant,
        ) -> None:
            if track.kind == rtc.TrackKind.KIND_VIDEO:
                event.set()

        self._room.on("track_subscribed", on_track_subscribed)

        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
            # Find the participant with video
            for participant in self._room.remote_participants.values():
                if self._has_video_track(participant):
                    return participant
        except asyncio.TimeoutError:
            logger.warning("Timeout waiting for video participant")
        finally:
            self._room.off("track_subscribed", on_track_subscribed)

        return None

    def _has_video_track(self, participant: rtc.RemoteParticipant) -> bool:
        """
        Check if participant has a video track.

        Args:
            participant: Remote participant to check

        Returns:
            True if participant has video track
        """
        for publication in participant.track_publications.values():
            if (
                publication.kind == rtc.TrackKind.KIND_VIDEO
                and publication.source == rtc.TrackSource.SOURCE_CAMERA
                and publication.subscribed
            ):
                return True
        return False

    async def _subscribe_to_video(
        self, participant: rtc.RemoteParticipant
    ) -> Optional[rtc.VideoStream]:
        """
        Subscribe to video track from participant.

        Args:
            participant: Remote participant

        Returns:
            Video stream, or None if subscription fails
        """
        try:
            # Find camera track
            for publication in participant.track_publications.values():
                if (
                    publication.kind == rtc.TrackKind.KIND_VIDEO
                    and publication.source == rtc.TrackSource.SOURCE_CAMERA
                ):
                    # Subscribe if not already subscribed
                    if not publication.subscribed:
                        publication.set_subscribed(True)
                        await asyncio.sleep(0.5)  # Wait for subscription

                    if publication.track:
                        # Create video stream
                        return rtc.VideoStream.from_participant(
                            participant=participant,
                            track_source=rtc.TrackSource.SOURCE_CAMERA,
                        )

        except Exception as e:
            logger.error(f"Error subscribing to video: {e}", exc_info=True)

        return None

    async def _process_frame(self, frame: rtc.VideoFrame) -> None:
        """
        Process a single video frame for obstacle detection.

        Args:
            frame: Video frame to process
        """
        try:
            # Convert frame to JPEG
            jpeg_bytes = encode(
                frame,
                EncodeOptions(
                    format="jpeg",
                    quality=settings.video_jpeg_quality,
                ),
            )

            # Detect obstacles using Gemini Vision
            detection_result = self._vision_service.detect_obstacles(jpeg_bytes)

            # Publish results via DataChannel
            await self._publish_detection_result(detection_result)

        except Exception as e:
            logger.error(f"Error processing video frame: {e}", exc_info=True)

    async def _publish_detection_result(self, result: dict) -> None:
        """
        Publish obstacle detection result via DataChannel.

        Args:
            result: Detection result dictionary
        """
        try:
            payload = json.dumps(result).encode("utf-8")
            await self._room.local_participant.publish_data(
                payload,
                topic=settings.obstacle_detection_topic,
                reliable=True,
            )

            logger.debug(
                f"Published obstacle detection result: {len(result.get('obstacles', []))} obstacles",
                extra={"obstacle_count": len(result.get("obstacles", []))},
            )

        except Exception as e:
            logger.error(f"Error publishing detection result: {e}", exc_info=True)

