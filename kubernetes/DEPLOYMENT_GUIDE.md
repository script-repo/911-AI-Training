# 911 Operator Training Simulator - Kubernetes Deployment Guide

This guide provides step-by-step instructions for deploying the 911 Operator Training Simulator to an on-premises Kubernetes cluster.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Quick Start (Automated)](#quick-start-automated)
4. [Manual Deployment](#manual-deployment)
5. [Helm Deployment](#helm-deployment)
6. [Post-Deployment Configuration](#post-deployment-configuration)
7. [Verification](#verification)
8. [Common Issues](#common-issues)

## Prerequisites

### Required Software

- **Kubernetes Cluster**: Version 1.19 or higher
- **kubectl**: Configured to access your cluster
- **Helm**: Version 3.0+ (for Helm deployment method)
- **Docker**: For building container images
- **Container Registry**: Docker Hub, Harbor, or private registry

### Cluster Requirements

- **Minimum Resources**:
  - 3 worker nodes (recommended for HA)
  - 8 CPU cores total
  - 16 GB RAM total
  - 200 GB storage

- **Recommended Resources**:
  - 5+ worker nodes
  - 16+ CPU cores total
  - 32+ GB RAM total
  - 500+ GB storage (SSD recommended for database)

### Network Requirements

- Nodes can access external registries (or use private registry)
- Ingress controller installed (Nginx recommended)
- LoadBalancer or NodePort capability for external access
- Internal DNS working correctly

### Access Requirements

- Cluster admin access (for creating namespaces, RBAC)
- Access to container registry
- OpenRouter API key (for LLM)
- S3/MinIO credentials (for audio storage)

## Pre-Deployment Checklist

### 1. Build Container Images

```bash
# Clone the repository
git clone https://github.com/yourusername/911-AI-Training.git
cd 911-AI-Training

# Build frontend image
cd frontend
docker build -t your-registry.com/911-training-frontend:v1.0.0 .
docker push your-registry.com/911-training-frontend:v1.0.0

# Build backend image
cd ../backend
docker build -t your-registry.com/911-training-backend:v1.0.0 .
docker push your-registry.com/911-training-backend:v1.0.0
```

### 2. Prepare Configuration

Create a configuration file with your values:

```bash
# config.env
OPENROUTER_API_KEY=sk-or-v1-...
DB_PASSWORD=your_secure_password_here
S3_ACCESS_KEY=your_s3_access_key
S3_SECRET_KEY=your_s3_secret_key
DOMAIN=training.example.com
FRONTEND_IMAGE=your-registry.com/911-training-frontend:v1.0.0
BACKEND_IMAGE=your-registry.com/911-training-backend:v1.0.0
```

### 3. Update Manifests

Update the following files with your configuration:

**deployments/frontend-deployment.yaml**:
- Line 32: Update `image` to your frontend image

**deployments/backend-deployment.yaml**:
- Line 32: Update `image` to your backend image

**configmaps/frontend-config.yaml**:
- Update `VITE_API_URL` and `VITE_WS_URL` with your domain

**ingress/ingress.yaml**:
- Line 55: Update `host` to your domain

## Quick Start (Automated)

Use the provided deployment script for automated deployment:

```bash
cd kubernetes

# Make script executable (if not already)
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

The script will:
1. Check prerequisites
2. Create namespace
3. Check for secrets (will prompt if missing)
4. Deploy ConfigMaps
5. Deploy infrastructure (PostgreSQL, Redis, Coqui TTS)
6. Wait for infrastructure to be ready
7. Deploy application (Backend, Frontend)
8. Deploy HPA
9. Optionally deploy Ingress
10. Show deployment status

## Manual Deployment

### Step 1: Create Namespace

```bash
kubectl apply -f namespace.yaml
```

**Verify**:
```bash
kubectl get namespace 911-training
```

### Step 2: Create Secrets

```bash
# Load configuration
source config.env

# Create OpenRouter secret
kubectl create secret generic openrouter-secret \
  --from-literal=OPENROUTER_API_KEY=$OPENROUTER_API_KEY \
  --namespace=911-training

# Create Database secret
kubectl create secret generic database-secret \
  --from-literal=POSTGRES_USER=postgres \
  --from-literal=POSTGRES_PASSWORD=$DB_PASSWORD \
  --from-literal=DATABASE_URL=postgresql://postgres:$DB_PASSWORD@postgresql-service:5432/training_db \
  --namespace=911-training

# Create S3 secret
kubectl create secret generic s3-secret \
  --from-literal=S3_ACCESS_KEY=$S3_ACCESS_KEY \
  --from-literal=S3_SECRET_KEY=$S3_SECRET_KEY \
  --namespace=911-training
```

**Verify**:
```bash
kubectl get secrets -n 911-training
```

### Step 3: Deploy ConfigMaps

```bash
kubectl apply -f configmaps/
```

**Verify**:
```bash
kubectl get configmaps -n 911-training
kubectl describe configmap backend-config -n 911-training
```

### Step 4: Deploy PostgreSQL

```bash
kubectl apply -f statefulsets/postgresql-statefulset.yaml
```

**Wait for PostgreSQL**:
```bash
kubectl wait --for=condition=ready pod -l component=database -n 911-training --timeout=300s
```

**Verify**:
```bash
kubectl get pods -n 911-training -l component=database
kubectl logs -n 911-training -l component=database --tail=50
```

### Step 5: Deploy Redis

```bash
kubectl apply -f deployments/redis-deployment.yaml
```

**Wait for Redis**:
```bash
kubectl wait --for=condition=ready pod -l component=redis -n 911-training --timeout=300s
```

**Verify**:
```bash
kubectl get pods -n 911-training -l component=redis
```

### Step 6: Deploy Coqui TTS

```bash
kubectl apply -f deployments/coqui-tts-deployment.yaml
```

**Wait for Coqui TTS** (may take 5-10 minutes to download models):
```bash
kubectl wait --for=condition=ready pod -l component=coqui-tts -n 911-training --timeout=600s
```

**Verify**:
```bash
kubectl get pods -n 911-training -l component=coqui-tts
kubectl logs -n 911-training -l component=coqui-tts --tail=100
```

### Step 7: Deploy Services

```bash
kubectl apply -f services/
```

**Verify**:
```bash
kubectl get services -n 911-training
kubectl get endpoints -n 911-training
```

### Step 8: Deploy Backend

```bash
kubectl apply -f deployments/backend-deployment.yaml
```

**Wait for Backend**:
```bash
kubectl wait --for=condition=ready pod -l component=backend -n 911-training --timeout=300s
```

**Verify**:
```bash
kubectl get pods -n 911-training -l component=backend
kubectl logs -n 911-training -l component=backend --tail=50

# Test health endpoint
kubectl run -it --rm curl-test --image=curlimages/curl --restart=Never -n 911-training -- \
  curl -s http://backend-service:8000/health
```

### Step 9: Deploy Frontend

```bash
kubectl apply -f deployments/frontend-deployment.yaml
```

**Wait for Frontend**:
```bash
kubectl wait --for=condition=ready pod -l component=frontend -n 911-training --timeout=300s
```

**Verify**:
```bash
kubectl get pods -n 911-training -l component=frontend
```

### Step 10: Deploy HPA

```bash
kubectl apply -f hpa/
```

**Verify**:
```bash
kubectl get hpa -n 911-training
kubectl describe hpa backend-hpa -n 911-training
```

### Step 11: Deploy Ingress

**Install Nginx Ingress Controller** (if not installed):
```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/baremetal/deploy.yaml

# Wait for it to be ready
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=300s
```

**Deploy Ingress**:
```bash
kubectl apply -f ingress/ingress.yaml
```

**Verify**:
```bash
kubectl get ingress -n 911-training
kubectl describe ingress 911-training-ingress -n 911-training
```

## Helm Deployment

### Step 1: Prepare Helm Values

Create a custom values file:

```yaml
# custom-values.yaml
frontend:
  image:
    repository: your-registry.com/911-training-frontend
    tag: v1.0.0
  config:
    viteApiUrl: "https://training.example.com/api"
    viteWsUrl: "wss://training.example.com/ws"

backend:
  image:
    repository: your-registry.com/911-training-backend
    tag: v1.0.0
  replicaCount: 5

postgresql:
  persistence:
    size: 500Gi
    storageClass: fast-ssd

ingress:
  enabled: true
  hosts:
    - host: training.example.com
      paths:
        - path: /api
          pathType: Prefix
          backend: backend
        - path: /ws
          pathType: Prefix
          backend: backend
        - path: /
          pathType: Prefix
          backend: frontend
  tls:
    - secretName: training-tls
      hosts:
        - training.example.com
```

### Step 2: Create Secrets

```bash
kubectl create namespace 911-training

kubectl create secret generic openrouter-secret \
  --from-literal=OPENROUTER_API_KEY=$OPENROUTER_API_KEY \
  -n 911-training

kubectl create secret generic database-secret \
  --from-literal=POSTGRES_USER=postgres \
  --from-literal=POSTGRES_PASSWORD=$DB_PASSWORD \
  --from-literal=DATABASE_URL=postgresql://postgres:$DB_PASSWORD@postgresql-service:5432/training_db \
  -n 911-training

kubectl create secret generic s3-secret \
  --from-literal=S3_ACCESS_KEY=$S3_ACCESS_KEY \
  --from-literal=S3_SECRET_KEY=$S3_SECRET_KEY \
  -n 911-training
```

### Step 3: Install Helm Chart

```bash
cd kubernetes

# Validate chart
helm lint helm-chart/

# Dry run to check what will be created
helm install 911-training helm-chart/ \
  -f custom-values.yaml \
  --dry-run --debug

# Install for real
helm install 911-training helm-chart/ \
  -f custom-values.yaml

# Or install with inline overrides
helm install 911-training helm-chart/ \
  --set frontend.image.tag=v1.0.0 \
  --set backend.image.tag=v1.0.0 \
  --set ingress.hosts[0].host=training.example.com
```

### Step 4: Verify Helm Installation

```bash
# Check release status
helm status 911-training -n 911-training

# List all resources
helm get all 911-training -n 911-training

# Check pods
kubectl get pods -n 911-training
```

## Post-Deployment Configuration

### 1. Initialize Database

```bash
# Run database migrations (if applicable)
kubectl exec -n 911-training -it deployment/backend -- python -m app.db.init_db

# Or create initial tables
kubectl exec -n 911-training -it postgresql-0 -- psql -U postgres -d training_db -f /path/to/schema.sql
```

### 2. Configure DNS

Point your domain to the Ingress IP:

```bash
# Get Ingress IP
kubectl get ingress 911-training-ingress -n 911-training

# Create DNS A record:
# training.example.com -> <ingress-ip>
```

### 3. Enable TLS (Optional but Recommended)

Install cert-manager:
```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create ClusterIssuer
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

Update ingress to use TLS:
```bash
kubectl annotate ingress 911-training-ingress -n 911-training \
  cert-manager.io/cluster-issuer=letsencrypt-prod
```

### 4. Set Up Monitoring (Recommended)

```bash
# Add Prometheus annotations to backend pods
kubectl patch deployment backend -n 911-training -p '
{
  "spec": {
    "template": {
      "metadata": {
        "annotations": {
          "prometheus.io/scrape": "true",
          "prometheus.io/port": "8000",
          "prometheus.io/path": "/metrics"
        }
      }
    }
  }
}'
```

## Verification

### Check All Components

```bash
# All pods should be Running
kubectl get pods -n 911-training

# All services should have endpoints
kubectl get endpoints -n 911-training

# HPA should show current metrics
kubectl get hpa -n 911-training

# Ingress should have an address
kubectl get ingress -n 911-training
```

### Test Backend Health

```bash
# Via service
kubectl run -it --rm curl-test --image=curlimages/curl --restart=Never -n 911-training -- \
  curl -v http://backend-service:8000/health

# Via ingress (if configured)
curl http://your-domain.com/api/health
```

### Test Frontend

```bash
# Via port-forward
kubectl port-forward -n 911-training svc/frontend-service 3000:80

# Open browser to http://localhost:3000

# Or via ingress
# Open browser to http://your-domain.com
```

### Test WebSocket Connection

```bash
# Install wscat
npm install -g wscat

# Test WebSocket
wscat -c ws://your-domain.com/ws
```

### Load Testing

```bash
# Install hey
go install github.com/rakyll/hey@latest

# Test backend
hey -n 1000 -c 10 http://your-domain.com/api/health

# Monitor HPA during load test
kubectl get hpa -n 911-training -w
```

## Common Issues

### Issue: Pods Stuck in Pending

**Symptoms**: Pods show `Pending` status

**Causes**:
- Insufficient resources
- PVC not bound
- Node selector not matching

**Solutions**:
```bash
# Check pod events
kubectl describe pod <pod-name> -n 911-training

# Check node resources
kubectl describe nodes

# Check PVC status
kubectl get pvc -n 911-training
```

### Issue: Pods Crash Looping

**Symptoms**: Pods show `CrashLoopBackOff`

**Causes**:
- Missing secrets
- Database connection failure
- Configuration errors

**Solutions**:
```bash
# Check logs
kubectl logs <pod-name> -n 911-training --previous

# Check secrets
kubectl get secrets -n 911-training

# Verify secret values
kubectl get secret database-secret -n 911-training -o yaml
```

### Issue: Cannot Access via Ingress

**Symptoms**: Ingress returns 503 or 404

**Causes**:
- Ingress controller not installed
- Backend pods not ready
- Service endpoints missing

**Solutions**:
```bash
# Check ingress controller
kubectl get pods -n ingress-nginx

# Check backend pods
kubectl get pods -n 911-training -l component=backend

# Check service endpoints
kubectl get endpoints backend-service -n 911-training

# Check ingress logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller
```

### Issue: Database Connection Failed

**Symptoms**: Backend logs show database connection errors

**Causes**:
- PostgreSQL not ready
- Incorrect credentials
- Network policy blocking

**Solutions**:
```bash
# Check PostgreSQL pod
kubectl get pods -n 911-training -l component=database

# Check PostgreSQL logs
kubectl logs -n 911-training postgresql-0

# Test connection
kubectl run -it --rm psql-test --image=postgres:15-alpine --restart=Never -n 911-training -- \
  psql -h postgresql-service -U postgres -d training_db

# Verify secret
kubectl get secret database-secret -n 911-training -o jsonpath='{.data.DATABASE_URL}' | base64 -d
```

### Issue: High Memory Usage

**Symptoms**: Pods being OOMKilled

**Solutions**:
```bash
# Check resource usage
kubectl top pods -n 911-training

# Increase memory limits
kubectl patch deployment backend -n 911-training -p '
{
  "spec": {
    "template": {
      "spec": {
        "containers": [
          {
            "name": "backend",
            "resources": {
              "limits": {
                "memory": "4Gi"
              }
            }
          }
        ]
      }
    }
  }
}'
```

## Next Steps

After successful deployment:

1. **Set up monitoring**: Install Prometheus and Grafana
2. **Configure backups**: Set up automated database backups
3. **Enable logging**: Configure centralized logging (ELK/Loki)
4. **Security hardening**: Enable Pod Security Policies, Network Policies
5. **Load testing**: Test with realistic traffic patterns
6. **Documentation**: Document your specific configuration

## Support

For additional help:
- Check logs: `kubectl logs -n 911-training <pod-name>`
- Review events: `kubectl get events -n 911-training --sort-by='.lastTimestamp'`
- Consult documentation: `kubernetes/README.md`
- Open an issue: GitHub Issues
