"""Audio encoding/decoding service"""

import logging
import base64
import io
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class AudioService:
    """Service for audio encoding, decoding, and format conversion"""

    def __init__(self):
        self.supported_formats = ["wav", "opus", "mp3", "ogg"]

    def encode_audio(self, audio_bytes: bytes) -> str:
        """
        Encode audio bytes to base64 string.

        Args:
            audio_bytes: Raw audio bytes

        Returns:
            Base64 encoded string
        """
        try:
            return base64.b64encode(audio_bytes).decode('utf-8')
        except Exception as e:
            logger.error(f"Audio encoding failed: {e}")
            raise ValueError(f"Failed to encode audio: {e}")

    def decode_audio(self, audio_base64: str) -> bytes:
        """
        Decode base64 audio string to bytes.

        Args:
            audio_base64: Base64 encoded audio string

        Returns:
            Raw audio bytes
        """
        try:
            return base64.b64decode(audio_base64)
        except Exception as e:
            logger.error(f"Audio decoding failed: {e}")
            raise ValueError(f"Failed to decode audio: {e}")

    def validate_audio_chunk(
        self,
        audio_data: str,
        max_size_kb: int = 512
    ) -> bool:
        """
        Validate audio chunk size and format.

        Args:
            audio_data: Base64 encoded audio data
            max_size_kb: Maximum allowed size in kilobytes

        Returns:
            bool: True if valid
        """
        try:
            # Check if valid base64
            audio_bytes = base64.b64decode(audio_data)

            # Check size
            size_kb = len(audio_bytes) / 1024
            if size_kb > max_size_kb:
                logger.warning(f"Audio chunk too large: {size_kb:.2f}KB > {max_size_kb}KB")
                return False

            return True

        except Exception as e:
            logger.error(f"Audio validation failed: {e}")
            return False

    def concatenate_audio_chunks(
        self,
        chunks: list[bytes],
        format: str = "wav"
    ) -> bytes:
        """
        Concatenate multiple audio chunks into a single file.

        Args:
            chunks: List of audio byte chunks
            format: Audio format

        Returns:
            Concatenated audio bytes
        """
        try:
            if format == "wav":
                return self._concatenate_wav_chunks(chunks)
            else:
                # For non-WAV formats, simple concatenation
                return b"".join(chunks)
        except Exception as e:
            logger.error(f"Audio concatenation failed: {e}")
            raise

    def _concatenate_wav_chunks(self, chunks: list[bytes]) -> bytes:
        """
        Concatenate WAV audio chunks properly.

        Note: This is a simplified version. Production systems should use
        a proper audio library like pydub or wave.
        """
        if not chunks:
            return b""

        if len(chunks) == 1:
            return chunks[0]

        # For simplicity, just concatenate the raw audio data
        # In production, properly handle WAV headers
        return b"".join(chunks)

    def get_audio_metadata(self, audio_bytes: bytes) -> Dict[str, Any]:
        """
        Extract metadata from audio bytes.

        Args:
            audio_bytes: Raw audio bytes

        Returns:
            Dict containing audio metadata
        """
        try:
            # Simple metadata extraction
            # In production, use proper audio library
            size_bytes = len(audio_bytes)
            size_kb = size_bytes / 1024

            # Try to detect format from header
            format_detected = "unknown"
            if audio_bytes[:4] == b"RIFF":
                format_detected = "wav"
            elif audio_bytes[:4] == b"OggS":
                format_detected = "ogg"
            elif audio_bytes[:3] == b"ID3" or audio_bytes[:2] == b"\xff\xfb":
                format_detected = "mp3"

            return {
                "size_bytes": size_bytes,
                "size_kb": size_kb,
                "format": format_detected
            }

        except Exception as e:
            logger.error(f"Failed to extract audio metadata: {e}")
            return {
                "size_bytes": len(audio_bytes),
                "size_kb": len(audio_bytes) / 1024,
                "format": "unknown",
                "error": str(e)
            }

    def convert_sample_rate(
        self,
        audio_bytes: bytes,
        source_rate: int,
        target_rate: int
    ) -> bytes:
        """
        Convert audio sample rate.

        Note: This is a placeholder. In production, use librosa, scipy, or ffmpeg.

        Args:
            audio_bytes: Raw audio bytes
            source_rate: Source sample rate
            target_rate: Target sample rate

        Returns:
            Converted audio bytes
        """
        logger.warning("Sample rate conversion not implemented - returning original audio")
        return audio_bytes


# Global service instance
audio_service = AudioService()
