# 911 Operator Training Simulator - Architecture

## System Overview

The 911 Operator Training Simulator is a web-based platform that provides realistic emergency call simulations for training 911 operators. The system uses AI-powered caller simulation, real-time audio processing, and natural language understanding to create immersive training scenarios.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Client (Browser)                          │
│  • React Frontend with WebSocket                             │
│  • Web Audio API for microphone capture                      │
│  • Real-time transcript display                              │
└──────────────┬──────────────────────────────────────────────┘
               │ HTTPS/WSS
               │
┌──────────────▼──────────────────────────────────────────────┐
│              Kubernetes Ingress (Nginx)                      │
│  • Routes: /api → Backend, /ws → Backend, / → Frontend      │
└──────────────┬──────────────────────────────────────────────┘
               │
       ┌───────┴────────┐
       │                │
┌──────▼──────┐  ┌─────▼────────────────────────────────────┐
│  Frontend   │  │          Backend (FastAPI)                │
│  (Nginx)    │  │  • WebSocket server                       │
│             │  │  • REST API                               │
│  2 replicas │  │  • Audio processing                       │
└─────────────┘  │  • NLP entity extraction                  │
                 │  • Dialogue management                    │
                 │  3-5 replicas (autoscaling)               │
                 └──────┬────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
┌───────▼──────┐ ┌─────▼─────┐ ┌──────▼─────────┐
│ Coqui TTS    │ │  Redis    │ │  PostgreSQL    │
│ (On-prem)    │ │           │ │                │
│              │ │ Sessions  │ │ Transcripts    │
│ 2 replicas   │ │ Cache     │ │ Entities       │
└──────────────┘ │ Pub/Sub   │ │ Scenarios      │
                 │           │ │                │
                 │ 1 replica │ │ 1 replica      │
                 └───────────┘ └────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
┌───────▼──────┐ ┌─────▼───────────────▼──────────┐
│ S3/MinIO     │ │   OpenRouter API (External)     │
│ (On-prem)    │ │   • LLM inference               │
│              │ │   • DeepSeek or other models    │
│ Audio storage│ └─────────────────────────────────┘
└──────────────┘
```

## Component Architecture

### Frontend (React + TypeScript)

**Technology Stack:**
- React 18 with TypeScript
- Vite for building
- Zustand for state management
- Tailwind CSS for styling
- Web Audio API for microphone capture
- Native WebSocket for real-time communication

**Key Components:**
- **Call Taker Dashboard**: Main interface with call controls
- **Audio Processor**: Microphone capture and visualization
- **Live Transcript**: Real-time transcript display with speaker labels
- **Entity Visualizer**: Extracted entity display with highlighting

**State Management:**
- Call state (current call, transcript, duration)
- Entity state (extracted entities)
- Connection state (WebSocket status)

### Backend (FastAPI + Python)

**Technology Stack:**
- FastAPI for async web framework
- SQLAlchemy 2.0 with asyncpg for database
- Redis for caching and pub/sub
- boto3 for S3 storage
- OpenAI SDK for LLM integration (OpenRouter)
- spaCy for NLP
- httpx for async HTTP

**Key Services:**
- **LLM Service**: OpenRouter API integration for AI caller responses
- **TTS Service**: Coqui TTS integration for speech synthesis
- **NLP Service**: Entity extraction and sentiment analysis
- **Audio Service**: Audio encoding/decoding
- **Storage Service**: S3/MinIO integration for audio storage
- **Dialogue Manager**: Conversation context and state management

**API Design:**
- REST endpoints for call management
- WebSocket for real-time audio and transcript streaming
- Health and readiness checks

### Data Flow

#### Call Session Lifecycle

```
1. User selects scenario
   ↓
2. Frontend sends POST /api/v1/calls/start
   ↓
3. Backend creates CallSession in PostgreSQL
   ↓
4. Frontend establishes WebSocket connection
   ↓
5. Backend sends initial AI greeting via TTS
   ↓
6. Real-time audio streaming loop:
   - Operator speaks → Audio chunk → Backend
   - Backend stores in Redis buffer
   - Backend extracts entities (NLP)
   - Backend generates AI response (LLM)
   - Backend synthesizes speech (TTS)
   - Backend sends audio + transcript to Frontend
   ↓
7. User ends call
   ↓
8. Backend finalizes recording in S3
   ↓
