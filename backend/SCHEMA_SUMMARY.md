# Database Schema Summary - 911 Operator Training Simulator

## Overview

Complete database schema and migration system for tracking 911 operator training sessions, call transcripts, entity extraction, and performance metrics.

## Database Schema

### Tables Created

#### 1. training_scenarios
Pre-configured training scenarios for operator practice.

**Columns:**
- `id` (UUID, PK) - Unique identifier
- `name` (VARCHAR(200)) - Scenario name
- `description` (TEXT) - Detailed description
- `caller_profile` (JSONB) - Personality, background, emotional state
- `scenario_script` (JSONB) - Initial conditions, expected flow
- `difficulty_level` (ENUM) - easy, medium, hard
- `is_active` (BOOLEAN) - Availability flag
- `created_at` (TIMESTAMP WITH TZ) - Creation timestamp
- `updated_at` (TIMESTAMP WITH TZ) - Last update timestamp

**Indexes:**
- `ix_training_scenarios_difficulty_active` on (difficulty_level, is_active)

**Seed Data:** 5 realistic scenarios included

---

#### 2. call_sessions
Training call session records.

**Columns:**
- `id` (UUID, PK) - Unique identifier
- `operator_id` (VARCHAR(100)) - Operator trainee ID
- `scenario_id` (UUID, FK) - Reference to training_scenarios
- `started_at` (TIMESTAMP WITH TZ) - Session start time
- `ended_at` (TIMESTAMP WITH TZ, NULLABLE) - Session end time
- `duration_ms` (INTEGER, NULLABLE) - Call duration in milliseconds
- `status` (ENUM) - active, completed, terminated, error
- `metadata` (JSONB, NULLABLE) - Flexible session data
- `created_at` (TIMESTAMP WITH TZ) - Record creation
- `updated_at` (TIMESTAMP WITH TZ) - Record update

**Indexes:**
- `ix_call_sessions_operator_id` on (operator_id)
- `ix_call_sessions_operator_started` on (operator_id, started_at)

**Foreign Keys:**
- scenario_id → training_scenarios.id (CASCADE DELETE)

---

#### 3. call_transcripts
Individual dialogue entries during calls.

**Columns:**
- `id` (UUID, PK) - Unique identifier
- `session_id` (UUID, FK) - Reference to call_sessions
- `timestamp_ms` (BIGINT) - Milliseconds from call start
- `speaker` (ENUM) - operator, caller
- `text` (TEXT) - Transcribed dialogue
- `audio_url` (VARCHAR(500), NULLABLE) - S3 audio URL
- `emotional_state` (VARCHAR(20), NULLABLE) - calm, anxious, panicked, hysterical
- `confidence_score` (FLOAT, NULLABLE) - Transcription confidence (0.0-1.0)
- `created_at` (TIMESTAMP WITH TZ) - Record creation

**Indexes:**
- `ix_call_transcripts_session_timestamp` on (session_id, timestamp_ms)

**Foreign Keys:**
- session_id → call_sessions.id (CASCADE DELETE)

---

#### 4. extracted_entities
Named entities extracted from transcripts.

**Columns:**
- `id` (UUID, PK) - Unique identifier
- `transcript_id` (UUID, FK) - Reference to call_transcripts
- `entity_type` (VARCHAR(50)) - WEAPON, INJURY, LOCATION, PERSON, VEHICLE, TIME_REFERENCE
- `entity_value` (TEXT) - Extracted text value
- `confidence_score` (FLOAT) - Extraction confidence (0.0-1.0)
- `start_char` (INTEGER) - Starting position in text
- `end_char` (INTEGER) - Ending position in text
- `metadata` (JSONB, NULLABLE) - Additional entity data
- `created_at` (TIMESTAMP WITH TZ) - Record creation

**Indexes:**
- `ix_extracted_entities_transcript_type` on (transcript_id, entity_type)

**Foreign Keys:**
- transcript_id → call_transcripts.id (CASCADE DELETE)

---

#### 5. performance_metrics
Operator performance tracking.

**Columns:**
- `id` (UUID, PK) - Unique identifier
- `session_id` (UUID, FK) - Reference to call_sessions
- `metric_name` (VARCHAR(100)) - Metric name (response_time, empathy_score, etc.)
- `metric_value` (FLOAT) - Numeric metric value
- `measured_at` (TIMESTAMP WITH TZ) - Measurement timestamp

**Indexes:**
- `ix_performance_metrics_session` on (session_id)

**Foreign Keys:**
- session_id → call_sessions.id (CASCADE DELETE)

---

## Enums

### difficulty_level_enum
- `easy` - Simple scenarios for beginners
- `medium` - Moderate complexity scenarios
- `hard` - Complex, high-stress scenarios

### call_session_status_enum
- `active` - Session in progress
- `completed` - Session finished normally
- `terminated` - Session ended early
- `error` - Session ended with error

### speaker_enum
- `operator` - 911 operator/trainee
- `caller` - Simulated caller

---

## Relationships

```
training_scenarios (1) ──< (N) call_sessions
call_sessions (1) ──< (N) call_transcripts
call_sessions (1) ──< (N) performance_metrics
call_transcripts (1) ──< (N) extracted_entities
```

---

## Migrations

### Migration 001: Initial Schema
- Creates all 5 tables with proper constraints
- Creates 3 enum types
- Creates 7 indexes for query optimization
- Adds table and column comments

### Migration 002: Seed Scenarios
Inserts 5 realistic training scenarios:

1. **Domestic Violence Call** (medium)
   - Fearful caller in locked bathroom
   - Partner is intoxicated with weapon
   - Requires calm, quiet communication

