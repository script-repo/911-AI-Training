# Codebase Review: 911 Operator Training Simulator

**Date:** 2026-02-26
**Reviewer:** Claude (automated review)
**Commit:** c2a4e43 (main)

---

## Executive Summary

This is a well-structured, production-oriented 911 operator training simulator combining a FastAPI backend with a React/TypeScript frontend, backed by PostgreSQL, Redis, and S3-compatible storage. The codebase demonstrates solid architecture choices and comprehensive infrastructure configuration. However, there are several bugs, security concerns, and architectural gaps that should be addressed before production deployment.

**Overall Assessment: Good foundation with significant issues to resolve**

---

## 1. Critical Bugs

### 1.1 Frontend: Naming collision in Dashboard.tsx

**File:** `frontend/src/pages/Dashboard.tsx:5-7`

```tsx
import { CallStatus } from '@/types';
import CallStatus from '@/components/CallTakerDashboard/CallStatus';
```

`CallStatus` is imported twice — once as the enum from types and once as the component. This will cause a compile error or shadowing bug. The component import will override the enum, breaking the `currentCall.status === CallStatus.ENDED` check on line 20.

**Fix:** Rename one of the imports (e.g., `import CallStatusPanel from '...CallStatus'`).

### 1.2 Backend: Difficulty level enum mismatch

**File:** `backend/app/models/schemas.py:154`

```python
difficulty_level: Literal["beginner", "intermediate", "advanced", "expert"] = "beginner"
```

The `TrainingScenarioCreate` schema uses `["beginner", "intermediate", "advanced", "expert"]` but the database enum `DifficultyLevel` uses `["easy", "medium", "hard"]`. When `create_scenario` (calls.py:322) does `DifficultyLevel(request.difficulty_level)`, it will always raise a `ValueError` for any valid input since no values overlap.

### 1.3 Backend: Database URL inconsistency between config.py and db/base.py

**File:** `backend/app/db/base.py:18-21` vs `backend/app/core/config.py:76-78`

The database module reads `DATABASE_URL` directly from the environment via `os.getenv()` (defaulting to `postgresql+asyncpg://...`), but `config.py` defines an `async_database_url` property that transforms `postgresql://` to `postgresql+asyncpg://`. The `db/base.py` module never uses the settings object, meaning:
- The `async_database_url` property is dead code
- The database connection ignores any validation/transformation in the config layer
- Different default URLs between the two modules could cause confusion

### 1.4 Backend: Session context is read once but never refreshed in WebSocket loop

**File:** `backend/app/api/routes/websocket.py:95`

```python
context = await dialogue_manager.get_session_context(session_id)
```

The `context` dict is fetched once at WebSocket connection time, then passed to all message handlers. But the dialogue manager updates context in Redis on every turn. The `handle_transcript_message` function reads `context.get("current_emotional_state")` (line 301), which will always return the initial state, not the updated one. Emotional state will never evolve during a call.

### 1.5 Backend: `update_session_context` overwrites instead of merging

**File:** `backend/app/services/dialogue_manager.py:114-128`

`add_conversation_turn` (line 167) calls `update_session_context(session_id, context)` with the **full** context object. But `update_session_context` does `context.update(updates)` — since `updates` IS the full context, this works. However, `update_emotional_state` (line 217-219) calls `update_session_context` with just `{"current_emotional_state": emotional_state}`. This will **overwrite** the entire context with just that one key, destroying conversation history, extracted entities, and all other data.

This is a **data-loss bug**.

---

## 2. Security Issues

### 2.1 Error messages expose internal details

**File:** `backend/app/api/routes/calls.py:86-87`

```python
detail=f"Failed to start call session: {str(e)}"
```

Multiple endpoints expose raw exception messages to the client. This can leak database connection strings, internal paths, and stack traces. All 500-error handlers across calls.py follow this pattern (lines 86, 118, 189, 235, 291, 341).

**Fix:** Return generic error messages in 500 responses. Log the details server-side only.

### 2.2 WebSocket error handler exposes internal error messages

**File:** `backend/app/api/routes/websocket.py:139`

```python
"error_message": str(e)
```

Internal exception details are sent directly over the WebSocket to the client.

### 2.3 No authentication or authorization

The entire application has no authentication mechanism. The frontend includes auth token handling in `api.service.ts` (lines 31-33, 46-49), but the backend has no auth middleware, no token validation, and no user model. The `operator_id` field is a free-text string with no verification.

For a training simulator this may be acceptable in development, but it should be addressed before any deployment beyond localhost.

### 2.4 No rate limiting

The `rate_limit_llm_per_minute` config value is defined but never enforced. There is no rate limiting middleware on the API or WebSocket endpoints. A malicious client could:
- Exhaust the OpenRouter API budget by spamming transcript messages
- Create unlimited call sessions
- DOS the TTS and NLP services

### 2.5 Missing WebSocket input validation

