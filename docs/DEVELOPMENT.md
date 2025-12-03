# Development Guide

This guide covers local development setup and workflows for the 911 Operator Training Simulator.

## Prerequisites

- **Docker** and **Docker Compose** (20.10+)
- **Python** 3.11+
- **Node.js** 20+
- **Git**
- **OpenRouter API key**

---

## Quick Start (Docker Compose)

The fastest way to get started for full-stack development:

```bash
# Clone repository
cd /home/user/911-AI-Training

# Configure environment
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Access application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
# MinIO Console: http://localhost:9001
```

---

## Backend Development

### Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Configure environment
cp ../.env.example .env
# Edit .env with your configuration
```

### Database Setup

```bash
# Ensure PostgreSQL is running (via Docker Compose or local install)

# Run migrations
alembic upgrade head

# Verify database setup
python -c "from app.db.utils import check_db; import asyncio; asyncio.run(check_db())"
```

### Run Backend

```bash
# Development server with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or use the run script
python run.py

# Backend will be available at:
# - API: http://localhost:8000
# - Docs: http://localhost:8000/docs
# - Health: http://localhost:8000/health
```

### Backend Project Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── api/
│   │   └── routes/
│   │       ├── calls.py        # Call management endpoints
│   │       └── websocket.py    # WebSocket handler
│   ├── core/
│   │   └── config.py           # Configuration
│   ├── services/
│   │   ├── llm_service.py      # OpenRouter integration
│   │   ├── tts_service.py      # Coqui TTS client
│   │   ├── nlp_service.py      # Entity extraction
│   │   ├── audio_service.py    # Audio processing
│   │   ├── storage_service.py  # S3/MinIO client
│   │   └── dialogue_manager.py # Conversation management
│   ├── models/
│   │   ├── database.py         # SQLAlchemy models
│   │   └── schemas.py          # Pydantic schemas
│   └── db/
│       ├── base.py             # Database session
│       └── utils.py            # Database utilities
├── alembic/                    # Database migrations
├── tests/                      # Tests
└── requirements.txt            # Python dependencies
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov httpx

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api.py

# Run specific test
pytest tests/test_api.py::test_start_call
```

### Testing Individual Services

```python
# Test LLM service
python -c "
from app.services.llm_service import OpenRouterLLMService
import asyncio

async def test():
    service = OpenRouterLLMService()
    response = await service.generate_caller_response(
        context={'emotional_state': 'panicked', 'scenario': {'name': 'Test'}},
        conversation_history=[{'role': 'user', 'content': 'What is your location?'}]
    )
    print(response)

asyncio.run(test())
"

# Test TTS service
python -c "
from app.services.tts_service import CoquiTTSService
import asyncio

async def test():
    service = CoquiTTSService()
    audio = await service.synthesize('Hello, I need help!')
    print(f'Audio length: {len(audio)} bytes')

asyncio.run(test())
"

# Test NLP service
python -c "
from app.services.nlp_service import NLPService

service = NLPService()
entities = service.extract_entities('Someone broke into my house at 123 Main Street with a gun')
print(entities)
"
```

---

## Frontend Development

### Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.development
# Edit .env.development with your backend URLs
```

### Run Frontend

```bash
# Development server with hot reload
npm run dev

# Frontend will be available at:
# http://localhost:3000
```

### Frontend Project Structure

```
frontend/
├── src/
│   ├── main.tsx                # Entry point
│   ├── App.tsx                 # Main app component
│   ├── types/
│   │   └── index.ts            # TypeScript types
│   ├── pages/
│   │   ├── Dashboard.tsx       # Main call interface
│   │   ├── ScenarioSelection.tsx
│   │   ├── CallHistory.tsx
│   │   └── CallReview.tsx
│   ├── components/
│   │   ├── Layout.tsx
│   │   ├── CallTakerDashboard/
│   │   ├── AudioProcessor/
│   │   ├── LiveTranscript/
│   │   └── EntityVisualizer/
│   ├── services/
│   │   ├── api.service.ts      # REST API client
│   │   ├── websocket.service.ts # WebSocket manager
│   │   └── audio.service.ts    # Web Audio API
│   ├── hooks/
│   │   ├── useWebSocket.ts
│   │   ├── useAudioStream.ts
│   │   ├── useCallSession.ts
│   │   └── useTranscript.ts
│   └── stores/
│       ├── callStore.ts        # Call state
│       └── entityStore.ts      # Entity state
├── public/
├── package.json
├── vite.config.ts
└── tsconfig.json
```

### Building Frontend

```bash
# Build for production
npm run build

