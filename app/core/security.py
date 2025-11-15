"""Security utilities for JWT token generation."""

from datetime import datetime, timedelta
from typing import Optional

from livekit import api

from app.core.config import settings


def generate_access_token(
    room_name: str,
    participant_identity: str,
    participant_name: Optional[str] = None,
    expires_in: int = 3600,
) -> str:
    """
    Generate a LiveKit access token for a participant.

    Args:
        room_name: Name of the LiveKit room
        participant_identity: Unique identity for the participant
        participant_name: Display name for the participant (optional)
        expires_in: Token expiration time in seconds (default: 1 hour)

    Returns:
        JWT access token string

    Raises:
        ValueError: If required settings are not configured
    """
    if not settings.livekit_api_key or not settings.livekit_api_secret:
        raise ValueError("LiveKit API key and secret must be configured")

    grant = api.VideoGrants(
        room_join=True,
        room=room_name,
        can_publish=True,
        can_subscribe=True,
        can_publish_data=True,
    )

    token = api.AccessToken(settings.livekit_api_key, settings.livekit_api_secret) \
        .with_identity(participant_identity) \
        .with_name(participant_name or participant_identity) \
        .with_grants(grant) \
        .with_ttl(timedelta(seconds=expires_in))

    return token.to_jwt()

