"""ElevenLabs TTS service wrapper."""

from livekit.plugins import elevenlabs

from app.core.config import settings


def create_tts():
    """
    Create an ElevenLabs TTS instance.

    Returns:
        elevenlabs.TTS instance configured with settings
    """
    return elevenlabs.TTS(api_key=settings.elevenlabs_api_key,
        voice_id=settings.elevenlabs_voice_id,
        model=settings.elevenlabs_model,
    )

