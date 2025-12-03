# 911 Operator Training Simulator

A web-based simulation platform for training 911 operators using AI-powered caller simulation.

## 🏗️ Architecture

This application consists of:

- **Frontend**: React + TypeScript with real-time WebSocket communication
- **Backend**: FastAPI with WebSocket support for real-time audio/transcript streaming
- **LLM**: OpenRouter API for AI caller responses
- **TTS**: Coqui TTS for speech synthesis
- **Database**: PostgreSQL for persistent storage
- **Cache**: Redis for session management and real-time state
- **Storage**: S3-compatible object storage for call recordings

## 📋 Prerequisites

- Docker and Docker Compose
- Node.js 20+ (for local frontend development)
- Python 3.11+ (for local backend development)
- Kubernetes cluster (for production deployment)
- OpenRouter API key

## 🚀 Quick Start (Local Development)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd 911-AI-Training
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENROUTER_API_KEY
   ```

3. **Start all services**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - MinIO Console: http://localhost:9001

## 📦 Project Structure

```
911-AI-Training/
├── frontend/               # React frontend application
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── services/      # API and WebSocket services
│   │   ├── hooks/         # Custom React hooks
│   │   └── stores/        # State management
│   └── Dockerfile
├── backend/               # FastAPI backend application
│   ├── app/
│   │   ├── api/          # API routes
│   │   ├── core/         # Core functionality
│   │   ├── services/     # Business logic services
│   │   ├── models/       # Database models
│   │   └── db/           # Database configuration
│   └── Dockerfile
├── kubernetes/           # Kubernetes manifests
│   ├── deployments/
│   ├── services/
│   ├── statefulsets/
│   └── helm-chart/
├── docs/                 # Documentation
└── docker-compose.yml    # Local development setup
```

## 🔧 Development

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

## 🚢 Production Deployment

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for Kubernetes deployment instructions.

## 📚 Documentation

- [API Documentation](docs/API.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Development Guide](docs/DEVELOPMENT.md)
- [Architecture Overview](docs/ARCHITECTURE.md)

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## 📝 License

[Add your license here]

## 🤝 Contributing

[Add contribution guidelines here]
