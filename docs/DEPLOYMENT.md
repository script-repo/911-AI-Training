# Deployment Guide

This guide covers deploying the 911 Operator Training Simulator to an on-premises Kubernetes cluster.

## Prerequisites

### Infrastructure Requirements

- **Kubernetes cluster**: 1.19+ with 3+ worker nodes
- **CPU**: Minimum 8 cores total (12+ recommended)
- **Memory**: Minimum 16GB total (24GB+ recommended)
- **Storage**:
  - 100GB for PostgreSQL (SSD recommended)
  - 500GB+ for audio recordings
- **Network**: 1Gbps recommended
- **Load Balancer**: MetalLB, HAProxy, or cloud provider LB

### Required Components

- **Nginx Ingress Controller** installed
- **Storage provisioner** (local-path, Ceph, Longhorn, or NFS)
- **Container registry** access (Docker Hub, GHCR, or private registry)
- **MinIO or S3-compatible storage** (can be deployed in cluster)

### External Services

- **OpenRouter API key** (https://openrouter.ai)
- **Domain name** for ingress (or use NodePort/IP)

---

## Step 1: Prepare Docker Images

### Build Images

```bash
cd /home/user/911-AI-Training

# Build all images
./scripts/build-images.sh

# Or build with version tag
./scripts/build-images.sh --version v1.0.0
```

### Push to Registry

```bash
# Login to your registry
docker login docker.io

# Build with registry prefix
./scripts/build-images.sh --registry docker.io/yourusername

# Push images
DOCKER_REGISTRY=docker.io/yourusername ./scripts/push-images.sh
```

### Alternative: Load Images Directly

For on-prem without external registry:

```bash
# Save images to tar files
docker save 911-training/backend:latest | gzip > backend.tar.gz
docker save 911-training/frontend:latest | gzip > frontend.tar.gz

# Copy to Kubernetes nodes and load
scp backend.tar.gz node1:/tmp/
ssh node1 'docker load < /tmp/backend.tar.gz'
```

---

## Step 2: Configure Kubernetes

### Create Namespace

```bash
kubectl apply -f kubernetes/namespace.yaml
```

### Create Secrets

```bash
cd kubernetes/secrets

# OpenRouter API Key
kubectl create secret generic openrouter-secret \
  --from-literal=OPENROUTER_API_KEY=your_api_key_here \
  -n 911-training

# Database credentials
kubectl create secret generic database-secret \
  --from-literal=username=postgres \
  --from-literal=password=your_secure_password \
  --from-literal=url=postgresql://postgres:your_secure_password@postgresql-service:5432/training_db \
  -n 911-training

# Redis credentials (optional if no password)
kubectl create secret generic redis-secret \
  --from-literal=password=your_redis_password \
  -n 911-training

# S3/MinIO credentials
kubectl create secret generic s3-secret \
  --from-literal=access-key=minioadmin \
  --from-literal=secret-key=your_secure_minio_password \
  -n 911-training
```

### Update ConfigMaps

Edit `kubernetes/configmaps/backend-config.yaml`:

```bash
# Update domain and URLs
kubectl edit configmap backend-config -n 911-training
```

Key values to update:
- `FRONTEND_URL`: Your frontend domain
- `S3_ENDPOINT`: MinIO/S3 endpoint
- `COQUI_TTS_URL`: TTS service URL

---

## Step 3: Deploy MinIO (Optional)

If you don't have external S3-compatible storage:

```bash
# Add MinIO Helm repo
helm repo add minio https://charts.min.io/
helm repo update

# Install MinIO
helm install minio minio/minio \
  --namespace 911-training \
  --set replicas=1 \
  --set persistence.size=500Gi \
  --set resources.requests.memory=2Gi \
  --set rootUser=minioadmin \
  --set rootPassword=your_secure_password
```

Wait for MinIO to be ready:
```bash
kubectl wait --for=condition=ready pod -l app=minio -n 911-training --timeout=300s
```

---

## Step 4: Deploy Database

### Method A: In Kubernetes (Recommended for Testing)

```bash
# Apply PostgreSQL StatefulSet
kubectl apply -f kubernetes/statefulsets/postgresql-statefulset.yaml
kubectl apply -f kubernetes/services/postgresql-service.yaml

# Wait for PostgreSQL to be ready
kubectl wait --for=condition=ready pod/postgresql-0 -n 911-training --timeout=300s

# Run database migrations
kubectl exec -it deployment/backend-api -n 911-training -- alembic upgrade head
```

### Method B: External VM (Recommended for Production)

1. **Provision PostgreSQL VM:**
   ```bash
   # On VM
   sudo dnf install postgresql15-server
   sudo postgresql-setup --initdb
   sudo systemctl enable --now postgresql
   ```

2. **Configure PostgreSQL:**
   ```sql
   -- On PostgreSQL VM
   CREATE DATABASE training_db;
   CREATE USER postgres WITH PASSWORD 'your_secure_password';
   GRANT ALL PRIVILEGES ON DATABASE training_db TO postgres;
   ```

3. **Update Kubernetes to use external DB:**
   ```bash
   # Create ExternalName service
   cat <<EOF | kubectl apply -f -
   apiVersion: v1
   kind: Service
   metadata:
     name: postgresql-service
     namespace: 911-training
   spec:
     type: ExternalName
     externalName: postgresql-vm.your-domain.com
   EOF
   ```

---

## Step 5: Deploy Application

### Method A: Using kubectl

```bash
cd kubernetes

# Deploy in order
kubectl apply -f configmaps/
kubectl apply -f deployments/redis-deployment.yaml
kubectl apply -f services/redis-service.yaml
kubectl apply -f deployments/coqui-tts-deployment.yaml
kubectl apply -f services/coqui-tts-service.yaml
kubectl apply -f deployments/backend-deployment.yaml
kubectl apply -f services/backend-service.yaml
kubectl apply -f deployments/frontend-deployment.yaml
kubectl apply -f services/frontend-service.yaml
kubectl apply -f hpa/backend-hpa.yaml
kubectl apply -f ingress/ingress.yaml
```

### Method B: Using Helm (Recommended)

```bash
# Update values.yaml with your configuration
cd kubernetes/helm-chart

# Edit values.yaml
vim values.yaml

# Install with Helm
helm install 911-training . \
  --namespace 911-training \
  --set backend.image.repository=docker.io/yourusername/911-training-backend \
  --set backend.image.tag=v1.0.0 \
  --set frontend.image.repository=docker.io/yourusername/911-training-frontend \
  --set frontend.image.tag=v1.0.0 \
  --set ingress.hosts[0].host=911-training.your-domain.com \
  --set openrouter.apiKey=your_api_key
```

### Method C: Using Deployment Script

```bash
cd kubernetes
./deploy.sh
```

---

## Step 6: Verify Deployment

### Check Pod Status

```bash
kubectl get pods -n 911-training
```

Expected output:
```
NAME                          READY   STATUS    RESTARTS   AGE
backend-api-xxxxx-yyyyy       1/1     Running   0          5m
backend-api-xxxxx-zzzzz       1/1     Running   0          5m
backend-api-xxxxx-aaaaa       1/1     Running   0          5m
coqui-tts-xxxxx-bbbbb         1/1     Running   0          5m
coqui-tts-xxxxx-ccccc         1/1     Running   0          5m
frontend-xxxxx-ddddd          1/1     Running   0          5m
frontend-xxxxx-eeeee          1/1     Running   0          5m
postgresql-0                  1/1     Running   0          5m
redis-xxxxx-fffff             1/1     Running   0          5m
```

### Check Services

```bash
kubectl get svc -n 911-training
```

### Check Ingress

```bash
kubectl get ingress -n 911-training
```

### Test Backend Health

```bash
# Port forward to test locally
kubectl port-forward svc/backend-service 8000:8000 -n 911-training

# Test health endpoint
curl http://localhost:8000/health

# Test readiness
curl http://localhost:8000/ready
```

---

## Step 7: Configure DNS

### Option A: Update DNS Records

Add A record pointing to your Ingress LoadBalancer IP:

```
911-training.your-domain.com  →  <EXTERNAL-IP>
```

Get external IP:
```bash
kubectl get svc -n ingress-nginx
```

### Option B: Use /etc/hosts (Development)

```bash
echo "<INGRESS-IP> 911-training.local" | sudo tee -a /etc/hosts
```

---

## Step 8: Access Application

1. **Open browser**: https://911-training.your-domain.com
2. **Select scenario**: Choose a training scenario
3. **Start call**: Begin training session
4. **Grant microphone permission**: Allow browser access

---

## Post-Deployment Configuration

### Enable TLS/SSL

#### Option A: cert-manager (Automated)

```bash
# Install cert-manager
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
    email: your-email@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF

# Update Ingress to use TLS
kubectl annotate ingress 911-training-ingress \
  cert-manager.io/cluster-issuer=letsencrypt-prod \
  -n 911-training
```

#### Option B: Manual Certificate

```bash
# Create TLS secret with your certificate
kubectl create secret tls 911-training-tls \
  --cert=path/to/cert.pem \
  --key=path/to/key.pem \
  -n 911-training

# Update Ingress to reference secret
kubectl patch ingress 911-training-ingress -n 911-training --type=json \
  -p='[{"op": "add", "path": "/spec/tls", "value": [{"hosts": ["911-training.your-domain.com"], "secretName": "911-training-tls"}]}]'
```

### Configure Monitoring

```bash
# Install Prometheus Operator (if not already installed)
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack -n monitoring --create-namespace

# Create ServiceMonitor for backend
cat <<EOF | kubectl apply -f -
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: backend-metrics
  namespace: 911-training
spec:
  selector:
    matchLabels:
      app: backend-api
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
EOF
```

### Configure Log Aggregation

If using ELK/Loki stack:

```bash
# Install Loki stack
helm repo add grafana https://grafana.github.io/helm-charts
helm install loki grafana/loki-stack \
  --namespace logging \
  --create-namespace \
  --set grafana.enabled=true
```

### Set Up Backups

#### Database Backups

```bash
# Create CronJob for pg_dump
cat <<EOF | kubectl apply -f -
apiVersion: batch/v1
kind: CronJob
metadata:
  name: postgres-backup
  namespace: 911-training
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: postgres:15-alpine
            command:
            - /bin/sh
            - -c
            - |
              pg_dump \$DATABASE_URL | gzip | \
              aws s3 cp - s3://backups/postgres/backup-\$(date +%Y%m%d).sql.gz
            env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: database-secret
                  key: url
            - name: AWS_ACCESS_KEY_ID
              valueFrom:
                secretKeyRef:
                  name: s3-secret
                  key: access-key
            - name: AWS_SECRET_ACCESS_KEY
              valueFrom:
                secretKeyRef:
                  name: s3-secret
                  key: secret-key
          restartPolicy: OnFailure
EOF
```

---

## Scaling

### Manual Scaling

```bash
# Scale backend
kubectl scale deployment backend-api --replicas=5 -n 911-training

# Scale frontend
kubectl scale deployment frontend --replicas=3 -n 911-training

# Scale Coqui TTS
kubectl scale deployment coqui-tts --replicas=4 -n 911-training
```

### HPA Configuration

HPA is already configured for backend. To adjust:

```bash
kubectl edit hpa backend-hpa -n 911-training
```

---

## Troubleshooting

### Pods Not Starting

```bash
# Check pod events
kubectl describe pod <pod-name> -n 911-training

# Check logs
kubectl logs <pod-name> -n 911-training

# Common issues:
# 1. Image pull errors - check registry credentials
# 2. CrashLoopBackOff - check application logs
# 3. Pending - check resource availability
```

### Database Connection Issues

```bash
# Test database connectivity
kubectl exec -it deployment/backend-api -n 911-training -- \
  python -c "import asyncpg; import asyncio; asyncio.run(asyncpg.connect('$DATABASE_URL'))"

# Check database secret
kubectl get secret database-secret -n 911-training -o yaml
```

### WebSocket Connection Failures

```bash
# Check Ingress annotations
kubectl describe ingress 911-training-ingress -n 911-training

# Ensure these annotations are present:
# nginx.ingress.kubernetes.io/websocket-services: backend-service
# nginx.ingress.kubernetes.io/proxy-read-timeout: "3600"
```

### High Memory Usage

```bash
# Check pod memory
kubectl top pods -n 911-training

# Adjust memory limits
kubectl edit deployment backend-api -n 911-training
```

---

## Rollback

### Helm Rollback

```bash
# List releases
helm history 911-training -n 911-training

# Rollback to previous version
helm rollback 911-training -n 911-training

# Rollback to specific revision
helm rollback 911-training 2 -n 911-training
```

### kubectl Rollback

```bash
# Rollback deployment
kubectl rollout undo deployment/backend-api -n 911-training

# Rollback to specific revision
kubectl rollout undo deployment/backend-api --to-revision=2 -n 911-training
```

---

## Upgrade

### Application Upgrade

```bash
# Build new images with version tag
./scripts/build-images.sh --version v1.1.0

# Push to registry
DOCKER_REGISTRY=docker.io/yourusername ./scripts/push-images.sh --version v1.1.0

# Upgrade with Helm
helm upgrade 911-training ./kubernetes/helm-chart \
  --namespace 911-training \
  --set backend.image.tag=v1.1.0 \
  --set frontend.image.tag=v1.1.0 \
  --reuse-values

# Or with kubectl
kubectl set image deployment/backend-api \
  fastapi=docker.io/yourusername/911-training-backend:v1.1.0 \
  -n 911-training

kubectl set image deployment/frontend \
  nginx=docker.io/yourusername/911-training-frontend:v1.1.0 \
  -n 911-training
```

### Database Migration

```bash
# Run migrations after backend upgrade
kubectl exec -it deployment/backend-api -n 911-training -- \
  alembic upgrade head
```

---

## Uninstall

### Helm Uninstall

```bash
helm uninstall 911-training -n 911-training
kubectl delete namespace 911-training
```

### kubectl Uninstall

```bash
kubectl delete -f kubernetes/ingress/
kubectl delete -f kubernetes/hpa/
kubectl delete -f kubernetes/deployments/
kubectl delete -f kubernetes/services/
kubectl delete -f kubernetes/statefulsets/
kubectl delete -f kubernetes/configmaps/
kubectl delete secret --all -n 911-training
kubectl delete pvc --all -n 911-training
kubectl delete namespace 911-training
```

---

## Production Checklist

Before going to production:

- [ ] TLS/SSL certificates configured
- [ ] Database backups scheduled
- [ ] Monitoring and alerting configured
- [ ] Log aggregation set up
- [ ] Resource limits tuned for expected load
- [ ] HPA configured and tested
- [ ] Persistent volumes backed up
- [ ] Disaster recovery plan documented
- [ ] Security audit completed
- [ ] Load testing performed
- [ ] Documentation updated
- [ ] Team trained on operations

---

## Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Helm Documentation](https://helm.sh/docs/)
- [Nginx Ingress Controller](https://kubernetes.github.io/ingress-nginx/)
- [cert-manager](https://cert-manager.io/docs/)
