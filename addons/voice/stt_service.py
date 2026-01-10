"""
Speech-to-Text Service
======================
Converts speech to text using OpenAI Whisper API.

Usage:
    from addons.voice.stt_service import SpeechToTextService

    stt = SpeechToTextService()
    result = stt.transcribe(audio_bytes, language="en")
"""

import logging
import requests
import base64
from typing import Optional, Dict, Any, Union
from io import BytesIO

from .config import VoiceConfig

logger = logging.getLogger(__name__)


class SpeechToTextService:
    """
    Speech-to-Text service using OpenAI Whisper API.

    Transcribes speech in multiple languages with auto-detection.
    """

    def __init__(self):
        """Initialize STT service."""
        self.api_key = VoiceConfig.OPENAI_API_KEY
        self.base_url = VoiceConfig.OPENAI_BASE_URL
        self.endpoint = f"{self.base_url}/audio/transcriptions"

        if not self.api_key:
            logger.warning("OpenAI API key not configured. STT will not work.")

    def transcribe(
        self,
        audio_data: Union[bytes, BytesIO],
        language: str = None,
        audio_format: str = "wav",
        filename: str = "audio.wav"
    ) -> Dict[str, Any]:
        """
        Transcribe audio to text using OpenAI Whisper.

        Args:
            audio_data: Audio bytes or BytesIO object
            language: Language code ISO-639-1 (e.g., "en", "hi", or None for auto-detect)
            audio_format: Format of audio (wav, mp3, webm, etc.)
            filename: Filename for the upload

        Returns:
            {
                "success": True/False,
                "transcript": "transcribed text",
                "language_code": "detected language",
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

        # Use defaults if not provided
        language = language or VoiceConfig.STT_DEFAULT_LANGUAGE

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

        data = {
            "model": VoiceConfig.STT_DEFAULT_MODEL,
            "response_format": "verbose_json"  # Get language info
        }

        # Only add language if specified (otherwise Whisper auto-detects)
        if language:
            data["language"] = language

        logger.info(f"STT Request: {len(audio_data)} bytes, lang={language or 'auto'}, format={audio_format}")

        try:
            response = requests.post(
                self.endpoint,
                headers=headers,
                files=files,
                data=data,
                timeout=60  # Whisper can take longer for larger files
            )

            if response.status_code == 200:
                result = response.json()
                transcript = result.get("text", "")
                detected_lang = result.get("language", language or "unknown")

                logger.info(f"STT Success: '{transcript[:50]}...' (lang={detected_lang})")

                return {
                    "success": True,
                    "transcript": transcript,
                    "language_code": detected_lang,
                    "duration": result.get("duration"),
                    "segments": result.get("segments")
                }

            else:
                error_msg = f"OpenAI API error: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", error_msg)
                except:
                    error_msg = response.text[:200]

                logger.error(f"STT Failed: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg
                }

        except requests.exceptions.Timeout:
            logger.error("STT request timed out")
            return {
                "success": False,
                "error": "Request timed out. Audio may be too long."
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"STT request failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"STT unexpected error: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }

    def transcribe_base64(
        self,
        audio_base64: str,
        language: str = None,
        audio_format: str = "wav"
    ) -> Dict[str, Any]:
        """
        Transcribe base64-encoded audio to text.

        Useful when receiving audio from browser's MediaRecorder API.

        Args:
            audio_base64: Base64 encoded audio string
            language: Language code
            audio_format: Format of audio

        Returns:
            Same as transcribe()
        """
        try:
            # Remove data URL prefix if present
            if "," in audio_base64:
                audio_base64 = audio_base64.split(",")[1]

            audio_bytes = base64.b64decode(audio_base64)
            return self.transcribe(audio_bytes, language, audio_format)

        except Exception as e:
            logger.error(f"Failed to decode base64 audio: {e}")
            return {
                "success": False,
                "error": f"Invalid base64 audio: {str(e)}"
            }
