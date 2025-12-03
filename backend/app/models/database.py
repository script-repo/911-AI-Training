"""
Database models for 911 Operator Training Simulator.

This module defines SQLAlchemy ORM models for the application including:
- CallSession: Records of operator training sessions
- CallTranscript: Dialogue entries during calls
- ExtractedEntity: Named entities extracted from transcripts
- TrainingScenario: Pre-configured training scenarios
- PerformanceMetrics: Metrics tracking operator performance
"""
import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


# Enums
class CallSessionStatus(str, enum.Enum):
    """Status of a call session."""
    ACTIVE = "active"
    COMPLETED = "completed"
    TERMINATED = "terminated"
    ERROR = "error"


class Speaker(str, enum.Enum):
    """Speaker in a call transcript."""
    OPERATOR = "operator"
    CALLER = "caller"


class DifficultyLevel(str, enum.Enum):
    """Difficulty level of training scenarios."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class TrainingScenario(Base):
    """
    Training scenarios for 911 operator simulation.

    Contains pre-configured scenarios with caller profiles and expected flows.
    """
    __tablename__ = "training_scenarios"
    __table_args__ = (
        Index("ix_training_scenarios_difficulty_active", "difficulty_level", "is_active"),
        {"comment": "Pre-configured training scenarios for operator practice"}
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique identifier for the scenario"
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Human-readable scenario name"
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Detailed description of the scenario"
    )
    caller_profile: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        comment="Caller personality, background, and emotional state"
    )
    scenario_script: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        comment="Initial conditions and expected dialogue flow"
    )
    difficulty_level: Mapped[DifficultyLevel] = mapped_column(
        Enum(DifficultyLevel, name="difficulty_level_enum", create_type=True),
        nullable=False,
        comment="Difficulty rating for the scenario"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether this scenario is available for training"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="When the scenario was created"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="When the scenario was last updated"
    )

    # Relationships
    call_sessions: Mapped[list["CallSession"]] = relationship(
        back_populates="scenario",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<TrainingScenario(id={self.id}, name='{self.name}', difficulty={self.difficulty_level.value})>"


class CallSession(Base):
    """
    Records of operator training call sessions.

    Tracks individual training calls from start to finish with metadata.
    """
    __tablename__ = "call_sessions"
    __table_args__ = (
        Index("ix_call_sessions_operator_started", "operator_id", "started_at"),
        {"comment": "Training call sessions with operators"}
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique identifier for the call session"
    )
    operator_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Identifier for the operator trainee"
    )
    scenario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("training_scenarios.id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to the training scenario used"
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="When the call session started"
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the call session ended"
    )
    duration_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Total duration of call in milliseconds"
    )
    status: Mapped[CallSessionStatus] = mapped_column(
        Enum(CallSessionStatus, name="call_session_status_enum", create_type=True),
        nullable=False,
        default=CallSessionStatus.ACTIVE,
        comment="Current status of the call session"
    )
    metadata: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Flexible storage for additional session data"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Record creation timestamp"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Record last update timestamp"
    )

    # Relationships
    scenario: Mapped["TrainingScenario"] = relationship(back_populates="call_sessions")
    transcripts: Mapped[list["CallTranscript"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="CallTranscript.timestamp_ms"
    )
    performance_metrics: Mapped[list["PerformanceMetrics"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<CallSession(id={self.id}, operator={self.operator_id}, status={self.status.value})>"


class CallTranscript(Base):
    """
    Individual dialogue entries during a call session.

    Records each utterance with timestamp, speaker, and emotional analysis.
    """
    __tablename__ = "call_transcripts"
    __table_args__ = (
        Index("ix_call_transcripts_session_timestamp", "session_id", "timestamp_ms"),
        {"comment": "Dialogue entries during call sessions"}
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique identifier for the transcript entry"
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("call_sessions.id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to the call session"
    )
    timestamp_ms: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        comment="Milliseconds from call start when this was spoken"
    )
    speaker: Mapped[Speaker] = mapped_column(
        Enum(Speaker, name="speaker_enum", create_type=True),
        nullable=False,
        comment="Who spoke this line (operator or caller)"
    )
    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Transcribed text of what was said"
    )
    audio_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="S3 URL to audio recording of this utterance"
    )
    emotional_state: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Detected emotional state (calm, anxious, panicked, hysterical)"
    )
    confidence_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Confidence score of transcription (0.0 to 1.0)"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Record creation timestamp"
    )

    # Relationships
    session: Mapped["CallSession"] = relationship(back_populates="transcripts")
    extracted_entities: Mapped[list["ExtractedEntity"]] = relationship(
        back_populates="transcript",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        preview = self.text[:50] + "..." if len(self.text) > 50 else self.text
        return f"<CallTranscript(id={self.id}, speaker={self.speaker.value}, text='{preview}')>"


class ExtractedEntity(Base):
    """
    Named entities extracted from call transcripts.

    Identifies key information like weapons, injuries, locations, etc.
    """
    __tablename__ = "extracted_entities"
    __table_args__ = (
        Index("ix_extracted_entities_transcript_type", "transcript_id", "entity_type"),
        {"comment": "Named entities extracted from transcripts"}
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique identifier for the entity"
    )
    transcript_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("call_transcripts.id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to the transcript containing this entity"
    )
    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Type of entity (WEAPON, INJURY, LOCATION, PERSON, VEHICLE, TIME_REFERENCE)"
    )
    entity_value: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="The actual text value of the entity"
    )
    confidence_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Confidence score of entity extraction (0.0 to 1.0)"
    )
    start_char: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Starting character position in transcript text"
    )
    end_char: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Ending character position in transcript text"
    )
    metadata: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Additional entity-specific data"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Record creation timestamp"
    )

    # Relationships
    transcript: Mapped["CallTranscript"] = relationship(back_populates="extracted_entities")

    def __repr__(self) -> str:
        return f"<ExtractedEntity(id={self.id}, type={self.entity_type}, value='{self.entity_value}')>"


class PerformanceMetrics(Base):
    """
    Performance metrics for operator training sessions.

    Tracks various performance indicators for analysis and improvement.
    """
    __tablename__ = "performance_metrics"
    __table_args__ = (
        Index("ix_performance_metrics_session", "session_id"),
        {"comment": "Performance metrics for operator training"}
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique identifier for the metric"
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("call_sessions.id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to the call session"
    )
    metric_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Name of the metric (response_time, empathy_score, info_gathered, etc.)"
    )
    metric_value: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Numeric value of the metric"
    )
    measured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="When this metric was measured"
    )

    # Relationships
    session: Mapped["CallSession"] = relationship(back_populates="performance_metrics")

    def __repr__(self) -> str:
        return f"<PerformanceMetrics(id={self.id}, metric={self.metric_name}, value={self.metric_value})>"
