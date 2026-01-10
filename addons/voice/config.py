"""
Voice Module Configuration
==========================
Centralized configuration for TTS/STT services using OpenAI APIs.

Enable/disable voice features via environment variables.
"""

import os
from dataclasses import dataclass
from typing import Optional

# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class VoiceConfig:
    """Voice module configuration for OpenAI APIs."""

    # OpenAI API Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"

    # Feature Toggle
    VOICE_ENABLED: bool = os.getenv("VOICE_ENABLED", "true").lower() == "true"

    # TTS Configuration (OpenAI TTS API)
    TTS_DEFAULT_VOICE: str = os.getenv("OPENAI_TTS_VOICE", "alloy")
    TTS_DEFAULT_MODEL: str = os.getenv("OPENAI_TTS_MODEL", "tts-1")
    TTS_OUTPUT_FORMAT: str = os.getenv("OPENAI_TTS_FORMAT", "mp3")
    TTS_SPEED: float = float(os.getenv("OPENAI_TTS_SPEED", "1.0"))

    # STT Configuration (OpenAI Whisper API)
    STT_DEFAULT_MODEL: str = os.getenv("OPENAI_STT_MODEL", "whisper-1")
    STT_DEFAULT_LANGUAGE: str = os.getenv("OPENAI_STT_LANGUAGE", "")  # Empty = auto-detect

    # Available OpenAI TTS voices
    AVAILABLE_VOICES = {
        "neutral": ["alloy", "fable"],
        "male": ["echo", "onyx"],
        "female": ["nova", "shimmer"]
    }

    # Supported output formats for TTS
    SUPPORTED_TTS_FORMATS = ["mp3", "opus", "aac", "flac", "wav", "pcm"]

    # Supported languages for Whisper (ISO-639-1 codes)
    # Whisper supports many languages, these are common ones
    SUPPORTED_LANGUAGES = [
        "en",  # English
        "hi",  # Hindi
        "bn",  # Bengali
        "ta",  # Tamil
        "te",  # Telugu
        "mr",  # Marathi
        "gu",  # Gujarati
        "kn",  # Kannada
        "ml",  # Malayalam
        "pa",  # Punjabi
        "or",  # Odia
        "es",  # Spanish
        "fr",  # French
        "de",  # German
        "ja",  # Japanese
        "zh",  # Chinese
        "ar",  # Arabic
        "ru",  # Russian
        "pt",  # Portuguese
        "it",  # Italian
    ]

    @classmethod
    def is_configured(cls) -> bool:
        """Check if OpenAI API is configured."""
        return bool(cls.OPENAI_API_KEY and cls.OPENAI_API_KEY.startswith("sk-"))

    @classmethod
    def get_all_voices(cls) -> list:
        """Get list of all available voices."""
        voices = []
        for category_voices in cls.AVAILABLE_VOICES.values():
            voices.extend(category_voices)
        return voices


def is_voice_enabled() -> bool:
    """
    Check if voice feature is enabled and properly configured.

    Returns:
        True if voice is enabled AND API key is configured
    """
    return VoiceConfig.VOICE_ENABLED and VoiceConfig.is_configured()


def get_voice_status() -> dict:
    """
    Get detailed voice module status.

    Returns:
        Dictionary with status information
    """
    return {
        "enabled": VoiceConfig.VOICE_ENABLED,
        "configured": VoiceConfig.is_configured(),
        "operational": is_voice_enabled(),
        "provider": "openai",
        "tts": {
            "default_voice": VoiceConfig.TTS_DEFAULT_VOICE,
            "model": VoiceConfig.TTS_DEFAULT_MODEL,
            "format": VoiceConfig.TTS_OUTPUT_FORMAT,
            "speed": VoiceConfig.TTS_SPEED,
        },
        "stt": {
            "model": VoiceConfig.STT_DEFAULT_MODEL,
            "default_language": VoiceConfig.STT_DEFAULT_LANGUAGE or "auto-detect",
        },
        "supported_languages": VoiceConfig.SUPPORTED_LANGUAGES,
        "available_voices": VoiceConfig.get_all_voices(),
    }
