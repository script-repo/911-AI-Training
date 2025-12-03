# API Documentation

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://your-domain.com/api`

## Authentication

Currently, no authentication is required. Session-based authentication will be added in future versions.

## REST API Endpoints

### Health Check

#### GET /health

Basic health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-03T10:30:00Z"
}
```

#### GET /ready

Readiness check verifying all dependencies.

**Response:**
```json
{
  "status": "ready",
  "checks": {
    "database": "connected",
    "redis": "connected",
    "s3": "connected",
    "tts": "connected"
  },
  "timestamp": "2025-12-03T10:30:00Z"
}
```

---

### Call Management

#### POST /api/v1/calls/start

Start a new training call session.

**Request Body:**
```json
{
  "operator_id": "operator_123",
  "scenario_id": "uuid-of-scenario",  // Optional
  "metadata": {
    "training_session": "2025-Q1",
    "supervisor": "John Doe"
  }
}
```

**Response:** `201 Created`
```json
{
  "id": "call-session-uuid",
  "operator_id": "operator_123",
  "scenario_id": "uuid-of-scenario",
  "started_at": "2025-12-03T10:30:00Z",
  "status": "active",
  "websocket_url": "ws://localhost:8000/ws/call/call-session-uuid"
}
```

#### GET /api/v1/calls/{call_id}

Get details of a specific call session.

**Response:** `200 OK`
```json
{
  "id": "call-session-uuid",
  "operator_id": "operator_123",
  "scenario_id": "uuid-of-scenario",
  "scenario_name": "Domestic Violence Call",
  "started_at": "2025-12-03T10:30:00Z",
  "ended_at": "2025-12-03T10:35:42Z",
  "duration_ms": 342000,
  "status": "completed",
  "metadata": {
    "entities_extracted": 12,
    "average_confidence": 0.87
  }
}
```

#### POST /api/v1/calls/{call_id}/end

End an active call session.

**Request Body:**
```json
{
  "notes": "Operator performed well, extracted all critical information",
  "performance_score": 8.5
}
```

**Response:** `200 OK`
```json
{
  "id": "call-session-uuid",
  "status": "completed",
  "ended_at": "2025-12-03T10:35:42Z",
  "duration_ms": 342000
}
```

#### GET /api/v1/calls/{call_id}/transcript

Get the complete transcript of a call.

**Query Parameters:**
- `include_entities` (boolean): Include extracted entities (default: false)
- `format` (string): Response format - "json" or "text" (default: json)

**Response:** `200 OK`
```json
{
  "call_id": "call-session-uuid",
  "segments": [
    {
      "id": "transcript-uuid-1",
      "timestamp_ms": 0,
      "speaker": "caller",
      "text": "Help! Someone broke into my house!",
      "emotional_state": "panicked",
      "confidence_score": 0.95,
      "entities": [
        {
          "type": "LOCATION",
          "value": "house",
          "confidence_score": 0.92,
          "start_char": 30,
          "end_char": 35
        }
      ]
    },
    {
      "id": "transcript-uuid-2",
      "timestamp_ms": 3500,
      "speaker": "operator",
      "text": "Okay, stay calm. What is your address?",
      "emotional_state": "calm",
      "confidence_score": 0.98,
      "entities": []
    }
  ],
  "total_segments": 42,
  "duration_ms": 342000
}
```

---

### Scenario Management

#### GET /api/v1/scenarios

List all available training scenarios.

**Query Parameters:**
- `difficulty_level` (string): Filter by difficulty - "easy", "medium", "hard"
- `active` (boolean): Filter by active status (default: true)
- `limit` (integer): Number of results (default: 50)
- `offset` (integer): Pagination offset (default: 0)

**Response:** `200 OK`
```json
{
  "scenarios": [
    {
      "id": "scenario-uuid-1",
      "name": "Domestic Violence Call",
      "description": "Caller reporting domestic violence situation",
      "difficulty_level": "medium",
      "is_active": true,
      "caller_profile": {
        "name": "Sarah",
        "emotional_state": "fearful",
        "background": "30-year-old woman in abusive relationship",
        "communication_style": "hesitant, speaks quietly"
      },
      "objectives": [
        "Ensure caller safety",
        "Obtain location information",
        "Identify if weapons present"
      ]
    }
  ],
  "total": 5,
  "limit": 50,
  "offset": 0
}
```

#### POST /api/v1/scenarios

Create a new training scenario.

**Request Body:**
```json
{
  "name": "Bank Robbery in Progress",
  "description": "Witness calling about active bank robbery",
  "difficulty_level": "hard",
  "caller_profile": {
    "name": "John",
    "age": 45,
    "emotional_state": "terrified",
    "background": "Bank teller hiding during robbery",
    "communication_style": "whispering, interrupted speech"
  },
  "scenario_script": {
    "initial_situation": "Active bank robbery with 3 armed suspects",
    "key_information": [
      "Number of suspects: 3",
      "Weapons: Handguns visible",
      "Hostages: Approximately 12 people",
      "Location: First National Bank, downtown"
    ],
    "expected_flow": [
      "Caller whispers about situation",
      "Operator must speak quietly",
      "Obtain specific location within bank",
      "Determine if caller is safe",
      "Keep caller on line until help arrives"
    ]
  }
}
```

**Response:** `201 Created`
```json
{
  "id": "new-scenario-uuid",
  "name": "Bank Robbery in Progress",
  "created_at": "2025-12-03T10:30:00Z",
  "is_active": true
}
```

#### GET /api/v1/scenarios/{scenario_id}

Get details of a specific scenario.

**Response:** `200 OK`
```json
{
  "id": "scenario-uuid",
  "name": "Medical Emergency - Heart Attack",
  "description": "Caller reporting family member having heart attack",
  "difficulty_level": "hard",
  "caller_profile": {
    "name": "Maria",
    "emotional_state": "panicked",
    "background": "Wife calling about husband's heart attack",
    "communication_style": "rapid speech, crying"
  },
  "scenario_script": {
    "initial_situation": "65-year-old male experiencing chest pain",
    "key_information": [
      "Symptoms: Chest pain, shortness of breath, sweating",
      "Medical history: Previous heart attack 5 years ago",
      "Medications: Blood thinners, beta blockers",
      "Location: Home address"
    ],
    "expected_actions": [
      "Confirm address",
      "Assess consciousness and breathing",
      "Provide CPR instructions if needed",
      "Keep caller calm",
      "Confirm EMS dispatch"
    ]
  },
  "created_at": "2025-12-01T08:00:00Z",
  "updated_at": "2025-12-01T08:00:00Z"
}
```

---

## WebSocket API

### Connection

**Endpoint:** `ws://localhost:8000/ws/call/{session_id}`

