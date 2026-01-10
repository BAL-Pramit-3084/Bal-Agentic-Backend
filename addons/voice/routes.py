"""
Voice API Routes
================
Flask blueprint for TTS, STT, and LID endpoints using OpenAI APIs.

Endpoints:
    POST /api/v1/voice/tts      - Convert text to speech
    POST /api/v1/voice/stt      - Convert speech to text (auto language detection)
    POST /api/v1/voice/lid      - Language identification only
    GET  /api/v1/voice/status   - Check voice feature status
    GET  /api/v1/voice/voices   - List available TTS voices
"""

import logging
import base64
from flask import Blueprint, request, jsonify, Response

from .config import VoiceConfig, is_voice_enabled, get_voice_status
from .tts_service import TextToSpeechService
from .stt_service import SpeechToTextService
from .lid_service import LanguageIdentificationService

logger = logging.getLogger(__name__)

# Create Blueprint
voice_bp = Blueprint("voice", __name__, url_prefix="/api/v1/voice")

# Initialize services (lazy - only when needed)
_tts_service = None
_stt_service = None
_lid_service = None


def get_tts_service() -> TextToSpeechService:
    """Get or create TTS service instance."""
    global _tts_service
    if _tts_service is None:
        _tts_service = TextToSpeechService()
    return _tts_service


def get_stt_service() -> SpeechToTextService:
    """Get or create STT service instance."""
    global _stt_service
    if _stt_service is None:
        _stt_service = SpeechToTextService()
    return _stt_service


def get_lid_service() -> LanguageIdentificationService:
    """Get or create LID service instance."""
    global _lid_service
    if _lid_service is None:
        _lid_service = LanguageIdentificationService()
    return _lid_service


# =============================================================================
# STATUS ENDPOINT
# =============================================================================

@voice_bp.route("/status", methods=["GET"])
def voice_status():
    """
    Check if voice feature is enabled and operational.

    Returns:
        {
            "enabled": true/false,
            "configured": true/false,
            "operational": true/false,
            "provider": "openai",
            "tts": {...},
            "stt": {...},
            "supported_languages": [...],
            "available_voices": [...]
        }
    """
    return jsonify(get_voice_status())


# =============================================================================
# VOICES ENDPOINT (renamed from speakers)
# =============================================================================

@voice_bp.route("/voices", methods=["GET"])
@voice_bp.route("/speakers", methods=["GET"])  # Keep backward compatibility
def list_voices():
    """
    List available TTS voices.

    Returns:
        {
            "voices": {
                "neutral": ["alloy", "fable"],
                "male": ["echo", "onyx"],
                "female": ["nova", "shimmer"]
            },
            "default": "alloy"
        }
    """
    return jsonify({
        "voices": VoiceConfig.AVAILABLE_VOICES,
        "speakers": VoiceConfig.AVAILABLE_VOICES,  # Backward compatibility
        "default": VoiceConfig.TTS_DEFAULT_VOICE,
        "all": VoiceConfig.get_all_voices()
    })


# =============================================================================
# TEXT-TO-SPEECH ENDPOINT
# =============================================================================

@voice_bp.route("/tts", methods=["POST"])
def text_to_speech():
    """
    Convert text to speech using OpenAI TTS.

    Request Body (JSON):
        {
            "text": "Hello, how are you?",      (required)
            "voice": "alloy",                    (optional, default: alloy)
            "model": "tts-1",                    (optional, default: tts-1)
            "speed": 1.0,                        (optional, 0.25 to 4.0)
            "format": "mp3"                      (optional, mp3/opus/aac/flac/wav/pcm)
        }

    Returns:
        Success: Audio file (binary) with appropriate Content-Type
        Error: JSON with error message
    """
    # Check if voice is enabled
    if not is_voice_enabled():
        return jsonify({
            "success": False,
            "error": "Voice feature is not enabled or not configured"
        }), 503

    # Parse request
    data = request.get_json()
    if not data:
        return jsonify({
            "success": False,
            "error": "Request body must be JSON"
        }), 400

    text = data.get("text", "").strip()
    if not text:
        return jsonify({
            "success": False,
            "error": "text field is required"
        }), 400

    # Get optional parameters
    voice = data.get("voice") or data.get("speaker")  # Accept both for compatibility
    model = data.get("model")
    speed = data.get("speed") or data.get("pace")  # Accept pace for compatibility
    output_format = data.get("format", "mp3")

    # Convert
    tts = get_tts_service()
    result = tts.convert(
        text=text,
        voice=voice,
        model=model,
        speed=speed,
        output_format=output_format
    )

    if result["success"]:
        # Return audio as binary response
        audio_bytes = base64.b64decode(result["audio_base64"])
        return Response(
            audio_bytes,
            mimetype=result["content_type"],
            headers={
                "Content-Disposition": f"inline; filename=speech.{output_format}"
            }
        )
    else:
        return jsonify({
            "success": False,
            "error": result.get("error", "TTS conversion failed")
        }), 500