**File:** `backend/app/api/routes/websocket.py:111-112`

```python
data = await websocket.receive_text()
message = json.loads(data)
```

No validation is performed on WebSocket messages beyond `json.loads`. An attacker could send arbitrarily large messages, malformed data, or messages with missing fields. The `message.get()` calls throughout the handlers will silently return `None` for missing fields rather than rejecting bad input.

### 2.6 Bare `except` clause

**File:** `backend/app/api/routes/websocket.py:140`

```python
except:
    pass
```

Bare `except` catches all exceptions including `SystemExit` and `KeyboardInterrupt`. Should be `except Exception:` at minimum.

---

## 3. Architecture & Design Issues

### 3.1 Blocking S3 client in async context

**File:** `backend/app/services/storage_service.py`

The `StorageService` uses `boto3` (synchronous) within `async` methods. All S3 operations (`put_object`, `get_object`, `delete_object`, etc.) are blocking calls that will block the event loop. This negates the benefits of the async FastAPI architecture and can cause request timeouts under load.

**Fix:** Use `aiobotocore` or `boto3` with `asyncio.to_thread()`.

### 3.2 Synchronous NLP in async method

**File:** `backend/app/services/nlp_service.py:61`

```python
doc = nlp(text)
```

spaCy's `nlp()` call is CPU-bound and synchronous. Running it in an `async` method without `asyncio.to_thread()` or a process pool will block the event loop.

### 3.3 New HTTP client created per LLM/TTS request

**Files:** `backend/app/services/llm_service.py:53`, `backend/app/services/tts_service.py:43`

```python
async with httpx.AsyncClient(timeout=30.0) as client:
```

A new `httpx.AsyncClient` is created and destroyed for every single LLM and TTS request. This means no connection pooling and a new TCP/TLS handshake for every request.

**Fix:** Create a persistent `httpx.AsyncClient` in the service constructor or as an application-scoped dependency.

### 3.4 Global service singletons instantiate at import time

**Files:** All service files (`llm_service.py:177`, `tts_service.py:134`, `storage_service.py:256`, etc.)

Services like `StorageService` make network calls in `__init__` (bucket existence check). This means importing the module triggers I/O. If S3 is unavailable at startup, the import fails and the entire application crashes, even if S3 is optional for some endpoints.

### 3.5 ScriptProcessorNode is deprecated (Frontend)

**File:** `frontend/src/services/audio.service.ts:54`

```typescript
this.processorNode = this.audioContext.createScriptProcessor(...)
```

`ScriptProcessorNode` is deprecated in the Web Audio API. It runs on the main thread and can cause audio glitches. The replacement is `AudioWorkletNode`, which runs in a separate thread.

### 3.6 `get_db` auto-commits on success

**File:** `backend/app/db/base.py:56-64`

The `get_db` dependency automatically commits on success. This is problematic because:
- Route handlers also call `await db.commit()` explicitly (e.g., `calls.py:60`)
- Double commits are wasteful and can mask issues
- It creates ambiguity about who owns the transaction lifecycle

**Fix:** Either auto-commit in the dependency OR commit in route handlers, but not both.

### 3.7 Count query fetches all rows

**File:** `backend/app/api/routes/calls.py:277-278`

```python
count_result = await db.execute(count_query)
total_count = len(count_result.scalars().all())
```

To count records, this loads every row into memory and then counts them in Python. For a large dataset, this is extremely inefficient.

**Fix:** Use `select(func.count()).select_from(TrainingScenario)`.

---

## 4. Code Quality Issues

### 4.1 `datetime.utcnow()` is deprecated

**Files:** Multiple backend files (`main.py:100`, `calls.py:56,153`, `storage_service.py:69,81`, `dialogue_manager.py:61,160`)

`datetime.utcnow()` is deprecated in Python 3.12+. Use `datetime.now(timezone.utc)` instead.

### 4.2 Frontend API service doesn't match backend API

**File:** `frontend/src/services/api.service.ts`

Several frontend API calls reference endpoints that don't exist in the backend:
- `GET /calls/history` (line 123) — backend has no history endpoint
- `GET /calls/{callId}/metrics` (line 134) — backend has no metrics endpoint
- `GET /users/me` (line 150) — no user endpoints exist
- `PATCH /users/{userId}` (line 156) — no user endpoints exist
- `POST /calls/start` sends `{ scenarioId }` but backend expects `{ operator_id, scenario_id }`

### 4.3 Frontend VITE_API_URL env vars are baked at build time

**File:** `frontend/Dockerfile:24-28`

The `VITE_*` variables are set as build args and baked into the static JS bundle. This means the frontend Docker image is environment-specific. You can't use the same image across staging/production.

**Fix:** Use runtime configuration (e.g., `window.__RUNTIME_CONFIG__` injected by nginx, or an `/api/config` endpoint).

### 4.4 Hardcoded Cursor VM host in vite.config.ts

**File:** `frontend/vite.config.ts:16-17`