Connect to this endpoint after creating a call session via `POST /api/v1/calls/start`.

**Connection Flow:**
1. Create call session via REST API
2. Receive `session_id` and `websocket_url`
3. Connect to WebSocket URL
4. Backend sends initial greeting
5. Begin bidirectional communication

---

### Client → Server Messages

#### Audio Chunk

Send audio data from operator's microphone.

```json
{
  "type": "audio_chunk",
  "data": "base64-encoded-audio-data",
  "timestamp": 1701600000123,
  "format": "pcm16",
  "sample_rate": 16000
}
```

#### Transcript Message

Send text transcript (alternative to audio).

```json
{
  "type": "transcript",
  "text": "What is your location?",
  "timestamp": 1701600000123
}
```

#### Control Command

Send call control commands.

```json
{
  "type": "control",
  "action": "mute",  // "mute", "unmute", "hold", "resume", "terminate"
  "timestamp": 1701600000123
}
```

---

### Server → Client Messages

#### Transcript Update

Real-time transcript segment from AI caller.

```json
{
  "type": "transcript_update",
  "speaker": "caller",
  "text": "I need help! Someone broke into my house!",
  "timestamp_ms": 1500,
  "emotional_state": "panicked",
  "confidence_score": 0.95
}
```

#### Audio Chunk

AI caller voice audio response.

```json
{
  "type": "audio_chunk",
  "data": "base64-encoded-audio-data",
  "timestamp": 1701600001456,
  "format": "wav",
  "sample_rate": 22050
}
```

#### Entity Detected

Newly extracted entity from conversation.

```json
{
  "type": "entity_detected",
  "entity": {
    "type": "WEAPON",
    "value": "gun",
    "confidence_score": 0.92,
    "context": "He has a gun",
    "transcript_id": "transcript-uuid"
  },
  "timestamp": 1701600002789
}
```

#### Emotional State Update

Updated emotional state of AI caller.

```json
{
  "type": "emotional_state",
  "state": "panicked",
  "confidence": 0.87,
  "previous_state": "anxious",
  "timestamp": 1701600003012
}
```