@voice_bp.route("/tts/base64", methods=["POST"])
def text_to_speech_base64():
    """
    Convert text to speech and return base64 encoded audio.

    Same request body as /tts endpoint.

    Returns:
        {
            "success": true,
            "audio_base64": "base64_encoded_audio",
            "content_type": "audio/mpeg"
        }
    """
    # Check if voice is enabled
    if not is_voice_enabled():
        return jsonify({
            "success": False,
            "error": "Voice feature is not enabled or not configured"
        }), 503

    # Parse request
    data = request.get_json()
    if not data:
        return jsonify({
            "success": False,
            "error": "Request body must be JSON"
        }), 400

    text = data.get("text", "").strip()
    if not text:
        return jsonify({
            "success": False,
            "error": "text field is required"
        }), 400

    # Get optional parameters
    voice = data.get("voice") or data.get("speaker")  # Accept both for compatibility
    model = data.get("model")
    speed = data.get("speed") or data.get("pace")  # Accept pace for compatibility
    output_format = data.get("format", "mp3")

    # Convert
    tts = get_tts_service()
    result = tts.convert(
        text=text,
        voice=voice,
        model=model,
        speed=speed,
        output_format=output_format
    )

    if result["success"]:
        return jsonify({
            "success": True,
            "audio_base64": result["audio_base64"],
            "content_type": result["content_type"]
        })
    else:
        return jsonify({
            "success": False,
            "error": result.get("error", "TTS conversion failed")
        }), 500


# =============================================================================
# SPEECH-TO-TEXT ENDPOINT
# =============================================================================

@voice_bp.route("/stt", methods=["POST"])
def speech_to_text():
    """
    Convert speech to text using OpenAI Whisper.

    Request: multipart/form-data
        - file: Audio file (required)
        - language: Language code ISO-639-1 (optional, auto-detect if not specified)

    OR

    Request: JSON
        {
            "audio_base64": "base64_encoded_audio",  (required)
            "language": "en",                         (optional)
            "format": "wav"                           (optional, helps with decoding)
        }

    Returns:
        {
            "success": true,
            "transcript": "transcribed text",
            "language_code": "en"
        }
    """
    # Check if voice is enabled
    if not is_voice_enabled():
        return jsonify({
            "success": False,
            "error": "Voice feature is not enabled or not configured"
        }), 503

    stt = get_stt_service()

    # Check if multipart form data (file upload)
    if request.content_type and "multipart/form-data" in request.content_type:
        # File upload
        if "file" not in request.files:
            return jsonify({
                "success": False,
                "error": "No audio file provided"
            }), 400

        audio_file = request.files["file"]
        if audio_file.filename == "":
            return jsonify({
                "success": False,
                "error": "No audio file selected"
            }), 400

        # Get language from form
        language = request.form.get("language")

        # Determine format from filename
        filename = audio_file.filename
        audio_format = filename.rsplit(".", 1)[-1] if "." in filename else "wav"

        # Read audio data
        audio_data = audio_file.read()

        result = stt.transcribe(
            audio_data=audio_data,
            language=language,
            audio_format=audio_format,
            filename=filename
        )

    else:
        # JSON with base64 audio
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "Request must be multipart/form-data with file OR JSON with audio_base64"
            }), 400

        audio_base64 = data.get("audio_base64", "")
        if not audio_base64:
            return jsonify({
                "success": False,
                "error": "audio_base64 field is required"
            }), 400

        language = data.get("language")
        audio_format = data.get("format", "wav")

        result = stt.transcribe_base64(
            audio_base64=audio_base64,
            language=language,
            audio_format=audio_format
        )

    if result["success"]:
        return jsonify({
            "success": True,
            "transcript": result["transcript"],
            "language_code": result.get("language_code"),
            "duration": result.get("duration")
        })
    else:
        return jsonify({
            "success": False,
            "error": result.get("error", "STT conversion failed")
        }), 500


