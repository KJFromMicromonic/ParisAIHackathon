"""Application configuration management using pydantic-settings."""

from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # LiveKit Configuration
    livekit_url: str = Field(
        ...,
        description="LiveKit server WebSocket URL (e.g., wss://your-livekit-server.com)",
    )
    livekit_api_key: str = Field(
        ...,
        description="LiveKit API key for authentication",
    )
    livekit_api_secret: str = Field(
        ...,
        description="LiveKit API secret for token generation",
    )

    # Google API Configuration
    google_api_key: str = Field(
        ...,
        description="Google API key for Gemini Vision and Realtime API",
    )
    google_maps_api_key: Optional[str] = Field(
        default=None,
        description="Google Maps API key for navigation and place search (optional if using external MCP server)",
    )

    # Mistral AI Configuration
    mistral_api_key: str = Field(
        ...,
        description="Mistral AI API key for Voxstral STT",
    )

    # ElevenLabs Configuration
    elevenlabs_api_key: str = Field(
        ...,
        description="ElevenLabs API key for TTS",
    )
    elevenlabs_voice_id: str = Field(
        default="EXAVITQu4vr4xnSDxMaL",
        description="ElevenLabs voice ID to use for TTS",
    )
    elevenlabs_model: str = Field(
        default="eleven_multilingual_v2",
        description="ElevenLabs TTS model to use",
    )

    # Gemini Configuration
    gemini_model: str = Field(
        default="gemini-2.0-flash-exp",
        description="Gemini Live Realtime model to use",
    )
    gemini_voice: str = Field(
        default="Puck",
        description="Gemini Live voice to use",
    )

    # Voxstral Configuration
    voxstral_model: str = Field(
        default="voxtral-mini-2507",
        description="Voxstral STT model to use",
    )

    # MCP Server Configuration
    mcp_server_urls: str = Field(
        default="",
        description="Comma-separated list of MCP server URLs (e.g., https://server1.com,https://server2.com). WhatsApp MCP server is added automatically if whatsapp_mcp_server_enabled is true.",
    )
    whatsapp_mcp_server_enabled: bool = Field(
        default=True,
        description="If True, start local WhatsApp MCP server wrapper. If False, use WhatsApp API directly (requires MCP protocol support).",
    )
    whatsapp_mcp_server_port: int = Field(
        default=8081,
        description="Port for local WhatsApp MCP server (default: 8081)",
    )
    mcp_server_headers: str = Field(
        default="{}",
        description="JSON object mapping server URLs to headers (e.g., {\"https://server1.com\": {\"Authorization\": \"Bearer token\"}})",
    )

    # Redis Configuration (Optional)
    redis_url: Optional[str] = Field(
        default=None,
        description="Redis connection URL for distributed session state (optional)",
    )

    # FastAPI Configuration
    api_host: str = Field(
        default="0.0.0.0",
        description="FastAPI server host",
    )
    api_port: int = Field(
        default=8000,
        description="FastAPI server port",
    )

    # Video Processing Configuration
    video_processing_fps: float = Field(
        default=2.0,
        description="Target FPS for video frame processing (throttle rate)",
    )
    video_jpeg_quality: int = Field(
        default=85,
        description="JPEG quality for video frame encoding (1-100)",
    )

    # Obstacle Detection Configuration
    obstacle_detection_topic: str = Field(
        default="obstacle_detection",
        description="DataChannel topic for obstacle detection results",
    )

    # WhatsApp API Configuration
    whatsapp_api_url: str = Field(
        default="https://whatsapp-mcp-794750095859.europe-west1.run.app",
        description="WhatsApp API base URL",
    )
    whatsapp_api_headers: str = Field(
        default="{}",
        description="JSON object with headers for WhatsApp API requests (e.g., {\"Authorization\": \"Bearer token\"})",
    )

    def get_mcp_server_urls(self) -> List[str]:
        """
        Parse MCP server URLs from comma-separated string.

        Returns:
            List of MCP server URLs
        """
        if not self.mcp_server_urls:
            return []
        return [url.strip() for url in self.mcp_server_urls.split(",") if url.strip()]

    def get_mcp_server_headers(self) -> dict[str, dict[str, str]]:
        """
        Parse MCP server headers from JSON string.

        Returns:
            Dictionary mapping server URLs to headers
        """
        import json

        if not self.mcp_server_headers:
            return {}
        try:
            return json.loads(self.mcp_server_headers)
        except json.JSONDecodeError:
            return {}

    def get_whatsapp_api_headers(self) -> dict[str, str]:
        """
        Parse WhatsApp API headers from JSON string.

        Returns:
            Dictionary with headers for WhatsApp API requests
        """
        import json

        if not self.whatsapp_api_headers:
            return {}
        try:
            return json.loads(self.whatsapp_api_headers)
        except json.JSONDecodeError:
            return {}


# Global settings instance
settings = Settings()