#### Error Message

Error notification.

```json
{
  "type": "error",
  "code": "LLM_ERROR",
  "message": "Failed to generate AI response",
  "timestamp": 1701600004567
}
```

#### Status Update

Call status updates.

```json
{
  "type": "status",
  "status": "active",
  "call_duration_ms": 45000,
  "timestamp": 1701600005890
}
```

---

## Error Responses

All error responses follow this format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field": "Additional error details"
    }
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_REQUEST` | 400 | Request validation failed |
| `SESSION_NOT_FOUND` | 404 | Call session not found |
| `SCENARIO_NOT_FOUND` | 404 | Training scenario not found |
| `SESSION_ALREADY_ENDED` | 409 | Attempt to modify ended session |
| `LLM_ERROR` | 500 | LLM service error |
| `TTS_ERROR` | 500 | TTS service error |
| `DATABASE_ERROR` | 500 | Database connection error |
| `STORAGE_ERROR` | 500 | S3 storage error |

---

## Rate Limiting

Rate limiting is applied to prevent abuse:

- **LLM requests**: 10 per minute per session
- **TTS requests**: 10 per minute per session
- **API endpoints**: 100 requests per minute per IP

When rate limit is exceeded, you'll receive:

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests. Please try again in 60 seconds.",
    "retry_after": 60
  }
}
```

HTTP Status: `429 Too Many Requests`

---

## Pagination

List endpoints support pagination:

**Request:**
```
GET /api/v1/scenarios?limit=20&offset=40
```

**Response:**
```json
{
  "scenarios": [...],
  "total": 100,
  "limit": 20,
  "offset": 40,
  "has_next": true,
  "has_prev": true
}
```

---

## Example Usage

### Starting a Training Call (JavaScript)

```javascript
// 1. Start call session
const response = await fetch('http://localhost:8000/api/v1/calls/start', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    operator_id: 'operator_123',
    scenario_id: 'scenario-uuid'
  })
});

const { id: sessionId, websocket_url } = await response.json();

// 2. Connect to WebSocket
const ws = new WebSocket(websocket_url);

ws.onopen = () => {
  console.log('Connected to call session');
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);

  switch (message.type) {
    case 'transcript_update':
      displayTranscript(message);
      break;
    case 'audio_chunk':
      playAudio(message.data);
      break;
    case 'entity_detected':
      highlightEntity(message.entity);
      break;
  }
};

// 3. Send audio from microphone
navigator.mediaDevices.getUserMedia({ audio: true })
  .then(stream => {
    const audioContext = new AudioContext({ sampleRate: 16000 });
    const source = audioContext.createMediaStreamSource(stream);
    const processor = audioContext.createScriptProcessor(4096, 1, 1);

    processor.onaudioprocess = (e) => {
      const audioData = e.inputBuffer.getChannelData(0);
      const base64Audio = btoa(String.fromCharCode(...new Uint8Array(audioData.buffer)));

      ws.send(JSON.stringify({
        type: 'audio_chunk',
        data: base64Audio,
        timestamp: Date.now()
      }));
    };

    source.connect(processor);
    processor.connect(audioContext.destination);
  });

// 4. End call
await fetch(`http://localhost:8000/api/v1/calls/${sessionId}/end`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    notes: 'Training completed successfully'
  })
});
```

### Python Example

```python
import asyncio
import aiohttp
import websockets
import json

async def training_call():
    # Start session
    async with aiohttp.ClientSession() as session:
        async with session.post(
            'http://localhost:8000/api/v1/calls/start',
            json={'operator_id': 'operator_123'}
        ) as resp:
            data = await resp.json()
            session_id = data['id']
            ws_url = data['websocket_url']

    # Connect to WebSocket
    async with websockets.connect(ws_url) as websocket:
        # Receive messages
        async for message in websocket:
            data = json.loads(message)
            print(f"Received: {data['type']}")

            if data['type'] == 'transcript_update':
                print(f"{data['speaker']}: {data['text']}")

asyncio.run(training_call())
```

---

## Interactive API Documentation

The backend provides interactive API documentation powered by FastAPI:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These interfaces allow you to:
- View all endpoints and schemas
- Test API calls directly from the browser
- Download OpenAPI specification

---

## Versioning

The API uses URL versioning (`/api/v1/`). Future versions will be released as `/api/v2/`, etc., with backwards compatibility maintained for at least 6 months after a new version is released.
