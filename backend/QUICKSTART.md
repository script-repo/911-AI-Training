# 911 Operator Training Simulator - Backend Quick Start

## Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Redis 7+
- MinIO or S3-compatible storage
- Coqui TTS service

## Setup Instructions

### 1. Install Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run setup script
python setup.py

# OR install manually
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 2. Configure Environment

```bash
# Copy environment template
cp ../.env.example .env

# Edit .env with your configuration
nano .env
```

Key configurations to set:
- `OPENROUTER_API_KEY`: Your OpenRouter API key
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `S3_ENDPOINT`: MinIO/S3 endpoint
- `COQUI_TTS_URL`: Coqui TTS service URL

### 3. Initialize Database

```bash
# Run migrations
alembic upgrade head

# This will:
# - Create all database tables
# - Seed initial training scenarios
```

### 4. Start the Server

```bash
# Development mode with auto-reload
python run.py

# OR using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 5. Verify Installation

```bash
# Health check
curl http://localhost:8000/health

# Readiness check (verifies all dependencies)
curl http://localhost:8000/ready

# API documentation
open http://localhost:8000/docs
```

## Project Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── core/
│   │   └── config.py           # Configuration management
│   ├── models/
│   │   ├── database.py         # SQLAlchemy ORM models
│   │   └── schemas.py          # Pydantic request/response schemas
│   ├── api/
│   │   └── routes/
│   │       ├── calls.py        # REST API endpoints
│   │       └── websocket.py    # WebSocket endpoint
│   ├── services/
│   │   ├── llm_service.py      # OpenRouter LLM integration
│   │   ├── tts_service.py      # Coqui TTS integration
│   │   ├── nlp_service.py      # spaCy entity extraction
│   │   ├── audio_service.py    # Audio encoding/decoding
│   │   ├── storage_service.py  # S3/MinIO storage
│   │   └── dialogue_manager.py # Conversation state management
│   └── db/
│       ├── base.py             # Database session management
│       └── utils.py            # Database utilities
├── alembic/
│   ├── versions/               # Database migrations
│   │   ├── 001_initial_schema.py
│   │   └── 002_seed_scenarios.py
│   └── env.py
├── requirements.txt
├── alembic.ini
├── setup.py
└── run.py
```

## API Endpoints

### Health & Status
- `GET /health` - Basic health check
- `GET /ready` - Readiness check with dependency status

### Calls Management
- `POST /api/v1/calls/start` - Start new training session
- `GET /api/v1/calls/{call_id}` - Get call session details
- `POST /api/v1/calls/{call_id}/end` - End call session
- `GET /api/v1/calls/{call_id}/transcript` - Get full transcript

### Scenarios
- `GET /api/v1/scenarios` - List training scenarios
- `POST /api/v1/scenarios` - Create new scenario
- `GET /api/v1/scenarios/{scenario_id}` - Get scenario details

### WebSocket
- `WS /ws/call/{session_id}` - Real-time call simulation

## WebSocket Protocol

### Client → Server Messages

1. **Audio Chunk**
```json
{
  "type": "audio_chunk",
  "session_id": "uuid",
  "audio_data": "base64-encoded-audio",
  "timestamp_ms": 1000
}
```

2. **Transcript** (operator speech)
```json
{
  "type": "transcript",
  "session_id": "uuid",
  "text": "What is your emergency?",
  "timestamp_ms": 1000
}
```

3. **Control**
```json
{
  "type": "control",
  "session_id": "uuid",
  "action": "mute|unmute|hold|resume|terminate"
}
```

### Server → Client Messages

1. **Transcript Update**
```json
{
  "type": "transcript_update",
  "session_id": "uuid",
  "transcript_id": "uuid",
  "speaker": "caller|operator",
  "text": "...",
  "timestamp_ms": 1000
}
```

2. **Audio Chunk** (AI caller response)
```json
{
  "type": "audio_chunk",
  "session_id": "uuid",
  "audio_data": "base64-encoded-audio",
  "timestamp_ms": 1000
}
```

3. **Entity Update**
```json
{
  "type": "entity_update",
  "session_id": "uuid",
  "entity_id": "uuid",
  "entity_type": "LOCATION|WEAPON|INJURY|...",
  "entity_value": "...",
  "confidence_score": 0.95
}
```

4. **Emotional State**
```json
{
  "type": "emotional_state",
  "session_id": "uuid",
  "state": "calm|anxious|panicked",
  "intensity": 0.7,
  "timestamp_ms": 1000
}
```

## Environment Variables

See `../.env.example` for all configuration options.

Key variables:
- `OPENROUTER_API_KEY` - Required for AI caller
- `DATABASE_URL` - PostgreSQL connection
- `REDIS_URL` - Redis connection
- `S3_ENDPOINT` - Object storage endpoint
- `COQUI_TTS_URL` - TTS service URL
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)
- `ENVIRONMENT` - Environment (development, production)

## Development

### Running Tests
```bash
pytest
pytest --cov=app tests/
```

### Code Quality
```bash
# Format code
black .

# Lint
ruff check .

# Type checking
mypy app/
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Troubleshooting

### Database Connection Issues
- Verify PostgreSQL is running
- Check DATABASE_URL in .env
- Ensure database exists: `createdb training_db`

### Redis Connection Issues
- Verify Redis is running: `redis-cli ping`
- Check REDIS_URL in .env

### S3/MinIO Issues
- Verify MinIO is running
- Check S3_ENDPOINT, S3_ACCESS_KEY, S3_SECRET_KEY
- Bucket will be auto-created on first use

### TTS Service Issues
- Verify Coqui TTS is running
- Check COQUI_TTS_URL
- Test: `curl http://localhost:5002/api/models`

### spaCy Model Missing
```bash
python -m spacy download en_core_web_sm
```

## Production Deployment

1. Set `ENVIRONMENT=production` in .env
2. Use proper database credentials
3. Set secure Redis password
4. Use HTTPS for all external services
5. Run with multiple workers: `uvicorn app.main:app --workers 4`
6. Set up reverse proxy (nginx/traefik)
7. Enable monitoring and logging
8. Use managed databases (RDS, etc.)

## Support

For issues or questions:
1. Check the logs in `LOG_LEVEL=DEBUG` mode
2. Verify all services are running with `/ready` endpoint
3. Check API documentation at `/docs`