```typescript
allowedHosts: [
  '5bad0d079c8bbdb484d6-pod-d6fhx5hnwneopaz33eowrngvna-3000.us5p.cursorvm.com',
  '.cursorvm.com',
],
```

This is development-specific configuration that shouldn't be committed. It also reveals infrastructure details.

### 4.5 Docker Compose version key is obsolete

**File:** `docker-compose.yml:1`

```yaml
version: '3.8'
```

The `version` key is [obsolete since Docker Compose v2](https://docs.docker.com/reference/compose-file/version-and-name/) and generates a warning.

### 4.6 Frontend environment variables set on wrong container

**File:** `docker-compose.yml:13-14`

```yaml
frontend:
  environment:
    - VITE_API_URL=http://localhost:8000
    - VITE_WS_URL=ws://localhost:8000
```

`VITE_*` variables are only used at **build time** by Vite. Setting them as runtime environment variables on the nginx container has no effect. They need to be passed as build args.

### 4.7 No test files exist

Despite `pytest`, `pytest-asyncio`, and `pytest-cov` being in `requirements.txt`, there are no actual test files anywhere in the repository. This is a significant gap for a safety-critical training application.

---

## 5. Infrastructure Issues

### 5.1 Backend container runs with multiple uvicorn workers + WebSocket

**File:** `backend/Dockerfile:81`

```dockerfile
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

Running multiple uvicorn workers with WebSocket connections is problematic because:
- The `ConnectionManager` (websocket.py:24) stores connections in-memory per worker
- WebSocket connections are not shared across workers
- A client connected to worker 1 cannot receive messages from worker 2

**Fix:** Use a single worker with `--workers 1`, or use Redis pub/sub for cross-worker WebSocket message broadcasting.

### 5.2 Kubernetes REDIS_URL in ConfigMap instead of Secret

**File:** `kubernetes/deployments/backend-deployment.yaml:92-94`

The `REDIS_URL` is pulled from a ConfigMap. If Redis has a password configured, the URL would contain credentials in plaintext in the ConfigMap. It should be in a Secret.

### 5.3 No resource limits on PostgreSQL StatefulSet

The PostgreSQL StatefulSet should define resource requests and limits to prevent it from being OOMKilled or starving other pods.

### 5.4 No network policies

There are no Kubernetes NetworkPolicy resources. Any pod in the cluster can access the database, Redis, and MinIO directly. Network policies should restrict access to only the backend pods.

---

## 6. Positive Observations

These aspects of the codebase are well-done:

1. **Clean project structure** — Clear separation of concerns between frontend, backend, and infrastructure
2. **Modern async stack** — FastAPI with async SQLAlchemy and asyncpg is a solid choice
3. **Well-designed database models** — Proper use of SQLAlchemy 2.0 Mapped columns, composite indexes, timezone-aware timestamps, and cascade deletes
4. **Comprehensive Pydantic schemas** — Good use of Pydantic v2 for request/response validation with `ConfigDict`
5. **Multi-stage Docker builds** — Both Dockerfiles use multi-stage builds with non-root users, reducing image size and attack surface
6. **Kubernetes production readiness** — HPA, pod anti-affinity, rolling updates with zero downtime, proper health/readiness probes
7. **Seed data migration** — Realistic 911 training scenarios with good variety across difficulty levels
8. **Frontend state management** — Clean Zustand stores with proper immutable updates
9. **WebSocket reconnection** — Exponential backoff with configurable max attempts
10. **Proper audio handling** — Correct float32-to-int16 conversion, echo cancellation, noise suppression

---

## 7. Summary of Findings by Severity

| Severity | Count | Key Items |
|----------|-------|-----------|
| **Critical Bug** | 5 | Dashboard naming collision, enum mismatch, emotional state never updates, context overwrite data loss, DB URL inconsistency |
| **Security** | 6 | Error message leakage, no auth, no rate limiting, no WS validation, bare except |
| **Architecture** | 7 | Blocking S3/NLP in async, no connection pooling, import-time I/O, deprecated ScriptProcessor |
| **Code Quality** | 7 | Dead code, API mismatch, no tests, deprecated APIs, hardcoded dev config |
| **Infrastructure** | 4 | Multi-worker WS conflict, Redis URL in ConfigMap, no resource limits, no network policies |

---

## 8. Recommended Priority Order

1. Fix the data-loss bug in `dialogue_manager.update_session_context` (Critical)
2. Fix the difficulty level enum mismatch (Critical — scenario creation is broken)
3. Fix the Dashboard.tsx import collision (Critical — page won't compile)
4. Refresh WebSocket context from Redis on each message turn
5. Stop exposing internal error messages to clients
6. Switch `boto3` to `aiobotocore` or wrap in `asyncio.to_thread()`
7. Create persistent `httpx.AsyncClient` instances
8. Add authentication middleware
9. Add rate limiting
10. Write tests for critical paths
