# Alembic Database Migration System

This directory contains database migrations for the 911 Operator Training Simulator using Alembic with async SQLAlchemy and PostgreSQL.

## Overview

The migration system manages database schema changes over time, allowing you to:
- Track schema changes in version control
- Apply migrations to upgrade databases
- Rollback migrations if needed
- Generate migrations automatically from model changes
- Maintain consistent database state across environments

## Setup

### Prerequisites

1. **PostgreSQL with asyncpg driver**:
   ```bash
   pip install sqlalchemy[asyncio] asyncpg alembic
   ```

2. **Database URL**:
   Set the `DATABASE_URL` environment variable:
   ```bash
   export DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/911_training"
   ```

   Or update the default in `alembic.ini`:
   ```ini
   sqlalchemy.url = postgresql+asyncpg://user:password@localhost:5432/911_training
   ```

### Configuration Files

- **alembic.ini**: Main configuration file with database URL and logging settings
- **env.py**: Alembic environment configuration for async SQLAlchemy
- **script.py.mako**: Template for generating new migration files
- **versions/**: Directory containing all migration files

## Migration Commands

### Running Migrations

Apply all pending migrations to upgrade to the latest version:
```bash
alembic upgrade head
```

Apply migrations up to a specific revision:
```bash
alembic upgrade <revision_id>
```

Apply the next migration only:
```bash
alembic upgrade +1
```

### Rolling Back Migrations

Rollback the last migration:
```bash
alembic downgrade -1
```

Rollback to a specific revision:
```bash
alembic downgrade <revision_id>
```

Rollback all migrations:
```bash
alembic downgrade base
```

### Creating New Migrations

**Auto-generate migration from model changes** (recommended):
```bash
alembic revision --autogenerate -m "description of changes"
```

**Create empty migration** (for manual SQL or data migrations):
```bash
alembic revision -m "description of changes"
```

### Viewing Migration Status

Show current database revision:
```bash
alembic current
```

Show migration history:
```bash
alembic history
```

Show migration history with details:
```bash
alembic history --verbose
```

Show pending migrations:
```bash
alembic heads
```

## Initial Migrations

### 001: Initial Schema

Creates the complete database schema including:

**Tables**:
- `training_scenarios`: Pre-configured training scenarios with difficulty levels
- `call_sessions`: Training call session records with operator and scenario info
- `call_transcripts`: Individual dialogue entries with timestamps and emotional analysis
- `extracted_entities`: Named entities extracted from transcripts (WEAPON, INJURY, LOCATION, etc.)
- `performance_metrics`: Operator performance tracking metrics

**Enums**:
- `difficulty_level_enum`: easy, medium, hard
- `call_session_status_enum`: active, completed, terminated, error
- `speaker_enum`: operator, caller

**Indexes**:
- Multi-column indexes for efficient querying on frequently accessed combinations
- Foreign key indexes for join performance

**Features**:
- UUID primary keys for all tables
- JSONB columns for flexible metadata storage
- Timestamp columns with timezone support
- Cascading deletes for referential integrity
- Table and column comments for documentation

### 002: Seed Training Scenarios

Seeds the database with 5 realistic training scenarios:

1. **Domestic Violence Call** (medium) - Fearful caller, requires careful questioning
2. **Medical Emergency - Heart Attack** (hard) - Panicked caller, needs CPR guidance
3. **Car Accident - Minor Injuries** (easy) - Calm witness, straightforward reporting
4. **Active Shooter Report** (hard) - Hysterical caller, critical situation
5. **Burglary in Progress** (medium) - Anxious homeowner, needs safety guidance

Each scenario includes:
- Detailed caller profile (emotional state, background, personality)
- Scenario script with initial conditions and key entities
- Expected dialogue flow for training evaluation

## Development Workflow

### Making Schema Changes

1. **Modify the SQLAlchemy models** in `app/models/database.py`

2. **Generate migration**:
   ```bash
   alembic revision --autogenerate -m "add new column to call_sessions"
   ```

3. **Review the generated migration** in `alembic/versions/`
   - Alembic may miss some changes (check the output warnings)
   - Add any manual changes needed
   - Verify upgrade and downgrade functions

4. **Test the migration**:
   ```bash
   # Apply migration
   alembic upgrade head

   # Verify it worked
   alembic current

   # Test rollback
   alembic downgrade -1

   # Re-apply
   alembic upgrade head
   ```

5. **Commit the migration** to version control

### Data Migrations

For migrations that modify data (not just schema):

1. **Create empty migration**:
   ```bash
   alembic revision -m "update existing call session statuses"
   ```

2. **Write custom upgrade/downgrade logic**:
   ```python
   def upgrade() -> None:
       # Use op.execute() for SQL
       op.execute("""
           UPDATE call_sessions
           SET status = 'completed'
           WHERE ended_at IS NOT NULL AND status = 'active'
       """)

       # Or use SQLAlchemy for more complex operations
       from sqlalchemy.orm import Session
       from app.models.database import CallSession

       bind = op.get_bind()
       session = Session(bind=bind)
       # ... perform operations ...
       session.commit()

   def downgrade() -> None:
       # Implement reverse operation if possible
       pass
   ```

## Production Workflow

### First-Time Database Setup

1. **Create PostgreSQL database**:
   ```sql
   CREATE DATABASE 911_training;
   ```

2. **Set environment variables**:
   ```bash
   export DATABASE_URL="postgresql+asyncpg://user:password@host:5432/911_training"
   ```

3. **Run migrations**:
   ```bash
   alembic upgrade head
   ```

4. **Verify**:
   ```bash
   alembic current
   # Should show: 002 (head)
   ```

### Deploying New Migrations

1. **Pull latest code** with new migrations

2. **Backup database** (important!):
   ```bash
   pg_dump 911_training > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

3. **Run migrations**:
   ```bash
   alembic upgrade head
   ```

4. **Verify**:
   ```bash
   alembic current
   ```

5. **If something goes wrong**:
   ```bash
   # Rollback
   alembic downgrade -1

   # Or restore from backup
   psql 911_training < backup_YYYYMMDD_HHMMSS.sql
   ```

### Zero-Downtime Migrations

For large tables or production systems that can't have downtime:

1. **Make changes backward-compatible**:
   - Add new columns as nullable first
   - Backfill data in separate migration
   - Remove old columns in later migration

2. **Example workflow**:
   ```bash
   # Migration 1: Add new nullable column
   alembic revision --autogenerate -m "add new_field to call_sessions"

   # Deploy and run migration
   alembic upgrade head

   # Migration 2: Backfill data (can run slowly)
   alembic revision -m "backfill new_field data"

   # Migration 3: Make column non-nullable
   alembic revision -m "make new_field required"

   # Migration 4: Remove old column
   alembic revision --autogenerate -m "remove old_field"
   ```

## Testing

### Local Testing

Use the database utilities for testing:

```bash
# Check database connection
python -m app.db.utils check

# Create tables (alternative to migrations for dev)
python -m app.db.utils create

# Seed with test data
python -m app.db.utils seed

# Reset database (drops all tables and recreates)
python -m app.db.utils reset

# Get database info
python -m app.db.utils info
```

### Integration Testing

For testing migrations in CI/CD:

```bash
#!/bin/bash
# test_migrations.sh

# Start PostgreSQL in Docker
docker run -d --name test-postgres \
  -e POSTGRES_PASSWORD=test \
  -e POSTGRES_DB=911_training_test \
  -p 5432:5432 \
  postgres:15

# Wait for database to be ready
sleep 5

# Set test database URL
export DATABASE_URL="postgresql+asyncpg://postgres:test@localhost:5432/911_training_test"

# Run all migrations
alembic upgrade head

# Run your tests
pytest tests/

# Cleanup
docker stop test-postgres
docker rm test-postgres
```

## Common Issues

### Issue: Alembic can't detect changes

**Solution**: Ensure you've imported all models in `env.py`:
```python
from app.models.database import Base
target_metadata = Base.metadata
```

### Issue: Migration conflicts

**Solution**: If multiple people create migrations simultaneously:
```bash
# Create merge migration
alembic merge heads -m "merge branches"
```

### Issue: Need to skip a migration

**Solution**: Use stamp to mark migration as applied without running it:
```bash
alembic stamp <revision_id>
```

### Issue: Database URL not found

**Solution**: Set the environment variable or update `alembic.ini`:
```bash
export DATABASE_URL="postgresql+asyncpg://user:password@host:5432/dbname"
```

### Issue: Async engine errors

**Solution**: Ensure you're using the async driver in the URL:
- Correct: `postgresql+asyncpg://...`
- Incorrect: `postgresql://...`

## Best Practices

1. **Always review auto-generated migrations** before applying
2. **Test migrations locally** before deploying to production
3. **Backup production databases** before running migrations
4. **Write reversible migrations** when possible (implement downgrade)
5. **Keep migrations small and focused** on one change
6. **Never modify applied migrations** - create new ones instead
7. **Document complex migrations** with comments
8. **Use transactions** - migrations run in transactions by default
9. **Test downgrades** to ensure they work correctly
10. **Version control** all migration files

## Schema Diagram

```
training_scenarios
├─ id (UUID, PK)
├─ name
├─ description
├─ caller_profile (JSONB)
├─ scenario_script (JSONB)
├─ difficulty_level (enum)
└─ is_active

call_sessions
├─ id (UUID, PK)
├─ operator_id
├─ scenario_id (FK → training_scenarios)
├─ started_at
├─ ended_at
├─ duration_ms
├─ status (enum)
└─ metadata (JSONB)

call_transcripts
├─ id (UUID, PK)
├─ session_id (FK → call_sessions)
├─ timestamp_ms
├─ speaker (enum)
├─ text
├─ audio_url
├─ emotional_state
└─ confidence_score

extracted_entities
├─ id (UUID, PK)
├─ transcript_id (FK → call_transcripts)
├─ entity_type
├─ entity_value
├─ confidence_score
├─ start_char
├─ end_char
└─ metadata (JSONB)

performance_metrics
├─ id (UUID, PK)
├─ session_id (FK → call_sessions)
├─ metric_name
├─ metric_value
└─ measured_at
```

## Additional Resources

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Async Documentation](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

## Support

For issues or questions about migrations:
1. Check this README for common solutions
2. Review the migration code in `alembic/versions/`
3. Check Alembic logs for detailed error messages
4. Consult the team's database administrator
