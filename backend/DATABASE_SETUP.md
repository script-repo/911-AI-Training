# Database Setup Guide

## Quick Start

### 1. Install Dependencies

```bash
cd /home/user/911-AI-Training/backend
pip install -r requirements.txt
```

### 2. Configure Database

Copy the example environment file and configure it:

```bash
cp .env.example .env
# Edit .env with your database credentials
```

Default configuration:
```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/911_training
```

### 3. Create PostgreSQL Database

```bash
# Using psql
createdb 911_training

# Or with SQL
psql -U postgres -c "CREATE DATABASE 911_training;"
```

### 4. Run Migrations

```bash
# Apply all migrations (creates schema and seeds data)
alembic upgrade head

# Verify
alembic current
```

You should see:
```
002 (head)
```

### 5. Verify Setup

```bash
# Check database connection and view info
python -m app.db.utils info
```

Expected output:
```
Database Info:
  connection: OK
  scenarios: 5
  sessions: 0
```

## Database Schema

The database includes 5 main tables:

### training_scenarios
Pre-configured training scenarios with various difficulty levels and emergency types.
- 5 seed scenarios included (domestic violence, heart attack, car accident, active shooter, burglary)
- JSONB fields for caller profiles and scenario scripts
- Difficulty levels: easy, medium, hard

### call_sessions
Records of training call sessions between operators and AI callers.
- Links operators to scenarios
- Tracks session status (active, completed, terminated, error)
- Records duration and timestamps
- JSONB metadata field for flexible data storage

### call_transcripts
Individual dialogue entries during a call session.
- Timestamped utterances with millisecond precision
- Speaker identification (operator or caller)
- Emotional state detection
- Audio URL references for recordings
- Confidence scores for transcription quality

### extracted_entities
Named entities extracted from call transcripts using NLP.
- Entity types: WEAPON, INJURY, LOCATION, PERSON, VEHICLE, TIME_REFERENCE
- Character position tracking for entity location in text
- Confidence scores for entity extraction
- JSONB metadata for additional entity information

### performance_metrics
Performance tracking for operator training sessions.
- Flexible metric system (response_time, empathy_score, info_gathered, etc.)
- Time-series data for tracking improvement
- Links to specific call sessions

## Development Commands

### Database Utilities

```bash
# Check database connection
python -m app.db.utils check

# Create tables (alternative to migrations)
python -m app.db.utils create

# Seed with training scenarios
python -m app.db.utils seed

# Reset database (WARNING: deletes all data)
python -m app.db.utils reset

# Get database statistics
python -m app.db.utils info
```

### Migration Commands

```bash
# Show current migration version
alembic current

# Show migration history
alembic history

# Apply all pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Create new migration (auto-generate from models)
alembic revision --autogenerate -m "description"

# Create empty migration (for data migrations)
alembic revision -m "description"
```

## Using in Python Code

### Get Database Session

```python
from app.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

@app.get("/scenarios")
async def get_scenarios(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from app.models import TrainingScenario
    
    result = await db.execute(select(TrainingScenario))
    scenarios = result.scalars().all()
    return scenarios
```

### Query Examples

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import (
    TrainingScenario,
    CallSession,
    CallTranscript,
    DifficultyLevel,
)

# Get all active scenarios
async def get_active_scenarios(db: AsyncSession):
    stmt = select(TrainingScenario).where(
        TrainingScenario.is_active == True
    )
    result = await db.execute(stmt)
    return result.scalars().all()

# Get scenarios by difficulty
async def get_scenarios_by_difficulty(db: AsyncSession, difficulty: DifficultyLevel):
    stmt = select(TrainingScenario).where(
        TrainingScenario.difficulty_level == difficulty
    )
    result = await db.execute(stmt)
    return result.scalars().all()

# Get call session with transcripts
async def get_session_with_transcripts(db: AsyncSession, session_id: str):
    from sqlalchemy.orm import selectinload
    
    stmt = select(CallSession).options(
        selectinload(CallSession.transcripts)
    ).where(CallSession.id == session_id)
    
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

