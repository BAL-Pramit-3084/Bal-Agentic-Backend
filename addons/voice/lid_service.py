"""
Language Identification Service
===============================
Auto-detects language from speech using OpenAI Whisper API.

Whisper automatically detects the spoken language during transcription.

Usage:
    from addons.voice.lid_service import LanguageIdentificationService

    lid = LanguageIdentificationService()
    result = lid.detect_language(audio_bytes)
    # Returns: {"success": True, "language_code": "hi", "language_name": "Hindi"}
"""

import logging
import requests
import base64
from typing import Dict, Any, Union
from io import BytesIO

from .config import VoiceConfig

logger = logging.getLogger(__name__)

# Language code to name mapping
LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi",
    "bn": "Bengali",
    "ta": "Tamil",
    "te": "Telugu",
    "mr": "Marathi",
    "gu": "Gujarati",
    "kn": "Kannada",
    "ml": "Malayalam",
    "pa": "Punjabi",
    "or": "Odia",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "ja": "Japanese",
    "zh": "Chinese",
    "ar": "Arabic",
    "ru": "Russian",
    "pt": "Portuguese",
    "it": "Italian",
    "ko": "Korean",
    "nl": "Dutch",
    "pl": "Polish",
    "tr": "Turkish",
    "vi": "Vietnamese",
    "th": "Thai",
    "id": "Indonesian",
    "ms": "Malay",
    "uk": "Ukrainian",
    "cs": "Czech",
    "ro": "Romanian",
    "el": "Greek",
    "hu": "Hungarian",
    "sv": "Swedish",
    "da": "Danish",
    "fi": "Finnish",
    "no": "Norwegian",
    "he": "Hebrew",
    "ur": "Urdu",
    "fa": "Persian",
}


class LanguageIdentificationService:
    """
    Language Identification service using OpenAI Whisper API.

    Uses Whisper's automatic language detection feature.
    """

    def __init__(self):
        """Initialize LID service."""
        self.api_key = VoiceConfig.OPENAI_API_KEY
        self.base_url = VoiceConfig.OPENAI_BASE_URL
        self.endpoint = f"{self.base_url}/audio/transcriptions"

        if not self.api_key:
            logger.warning("OpenAI API key not configured. LID will not work.")

    def detect_language(
        self,
        audio_data: Union[bytes, BytesIO],
        audio_format: str = "wav",
        filename: str = "audio.wav"
    ) -> Dict[str, Any]:
        """
        Detect language from audio using Whisper.

        Args:
            audio_data: Audio bytes or BytesIO object
            audio_format: Format of audio (wav, mp3, webm, etc.)
            filename: Filename for the upload

        Returns:
            {
                "success": True/False,
                "language_code": "detected language code (e.g., hi)",
                "language_name": "Hindi",
                "transcript": "transcribed text (bonus)",
                "error": "error message if failed"
            }
        """
        if not self.api_key:
            return {
                "success": False,
                "error": "OpenAI API key not configured"
            }

        # Handle BytesIO
        if isinstance(audio_data, BytesIO):
            audio_data = audio_data.read()

        if not audio_data:
            return {
                "success": False,
                "error": "Audio data cannot be empty"
            }

        # Build headers
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        # Ensure filename has correct extension
        if not filename.endswith(f".{audio_format}"):
            filename = f"audio.{audio_format}"

        # Map MIME types
        mime_types = {
            "wav": "audio/wav",
            "mp3": "audio/mpeg",
            "webm": "audio/webm",
            "ogg": "audio/ogg",
            "m4a": "audio/m4a",
            "flac": "audio/flac",
            "opus": "audio/opus",
            "mp4": "audio/mp4"
        }
        mime_type = mime_types.get(audio_format.lower(), f"audio/{audio_format}")

        # Multipart form data
        files = {
            "file": (filename, audio_data, mime_type)
        }

        # Request verbose_json to get language detection
        data = {
            "model": VoiceConfig.STT_DEFAULT_MODEL,
            "response_format": "verbose_json"
            # Don't specify language - let Whisper auto-detect
        }

        logger.info(f"LID Request: {len(audio_data)} bytes, format={audio_format}")

        try:
            response = requests.post(
                self.endpoint,
                headers=headers,
                files=files,
                data=data,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                detected_lang = result.get("language", "unknown")
                transcript = result.get("text", "")

                logger.info(f"LID Success: Detected language = {detected_lang}")

                return {
                    "success": True,
                    "language_code": detected_lang,
                    "language_name": LANGUAGE_NAMES.get(detected_lang, "Unknown"),
                    "transcript": transcript,
                }

            else:
                error_msg = f"OpenAI API error: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", error_msg)
                except:
                    error_msg = response.text[:200]

                logger.error(f"LID Failed: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg
                }

        except requests.exceptions.Timeout:
            logger.error("LID request timed out")
            return {
                "success": False,
                "error": "Request timed out"
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"LID request failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"LID unexpected error: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }

    def detect_language_base64(
        self,
        audio_base64: str,
        audio_format: str = "wav"
    ) -> Dict[str, Any]:
        """
        Detect language from base64-encoded audio.

        Args:
            audio_base64: Base64 encoded audio string
            audio_format: Format of audio

        Returns:
            Same as detect_language()
        """
        try:
            # Remove data URL prefix if present
            if "," in audio_base64:
                audio_base64 = audio_base64.split(",")[1]

            audio_bytes = base64.b64decode(audio_base64)
            return self.detect_language(audio_bytes, audio_format)

        except Exception as e:
            logger.error(f"Failed to decode base64 audio: {e}")
            return {
                "success": False,
                "error": f"Invalid base64 audio: {str(e)}"
            }
