"""
OpenAI Realtime Voice Service
=============================
Manages sessions for OpenAI Realtime API.

The Realtime API enables real-time, bidirectional audio streaming
for voice conversations with AI.

Usage:
    from addons.voice.realtime_service import RealtimeVoiceService

    service = RealtimeVoiceService()
    session = service.create_session(
        instructions="You are a helpful assistant.",
        voice="alloy"
    )
    # Returns ephemeral token for frontend WebSocket connection
"""

import logging
import requests
from typing import Dict, Any, Optional

from .config import VoiceConfig

logger = logging.getLogger(__name__)

# OpenAI Realtime API configuration
REALTIME_MODEL = "gpt-4o-realtime-preview-2024-12-17"
REALTIME_SESSION_URL = "https://api.openai.com/v1/realtime/sessions"
REALTIME_WEBSOCKET_URL = "wss://api.openai.com/v1/realtime"


class RealtimeVoiceService:
    """
    Service for managing OpenAI Realtime Voice sessions.

    Creates ephemeral session tokens that frontend can use to connect
    directly to OpenAI's Realtime WebSocket API.
    """

    def __init__(self):
        """Initialize Realtime Voice service."""
        self.api_key = VoiceConfig.OPENAI_API_KEY

        if not self.api_key:
            logger.warning("OpenAI API key not configured. Realtime Voice will not work.")

    def create_session(
        self,
        instructions: str = None,
        voice: str = None,
        input_audio_format: str = "pcm16",
        output_audio_format: str = "pcm16",
        input_audio_transcription: bool = True,
        turn_detection: Dict[str, Any] = None,
        tools: list = None,
        temperature: float = 0.8,
        max_response_output_tokens: int = 4096
    ) -> Dict[str, Any]:
        """
        Create a new Realtime API session and get ephemeral client token.

        Args:
            instructions: System instructions for the AI assistant
            voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer)
            input_audio_format: Audio format for input (pcm16, g711_ulaw, g711_alaw)
            output_audio_format: Audio format for output (pcm16, g711_ulaw, g711_alaw)
            input_audio_transcription: Whether to transcribe user's audio
            turn_detection: Turn detection config (server_vad or none)
            tools: List of tools/functions the AI can call
            temperature: Response randomness (0.6 to 1.2)
            max_response_output_tokens: Max tokens in response

        Returns:
            {
                "success": True/False,
                "client_secret": "ephemeral token for WebSocket auth",
                "expires_at": Unix timestamp,
                "session_id": "session identifier",
                "websocket_url": "wss://api.openai.com/v1/realtime?model=...",
                "config": { session configuration },
                "error": "error message if failed"
            }
        """
        if not self.api_key:
            return {
                "success": False,
                "error": "OpenAI API key not configured"
            }

        # Use defaults
        voice = voice or VoiceConfig.TTS_DEFAULT_VOICE
        instructions = instructions or "You are a helpful AI assistant. Be concise and friendly."

        # Default turn detection (Voice Activity Detection)
        if turn_detection is None:
            turn_detection = {
                "type": "server_vad",
                "threshold": 0.5,
                "prefix_padding_ms": 300,
                "silence_duration_ms": 500
            }

        # Build session configuration
        session_config = {
            "model": REALTIME_MODEL,
            "voice": voice,
            "instructions": instructions,
            "input_audio_format": input_audio_format,
            "output_audio_format": output_audio_format,
            "input_audio_transcription": {
                "model": "whisper-1"
            } if input_audio_transcription else None,
            "turn_detection": turn_detection,
            "temperature": temperature,
            "max_response_output_tokens": max_response_output_tokens
        }

        # Add tools if provided
        if tools:
            session_config["tools"] = tools
            session_config["tool_choice"] = "auto"

        # Remove None values
        session_config = {k: v for k, v in session_config.items() if v is not None}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        logger.info(f"Creating Realtime session: voice={voice}, model={REALTIME_MODEL}")

        try:
            response = requests.post(
                REALTIME_SESSION_URL,
                headers=headers,
                json=session_config,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()

                # Extract client secret (ephemeral token)
                client_secret = data.get("client_secret", {})

                logger.info(f"Realtime session created: {data.get('id', 'unknown')}")

                return {
                    "success": True,
                    "session_id": data.get("id"),
                    "client_secret": client_secret.get("value"),
                    "expires_at": client_secret.get("expires_at"),
                    "websocket_url": f"{REALTIME_WEBSOCKET_URL}?model={REALTIME_MODEL}",
                    "model": REALTIME_MODEL,
                    "voice": voice,
                    "config": {
                        "input_audio_format": input_audio_format,
                        "output_audio_format": output_audio_format,
                        "sample_rate": 24000,  # OpenAI Realtime uses 24kHz
                        "channels": 1,  # Mono
                        "turn_detection": turn_detection
                    }
                }

            else:
                error_msg = f"OpenAI API error: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", error_msg)
                except:
                    error_msg = response.text[:200]

                logger.error(f"Realtime session creation failed: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg
                }

        except requests.exceptions.Timeout:
            logger.error("Realtime session request timed out")
            return {
                "success": False,
                "error": "Request timed out"
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Realtime session request failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Realtime session unexpected error: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }

    def get_connection_info(self) -> Dict[str, Any]:
        """
        Get information about how to connect to OpenAI Realtime API.

        Returns:
            Connection configuration and requirements
        """
        return {
            "websocket_url": f"{REALTIME_WEBSOCKET_URL}?model={REALTIME_MODEL}",
            "model": REALTIME_MODEL,
            "audio_config": {
                "sample_rate": 24000,
                "channels": 1,
                "format": "pcm16",
                "bits_per_sample": 16
            },
            "available_voices": VoiceConfig.get_all_voices(),
            "default_voice": VoiceConfig.TTS_DEFAULT_VOICE,
            "turn_detection_modes": ["server_vad", "none"],
            "documentation": "https://platform.openai.com/docs/guides/realtime"
        }