9. Backend updates CallSession status
```

#### WebSocket Message Flow

**Client → Server:**
- `audio_chunk`: Base64 encoded audio data
- `transcript`: Text message from operator
- `control`: Mute, hold, transfer, terminate commands

**Server → Client:**
- `transcript_update`: New transcript segment with timestamp
- `audio_chunk`: AI caller audio response
- `entity_detected`: Newly extracted entity
- `emotional_state`: Updated emotional state of caller
- `error`: Error messages

### Data Storage

#### Redis (In-Memory)
- **Session state**: Active WebSocket connections (5-min TTL)
- **Audio buffers**: Temporary audio chunks (1-min TTL)
- **Conversation context**: Recent dialogue for LLM (5-min TTL)
- **Rate limits**: API rate limiting counters (1-min TTL)
- **Pub/Sub**: Real-time message distribution across backend pods

#### PostgreSQL (Persistent)
- **call_sessions**: Training session records
- **call_transcripts**: Individual utterances with timestamps
- **extracted_entities**: Named entities from transcripts
- **training_scenarios**: Pre-configured training scenarios
- **performance_metrics**: Operator performance data

#### S3/MinIO (Object Storage)
- **Audio recordings**: Complete call recordings in WAV format
- **Bucket**: `911-training-recordings`
- **Structure**: `recordings/{session_id}/{timestamp}.wav`

### Scaling Architecture

#### Horizontal Scaling
- **Frontend**: 2 replicas (stateless, can scale to N)
- **Backend**: 3-10 replicas with HPA (70% CPU, 80% memory)
- **Coqui TTS**: 2 replicas (CPU-intensive, can scale with demand)
- **Redis**: 1 replica (can add Sentinel for HA)
- **PostgreSQL**: 1 primary (can add read replicas)

#### Auto-scaling Policies
- Backend scales up immediately when CPU > 70%
- Backend scales down after 5 minutes of CPU < 70%
- Min 3 replicas, max 10 replicas

### Security Architecture

#### Network Security
- All internal communication via ClusterIP services
- Only Ingress exposed externally
- WebSocket connections authenticated (session-based later)
- CORS configured for allowed origins

#### Data Security
- Secrets stored in Kubernetes Secrets
- Database credentials never in code
- API keys from environment variables
- Audio recordings accessible only via presigned URLs

#### Container Security
- Non-root users in all containers
- Minimal base images (Alpine, Slim)
- No secrets in Docker images
- Security headers in Nginx

### High Availability

#### Fault Tolerance
- Multiple replicas for stateless services
- Pod anti-affinity for node distribution
- Liveness and readiness probes
- Graceful shutdown handling
- Automatic pod restart on failure

#### Data Persistence
- PostgreSQL with PVC (100GB)
- Regular backups to S3
- Database migrations for schema changes
- Point-in-time recovery capability

### Monitoring and Observability

#### Health Checks
- `/health`: Basic application health
- `/ready`: Dependency health (DB, Redis, S3, TTS)
- Kubernetes liveness and readiness probes

#### Logging
- Structured JSON logging
- stdout/stderr for container logs
- Log aggregation via Kubernetes
- Debug mode for development

#### Metrics (Future)
- Prometheus metrics endpoint
- Request latency tracking
- Error rate monitoring
- Resource utilization
- Call quality metrics

### Performance Characteristics

#### Expected Load
- **Target**: 10-20 concurrent training sessions
- **Peak**: 50 concurrent sessions
- **Audio**: 16kHz, 20ms frames = 50 frames/sec per session
- **LLM calls**: 2-3 per minute per session
- **TTS calls**: 2-3 per minute per session

#### Latency Targets
- **Audio end-to-end**: < 1 second
- **LLM response**: 1-3 seconds
- **TTS synthesis**: 0.5-2 seconds
- **Entity extraction**: < 100ms
- **Database queries**: < 50ms

#### Resource Requirements
- **CPU**: 8-12 cores total (baseline)
- **Memory**: 16-24GB total (baseline)
- **Storage**: 100GB database + 500GB audio
- **Network**: 1Gbps recommended

## Technology Decisions

### Why Redis?
- 100x faster than PostgreSQL for session state
- Native pub/sub for multi-pod coordination
- Automatic TTL expiration for cleanup
- Specialized data structures (lists, sets)

### Why PostgreSQL?
- ACID transactions for data integrity
- Complex queries with JOINs
- JSONB for flexible metadata
- Proven reliability and tooling

### Why On-Prem?
- Data sovereignty requirements
- No cloud costs for compute/storage
- Existing infrastructure utilization
- Full control over environment

### Why Kubernetes?
- Declarative infrastructure
- Auto-scaling and self-healing
- Service discovery and load balancing
- Rolling updates with zero downtime
- Portable across environments

### Why OpenRouter?
- Access to multiple LLM providers
- No need to host LLM infrastructure
- Easy model switching
- Cost-effective for training workload

### Why Coqui TTS?
- Open-source and self-hostable
- High-quality speech synthesis
- Emotional prosody control
- No per-use API costs

## Deployment Architecture

### Development Environment
- Docker Compose for local development
- All services on single machine
- Hot reloading for rapid iteration
- Local MinIO for S3 simulation

### Production Environment
- Kubernetes cluster (3+ nodes)
- Helm chart for deployment
- Persistent volumes for data
- Ingress for external access
- Monitoring and logging stack

## Future Enhancements

### Phase 2 Features
- Real-time performance scoring
- Voice stress analysis
- Multi-language support
- Advanced scenario branching

### Scaling Beyond 50 Sessions
- Redis Cluster for distributed cache
- PostgreSQL read replicas
- Dedicated TTS service cluster
- CDN for static assets
- Horizontal database sharding

### ML Enhancements
- Fine-tuned LLM on 911 transcripts
- Custom NER model for emergency entities
- Emotion detection from voice (not just text)
- Anomaly detection for training quality
