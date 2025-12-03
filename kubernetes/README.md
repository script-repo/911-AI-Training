# 911 Operator Training Simulator - Kubernetes Deployment

This directory contains comprehensive Kubernetes manifests for deploying the 911 Operator Training Simulator to an on-premises Kubernetes cluster.

## Directory Structure

```
kubernetes/
├── namespace.yaml                  # Creates the 911-training namespace
├── configmaps/                     # Non-sensitive configuration
│   ├── backend-config.yaml         # Backend environment variables
│   └── frontend-config.yaml        # Frontend environment variables
├── secrets/                        # Sensitive configuration (examples only)
│   ├── README.md                   # Instructions for creating secrets
│   ├── openrouter-secret.yaml.example
│   ├── database-secret.yaml.example
│   ├── redis-secret.yaml.example
│   └── s3-secret.yaml.example
├── deployments/                    # Application deployments
│   ├── frontend-deployment.yaml    # React frontend (2 replicas)
│   ├── backend-deployment.yaml     # FastAPI backend (3 replicas)
│   ├── coqui-tts-deployment.yaml   # TTS service (2 replicas)
│   └── redis-deployment.yaml       # Redis cache (1 replica)
├── statefulsets/                   # Stateful applications
│   └── postgresql-statefulset.yaml # PostgreSQL database
├── services/                       # Kubernetes services
│   ├── frontend-service.yaml
│   ├── backend-service.yaml
│   ├── coqui-tts-service.yaml
│   ├── postgresql-service.yaml
│   └── redis-service.yaml
├── ingress/                        # Ingress configuration
│   └── ingress.yaml                # Nginx Ingress with WebSocket support
├── pvcs/                           # Persistent volume claims
│   └── postgres-pvc.yaml           # PostgreSQL storage
├── hpa/                            # Horizontal Pod Autoscaler
│   └── backend-hpa.yaml            # Backend autoscaling
├── helm-chart/                     # Helm chart for easy deployment
│   ├── Chart.yaml
│   ├── values.yaml
│   ├── README.md
│   └── templates/                  # Templated manifests
└── README.md                       # This file
```

## Deployment Options

### Option 1: Using Raw Kubernetes Manifests (Recommended for learning)

#### Step 1: Prepare Your Environment

1. **Build and Push Docker Images**:

```bash
# Build frontend
cd frontend
docker build -t your-registry/911-training-frontend:latest .
docker push your-registry/911-training-frontend:latest

# Build backend
cd ../backend
docker build -t your-registry/911-training-backend:latest .
docker push your-registry/911-training-backend:latest
```

2. **Update Image References**:

Edit the following files to use your registry:
- `deployments/frontend-deployment.yaml` - Line 32
- `deployments/backend-deployment.yaml` - Line 32

#### Step 2: Create Namespace

```bash
kubectl apply -f namespace.yaml
```

#### Step 3: Create Secrets

```bash
# Create secrets (DO NOT use the example values in production!)
kubectl create secret generic openrouter-secret \
  --from-literal=OPENROUTER_API_KEY=your_actual_api_key_here \
  --namespace=911-training

kubectl create secret generic database-secret \
  --from-literal=POSTGRES_USER=postgres \
  --from-literal=POSTGRES_PASSWORD=your_secure_password_here \
  --from-literal=DATABASE_URL=postgresql://postgres:your_secure_password_here@postgresql-service:5432/training_db \
  --namespace=911-training

kubectl create secret generic s3-secret \
  --from-literal=S3_ACCESS_KEY=your_s3_access_key \
  --from-literal=S3_SECRET_KEY=your_s3_secret_key \
  --namespace=911-training
```

See `secrets/README.md` for more options including Sealed Secrets and External Secrets Operator.

#### Step 4: Update ConfigMaps

Edit `configmaps/frontend-config.yaml` to set your domain:

```yaml
VITE_API_URL: "http://your-domain.com/api"
VITE_WS_URL: "ws://your-domain.com/ws"
```

#### Step 5: Deploy Infrastructure Components

```bash
# Deploy ConfigMaps
kubectl apply -f configmaps/

# Deploy PostgreSQL (stateful)
kubectl apply -f statefulsets/postgresql-statefulset.yaml

# Deploy Redis
kubectl apply -f deployments/redis-deployment.yaml

# Deploy Coqui TTS
kubectl apply -f deployments/coqui-tts-deployment.yaml

# Create Services
kubectl apply -f services/
```

#### Step 6: Wait for Infrastructure

