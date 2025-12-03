"""Coqui TTS integration service for text-to-speech"""

import logging
import base64
from typing import Dict, Any, Optional
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


class TTSService:
    """Service for text-to-speech using Coqui TTS"""

    def __init__(self):
        self.tts_url = settings.coqui_tts_url
        self.model = settings.tts_model
        self.vocoder = settings.tts_vocoder
        self.sample_rate = settings.tts_sample_rate

    async def synthesize_speech(
        self,
        text: str,
        emotional_state: Optional[str] = "neutral",
        speaker_profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Synthesize speech from text using Coqui TTS.

        Args:
            text: Text to convert to speech
            emotional_state: Emotional state to apply (affects prosody)
            speaker_profile: Optional speaker characteristics

        Returns:
            Dict containing audio data, sample rate, duration, and format
        """
        try:
            # Adjust text based on emotional state
            processed_text = self._apply_emotional_prosody(text, emotional_state)

            # Call Coqui TTS API
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.tts_url}/api/tts",
                    params={
                        "text": processed_text,
                        "model_name": self.model,
                        "vocoder_name": self.vocoder,
                    }
                )
                response.raise_for_status()

            # Encode audio data to base64
            audio_bytes = response.content
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')

            # Calculate approximate duration (rough estimate)
            # Actual duration depends on speech rate, typically ~150 words/minute
            word_count = len(text.split())
            estimated_duration_ms = int((word_count / 150) * 60 * 1000)

            return {
                "audio_data": audio_base64,
                "sample_rate": self.sample_rate,
                "duration_ms": estimated_duration_ms,
                "format": "wav"
            }

        except httpx.HTTPError as e:
            logger.error(f"TTS API request failed: {e}")
            raise Exception(f"TTS service unavailable: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in TTS service: {e}")
            raise

    def _apply_emotional_prosody(self, text: str, emotional_state: Optional[str]) -> str:
        """
        Apply emotional prosody markers to text.

        Note: This is a simplified approach. Production systems would use
        more sophisticated prosody control through the TTS engine.
        """
        if not emotional_state or emotional_state == "calm":
            return text

        # Add pauses and emphasis based on emotional state
        if emotional_state == "panicked":
            # Add urgency with shorter phrases
            text = text.replace(". ", "... ")
            text = text.upper() if len(text) < 50 else text
        elif emotional_state == "anxious":
            # Add hesitation markers
            words = text.split()
            if len(words) > 3:
                words.insert(len(words) // 2, "um,")
            text = " ".join(words)

        return text

    async def get_available_models(self) -> Dict[str, Any]:
        """
        Get list of available TTS models.

        Returns:
            Dict containing available models and vocoders
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.tts_url}/api/models")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch TTS models: {e}")
            return {"models": [], "vocoders": []}

    async def health_check(self) -> bool:
        """
        Check if TTS service is healthy.

        Returns:
            bool: True if service is healthy
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.tts_url}/api/models")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"TTS health check failed: {e}")
            return False


# Global service instance
tts_service = TTSService()
