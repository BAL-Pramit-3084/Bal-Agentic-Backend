"""
Voice Addon Module
==================
Voice features using OpenAI APIs:
- TTS (Text-to-Speech) - OpenAI TTS API
- STT (Speech-to-Text) - OpenAI Whisper API
- LID (Language Identification) - OpenAI Whisper API
- Realtime Voice - OpenAI Realtime API (WebSocket-based live conversations)

This is an OPTIONAL addon that can be enabled/disabled via config.

Usage:
    from addons.voice import voice_bp, is_voice_enabled

    if is_voice_enabled():
        app.register_blueprint(voice_bp)

API Endpoints:
    # Traditional TTS/STT (Request/Response)
    POST /api/v1/voice/tts          - Convert text to speech
    POST /api/v1/voice/tts/base64   - Convert text to speech (returns base64)
    POST /api/v1/voice/stt          - Convert speech to text
    POST /api/v1/voice/lid          - Language identification
    GET  /api/v1/voice/status       - Check voice feature status
    GET  /api/v1/voice/voices       - List available TTS voices

    # Realtime Voice (WebSocket-based)
    POST /api/v1/voice/realtime/session - Create realtime session (get ephemeral token)
    GET  /api/v1/voice/realtime/info    - Get realtime connection requirements
"""

from .config import is_voice_enabled, VoiceConfig
from .routes import voice_bp
from .tts_service import TextToSpeechService
from .stt_service import SpeechToTextService
from .lid_service import LanguageIdentificationService
from .realtime_service import RealtimeVoiceService

__all__ = [
    'voice_bp',
    'is_voice_enabled',
    'VoiceConfig',
    'TextToSpeechService',
    'SpeechToTextService',
    'LanguageIdentificationService',
    'RealtimeVoiceService'
]