# Preview production build
npm run preview

# Build output will be in dist/
```

### Frontend Testing

```bash
# Run tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage
```

---

## Database Development

### Create New Migration

```bash
cd backend

# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add new field to CallSession"

# Create empty migration
alembic revision -m "Add custom index"

# Edit migration file in alembic/versions/
```

### Apply Migrations

```bash
# Upgrade to latest
alembic upgrade head

# Upgrade one version
alembic upgrade +1

# Downgrade one version
alembic downgrade -1

# Downgrade to specific version
alembic downgrade <revision>
```

### Database Utilities

```bash
# Check database connection
python -c "from app.db.utils import check_db; import asyncio; asyncio.run(check_db())"

# Create all tables (development only)
python -c "from app.db.utils import create_tables; import asyncio; asyncio.run(create_tables())"

# Seed database with scenarios
python -c "from app.db.utils import seed_database; import asyncio; asyncio.run(seed_database())"

# Reset database (CAUTION: deletes all data)
python -c "from app.db.utils import reset_database; import asyncio; asyncio.run(reset_database())"
```

### Inspect Database

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U postgres -d training_db

# List tables
\dt

# Describe table
\d call_sessions

# Query data
SELECT * FROM training_scenarios;
```

---

## Common Development Tasks

### Adding a New API Endpoint

1. **Define Pydantic schema** in `backend/app/models/schemas.py`:
```python
class NewFeatureRequest(BaseModel):
    field1: str
    field2: int

class NewFeatureResponse(BaseModel):
    id: UUID
    result: str
```

2. **Create route** in `backend/app/api/routes/`:
```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db
from app.models.schemas import NewFeatureRequest, NewFeatureResponse

router = APIRouter()

@router.post("/new-feature", response_model=NewFeatureResponse)
async def create_new_feature(
    request: NewFeatureRequest,
    db: AsyncSession = Depends(get_db)
):
    # Implementation
    return NewFeatureResponse(id=uuid4(), result="Success")
```

3. **Register router** in `backend/app/main.py`:
```python
from app.api.routes import new_feature

app.include_router(
    new_feature.router,
    prefix="/api/v1/features",
    tags=["features"]
)
```

4. **Test endpoint**:
```bash
curl -X POST http://localhost:8000/api/v1/features/new-feature \
  -H "Content-Type: application/json" \
  -d '{"field1": "value", "field2": 42}'
```

### Adding a New React Component

1. **Create component** in `frontend/src/components/`:
```typescript
// NewComponent.tsx
import { FC } from 'react';

interface NewComponentProps {
  data: string;
}

export const NewComponent: FC<NewComponentProps> = ({ data }) => {
  return (
    <div className="p-4 bg-white rounded shadow">
      <h2 className="text-xl font-bold">{data}</h2>
    </div>
  );
};
```

2. **Use component**:
```typescript
import { NewComponent } from '@/components/NewComponent';

function ParentComponent() {
  return <NewComponent data="Hello" />;
}
```

### Adding a New Service

1. **Create service** in `backend/app/services/`:
```python
# new_service.py
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class NewService:
    def __init__(self):
        self.config = {}

    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process data"""
        try:
            # Implementation
            return {"result": "success"}
        except Exception as e:
            logger.error(f"Error in NewService: {e}")
            raise
```

2. **Use service**:
```python
from app.services.new_service import NewService

service = NewService()
result = await service.process(data)
```

---

## Debugging

### Backend Debugging

#### VS Code Debug Configuration

Add to `.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
      ],
      "jinja": true,
      "justMyCode": false
    }
  ]
}
```