# =============================================================================
# TEXT LANGUAGE DETECTION ENDPOINT
# =============================================================================

@voice_bp.route("/detect-text-language", methods=["POST"])
def detect_text_language():
    """
    Detect language from text using Unicode character analysis.

    This is a fast, client-side alternative to audio-based LID.
    Uses Unicode character ranges to detect languages.

    Request Body (JSON):
        {
            "text": "Hello, how are you?"
        }

    Returns:
        {
            "success": true,
            "language_code": "en",
            "language_name": "English",
            "confidence": "high"
        }
    """
    data = request.get_json()
    if not data or not data.get("text"):
        return jsonify({
            "success": False,
            "error": "text field is required"
        }), 400

    text = data.get("text", "").strip()

    # Unicode ranges for various languages
    language_ranges = {
        "hi": (0x0900, 0x097F, "Hindi"),      # Devanagari
        "bn": (0x0980, 0x09FF, "Bengali"),    # Bengali
        "pa": (0x0A00, 0x0A7F, "Punjabi"),    # Gurmukhi
        "gu": (0x0A80, 0x0AFF, "Gujarati"),   # Gujarati
        "or": (0x0B00, 0x0B7F, "Odia"),       # Oriya
        "ta": (0x0B80, 0x0BFF, "Tamil"),      # Tamil
        "te": (0x0C00, 0x0C7F, "Telugu"),     # Telugu
        "kn": (0x0C80, 0x0CFF, "Kannada"),    # Kannada
        "ml": (0x0D00, 0x0D7F, "Malayalam"),  # Malayalam
        "th": (0x0E00, 0x0E7F, "Thai"),       # Thai
        "ja": (0x3040, 0x30FF, "Japanese"),   # Hiragana + Katakana
        "zh": (0x4E00, 0x9FFF, "Chinese"),    # CJK Unified Ideographs
        "ko": (0xAC00, 0xD7AF, "Korean"),     # Hangul Syllables
        "ar": (0x0600, 0x06FF, "Arabic"),     # Arabic
        "he": (0x0590, 0x05FF, "Hebrew"),     # Hebrew
        "ru": (0x0400, 0x04FF, "Russian"),    # Cyrillic
    }

    # Count characters in each script
    script_counts = {}
    total_chars = 0

    for char in text:
        code_point = ord(char)
        if char.isspace() or char in '.,!?;:"\'-()[]{}':
            continue
        total_chars += 1

        for lang_code, (start, end, lang_name) in language_ranges.items():
            if start <= code_point <= end:
                script_counts[lang_code] = script_counts.get(lang_code, 0) + 1
                break
        else:
            # ASCII/Latin characters = English
            if 0x0041 <= code_point <= 0x007A:
                script_counts["en"] = script_counts.get("en", 0) + 1

    if not script_counts:
        return jsonify({
            "success": True,
            "language_code": "en",
            "language_name": "English",
            "confidence": "low"
        })

    # Find dominant language
    dominant_lang = max(script_counts, key=script_counts.get)
    dominant_count = script_counts[dominant_lang]

    # Determine confidence
    if total_chars > 0:
        ratio = dominant_count / total_chars
        if ratio > 0.8:
            confidence = "high"
        elif ratio > 0.5:
            confidence = "medium"
        else:
            confidence = "low"
    else:
        confidence = "low"

    # Get language name
    lang_name = "English"
    if dominant_lang in language_ranges:
        lang_name = language_ranges[dominant_lang][2]

    return jsonify({
        "success": True,
        "language_code": dominant_lang,
        "language_name": lang_name,
        "confidence": confidence
    })


# =============================================================================
# LANGUAGE IDENTIFICATION ENDPOINT
# =============================================================================