2. **Medical Emergency - Heart Attack** (hard)
   - Panicked caller, father having heart attack
   - Requires CPR guidance and calm direction
   - Critical time-sensitive situation

3. **Car Accident - Minor Injuries** (easy)
   - Calm witness reporting collision
   - Minor injuries, straightforward reporting
   - Good for beginner training

4. **Active Shooter Report** (hard)
   - Hysterical teacher hiding with students
   - Active shooter in school building
   - Requires extreme calm and clear instructions

5. **Burglary in Progress** (medium)
   - Anxious homeowner hearing intruder
   - Hiding upstairs while break-in occurs
   - Requires safety guidance and officer coordination

---

## Key Features

### UUID Primary Keys
- All tables use UUID for globally unique identifiers
- Better for distributed systems and API exposure
- No integer sequence conflicts

### JSONB Columns
- Flexible metadata storage in PostgreSQL native format
- Efficient querying with GIN indexes (can be added later)
- Perfect for caller profiles and scenario scripts

### Timestamp Tracking
- All tables have timezone-aware timestamps
- Automatic created_at/updated_at tracking
- Millisecond precision for call events

### Cascading Deletes
- Foreign keys configured with ON DELETE CASCADE
- Deleting a scenario removes all related sessions
- Deleting a session removes transcripts and metrics
- Deleting a transcript removes entities

### Proper Indexing
- Multi-column indexes for common query patterns
- Foreign key indexes for join performance
- Composite indexes for filtering and sorting

### Enum Types
- Type-safe status and role tracking
- Database-level validation
- Clear documentation of valid values

---

## File Structure

```
backend/
├── alembic/
│   ├── versions/
│   │   ├── 001_initial_schema.py      # Creates all tables
│   │   └── 002_seed_scenarios.py      # Seeds training data
│   ├── env.py                          # Async SQLAlchemy config
│   ├── script.py.mako                  # Migration template
│   └── README.md                       # Migration documentation
├── app/
│   ├── models/
│   │   ├── database.py                 # SQLAlchemy ORM models
│   │   └── __init__.py
│   └── db/
│       ├── base.py                     # Database configuration
│       ├── utils.py                    # Database utilities
│       └── __init__.py
├── alembic.ini                         # Alembic configuration
├── requirements.txt                    # Python dependencies
├── .env.example                        # Environment template
├── DATABASE_SETUP.md                   # Setup instructions
└── SCHEMA_SUMMARY.md                   # This file
```

---

## Usage Examples

### Query Training Scenarios

```python
from sqlalchemy import select
from app.models import TrainingScenario, DifficultyLevel
from app.db import AsyncSessionLocal

async with AsyncSessionLocal() as session:
    # Get all medium difficulty scenarios
    stmt = select(TrainingScenario).where(
        TrainingScenario.difficulty_level == DifficultyLevel.MEDIUM,
        TrainingScenario.is_active == True
    )
    result = await session.execute(stmt)
    scenarios = result.scalars().all()
```

### Create Call Session

```python
from datetime import datetime, timezone
from app.models import CallSession, CallSessionStatus
from app.db import AsyncSessionLocal

async with AsyncSessionLocal() as session:
    call = CallSession(
        operator_id="operator_123",
        scenario_id=scenario_uuid,
        started_at=datetime.now(timezone.utc),
        status=CallSessionStatus.ACTIVE
    )
    session.add(call)
    await session.commit()
```

### Add Transcript Entry

```python
from app.models import CallTranscript, Speaker

async with AsyncSessionLocal() as session:
    transcript = CallTranscript(
        session_id=session_uuid,
        timestamp_ms=1500,
        speaker=Speaker.CALLER,
        text="I need help, someone broke into my house!",
        emotional_state="panicked",
        confidence_score=0.95
    )
    session.add(transcript)
    await session.commit()
```

### Extract Entities

```python
from app.models import ExtractedEntity

async with AsyncSessionLocal() as session:
    entity = ExtractedEntity(
        transcript_id=transcript_uuid,
        entity_type="LOCATION",
        entity_value="123 Oak Street",
        confidence_score=0.89,
        start_char=45,
        end_char=59
    )
    session.add(entity)
    await session.commit()
```

---

## Quick Setup Commands

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure database
cp .env.example .env
# Edit .env with your database credentials

# 3. Create database
createdb 911_training

# 4. Run migrations
alembic upgrade head

# 5. Verify setup
python -m app.db.utils info
```

---

## Important Notes

1. **Async/Await Required**: All database operations must use async/await
2. **PostgreSQL Only**: Schema uses PostgreSQL-specific features (JSONB, UUID)
3. **asyncpg Driver**: Must use `postgresql+asyncpg://` in connection string
4. **Environment Variables**: Set DATABASE_URL before running migrations
5. **Backup Before Migrations**: Always backup production data first

---

## Performance Considerations

### Indexing
- Current indexes cover common query patterns
- Add GIN indexes for JSONB searching if needed
- Monitor slow queries and add indexes accordingly

### Connection Pooling
- Configured in `app/db/base.py`
- Default pool size: 5 connections
- Max overflow: 10 connections
- Adjust based on load

### Query Optimization
- Use `selectinload()` for eager loading relationships
- Select only needed columns
- Use pagination for large result sets
- Consider materialized views for complex analytics

---

## Next Steps

1. **Run migrations** to create the schema
2. **Verify seed data** was inserted correctly
3. **Build API endpoints** using the models
4. **Implement services** for business logic
5. **Add performance tracking** as metrics are defined
6. **Monitor and optimize** based on usage patterns

For detailed documentation, see:
- `/home/user/911-AI-Training/backend/alembic/README.md`
- `/home/user/911-AI-Training/backend/DATABASE_SETUP.md`
