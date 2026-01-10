"""
Text-to-Speech Service
======================
Converts text to speech using OpenAI TTS API.

Usage:
    from addons.voice.tts_service import TextToSpeechService

    tts = TextToSpeechService()
    result = tts.convert("Hello, how are you?", voice="alloy")
"""

import logging
import requests
import base64
from typing import Optional, Dict, Any, List

from .config import VoiceConfig

logger = logging.getLogger(__name__)

# OpenAI TTS has a limit of 4096 characters per request
MAX_CHUNK_SIZE = 4000


class TextToSpeechService:
    """
    Text-to-Speech service using OpenAI TTS API.

    Converts text to natural-sounding speech with multiple voice options.
    """

    def __init__(self):
        """Initialize TTS service."""
        self.api_key = VoiceConfig.OPENAI_API_KEY
        self.base_url = VoiceConfig.OPENAI_BASE_URL
        self.endpoint = f"{self.base_url}/audio/speech"

        if not self.api_key:
            logger.warning("OpenAI API key not configured. TTS will not work.")

    def _split_text_into_chunks(self, text: str, max_size: int = MAX_CHUNK_SIZE) -> List[str]:
        """
        Split text into chunks at sentence boundaries.

        Args:
            text: Text to split
            max_size: Maximum characters per chunk

        Returns:
            List of text chunks
        """
        if len(text) <= max_size:
            return [text]

        chunks = []
        current_chunk = ""

        # Split by sentences
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            if len(sentence) > max_size:
                # Split long sentences by commas or words
                parts = re.split(r'(?<=[,;:])\s+', sentence)
                for part in parts:
                    part = part.strip()
                    if not part:
                        continue
                    if len(current_chunk) + len(part) + 1 <= max_size:
                        current_chunk = (current_chunk + " " + part).strip()
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        if len(part) > max_size:
                            # Split by words as last resort
                            words = part.split()
                            current_chunk = ""
                            for word in words:
                                if len(current_chunk) + len(word) + 1 <= max_size:
                                    current_chunk = (current_chunk + " " + word).strip()
                                else:
                                    if current_chunk:
                                        chunks.append(current_chunk)
                                    current_chunk = word
                        else:
                            current_chunk = part
            else:
                if len(current_chunk) + len(sentence) + 1 <= max_size:
                    current_chunk = (current_chunk + " " + sentence).strip()
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = sentence

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def convert(
        self,
        text: str,
        voice: str = None,
        model: str = None,
        speed: float = None,
        output_format: str = None,
        **kwargs  # Accept but ignore legacy parameters like language, pitch, pace, loudness
    ) -> Dict[str, Any]:
        """
        Convert text to speech using OpenAI TTS.

        Args:
            text: Text to convert (any length - will be chunked if needed)
            voice: Voice name (alloy, echo, fable, onyx, nova, shimmer)
            model: TTS model (tts-1, tts-1-hd)
            speed: Speech speed (0.25 to 4.0)
            output_format: Audio format (mp3, opus, aac, flac, wav, pcm)

        Returns:
            {
                "success": True/False,
                "audio_base64": "base64_encoded_audio",
                "content_type": "audio/mpeg",
                "error": "error message if failed"
            }
        """
        if not self.api_key:
            return {
                "success": False,
                "error": "OpenAI API key not configured"
            }

        if not text or not text.strip():
            return {
                "success": False,
                "error": "Text cannot be empty"
            }

        # Use defaults if not provided
        voice = voice or VoiceConfig.TTS_DEFAULT_VOICE
        model = model or VoiceConfig.TTS_DEFAULT_MODEL
        speed = speed if speed is not None else VoiceConfig.TTS_SPEED
        output_format = output_format or VoiceConfig.TTS_OUTPUT_FORMAT

        # Validate voice
        valid_voices = VoiceConfig.get_all_voices()
        if voice.lower() not in valid_voices:
            logger.warning(f"Voice {voice} not valid, using default")
            voice = VoiceConfig.TTS_DEFAULT_VOICE

        # Validate format
        if output_format not in VoiceConfig.SUPPORTED_TTS_FORMATS:
            logger.warning(f"Format {output_format} not supported, using mp3")
            output_format = "mp3"

        # Clamp speed to valid range
        speed = max(0.25, min(4.0, speed))

        # Build headers
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Split text into chunks if needed
        chunks = self._split_text_into_chunks(text.strip())
        logger.info(f"TTS Request: {len(text)} chars, {len(chunks)} chunks, voice={voice}, model={model}")

        # Determine content type
        content_types = {
            "mp3": "audio/mpeg",
            "opus": "audio/opus",
            "aac": "audio/aac",
            "flac": "audio/flac",
            "wav": "audio/wav",
            "pcm": "audio/pcm"
        }
        content_type = content_types.get(output_format, "audio/mpeg")

        try:
            audio_parts = []

            for i, chunk in enumerate(chunks):
                logger.info(f"TTS Chunk {i+1}/{len(chunks)}: {len(chunk)} chars")

                payload = {
                    "model": model,
                    "input": chunk,
                    "voice": voice.lower(),
                    "response_format": output_format,
                    "speed": speed
                }

                response = requests.post(
                    self.endpoint,
                    headers=headers,
                    json=payload,
                    timeout=60
                )

                if response.status_code == 200:
                    audio_parts.append(response.content)
                else:
                    error_msg = f"OpenAI API error: {response.status_code}"
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("error", {}).get("message", error_msg)
                    except:
                        error_msg = response.text[:200]

                    logger.error(f"TTS Chunk {i+1} failed: {error_msg}")
                    return {
                        "success": False,
                        "error": error_msg
                    }

            # Concatenate audio parts
            combined_audio = b''.join(audio_parts)
            combined_base64 = base64.b64encode(combined_audio).decode('utf-8')

            logger.info(f"TTS Success: Generated audio ({len(combined_base64)} chars base64)")

            return {
                "success": True,
                "audio_base64": combined_base64,
                "content_type": content_type,
                "chunks_processed": len(chunks)
            }

        except requests.exceptions.Timeout:
            logger.error("TTS request timed out")
            return {
                "success": False,
                "error": "Request timed out"
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"TTS request failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"TTS unexpected error: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }

    def get_audio_bytes(self, audio_base64: str) -> bytes:
        """
        Decode base64 audio to bytes.

        Args:
            audio_base64: Base64 encoded audio string

        Returns:
            Audio bytes
        """
        return base64.b64decode(audio_base64)
