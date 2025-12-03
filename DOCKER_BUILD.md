# Docker Build Guide - 911 Operator Training Simulator

This document provides instructions for building and deploying the 911 Training Simulator using Docker.

## Overview

The project uses multi-stage Docker builds optimized for production deployment:

- **Backend**: Python 3.11-slim with FastAPI, runs with uvicorn
- **Frontend**: Node 20 Alpine build + Nginx Alpine runtime

## Files Created

### Backend
- `/backend/Dockerfile` - Multi-stage Python backend image
- `/backend/.dockerignore` - Excludes unnecessary files from build context
- `/backend/requirements.txt` - Python dependencies

### Frontend
- `/frontend/Dockerfile` - Multi-stage React build with Nginx
- `/frontend/.dockerignore` - Excludes node_modules, tests, etc.
- `/frontend/nginx.conf` - Production Nginx configuration with SPA routing

### Build Scripts
- `/scripts/build-images.sh` - Build all Docker images
- `/scripts/push-images.sh` - Push images to container registry

## Quick Start

### 1. Build All Images

```bash
# Using build script (recommended)
./scripts/build-images.sh

# Or build individually
docker build -t 911-training/backend:latest ./backend
docker build -t 911-training/frontend:latest ./frontend
```

### 2. Run with Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 3. Build with Custom Configuration

```bash
# Build with custom version
./scripts/build-images.sh --version v1.0.0

# Build only backend
./scripts/build-images.sh --backend

# Build with custom registry
./scripts/build-images.sh --registry docker.io/yourusername

# Build frontend with custom API URL
VITE_API_URL=https://api.example.com ./scripts/build-images.sh --frontend
```

## Build Scripts Usage

### build-images.sh

```bash
# Show help
./scripts/build-images.sh --help

# Build all images
./scripts/build-images.sh

# Build specific service
./scripts/build-images.sh --backend
./scripts/build-images.sh --frontend

# Build with version tag
./scripts/build-images.sh --version v1.0.0

# Build for registry
./scripts/build-images.sh --registry ghcr.io/yourorg
```

### push-images.sh

```bash
# Push to Docker Hub
docker login
DOCKER_REGISTRY=docker.io/yourusername ./scripts/push-images.sh

# Push to GitHub Container Registry
docker login ghcr.io
DOCKER_REGISTRY=ghcr.io/yourorg ./scripts/push-images.sh

# Push to AWS ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com
DOCKER_REGISTRY=123456789.dkr.ecr.us-east-1.amazonaws.com ./scripts/push-images.sh
```

## Environment Variables

### Backend Build Arguments
- Build-time variables (set in Dockerfile):
  - `BUILD_DATE` - Build timestamp
  - `GIT_COMMIT` - Git commit hash

