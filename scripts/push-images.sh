#!/bin/bash

# Push script for 911 Training Simulator Docker images
# This script pushes Docker images to a container registry

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REGISTRY="${DOCKER_REGISTRY:-}"
VERSION="${VERSION:-latest}"

# Image names
BACKEND_IMAGE="911-training/backend"
FRONTEND_IMAGE="911-training/frontend"

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

push_image() {
    local image=$1
    local version=$2

    if [[ -z "$REGISTRY" ]]; then
        log_error "Docker registry not set. Please set DOCKER_REGISTRY or use --registry option."
        exit 1
    fi

    local full_image="${REGISTRY}/${image}:${version}"

    log_info "Pushing ${full_image}..."

    # Check if image exists locally
    if ! docker images | grep -q "${image}.*${version}"; then
        log_warn "Image ${image}:${version} not found locally. Tagging..."
        docker tag "${image}:${version}" "${full_image}" 2>/dev/null || {
            log_error "Failed to tag image. Make sure the image exists locally."
            exit 1
        }
    fi

    # Push image
    if docker push "${full_image}"; then
        log_success "Successfully pushed ${full_image}"
    else
        log_error "Failed to push ${full_image}"
        exit 1
    fi
}

push_backend() {
    log_info "Pushing backend image..."
    push_image "$BACKEND_IMAGE" "$VERSION"
    [[ "$VERSION" != "latest" ]] && push_image "$BACKEND_IMAGE" "latest"
}

push_frontend() {
    log_info "Pushing frontend image..."
    push_image "$FRONTEND_IMAGE" "$VERSION"
    [[ "$VERSION" != "latest" ]] && push_image "$FRONTEND_IMAGE" "latest"
}

verify_registry_login() {
    log_info "Verifying Docker registry login..."

    if [[ -z "$REGISTRY" ]]; then
        log_error "Docker registry not set."
        exit 1
    fi

    # Extract registry domain (handle different registry formats)
    local registry_domain
    if [[ "$REGISTRY" =~ ^([^/]+)/ ]]; then
        registry_domain="${BASH_REMATCH[1]}"
    else
        registry_domain="$REGISTRY"
    fi

    # Try to authenticate
    if docker info 2>/dev/null | grep -q "Username"; then
        log_success "Already logged in to Docker registry"
    else
        log_warn "Not logged in to Docker registry. Please login first:"
        log_info "Run: docker login ${registry_domain}"
        exit 1
    fi
}

show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Push Docker images to container registry

OPTIONS:
    -b, --backend       Push only backend image
    -f, --frontend      Push only frontend image
    -a, --all           Push all images (default)
    -r, --registry      Set Docker registry (e.g., docker.io/username)
    -v, --version       Set image version tag (default: latest)
    -h, --help          Show this help message

ENVIRONMENT VARIABLES:
    DOCKER_REGISTRY     Docker registry URL (required)
    VERSION             Image version tag

EXAMPLES:
    # Push all images
    DOCKER_REGISTRY=docker.io/myuser $0

    # Push only backend
    $0 --registry docker.io/myuser --backend

    # Push specific version
    $0 --registry docker.io/myuser --version v1.0.0

    # Push to GitHub Container Registry
    DOCKER_REGISTRY=ghcr.io/myuser $0

    # Push to AWS ECR
    DOCKER_REGISTRY=123456789.dkr.ecr.us-east-1.amazonaws.com $0

PREREQUISITES:
    1. Build images first: ./scripts/build-images.sh
    2. Login to registry: docker login <registry>
    3. Ensure images are tagged correctly
EOF
}

# Main script
main() {
    local push_backend=false
    local push_frontend=false
    local push_all=true

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -b|--backend)
                push_backend=true
                push_all=false
                shift
                ;;
            -f|--frontend)
                push_frontend=true
                push_all=false
                shift
                ;;
            -a|--all)
                push_all=true
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

    # Verify registry is set
    if [[ -z "$REGISTRY" ]]; then
        log_error "Docker registry not specified."
        log_info "Set DOCKER_REGISTRY environment variable or use --registry option."
        echo ""
        show_usage
        exit 1
    fi

    log_info "Starting Docker push process..."
    log_info "Registry: $REGISTRY"
    log_info "Version: $VERSION"
    echo ""

    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi

    # Verify registry login
    # verify_registry_login

    # Push images
    if [[ "$push_all" == true ]]; then
        push_backend
        push_frontend
    else
        [[ "$push_backend" == true ]] && push_backend
        [[ "$push_frontend" == true ]] && push_frontend
    fi

    echo ""
    log_success "Push process completed successfully!"
    log_info "Images available at:"
    log_info "  - ${REGISTRY}/${BACKEND_IMAGE}:${VERSION}"
    log_info "  - ${REGISTRY}/${FRONTEND_IMAGE}:${VERSION}"
}

# Run main function
main "$@"
