#!/bin/bash

# Build script for 911 Training Simulator Docker images
# This script builds both frontend and backend Docker images with optimized caching

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REGISTRY="${DOCKER_REGISTRY:-}"
VERSION="${VERSION:-latest}"
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

# Image names
BACKEND_IMAGE="911-training/backend"
FRONTEND_IMAGE="911-training/frontend"

# Build arguments
VITE_API_URL="${VITE_API_URL:-http://localhost:8000}"
VITE_WS_URL="${VITE_WS_URL:-ws://localhost:8000}"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

build_backend() {
    log_info "Building backend image..."

    cd "$PROJECT_ROOT/backend"

    # Build with cache optimization
    docker build \
        --build-arg BUILD_DATE="$BUILD_DATE" \
        --build-arg GIT_COMMIT="$GIT_COMMIT" \
        --tag "${BACKEND_IMAGE}:${VERSION}" \
        --tag "${BACKEND_IMAGE}:latest" \
        ${REGISTRY:+--tag "${REGISTRY}/${BACKEND_IMAGE}:${VERSION}"} \
        ${REGISTRY:+--tag "${REGISTRY}/${BACKEND_IMAGE}:latest"} \
        --file Dockerfile \
        .

    log_success "Backend image built successfully!"
}

build_frontend() {
    log_info "Building frontend image..."

    cd "$PROJECT_ROOT/frontend"

    # Build with build args for environment variables
    docker build \
        --build-arg BUILD_DATE="$BUILD_DATE" \
        --build-arg GIT_COMMIT="$GIT_COMMIT" \
        --build-arg VITE_API_URL="$VITE_API_URL" \
        --build-arg VITE_WS_URL="$VITE_WS_URL" \
        --tag "${FRONTEND_IMAGE}:${VERSION}" \
        --tag "${FRONTEND_IMAGE}:latest" \
        ${REGISTRY:+--tag "${REGISTRY}/${FRONTEND_IMAGE}:${VERSION}"} \
        ${REGISTRY:+--tag "${REGISTRY}/${FRONTEND_IMAGE}:latest"} \
        --file Dockerfile \
        .

    log_success "Frontend image built successfully!"
}

list_images() {
    log_info "Built images:"
    echo ""
    docker images | grep "911-training" || log_warn "No images found"
    echo ""
}

show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Build Docker images for 911 Training Simulator

OPTIONS:
    -b, --backend       Build only backend image
    -f, --frontend      Build only frontend image
    -a, --all           Build all images (default)
    -r, --registry      Set Docker registry (e.g., docker.io/username)
    -v, --version       Set image version tag (default: latest)
    -h, --help          Show this help message

ENVIRONMENT VARIABLES:
    DOCKER_REGISTRY     Docker registry URL
    VERSION             Image version tag
    VITE_API_URL        Frontend API URL
    VITE_WS_URL         Frontend WebSocket URL

EXAMPLES:
    # Build all images
    $0

    # Build only backend
    $0 --backend

    # Build with custom registry and version
    $0 --registry docker.io/myuser --version v1.0.0

    # Build with environment variables
    VITE_API_URL=https://api.example.com $0 --frontend
EOF
}

# Main script
main() {
    local build_backend=false
    local build_frontend=false
    local build_all=true

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -b|--backend)
                build_backend=true
                build_all=false
                shift
                ;;
            -f|--frontend)
                build_frontend=true
                build_all=false
                shift
                ;;
            -a|--all)
                build_all=true
                shift
                ;;
            -r|--registry)
                REGISTRY="$2"
                shift 2
                ;;
            -v|--version)
                VERSION="$2"
                shift 2
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done

    log_info "Starting Docker build process..."
    log_info "Project root: $PROJECT_ROOT"
    log_info "Version: $VERSION"
    log_info "Git commit: $GIT_COMMIT"
    [[ -n "$REGISTRY" ]] && log_info "Registry: $REGISTRY"
    echo ""

    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi

    # Build images
    if [[ "$build_all" == true ]]; then
        build_backend
        build_frontend
    else
        [[ "$build_backend" == true ]] && build_backend
        [[ "$build_frontend" == true ]] && build_frontend
    fi

    # List built images
    list_images

    log_success "Build process completed successfully!"

    if [[ -n "$REGISTRY" ]]; then
        log_info "To push images to registry, run: ./scripts/push-images.sh"
    fi
}

# Run main function
main "$@"
