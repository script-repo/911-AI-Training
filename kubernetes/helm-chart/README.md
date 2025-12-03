# 911 Operator Training Simulator - Helm Chart

This Helm chart deploys the 911 Operator Training Simulator to a Kubernetes cluster.

## Prerequisites

- Kubernetes 1.19+
- Helm 3.0+
- PersistentVolume provisioner support in the underlying infrastructure (for PostgreSQL)
- Nginx Ingress Controller (if using Ingress)

## Installing the Chart

### 1. Create Secrets

First, create the required secrets:

```bash
# Create namespace
kubectl create namespace 911-training

# OpenRouter API Key
kubectl create secret generic openrouter-secret \
  --from-literal=OPENROUTER_API_KEY=your_openrouter_api_key_here \
  --namespace=911-training

# Database credentials
kubectl create secret generic database-secret \
  --from-literal=POSTGRES_USER=postgres \
  --from-literal=POSTGRES_PASSWORD=your_secure_password \
  --from-literal=DATABASE_URL=postgresql://postgres:your_secure_password@postgresql-service:5432/training_db \
  --namespace=911-training

# S3/MinIO credentials
kubectl create secret generic s3-secret \
  --from-literal=S3_ACCESS_KEY=your_s3_access_key \
  --from-literal=S3_SECRET_KEY=your_s3_secret_key \
  --namespace=911-training
```

### 2. Install the Chart

Install the chart with the release name `911-training`:

```bash
# Install with default values
helm install 911-training ./helm-chart

# Install with custom values
helm install 911-training ./helm-chart -f custom-values.yaml

# Install with overrides
helm install 911-training ./helm-chart \
  --set frontend.image.repository=your-registry/frontend \
  --set backend.image.repository=your-registry/backend \
  --set ingress.hosts[0].host=your-domain.com
```

### 3. Verify Installation

```bash
# Check release status
helm status 911-training -n 911-training

# Check pods
kubectl get pods -n 911-training

# Check services
kubectl get services -n 911-training

# Check ingress
kubectl get ingress -n 911-training
```

## Configuration

The following table lists the configurable parameters and their default values:

### Global Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `global.namespace` | Kubernetes namespace | `911-training` |

### Frontend Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `frontend.enabled` | Enable frontend deployment | `true` |
| `frontend.replicaCount` | Number of frontend replicas | `2` |
| `frontend.image.repository` | Frontend image repository | `your-registry/911-training-frontend` |
| `frontend.image.tag` | Frontend image tag | `latest` |
| `frontend.resources.requests.cpu` | CPU request | `100m` |
| `frontend.resources.requests.memory` | Memory request | `128Mi` |
| `frontend.resources.limits.cpu` | CPU limit | `250m` |
| `frontend.resources.limits.memory` | Memory limit | `256Mi` |

### Backend Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `backend.enabled` | Enable backend deployment | `true` |
| `backend.replicaCount` | Number of backend replicas | `3` |
| `backend.image.repository` | Backend image repository | `your-registry/911-training-backend` |
| `backend.image.tag` | Backend image tag | `latest` |
| `backend.resources.requests.cpu` | CPU request | `500m` |
| `backend.resources.requests.memory` | Memory request | `1Gi` |
| `backend.resources.limits.cpu` | CPU limit | `2000m` |
| `backend.resources.limits.memory` | Memory limit | `3Gi` |
| `backend.autoscaling.enabled` | Enable HPA | `true` |
| `backend.autoscaling.minReplicas` | Minimum replicas | `3` |
| `backend.autoscaling.maxReplicas` | Maximum replicas | `10` |

### PostgreSQL Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `postgresql.enabled` | Enable PostgreSQL | `true` |
| `postgresql.persistence.enabled` | Enable persistence | `true` |
| `postgresql.persistence.size` | PVC size | `100Gi` |
| `postgresql.resources.requests.cpu` | CPU request | `1000m` |
| `postgresql.resources.requests.memory` | Memory request | `2Gi` |

### Ingress Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `ingress.enabled` | Enable Ingress | `true` |
| `ingress.className` | Ingress class name | `nginx` |
| `ingress.hosts[0].host` | Hostname | `your-domain.com` |
| `ingress.tls` | TLS configuration | `[]` |

## Upgrading the Chart

```bash
# Upgrade with default values
helm upgrade 911-training ./helm-chart

# Upgrade with custom values
helm upgrade 911-training ./helm-chart -f custom-values.yaml

# Upgrade with overrides
helm upgrade 911-training ./helm-chart \
  --set backend.image.tag=v2.0.0
```

## Uninstalling the Chart

```bash
# Uninstall the release
helm uninstall 911-training -n 911-training

# Optionally, delete the namespace and PVCs
kubectl delete namespace 911-training
```

## Production Considerations

### 1. Image Registry

Update the image repositories to point to your container registry:

```yaml
frontend:
  image:
    repository: your-registry.com/911-training-frontend
    tag: v1.0.0

backend:
  image:
    repository: your-registry.com/911-training-backend
    tag: v1.0.0
```

### 2. Secrets Management

For production, use a secrets management solution:

- **Sealed Secrets**: Encrypt secrets for GitOps
- **External Secrets Operator**: Sync from AWS Secrets Manager, Vault, etc.
- **HashiCorp Vault**: Inject secrets directly into pods

### 3. TLS/SSL

Enable TLS for secure communication:

```yaml
ingress:
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
  tls:
  - secretName: 911-training-tls
    hosts:
    - your-domain.com
```

### 4. Resource Limits

Adjust resource limits based on your workload:

```bash
# Monitor resource usage
kubectl top pods -n 911-training
kubectl top nodes

# Adjust in values.yaml
backend:
  resources:
    requests:
      cpu: 1000m
      memory: 2Gi
    limits:
      cpu: 4000m
      memory: 6Gi
```

### 5. Persistence

Configure storage classes for optimal performance:

```yaml
postgresql:
  persistence:
    storageClass: fast-ssd
    size: 500Gi
```

### 6. High Availability

- Use multiple replicas for stateless components
- Configure pod anti-affinity to spread across nodes
- Set up database backups and disaster recovery

### 7. Monitoring

Add monitoring and observability:

```yaml
# Add Prometheus annotations
backend:
  podAnnotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "8000"
    prometheus.io/path: "/metrics"
```

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl describe pod <pod-name> -n 911-training

# Check logs
kubectl logs <pod-name> -n 911-training

# Check events
kubectl get events -n 911-training --sort-by='.lastTimestamp'
```

### Database Connection Issues

```bash
# Check database service
kubectl get svc postgresql-service -n 911-training

# Test database connection
kubectl run -it --rm debug --image=postgres:15-alpine --restart=Never -n 911-training -- psql -h postgresql-service -U postgres -d training_db
```

### Ingress Not Working

```bash
# Check ingress status
kubectl describe ingress 911-training-ingress -n 911-training

# Check ingress controller logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller
```

## Support

For issues and questions:
- GitHub Issues: https://github.com/yourusername/911-AI-Training/issues
- Documentation: https://github.com/yourusername/911-AI-Training/docs
