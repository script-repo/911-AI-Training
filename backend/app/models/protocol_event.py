"""Protocol event and scoring models for call evaluation"""
import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.database import Base


class ProtocolEventType(str, enum.Enum):
    """Standard 911 protocol events tracked during calls."""
    LOCATION_OBTAINED = "location_obtained"
    CALLBACK_NUMBER_OBTAINED = "callback_number_obtained"
    CHIEF_COMPLAINT_IDENTIFIED = "chief_complaint_identified"
    CONSCIOUSNESS_VERIFIED = "consciousness_verified"
    BREATHING_VERIFIED = "breathing_verified"
    WEAPON_INQUIRY = "weapon_inquiry"
    WEAPON_TYPE_CONFIRMED = "weapon_type_confirmed"
    SUSPECT_DESCRIPTION = "suspect_description"
    CALLER_SAFETY_VERIFIED = "caller_safety_verified"
    MEDICAL_HISTORY_ASKED = "medical_history_asked"
    SCENE_SAFETY_ASSESSED = "scene_safety_assessed"
    CALLER_NAME_OBTAINED = "caller_name_obtained"
    VICTIM_COUNT_CONFIRMED = "victim_count_confirmed"
    DISPATCH_INITIATED = "dispatch_initiated"
    CPR_INSTRUCTIONS_GIVEN = "cpr_instructions_given"
    CALLER_CALMED = "caller_calmed"
    CUSTOM = "custom"


class ProtocolEvent(Base):
    """Individual protocol adherence events tracked during a call."""
    __tablename__ = "protocol_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    call_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("call_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[ProtocolEventType] = mapped_column(
        Enum(ProtocolEventType, name="protocol_event_type_enum", create_type=True),
        nullable=False,
    )
    timestamp_ms: Mapped[int] = mapped_column(
        Integer, nullable=False,
        comment="Milliseconds from call start when event was detected"
    )
    details: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True,
        comment="Additional event details (extracted value, confidence, etc.)"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    session: Mapped["CallSession"] = relationship(back_populates="protocol_events")

    def __repr__(self) -> str:
        return f"<ProtocolEvent(type={self.event_type.value}, at={self.timestamp_ms}ms)>"


class CallScore(Base):
    """Computed score for a completed call session."""
    __tablename__ = "call_scores"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    call_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("call_sessions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    total_score: Mapped[float] = mapped_column(Float, nullable=False)
    max_possible_score: Mapped[float] = mapped_column(Float, nullable=False, default=100.0)
    subscores: Mapped[dict] = mapped_column(
        JSONB, nullable=False,
        comment="Per-criterion scores: {criterion: {points, max, threshold_met, details}}"
    )
    protocol_errors: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True,
        comment="List of protocol errors: missed questions, late responses, etc."
    )
    feedback: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True,
        comment="Actionable feedback items for the trainee"
    )
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    session: Mapped["CallSession"] = relationship(back_populates="score")

    def __repr__(self) -> str:
        return f"<CallScore(call={self.call_id}, score={self.total_score})>"