```bash
# Wait for PostgreSQL to be ready
kubectl wait --for=condition=ready pod -l component=database -n 911-training --timeout=300s

# Wait for Redis to be ready
kubectl wait --for=condition=ready pod -l component=redis -n 911-training --timeout=300s

# Wait for Coqui TTS to be ready (may take longer to download models)
kubectl wait --for=condition=ready pod -l component=coqui-tts -n 911-training --timeout=600s
```

#### Step 7: Deploy Application Components

```bash
# Deploy Backend
kubectl apply -f deployments/backend-deployment.yaml

# Deploy Frontend
kubectl apply -f deployments/frontend-deployment.yaml

# Deploy HPA
kubectl apply -f hpa/backend-hpa.yaml
```

#### Step 8: Deploy Ingress

1. **Install Nginx Ingress Controller** (if not already installed):

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/baremetal/deploy.yaml
```

2. **Update Ingress Configuration**:

Edit `ingress/ingress.yaml` to set your domain (line 55).

3. **Apply Ingress**:

```bash
kubectl apply -f ingress/ingress.yaml
```

#### Step 9: Verify Deployment

```bash
# Check all pods
kubectl get pods -n 911-training

# Check services
kubectl get services -n 911-training

# Check ingress
kubectl get ingress -n 911-training

# Check HPA
kubectl get hpa -n 911-training

# View logs
kubectl logs -n 911-training -l component=backend --tail=50
kubectl logs -n 911-training -l component=frontend --tail=50
```

### Option 2: Using Helm Chart (Recommended for production)

#### Step 1: Prepare Helm Chart

1. **Update Values**:

Edit `helm-chart/values.yaml`:
- Set image repositories
- Configure domain names
- Adjust resource limits
- Set replica counts

2. **Create Secrets**:

```bash
kubectl create namespace 911-training

kubectl create secret generic openrouter-secret \
  --from-literal=OPENROUTER_API_KEY=your_key \
  -n 911-training

kubectl create secret generic database-secret \
  --from-literal=POSTGRES_USER=postgres \
  --from-literal=POSTGRES_PASSWORD=your_password \
  --from-literal=DATABASE_URL=postgresql://postgres:your_password@postgresql-service:5432/training_db \
  -n 911-training

kubectl create secret generic s3-secret \
  --from-literal=S3_ACCESS_KEY=your_key \
  --from-literal=S3_SECRET_KEY=your_secret \
  -n 911-training
```

#### Step 2: Install Helm Chart

```bash
# Install with default values
helm install 911-training ./helm-chart

# Or install with custom values
helm install 911-training ./helm-chart \
  --set frontend.image.repository=your-registry/frontend \
  --set backend.image.repository=your-registry/backend \
  --set ingress.hosts[0].host=your-domain.com
```

#### Step 3: Verify Installation

```bash
helm status 911-training -n 911-training
kubectl get pods -n 911-training
```

See `helm-chart/README.md` for detailed Helm documentation.

## Accessing the Application

### Via Ingress (Production)

Once deployed, access the application at:
- Frontend: `http://your-domain.com`
- Backend API: `http://your-domain.com/api`
- API Documentation: `http://your-domain.com/api/docs`
- WebSocket: `ws://your-domain.com/ws`

### Via Port Forwarding (Development/Testing)

```bash
# Frontend
kubectl port-forward -n 911-training svc/frontend-service 3000:80

# Backend
kubectl port-forward -n 911-training svc/backend-service 8000:8000

# PostgreSQL
kubectl port-forward -n 911-training svc/postgresql-service 5432:5432

# Redis
kubectl port-forward -n 911-training svc/redis-service 6379:6379
```

### Via NodePort (On-Prem without Ingress)

If you don't have an Ingress controller, you can expose services via NodePort:

```bash
# Edit frontend-service.yaml
kubectl patch svc frontend-service -n 911-training -p '{"spec":{"type":"NodePort"}}'

# Get the NodePort
kubectl get svc frontend-service -n 911-training

# Access via: http://<node-ip>:<node-port>
```

## Scaling

### Manual Scaling

```bash
# Scale backend
kubectl scale deployment backend --replicas=5 -n 911-training

# Scale frontend
kubectl scale deployment frontend --replicas=3 -n 911-training

# Scale Coqui TTS
kubectl scale deployment coqui-tts --replicas=3 -n 911-training
```

### Autoscaling

The backend has HPA configured by default:
- Min replicas: 3
- Max replicas: 10
- Target CPU: 70%
- Target Memory: 80%

Monitor autoscaling:
```bash
kubectl get hpa -n 911-training -w
```

## Monitoring and Maintenance

### Check Resource Usage

