"""Gemini Vision API client for obstacle detection using LiveKit Google plugin."""

import base64
import json
import re
import time
from typing import Any, Dict, List, Optional

from livekit.agents import ChatContext, ChatRole
from livekit.agents.llm import ImageContent
from livekit.agents.log import logger
from livekit.plugins import google

from app.core.config import settings


class GeminiVisionService:
    """Service for detecting obstacles using LiveKit Google plugin LLM with vision support."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Gemini Vision service.

        Args:
            api_key: Google API key (defaults to settings.google_api_key)
        """
        self._api_key = api_key or settings.google_api_key
        if not self._api_key:
            raise ValueError("Google API key is required")

        # Use LiveKit Google plugin LLM with the same model as configured in settings
        self._llm = google.LLM(
            model=settings.gemini_model,
            api_key=self._api_key,
            temperature=0.3,
            max_output_tokens=2048,
        )

    async def detect_obstacles(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Detect obstacles in an image using LiveKit Google plugin LLM with vision.

        Args:
            image_bytes: JPEG-encoded image bytes

        Returns:
            Dictionary containing obstacle detection results with the following structure:
            {
                "obstacles": [
                    {
                        "type": str,  # e.g., "person", "vehicle", "pole", "step"
                        "location": {"x": float, "y": float},  # Normalized coordinates (0-1)
                        "distance_estimate": str,  # e.g., "close", "medium", "far"
                        "description": str,  # Human-readable description
                        "severity": str,  # "low", "medium", "high"
                    }
                ],
                "recommendation": str,  # Navigation recommendation
                "timestamp": float,  # Unix timestamp
            }

        Raises:
            Exception: If the API call fails
        """
        try:
            # Encode image to base64 data URL
            image_base64 = base64.b64encode(image_bytes).decode("utf-8")
            image_data_url = f"data:image/jpeg;base64,{image_base64}"

            # Construct the prompt for obstacle detection
            prompt = """Analyze this image from a mobile camera for obstacle detection to help a visually impaired person navigate safely.

Identify and describe any obstacles in the path, including:
- People or pedestrians
- Vehicles (cars, bikes, etc.)
- Street furniture (poles, benches, trash cans)
- Steps, curbs, or elevation changes
- Other obstacles that could impede navigation

For each obstacle, provide:
1. Type of obstacle
2. Approximate location in the frame (normalized coordinates 0-1)
3. Estimated distance (close/medium/far)
4. Severity level (low/medium/high)
5. A brief description

Also provide a navigation recommendation based on the obstacles detected.

Return the response as a JSON object with this structure:
{
    "obstacles": [
        {
            "type": "string",
            "location": {"x": 0.5, "y": 0.5},
            "distance_estimate": "close|medium|far",
            "description": "string",
            "severity": "low|medium|high"
        }
    ],
    "recommendation": "string"
}"""

            # Create chat context with image using ImageContent
            chat_ctx = ChatContext()
            chat_ctx.add_message(
                role=ChatRole.USER,
                content=[
                    prompt,
                    ImageContent(image=image_data_url),  # Use ImageContent for proper formatting
                ],
            )

            # Call Gemini LLM with vision support
            stream = self._llm.chat(chat_ctx=chat_ctx)
            
            # Collect the response from ChatChunk objects
            response_text = ""
            async for chunk in stream:
                # ChatChunk has delta.content for text content
                if chunk.delta and chunk.delta.content:
                    response_text += chunk.delta.content

            response_text = response_text.strip()

            # Try to extract JSON from the response
            # Look for JSON in the response
            json_match = re.search(r"\{[\s\S]*\}", response_text)
            if json_match:
                response_text = json_match.group(0)

            result = json.loads(response_text)

            # Add timestamp
            result["timestamp"] = time.time()

            # Validate and normalize the response
            if "obstacles" not in result:
                result["obstacles"] = []

            if "recommendation" not in result:
                result["recommendation"] = "No specific recommendation available."

            # Normalize obstacles
            normalized_obstacles = []
            for obstacle in result.get("obstacles", []):
                normalized_obstacle = {
                    "type": obstacle.get("type", "unknown"),
                    "location": obstacle.get("location", {"x": 0.5, "y": 0.5}),
                    "distance_estimate": obstacle.get("distance_estimate", "unknown"),
                    "description": obstacle.get("description", ""),
                    "severity": obstacle.get("severity", "low"),
                }
                normalized_obstacles.append(normalized_obstacle)

            result["obstacles"] = normalized_obstacles

            logger.debug(
                f"Detected {len(normalized_obstacles)} obstacles",
                extra={"obstacle_count": len(normalized_obstacles)},
            )

            return result

        except Exception as e:
            logger.error(f"Error detecting obstacles with Gemini Vision: {e}", exc_info=True)
            # Return a safe default response
            return {
                "obstacles": [],
                "recommendation": "Unable to analyze image. Please proceed with caution.",
                "timestamp": time.time(),
                "error": str(e),
            }


# Global service instance
_vision_service: Optional[GeminiVisionService] = None


def get_vision_service() -> GeminiVisionService:
    """
    Get or create the global Gemini Vision service instance.

    Returns:
        GeminiVisionService instance
    """
    global _vision_service
    if _vision_service is None:
        _vision_service = GeminiVisionService()
    return _vision_service

