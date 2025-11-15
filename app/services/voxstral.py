"""Voxstral STT service wrapper."""

from livekit.plugins import mistralai

from app.core.config import settings


def create_stt():
    """
    Create a Voxstral STT instance.

    Returns:
        mistralai.STT instance configured with settings
    """
    return mistralai.STT(model=settings.voxstral_model)