#### Print Debugging
```python
import logging
logger = logging.getLogger(__name__)

# Use logger instead of print
logger.debug(f"Variable value: {variable}")
logger.info(f"Processing request: {request_id}")
logger.error(f"Error occurred: {error}")
```

#### Interactive Debugging
```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use ipdb for better experience
import ipdb; ipdb.set_trace()
```

### Frontend Debugging

#### Browser DevTools
- Open DevTools (F12)
- Console tab for logs
- Network tab for API calls
- Application tab for storage

#### React DevTools
```bash
# Install React DevTools browser extension
# Inspect component hierarchy and state
```

#### WebSocket Debugging
```javascript
// In browser console
const ws = new WebSocket('ws://localhost:8000/ws/call/test-session');
ws.onmessage = (event) => console.log('Received:', event.data);
ws.send(JSON.stringify({ type: 'test', data: 'hello' }));
```

---

## Environment Variables

### Backend (.env)
```bash
# LLM
OPENROUTER_API_KEY=your_key
LLM_MODEL=deepseek/deepseek-chat

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/training_db

# Redis
REDIS_URL=redis://localhost:6379/0

# S3
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin

# TTS
COQUI_TTS_URL=http://localhost:5002

# App
LOG_LEVEL=DEBUG
ENVIRONMENT=development
```

### Frontend (.env.development)
```bash
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
VITE_ENABLE_DEBUG_MODE=true
```

---

## Code Style

### Python (Backend)

Follow PEP 8 with these tools:

```bash
# Install tools
pip install black isort flake8 mypy

# Format code
black app/

# Sort imports
isort app/

# Lint
flake8 app/

# Type checking
mypy app/
```

### TypeScript (Frontend)

Follow Airbnb style guide:

```bash
# Lint
npm run lint

# Fix auto-fixable issues
npm run lint:fix

# Format with Prettier
npm run format
```

---

## Git Workflow

### Branch Strategy

```bash
# Create feature branch
git checkout -b feature/add-new-scenario-type

# Make changes and commit
git add .
git commit -m "feat: add new scenario type support"

# Push to remote
git push origin feature/add-new-scenario-type

# Create pull request on GitHub
```

### Commit Message Format

Follow Conventional Commits:

```
feat: add new feature
fix: fix bug
docs: update documentation
style: code style changes
refactor: code refactoring
test: add tests
chore: maintenance tasks
```

---

## Performance Profiling

### Backend Profiling

```python
# Add profiling decorator
from functools import wraps
import time

def profile(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} took {end - start:.2f}s")
        return result
    return wrapper

@profile
async def slow_function():
    # Your code
    pass
```

### Frontend Profiling

```javascript
// React Profiler
import { Profiler } from 'react';

function onRenderCallback(id, phase, actualDuration) {
  console.log(`${id} (${phase}) took ${actualDuration}ms`);
}

<Profiler id="CallDashboard" onRender={onRenderCallback}>
  <CallDashboard />
</Profiler>
```

---

## Useful Commands

### Docker

```bash
# Rebuild specific service
docker-compose build backend

# View logs for specific service
docker-compose logs -f backend

# Execute command in container
docker-compose exec backend bash

# Stop all services
docker-compose down

# Remove volumes (CAUTION: deletes data)
docker-compose down -v
```

### Database

```bash
# Backup database
docker-compose exec postgres pg_dump -U postgres training_db > backup.sql

# Restore database
docker-compose exec -T postgres psql -U postgres training_db < backup.sql

# Connect to PostgreSQL
docker-compose exec postgres psql -U postgres training_db
```

### Redis

```bash
# Connect to Redis CLI
docker-compose exec redis redis-cli

# View all keys
redis-cli KEYS "*"

# Get key value
redis-cli GET "session:abc-123"

# Clear all data
redis-cli FLUSHALL
```

---

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

### Docker Issues

```bash
# Remove all containers and volumes
docker-compose down -v

# Rebuild from scratch
docker-compose build --no-cache

# Check Docker logs
docker-compose logs -f
```

### Module Not Found

```bash
# Reinstall dependencies
cd backend
pip install -r requirements.txt

cd frontend
npm install
```

---

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/documentation)
