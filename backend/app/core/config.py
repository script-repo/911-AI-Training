"""Application configuration management using Pydantic Settings"""

from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # OpenRouter LLM Configuration
    openrouter_api_key: str = Field(..., alias="OPENROUTER_API_KEY")
    llm_model: str = Field(default="deepseek/deepseek-chat", alias="LLM_MODEL")
    llm_base_url: str = Field(default="https://openrouter.ai/api/v1", alias="LLM_BASE_URL")
    llm_temperature: float = Field(default=0.8, alias="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=150, alias="LLM_MAX_TOKENS")

    # Database Configuration
    database_url: str = Field(..., alias="DATABASE_URL")
    db_username: str = Field(default="postgres", alias="DB_USERNAME")
    db_password: str = Field(default="postgres", alias="DB_PASSWORD")
    db_host: str = Field(default="postgresql-service", alias="DB_HOST")
    db_port: int = Field(default=5432, alias="DB_PORT")
    db_name: str = Field(default="training_db", alias="DB_NAME")

    # Redis Configuration
    redis_url: str = Field(..., alias="REDIS_URL")
    redis_host: str = Field(default="redis-service", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_password: Optional[str] = Field(default="", alias="REDIS_PASSWORD")
    redis_db: int = Field(default=0, alias="REDIS_DB")

    # S3/MinIO Configuration
    s3_endpoint: str = Field(..., alias="S3_ENDPOINT")
    s3_access_key: str = Field(..., alias="S3_ACCESS_KEY")
    s3_secret_key: str = Field(..., alias="S3_SECRET_KEY")
    s3_bucket_name: str = Field(default="911-training-recordings", alias="S3_BUCKET_NAME")
    s3_region: str = Field(default="us-east-1", alias="S3_REGION")
    s3_secure: bool = Field(default=False, alias="S3_SECURE")

    # Coqui TTS Configuration
    coqui_tts_url: str = Field(..., alias="COQUI_TTS_URL")
    tts_model: str = Field(default="tts_models/en/ljspeech/tacotron2-DDC", alias="TTS_MODEL")
    tts_vocoder: str = Field(default="vocoder_models/en/ljspeech/hifigan_v2", alias="TTS_VOCODER")
    tts_sample_rate: int = Field(default=22050, alias="TTS_SAMPLE_RATE")

    # Application Configuration
    backend_host: str = Field(default="0.0.0.0", alias="BACKEND_HOST")
    backend_port: int = Field(default=8000, alias="BACKEND_PORT")
    backend_workers: int = Field(default=4, alias="BACKEND_WORKERS")
    frontend_port: int = Field(default=3000, alias="FRONTEND_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    environment: str = Field(default="development", alias="ENVIRONMENT")

    # Audio Processing
    audio_codec: str = Field(default="opus", alias="AUDIO_CODEC")
    audio_sample_rate: int = Field(default=16000, alias="AUDIO_SAMPLE_RATE")
    audio_channels: int = Field(default=1, alias="AUDIO_CHANNELS")
    audio_bitrate: int = Field(default=24000, alias="AUDIO_BITRATE")
    audio_frame_duration_ms: int = Field(default=20, alias="AUDIO_FRAME_DURATION_MS")

    # Session Configuration
    session_ttl: int = Field(default=3600, alias="SESSION_TTL")
    max_concurrent_calls: int = Field(default=50, alias="MAX_CONCURRENT_CALLS")
    rate_limit_llm_per_minute: int = Field(default=10, alias="RATE_LIMIT_LLM_PER_MINUTE")

    # CORS Configuration
    cors_origins: str = Field(default="http://localhost:3000,http://localhost:8000", alias="CORS_ORIGINS")

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def async_database_url(self) -> str:
        """Get async database URL for SQLAlchemy"""
        return self.database_url.replace("postgresql://", "postgresql+asyncpg://")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Global settings instance
settings = Settings()
