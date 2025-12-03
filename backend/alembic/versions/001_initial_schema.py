"""Initial database schema for 911 Operator Training Simulator

Revision ID: 001
Revises:
Create Date: 2025-12-03

This migration creates the initial database schema including:
- training_scenarios: Pre-configured training scenarios
- call_sessions: Training call session records
- call_transcripts: Dialogue entries during calls
- extracted_entities: Named entities from transcripts
- performance_metrics: Operator performance tracking

All tables use UUID primary keys and include proper indexes and constraints.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all initial tables and indexes."""

    # Create enum types
    op.execute("CREATE TYPE difficulty_level_enum AS ENUM ('easy', 'medium', 'hard')")
    op.execute("CREATE TYPE call_session_status_enum AS ENUM ('active', 'completed', 'terminated', 'error')")
    op.execute("CREATE TYPE speaker_enum AS ENUM ('operator', 'caller')")

    # Create training_scenarios table
    op.create_table(
        'training_scenarios',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='Unique identifier for the scenario'),
        sa.Column('name', sa.String(length=200), nullable=False, comment='Human-readable scenario name'),
        sa.Column('description', sa.Text(), nullable=False, comment='Detailed description of the scenario'),
        sa.Column('caller_profile', postgresql.JSONB(astext_type=sa.Text()), nullable=False, comment='Caller personality, background, and emotional state'),
        sa.Column('scenario_script', postgresql.JSONB(astext_type=sa.Text()), nullable=False, comment='Initial conditions and expected dialogue flow'),
        sa.Column('difficulty_level', sa.Enum('easy', 'medium', 'hard', name='difficulty_level_enum', create_type=False), nullable=False, comment='Difficulty rating for the scenario'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', comment='Whether this scenario is available for training'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='When the scenario was created'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='When the scenario was last updated'),
        sa.PrimaryKeyConstraint('id'),
        comment='Pre-configured training scenarios for operator practice'
    )
    op.create_index('ix_training_scenarios_difficulty_active', 'training_scenarios', ['difficulty_level', 'is_active'])

    # Create call_sessions table
    op.create_table(
        'call_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='Unique identifier for the call session'),
        sa.Column('operator_id', sa.String(length=100), nullable=False, comment='Identifier for the operator trainee'),
        sa.Column('scenario_id', postgresql.UUID(as_uuid=True), nullable=False, comment='Reference to the training scenario used'),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='When the call session started'),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True, comment='When the call session ended'),
        sa.Column('duration_ms', sa.Integer(), nullable=True, comment='Total duration of call in milliseconds'),
        sa.Column('status', sa.Enum('active', 'completed', 'terminated', 'error', name='call_session_status_enum', create_type=False), nullable=False, comment='Current status of the call session'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Flexible storage for additional session data'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record last update timestamp'),
        sa.ForeignKeyConstraint(['scenario_id'], ['training_scenarios.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='Training call sessions with operators'
    )
    op.create_index('ix_call_sessions_operator_id', 'call_sessions', ['operator_id'])
    op.create_index('ix_call_sessions_operator_started', 'call_sessions', ['operator_id', 'started_at'])

    # Create call_transcripts table
    op.create_table(
        'call_transcripts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='Unique identifier for the transcript entry'),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False, comment='Reference to the call session'),
        sa.Column('timestamp_ms', sa.BigInteger(), nullable=False, comment='Milliseconds from call start when this was spoken'),
        sa.Column('speaker', sa.Enum('operator', 'caller', name='speaker_enum', create_type=False), nullable=False, comment='Who spoke this line (operator or caller)'),
        sa.Column('text', sa.Text(), nullable=False, comment='Transcribed text of what was said'),
        sa.Column('audio_url', sa.String(length=500), nullable=True, comment='S3 URL to audio recording of this utterance'),
        sa.Column('emotional_state', sa.String(length=20), nullable=True, comment='Detected emotional state (calm, anxious, panicked, hysterical)'),
        sa.Column('confidence_score', sa.Float(), nullable=True, comment='Confidence score of transcription (0.0 to 1.0)'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record creation timestamp'),
        sa.ForeignKeyConstraint(['session_id'], ['call_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='Dialogue entries during call sessions'
    )
    op.create_index('ix_call_transcripts_session_timestamp', 'call_transcripts', ['session_id', 'timestamp_ms'])

    # Create extracted_entities table
    op.create_table(
        'extracted_entities',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='Unique identifier for the entity'),
        sa.Column('transcript_id', postgresql.UUID(as_uuid=True), nullable=False, comment='Reference to the transcript containing this entity'),
        sa.Column('entity_type', sa.String(length=50), nullable=False, comment='Type of entity (WEAPON, INJURY, LOCATION, PERSON, VEHICLE, TIME_REFERENCE)'),
        sa.Column('entity_value', sa.Text(), nullable=False, comment='The actual text value of the entity'),
        sa.Column('confidence_score', sa.Float(), nullable=False, comment='Confidence score of entity extraction (0.0 to 1.0)'),
        sa.Column('start_char', sa.Integer(), nullable=False, comment='Starting character position in transcript text'),
        sa.Column('end_char', sa.Integer(), nullable=False, comment='Ending character position in transcript text'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Additional entity-specific data'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record creation timestamp'),
        sa.ForeignKeyConstraint(['transcript_id'], ['call_transcripts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='Named entities extracted from transcripts'
    )
    op.create_index('ix_extracted_entities_transcript_type', 'extracted_entities', ['transcript_id', 'entity_type'])

    # Create performance_metrics table
    op.create_table(
        'performance_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='Unique identifier for the metric'),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False, comment='Reference to the call session'),
        sa.Column('metric_name', sa.String(length=100), nullable=False, comment='Name of the metric (response_time, empathy_score, info_gathered, etc.)'),
        sa.Column('metric_value', sa.Float(), nullable=False, comment='Numeric value of the metric'),
        sa.Column('measured_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='When this metric was measured'),
        sa.ForeignKeyConstraint(['session_id'], ['call_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='Performance metrics for operator training'
    )
    op.create_index('ix_performance_metrics_session', 'performance_metrics', ['session_id'])


def downgrade() -> None:
    """Drop all tables and enum types."""

    # Drop tables in reverse order (respecting foreign keys)
    op.drop_index('ix_performance_metrics_session', table_name='performance_metrics')
    op.drop_table('performance_metrics')

    op.drop_index('ix_extracted_entities_transcript_type', table_name='extracted_entities')
    op.drop_table('extracted_entities')

    op.drop_index('ix_call_transcripts_session_timestamp', table_name='call_transcripts')
    op.drop_table('call_transcripts')

    op.drop_index('ix_call_sessions_operator_started', table_name='call_sessions')
    op.drop_index('ix_call_sessions_operator_id', table_name='call_sessions')
    op.drop_table('call_sessions')

    op.drop_index('ix_training_scenarios_difficulty_active', table_name='training_scenarios')
    op.drop_table('training_scenarios')

    # Drop enum types
    op.execute("DROP TYPE speaker_enum")
    op.execute("DROP TYPE call_session_status_enum")
    op.execute("DROP TYPE difficulty_level_enum")
