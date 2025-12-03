"""Pydantic schemas for request/response validation"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


# WebSocket Message Schemas
class WSMessageBase(BaseModel):
    """Base WebSocket message schema"""
    type: str
    session_id: UUID


class WSAudioChunk(WSMessageBase):
    """WebSocket audio chunk message"""
    type: Literal["audio_chunk"] = "audio_chunk"
    audio_data: str = Field(..., description="Base64 encoded audio data")
    timestamp_ms: int


class WSControlMessage(WSMessageBase):
    """WebSocket control message"""
    type: Literal["control"] = "control"
    action: Literal["mute", "unmute", "hold", "resume", "terminate"]


class WSTranscriptUpdate(WSMessageBase):
    """WebSocket transcript update message"""
    type: Literal["transcript_update"] = "transcript_update"
    transcript_id: UUID
    speaker: Literal["operator", "caller"]
    text: str
    timestamp_ms: int
    confidence_score: Optional[float] = None


class WSEntityUpdate(WSMessageBase):
    """WebSocket entity extraction update"""
    type: Literal["entity_update"] = "entity_update"
    entity_id: UUID
    entity_type: str
    entity_value: str
    confidence_score: float


class WSEmotionalState(WSMessageBase):
    """WebSocket emotional state update"""
    type: Literal["emotional_state"] = "emotional_state"
    state: str
    intensity: float
    timestamp_ms: int


class WSError(WSMessageBase):
    """WebSocket error message"""
    type: Literal["error"] = "error"
    error_code: str
    error_message: str


# Call Session Schemas
class CallSessionCreate(BaseModel):
    """Schema for creating a new call session"""
    operator_id: str = Field(..., min_length=1, max_length=100)
    scenario_id: UUID


class CallSessionResponse(BaseModel):
    """Schema for call session response"""
    id: UUID
    operator_id: str
    scenario_id: UUID
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    status: str
    metadata: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class CallSessionEnd(BaseModel):
    """Schema for ending a call session"""
    notes: Optional[str] = None
    operator_feedback: Optional[Dict[str, Any]] = None


# Transcript Schemas
class TranscriptEntryResponse(BaseModel):
    """Schema for transcript entry response"""
    id: UUID
    session_id: UUID
    timestamp_ms: int
    speaker: str
    text: str
    audio_url: Optional[str] = None
    emotional_state: Optional[str] = None
    confidence_score: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class TranscriptListResponse(BaseModel):
    """Schema for list of transcript entries"""
    session_id: UUID
    transcripts: List[TranscriptEntryResponse]
    total_count: int


# Entity Schemas
class ExtractedEntityResponse(BaseModel):
    """Schema for extracted entity response"""
    id: UUID
    transcript_id: UUID
    entity_type: str
    entity_value: str
    confidence_score: float
    start_char: int
    end_char: int
    metadata: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


# Training Scenario Schemas
class CallerProfile(BaseModel):
    """Schema for caller profile configuration"""
    name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    initial_emotional_state: str = "calm"
    personality_traits: List[str] = Field(default_factory=list)
    background_story: Optional[str] = None


class ScenarioScript(BaseModel):
    """Schema for scenario script configuration"""
    initial_situation: str
    emergency_type: str
    location_type: str
    key_information: Dict[str, Any]
    escalation_triggers: List[str] = Field(default_factory=list)
    expected_questions: List[str] = Field(default_factory=list)


class TrainingScenarioCreate(BaseModel):
    """Schema for creating a training scenario"""
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    caller_profile: CallerProfile
    scenario_script: ScenarioScript
    difficulty_level: Literal["beginner", "intermediate", "advanced", "expert"] = "beginner"


class TrainingScenarioResponse(BaseModel):
    """Schema for training scenario response"""
    id: UUID
    name: str
    description: str
    caller_profile: Dict[str, Any]
    scenario_script: Dict[str, Any]
    difficulty_level: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TrainingScenarioListResponse(BaseModel):
    """Schema for list of training scenarios"""
    scenarios: List[TrainingScenarioResponse]
    total_count: int


# Health Check Schemas
class HealthCheckResponse(BaseModel):
    """Schema for health check response"""
    status: str
    timestamp: datetime
    version: str


class ReadinessCheckResponse(BaseModel):
    """Schema for readiness check response"""
    status: str
    database: bool
    redis: bool
    s3: bool
    tts: bool
    timestamp: datetime


# LLM Service Schemas
class LLMRequest(BaseModel):
    """Schema for LLM request"""
    session_id: UUID
    conversation_history: List[Dict[str, str]]
    caller_profile: Dict[str, Any]
    scenario_context: Dict[str, Any]
    current_emotional_state: str


class LLMResponse(BaseModel):
    """Schema for LLM response"""
    response_text: str
    emotional_state: str
    confidence: float
    metadata: Optional[Dict[str, Any]] = None


# TTS Service Schemas
class TTSRequest(BaseModel):
    """Schema for TTS request"""
    text: str
    emotional_state: Optional[str] = "neutral"
    speaker_profile: Optional[Dict[str, Any]] = None


class TTSResponse(BaseModel):
    """Schema for TTS response"""
    audio_data: str = Field(..., description="Base64 encoded audio data")
    sample_rate: int
    duration_ms: int
    format: str


# NLP Service Schemas
class EntityExtractionRequest(BaseModel):
    """Schema for entity extraction request"""
    text: str
    session_id: UUID
    timestamp_ms: int


class EntityExtractionResponse(BaseModel):
    """Schema for entity extraction response"""
    entities: List[Dict[str, Any]]
    text: str
    processing_time_ms: float