```bash
# Pod resource usage
kubectl top pods -n 911-training

# Node resource usage
kubectl top nodes
```

### View Logs

```bash
# All backend logs
kubectl logs -n 911-training -l component=backend --all-containers=true

# Follow frontend logs
kubectl logs -n 911-training -l component=frontend -f

# Database logs
kubectl logs -n 911-training -l component=database --tail=100
```

### Database Maintenance

```bash
# Backup PostgreSQL
kubectl exec -n 911-training postgresql-0 -- pg_dump -U postgres training_db > backup.sql

# Restore PostgreSQL
kubectl exec -i -n 911-training postgresql-0 -- psql -U postgres training_db < backup.sql

# Access PostgreSQL shell
kubectl exec -it -n 911-training postgresql-0 -- psql -U postgres -d training_db
```

### Redis Maintenance

```bash
# Check Redis info
kubectl exec -n 911-training -it $(kubectl get pod -n 911-training -l component=redis -o jsonpath='{.items[0].metadata.name}') -- redis-cli INFO

# Flush Redis cache
kubectl exec -n 911-training -it $(kubectl get pod -n 911-training -l component=redis -o jsonpath='{.items[0].metadata.name}') -- redis-cli FLUSHALL
```

## Updating the Application

### Rolling Update

```bash
# Update backend image
kubectl set image deployment/backend backend=your-registry/backend:v2.0.0 -n 911-training

# Update frontend image
kubectl set image deployment/frontend frontend=your-registry/frontend:v2.0.0 -n 911-training

# Check rollout status
kubectl rollout status deployment/backend -n 911-training
```

### Rollback

```bash
# Rollback backend
kubectl rollout undo deployment/backend -n 911-training

# Rollback to specific revision
kubectl rollout undo deployment/backend --to-revision=2 -n 911-training
```

## Troubleshooting

### Pod Not Starting

```bash
# Describe pod
kubectl describe pod <pod-name> -n 911-training

# Check events
kubectl get events -n 911-training --sort-by='.lastTimestamp'

# Check logs
kubectl logs <pod-name> -n 911-training --previous
```

### Service Connection Issues

```bash
# Test DNS resolution
kubectl run -it --rm debug --image=busybox --restart=Never -n 911-training -- nslookup backend-service

# Test service connectivity
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -n 911-training -- curl http://backend-service:8000/health
```

### Database Connection Issues

```bash
# Check database service
kubectl get endpoints postgresql-service -n 911-training

# Test database connection
kubectl run -it --rm psql-test --image=postgres:15-alpine --restart=Never -n 911-training -- psql -h postgresql-service -U postgres -d training_db
```

### Ingress Not Working

```bash
# Check ingress
kubectl describe ingress 911-training-ingress -n 911-training

# Check ingress controller logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller

# Verify ingress backend
kubectl get ingress 911-training-ingress -n 911-training -o yaml
```

## Production Best Practices

### 1. Resource Management
- Set appropriate resource requests and limits
- Monitor actual usage and adjust
- Use HPA for automatic scaling

### 2. Security
- Use RBAC for access control
- Enable Pod Security Policies
- Use Network Policies to restrict traffic
- Regularly update container images
- Scan images for vulnerabilities

### 3. High Availability
- Run multiple replicas of stateless services
- Use pod anti-affinity for distribution
- Set up proper health checks
- Configure PodDisruptionBudgets

### 4. Persistence
- Use appropriate StorageClasses
- Regular database backups
- Test restore procedures
- Monitor disk usage

### 5. Monitoring
- Set up Prometheus for metrics
- Configure Grafana dashboards
- Set up alerting rules
- Collect and analyze logs

### 6. Secrets Management
- Use external secrets management (Vault, AWS Secrets Manager)
- Rotate secrets regularly
- Never commit secrets to git
- Use Sealed Secrets for GitOps

### 7. TLS/SSL
- Use cert-manager for automatic certificate management
- Enable HTTPS for all ingress traffic
- Use secure communication between services

## Cleanup

### Delete All Resources

```bash
# Using kubectl
kubectl delete namespace 911-training

# Using Helm
helm uninstall 911-training -n 911-training
kubectl delete namespace 911-training
```

### Delete PVCs (Optional)

```bash
kubectl delete pvc -n 911-training --all
```

## Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Helm Documentation](https://helm.sh/docs/)
- [Nginx Ingress Controller](https://kubernetes.github.io/ingress-nginx/)
- [cert-manager](https://cert-manager.io/docs/)

## Support

For issues and questions:
- GitHub Issues: https://github.com/yourusername/911-AI-Training/issues
- Documentation: See `docs/` directory