- Runtime variables (set in docker-compose.yml or at runtime):
  - `OPENROUTER_API_KEY` - OpenRouter API key
  - `DATABASE_URL` - PostgreSQL connection string
  - `REDIS_URL` - Redis connection string
  - `S3_ENDPOINT` - S3-compatible storage endpoint
  - `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)

### Frontend Build Arguments
- Build-time variables:
  - `VITE_API_URL` - Backend API URL (default: http://localhost:8000)
  - `VITE_WS_URL` - WebSocket URL (default: ws://localhost:8000)
  - `BUILD_DATE` - Build timestamp
  - `GIT_COMMIT` - Git commit hash

## Image Details

### Backend Image (`911-training/backend:latest`)

**Base Image**: `python:3.11-slim`

**Features**:
- Multi-stage build (builder + runtime)
- Non-root user (appuser, UID 1000)
- System dependencies: libopus, ffmpeg
- Python dependencies from requirements.txt
- spaCy model pre-downloaded (en_core_web_sm)
- Health check on /health endpoint
- 4 uvicorn workers for production

**Size**: ~800MB (optimized)

**Exposed Ports**: 8000

### Frontend Image (`911-training/frontend:latest`)

**Base Images**:
- Build: `node:20-alpine`
- Runtime: `nginx:1.25-alpine`

**Features**:
- Multi-stage build (reduces final image size by ~90%)
- React app built with Vite
- Nginx with SPA routing
- Gzip compression enabled
- Static asset caching (1 year)
- Non-root user (appuser, UID 1000)
- Health check on / endpoint

**Size**: ~25MB (highly optimized)

**Exposed Ports**: 80

## Best Practices Implemented

### Dockerfile Optimization
- ✅ Multi-stage builds to minimize image size
- ✅ .dockerignore to reduce build context
- ✅ Layer caching optimization (dependencies first)
- ✅ Specific base image versions (no :latest)
- ✅ Non-root user execution
- ✅ Health checks for container orchestration
- ✅ Labels for metadata
- ✅ Cleanup of package manager cache

### Security
- ✅ Non-root users (UID 1000)
- ✅ No secrets in images
- ✅ Security headers in Nginx
- ✅ Minimal attack surface (slim/alpine images)

### Performance
- ✅ Gzip compression
- ✅ Static asset caching
- ✅ Multi-worker uvicorn setup
- ✅ Optimized layer ordering

## Troubleshooting

### Build fails with "requirements.txt not found"
Ensure you're in the project root directory and requirements.txt exists in /backend/

### Frontend build fails with "package.json not found"
Ensure package.json exists in /frontend/ directory

### Permission denied errors
The containers run as non-root users. Ensure volumes have correct permissions:
```bash
chmod -R 755 ./backend/app
chmod -R 755 ./frontend/src
```

### Health check failing
- Backend: Check if /health endpoint is accessible
- Frontend: Check if Nginx is serving files correctly

### Image size too large
- Ensure .dockerignore files are properly configured
- Verify multi-stage builds are being used
- Check for unnecessary dependencies

## Development vs Production

### Development
```bash
# Use docker-compose.yml (includes hot reload)
docker-compose up
```

### Production
```bash
# Build production images
./scripts/build-images.sh --version v1.0.0

# Use Kubernetes manifests
kubectl apply -f kubernetes/

# Or use production docker-compose
docker-compose -f docker-compose.prod.yml up -d
```

## Container Registry Examples

### Docker Hub
```bash
docker login
./scripts/build-images.sh --registry docker.io/yourusername
./scripts/push-images.sh --registry docker.io/yourusername
```

### GitHub Container Registry (GHCR)
```bash
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
./scripts/build-images.sh --registry ghcr.io/yourorg
./scripts/push-images.sh --registry ghcr.io/yourorg
```

### AWS Elastic Container Registry (ECR)
```bash
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  123456789.dkr.ecr.us-east-1.amazonaws.com

./scripts/build-images.sh --registry 123456789.dkr.ecr.us-east-1.amazonaws.com
./scripts/push-images.sh --registry 123456789.dkr.ecr.us-east-1.amazonaws.com
```

### Google Container Registry (GCR)
```bash
gcloud auth configure-docker
./scripts/build-images.sh --registry gcr.io/project-id
./scripts/push-images.sh --registry gcr.io/project-id
```

## Monitoring

### Check Container Health
```bash
# Using Docker
docker ps
docker inspect <container-id> | grep -A 10 "Health"

# Using docker-compose
docker-compose ps
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Resource Usage
```bash
docker stats
```

## CI/CD Integration

Example GitHub Actions workflow:

```yaml
name: Build and Push Docker Images

on:
  push:
    branches: [ main ]
    tags: [ 'v*' ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build images
        run: ./scripts/build-images.sh --version ${{ github.ref_name }}

      - name: Login to registry
        run: echo "${{ secrets.DOCKER_PASSWORD }}" | docker login -u "${{ secrets.DOCKER_USERNAME }}" --password-stdin

      - name: Push images
        run: DOCKER_REGISTRY=docker.io/yourusername ./scripts/push-images.sh --version ${{ github.ref_name }}
```

## Additional Resources

- Docker documentation: https://docs.docker.com
- Docker Compose: https://docs.docker.com/compose/
- Multi-stage builds: https://docs.docker.com/build/building/multi-stage/
- Best practices: https://docs.docker.com/develop/dev-best-practices/