@voice_bp.route("/lid", methods=["POST"])
def language_identification():
    """
    Detect language from speech using OpenAI Whisper.

    This endpoint uses Whisper's language identification feature
    to automatically detect what language is being spoken.

    Request: multipart/form-data
        - file: Audio file (required)

    OR

    Request: JSON
        {
            "audio_base64": "base64_encoded_audio",  (required)
            "format": "wav"                           (optional)
        }

    Returns:
        {
            "success": true,
            "language_code": "hi",
            "language_name": "Hindi",
            "transcript": "transcribed text (bonus)"
        }
    """
    # Check if voice is enabled
    if not is_voice_enabled():
        return jsonify({
            "success": False,
            "error": "Voice feature is not enabled or not configured"
        }), 503

    lid = get_lid_service()

    # Check if multipart form data (file upload)
    if request.content_type and "multipart/form-data" in request.content_type:
        # File upload
        if "file" not in request.files:
            return jsonify({
                "success": False,
                "error": "No audio file provided"
            }), 400

        audio_file = request.files["file"]
        if audio_file.filename == "":
            return jsonify({
                "success": False,
                "error": "No audio file selected"
            }), 400

        # Determine format from filename
        filename = audio_file.filename
        audio_format = filename.rsplit(".", 1)[-1] if "." in filename else "wav"

        # Read audio data
        audio_data = audio_file.read()

        result = lid.detect_language(
            audio_data=audio_data,
            audio_format=audio_format,
            filename=filename
        )

    else:
        # JSON with base64 audio
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "Request must be multipart/form-data with file OR JSON with audio_base64"
            }), 400

        audio_base64 = data.get("audio_base64", "")
        if not audio_base64:
            return jsonify({
                "success": False,
                "error": "audio_base64 field is required"
            }), 400

        audio_format = data.get("format", "wav")

        result = lid.detect_language_base64(
            audio_base64=audio_base64,
            audio_format=audio_format
        )

    if result["success"]:
        return jsonify({
            "success": True,
            "language_code": result["language_code"],
            "language_name": result.get("language_name", "Unknown"),
            "transcript": result.get("transcript", "")
        })
    else:
        return jsonify({
            "success": False,
            "error": result.get("error", "Language identification failed")
        }), 500


# =============================================================================
# REALTIME VOICE API ENDPOINTS
# =============================================================================

_realtime_service = None


def get_realtime_service():
    """Get or create Realtime Voice service instance."""
    global _realtime_service
    if _realtime_service is None:
        from .realtime_service import RealtimeVoiceService
        _realtime_service = RealtimeVoiceService()
    return _realtime_service


@voice_bp.route("/realtime/session", methods=["POST"])
def create_realtime_session():
    """
    Create a new OpenAI Realtime Voice session.

    Returns an ephemeral client token that frontend can use to connect
    directly to OpenAI's Realtime WebSocket API.

    Request Body (JSON, all optional):
        {
            "instructions": "You are a helpful assistant...",
            "voice": "alloy",
            "tools": [...],
            "temperature": 0.8
        }

    Returns:
        {
            "success": true,
            "session_id": "sess_xxx",
            "client_secret": "ek_xxx...",
            "expires_at": 1234567890,
            "websocket_url": "wss://api.openai.com/v1/realtime?model=...",
            "model": "gpt-4o-realtime-preview-2024-12-17",
            "voice": "alloy",
            "config": {
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "sample_rate": 24000,
                "channels": 1,
                "turn_detection": {...}
            }
        }

    Frontend Usage:
        1. Call this endpoint to get client_secret
        2. Connect WebSocket to websocket_url with auth header:
           Authorization: Bearer {client_secret}
        3. Stream audio in PCM16 format at 24kHz mono
    """
    # Check if voice is enabled
    if not is_voice_enabled():
        return jsonify({
            "success": False,
            "error": "Voice feature is not enabled or not configured"
        }), 503

    # Parse optional request body
    data = request.get_json() or {}

    instructions = data.get("instructions")
    voice = data.get("voice")
    tools = data.get("tools")
    temperature = data.get("temperature", 0.8)

    # Create session
    realtime = get_realtime_service()
    result = realtime.create_session(
        instructions=instructions,
        voice=voice,
        tools=tools,
        temperature=temperature
    )

    if result["success"]:
        return jsonify(result)
    else:
        return jsonify(result), 500


@voice_bp.route("/realtime/info", methods=["GET"])
def realtime_connection_info():
    """
    Get information about OpenAI Realtime Voice API connection requirements.

    Returns:
        {
            "websocket_url": "wss://api.openai.com/v1/realtime?model=...",
            "model": "gpt-4o-realtime-preview-2024-12-17",
            "audio_config": {
                "sample_rate": 24000,
                "channels": 1,
                "format": "pcm16",
                "bits_per_sample": 16
            },
            "available_voices": ["alloy", "echo", ...],
            "default_voice": "alloy",
            "turn_detection_modes": ["server_vad", "none"],
            "documentation": "https://platform.openai.com/docs/guides/realtime"
        }
    """
    realtime = get_realtime_service()
    return jsonify(realtime.get_connection_info())
