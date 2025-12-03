#!/bin/bash

# 911 Operator Training Simulator - Kubernetes Deployment Script
# This script helps deploy the application to a Kubernetes cluster

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="911-training"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Functions
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    print_info "Checking prerequisites..."

    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl not found. Please install kubectl."
        exit 1
    fi

    # Check cluster connectivity
    if ! kubectl cluster-info &> /dev/null; then
        print_error "Cannot connect to Kubernetes cluster. Please check your kubeconfig."
        exit 1
    fi

    print_info "Prerequisites check passed!"
}

create_namespace() {
    print_info "Creating namespace: $NAMESPACE"
    kubectl apply -f "$SCRIPT_DIR/namespace.yaml"
}

check_secrets() {
    print_info "Checking for required secrets..."

    missing_secrets=()

    if ! kubectl get secret openrouter-secret -n "$NAMESPACE" &> /dev/null; then
        missing_secrets+=("openrouter-secret")
    fi

    if ! kubectl get secret database-secret -n "$NAMESPACE" &> /dev/null; then
        missing_secrets+=("database-secret")
    fi

    if ! kubectl get secret s3-secret -n "$NAMESPACE" &> /dev/null; then
        missing_secrets+=("s3-secret")
    fi

    if [ ${#missing_secrets[@]} -ne 0 ]; then
        print_warning "Missing secrets: ${missing_secrets[*]}"
        print_warning "Please create the secrets before continuing."
        print_info "See secrets/README.md for instructions."

        read -p "Do you want to continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        print_info "All required secrets found!"
    fi
}

deploy_configmaps() {
    print_info "Deploying ConfigMaps..."
    kubectl apply -f "$SCRIPT_DIR/configmaps/"
}

deploy_infrastructure() {
    print_info "Deploying infrastructure components..."

    # Deploy PostgreSQL
    print_info "Deploying PostgreSQL..."
    kubectl apply -f "$SCRIPT_DIR/statefulsets/postgresql-statefulset.yaml"

    # Deploy Redis
    print_info "Deploying Redis..."
    kubectl apply -f "$SCRIPT_DIR/deployments/redis-deployment.yaml"

    # Deploy Coqui TTS
    print_info "Deploying Coqui TTS..."
    kubectl apply -f "$SCRIPT_DIR/deployments/coqui-tts-deployment.yaml"

    # Deploy Services
    print_info "Deploying Services..."
    kubectl apply -f "$SCRIPT_DIR/services/"
}

wait_for_infrastructure() {
    print_info "Waiting for infrastructure to be ready..."

    print_info "Waiting for PostgreSQL..."
    kubectl wait --for=condition=ready pod -l component=database -n "$NAMESPACE" --timeout=300s || true

    print_info "Waiting for Redis..."
    kubectl wait --for=condition=ready pod -l component=redis -n "$NAMESPACE" --timeout=300s || true

    print_info "Waiting for Coqui TTS (this may take a while to download models)..."
    kubectl wait --for=condition=ready pod -l component=coqui-tts -n "$NAMESPACE" --timeout=600s || true
}

deploy_application() {
    print_info "Deploying application components..."

    # Deploy Backend
    print_info "Deploying Backend..."
    kubectl apply -f "$SCRIPT_DIR/deployments/backend-deployment.yaml"

    # Deploy Frontend
    print_info "Deploying Frontend..."
    kubectl apply -f "$SCRIPT_DIR/deployments/frontend-deployment.yaml"

    # Deploy HPA
    print_info "Deploying HorizontalPodAutoscaler..."
    kubectl apply -f "$SCRIPT_DIR/hpa/"
}

deploy_ingress() {
    print_info "Deploying Ingress..."

    # Check if Nginx Ingress Controller is installed
    if ! kubectl get namespace ingress-nginx &> /dev/null; then
        print_warning "Nginx Ingress Controller not found."
        read -p "Do you want to install it? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_info "Installing Nginx Ingress Controller..."
            kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/baremetal/deploy.yaml
            print_info "Waiting for Ingress Controller to be ready..."
            kubectl wait --namespace ingress-nginx \
                --for=condition=ready pod \
                --selector=app.kubernetes.io/component=controller \
                --timeout=300s
        fi
    fi

    kubectl apply -f "$SCRIPT_DIR/ingress/"
}

show_status() {
    print_info "Deployment Status:"
    echo ""
    echo "=== Pods ==="
    kubectl get pods -n "$NAMESPACE"
    echo ""
    echo "=== Services ==="
    kubectl get services -n "$NAMESPACE"
    echo ""
    echo "=== Ingress ==="
    kubectl get ingress -n "$NAMESPACE"
    echo ""
    echo "=== HPA ==="
    kubectl get hpa -n "$NAMESPACE"
}

show_access_info() {
    print_info "Access Information:"
    echo ""

    # Get ingress info
    INGRESS_HOST=$(kubectl get ingress 911-training-ingress -n "$NAMESPACE" -o jsonpath='{.spec.rules[0].host}' 2>/dev/null || echo "Not configured")

    if [ "$INGRESS_HOST" != "Not configured" ]; then
        echo "Frontend: http://$INGRESS_HOST"
        echo "Backend API: http://$INGRESS_HOST/api"
        echo "API Docs: http://$INGRESS_HOST/api/docs"
        echo "WebSocket: ws://$INGRESS_HOST/ws"
    else
        echo "Ingress not configured. Use port-forwarding:"
        echo ""
        echo "Frontend:"
        echo "  kubectl port-forward -n $NAMESPACE svc/frontend-service 3000:80"
        echo "  Access: http://localhost:3000"
        echo ""
        echo "Backend:"
        echo "  kubectl port-forward -n $NAMESPACE svc/backend-service 8000:8000"
        echo "  Access: http://localhost:8000/docs"
    fi
}

# Main deployment flow
main() {
    echo ""
    echo "=========================================="
    echo "  911 Training Simulator Deployment"
    echo "=========================================="
    echo ""

    check_prerequisites
    create_namespace
    check_secrets
    deploy_configmaps
    deploy_infrastructure
    wait_for_infrastructure
    deploy_application

    read -p "Do you want to deploy Ingress? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        deploy_ingress
    fi

    echo ""
    print_info "Waiting for application pods to be ready..."
    sleep 10

    show_status
    echo ""
    show_access_info
    echo ""
    print_info "Deployment complete!"
    echo ""
    print_info "To view logs:"
    echo "  kubectl logs -n $NAMESPACE -l component=backend -f"
    echo "  kubectl logs -n $NAMESPACE -l component=frontend -f"
    echo ""
}

# Run main function
main