# Create new call session
async def create_call_session(
    db: AsyncSession,
    operator_id: str,
    scenario_id: str
):
    from datetime import datetime, timezone
    
    session = CallSession(
        operator_id=operator_id,
        scenario_id=scenario_id,
        started_at=datetime.now(timezone.utc),
        status=CallSessionStatus.ACTIVE
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session
```

## Docker Setup (Optional)

Run PostgreSQL in Docker for development:

```bash
# Start PostgreSQL
docker run -d \
  --name 911-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=911_training \
  -p 5432:5432 \
  -v 911-postgres-data:/var/lib/postgresql/data \
  postgres:15

# Stop PostgreSQL
docker stop 911-postgres

# Start again
docker start 911-postgres

# Remove container and data
docker stop 911-postgres
docker rm 911-postgres
docker volume rm 911-postgres-data
```

## Troubleshooting

### Connection Refused

```
sqlalchemy.exc.OperationalError: connection refused
```

**Solution**: Ensure PostgreSQL is running:
```bash
# Check if PostgreSQL is running
pg_isready

# Start PostgreSQL (Linux)
sudo systemctl start postgresql

# Start PostgreSQL (macOS with Homebrew)
brew services start postgresql
```

### Database Does Not Exist

```
sqlalchemy.exc.OperationalError: database "911_training" does not exist
```

**Solution**: Create the database:
```bash
createdb 911_training
```

### Permission Denied

```
sqlalchemy.exc.ProgrammingError: permission denied for schema public
```

**Solution**: Grant permissions:
```sql
GRANT ALL PRIVILEGES ON DATABASE 911_training TO your_user;
```

### Migration Already Applied

```
alembic.util.exc.CommandError: Target database is not up to date
```

**Solution**: Check current version and history:
```bash
alembic current
alembic history
```

If database is ahead of migrations, stamp to the correct version:
```bash
alembic stamp head
```

## Environment Variables

All database configuration can be set via environment variables:

```bash
# Required
DATABASE_URL=postgresql+asyncpg://user:password@host:port/database

# Optional (with defaults)
DB_POOL_SIZE=5                # Connection pool size
DB_MAX_OVERFLOW=10            # Max overflow connections
SQL_ECHO=false                # Log SQL queries (true/false)
```

## Production Considerations

### Security

1. **Never commit .env files** - Add to .gitignore
2. **Use strong passwords** for database users
3. **Limit database user permissions** to only what's needed
4. **Use SSL/TLS** for database connections in production
5. **Rotate credentials** regularly

### Performance

1. **Connection pooling** - Configured in `app/db/base.py`
2. **Indexes** - Already created on frequently queried columns
3. **Query optimization** - Use `select` with specific columns
4. **Eager loading** - Use `selectinload` for relationships

### Monitoring

1. **Enable SQL logging** temporarily for debugging:
   ```bash
   export SQL_ECHO=true
   ```

2. **Monitor connection pool**:
   ```python
   from app.db import engine
   print(engine.pool.status())
   ```

3. **Track query performance** - Use PostgreSQL's `pg_stat_statements`

### Backup

Always backup before running migrations in production:

```bash
# Backup
pg_dump 911_training > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore if needed
psql 911_training < backup_YYYYMMDD_HHMMSS.sql
```

## Next Steps

1. **Install dependencies**: `pip install -r requirements.txt`
2. **Configure database**: Copy `.env.example` to `.env`
3. **Run migrations**: `alembic upgrade head`
4. **Verify setup**: `python -m app.db.utils info`
5. **Start building**: Import models and start coding!

For more detailed information, see:
- `/home/user/911-AI-Training/backend/alembic/README.md` - Migration system documentation
- `/home/user/911-AI-Training/backend/app/models/database.py` - Model definitions
- `/home/user/911-AI-Training/backend/app/db/utils.py` - Database utilities
