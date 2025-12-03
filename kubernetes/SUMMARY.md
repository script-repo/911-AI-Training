# Kubernetes Deployment - Complete Summary

## Overview

Complete Kubernetes manifests and Helm chart have been created for deploying the 911 Operator Training Simulator to an on-premises Kubernetes cluster. This includes all necessary configurations for a production-ready deployment with high availability, autoscaling, and proper security practices.

## What Was Created

### Total Files: 46

### Directory Structure

```
kubernetes/
├── namespace.yaml                              # Namespace definition
├── README.md                                   # Complete documentation
├── DEPLOYMENT_GUIDE.md                         # Step-by-step deployment guide
├── KUBECTL_CHEATSHEET.md                       # Quick reference for kubectl commands
├── SUMMARY.md                                  # This file
├── deploy.sh                                   # Automated deployment script
│
├── configmaps/                                 # Configuration files (2 files)
│   ├── backend-config.yaml                     # Backend environment variables
│   └── frontend-config.yaml                    # Frontend environment variables
│
├── secrets/                                    # Secret templates (5 files)
│   ├── README.md                               # Secret creation instructions
│   ├── openrouter-secret.yaml.example          # OpenRouter API key template
│   ├── database-secret.yaml.example            # Database credentials template
│   ├── redis-secret.yaml.example               # Redis password template
│   └── s3-secret.yaml.example                  # S3/MinIO credentials template
│
├── deployments/                                # Application deployments (4 files)
│   ├── frontend-deployment.yaml                # React frontend (2 replicas)
│   ├── backend-deployment.yaml                 # FastAPI backend (3 replicas)
│   ├── coqui-tts-deployment.yaml              # TTS service (2 replicas)
│   └── redis-deployment.yaml                   # Redis cache (1 replica)
│
├── statefulsets/                               # Stateful applications (1 file)
│   └── postgresql-statefulset.yaml             # PostgreSQL database with PVC
│
├── services/                                   # Kubernetes services (5 files)
│   ├── frontend-service.yaml                   # Frontend ClusterIP service
│   ├── backend-service.yaml                    # Backend ClusterIP with sticky sessions
│   ├── coqui-tts-service.yaml                 # TTS ClusterIP service
│   ├── postgresql-service.yaml                 # PostgreSQL headless service
│   └── redis-service.yaml                      # Redis ClusterIP service
│
├── ingress/                                    # Ingress configuration (1 file)
│   └── ingress.yaml                            # Nginx Ingress with WebSocket support
│
├── pvcs/                                       # Persistent Volume Claims (1 file)
│   └── postgres-pvc.yaml                       # PostgreSQL storage (100GB)
│
├── hpa/                                        # Horizontal Pod Autoscalers (1 file)
│   └── backend-hpa.yaml                        # Backend autoscaling (3-10 replicas)
│
└── helm-chart/                                 # Complete Helm chart (26 files)
    ├── Chart.yaml                              # Chart metadata
    ├── values.yaml                             # Default configuration values
    ├── README.md                               # Helm chart documentation
    ├── .helmignore                             # Files to ignore in chart
    └── templates/                              # Templated manifests
        ├── NOTES.txt                           # Post-install instructions
        ├── _helpers.tpl                        # Template helpers
        ├── namespace.yaml                      # Namespace template
        ├── configmap-backend.yaml              # Backend ConfigMap template
        ├── configmap-frontend.yaml             # Frontend ConfigMap template
        ├── deployment-frontend.yaml            # Frontend deployment template
        ├── deployment-backend.yaml             # Backend deployment template
        ├── deployment-coqui-tts.yaml          # TTS deployment template
        ├── deployment-redis.yaml               # Redis deployment template
        ├── statefulset-postgresql.yaml         # PostgreSQL StatefulSet template
        ├── service-frontend.yaml               # Frontend service template
        ├── service-backend.yaml                # Backend service template
        ├── service-coqui-tts.yaml             # TTS service template
        ├── service-postgresql.yaml             # PostgreSQL service template
        ├── service-redis.yaml                  # Redis service template
        ├── ingress.yaml                        # Ingress template
        └── hpa-backend.yaml                    # HPA template
```

## Components Overview

### 1. Frontend (React + Nginx)
- **Replicas**: 2
- **Resources**: 100m-250m CPU, 128Mi-256Mi RAM
- **Features**:
  - Liveness and readiness probes
  - Pod anti-affinity for HA
  - Rolling update strategy

### 2. Backend (FastAPI)
- **Replicas**: 3 (with HPA: 3-10)
- **Resources**: 500m-2000m CPU, 1Gi-3Gi RAM
- **Features**:
  - Health check endpoints (/health, /ready)
  - Horizontal Pod Autoscaler
  - WebSocket support
  - Environment variables from ConfigMaps and Secrets
  - Pod anti-affinity for HA

### 3. Coqui TTS (Text-to-Speech)
- **Replicas**: 2
- **Resources**: 1000m-2000m CPU, 2Gi-4Gi RAM
- **Features**:
  - Model caching via emptyDir volume (10GB)
  - Pre-configured with ljspeech models
  - Pod anti-affinity for HA

### 4. PostgreSQL (Database)
- **Type**: StatefulSet
- **Replicas**: 1
- **Resources**: 1000m-4000m CPU, 2Gi-8Gi RAM
- **Storage**: 100GB PVC (configurable)
- **Features**:
  - Persistent storage
  - Health checks
  - Performance tuning variables

### 5. Redis (Cache)
- **Replicas**: 1
- **Resources**: 250m-1000m CPU, 512Mi-2Gi RAM
- **Features**:
  - AOF persistence enabled
  - Health checks
  - Optional emptyDir or PVC storage

### 6. Ingress (Nginx)
- **Features**:
  - WebSocket support
  - Sticky sessions
  - Long-lived connection timeouts
  - Large body size support (100MB)
  - TLS/SSL ready
  - Path-based routing

### 7. Horizontal Pod Autoscaler (HPA)
- **Target**: Backend deployment
- **Min/Max**: 3-10 replicas
- **Metrics**: CPU 70%, Memory 80%
- **Features**:
  - Conservative scale-down policy
  - Aggressive scale-up policy
  - 5-minute stabilization window

## Key Features

### High Availability
- Multiple replicas for stateless services
- Pod anti-affinity rules
- Rolling update strategy with zero downtime
- Health checks for all services

### Security
- Secrets for sensitive data
- Example files with placeholders (not committed)
- Support for external secrets management
- Instructions for Sealed Secrets and External Secrets Operator

### Scalability
- Horizontal Pod Autoscaler for backend
- Configurable replica counts
- Resource requests and limits
- Proper resource allocation

### Observability
- Health check endpoints
- Readiness probes
- Liveness probes
- Labels for monitoring

### Production Ready
- Resource limits
- Persistent storage
- Proper service discovery
- Load balancing
- WebSocket support
- SSL/TLS ready

## Deployment Options

### Option 1: Automated Script (Quickest)
```bash
cd kubernetes
./deploy.sh
```
The script handles the entire deployment process interactively.

### Option 2: Manual kubectl (Most Control)
```bash
# Step-by-step deployment using raw manifests
# See DEPLOYMENT_GUIDE.md for detailed instructions
kubectl apply -f namespace.yaml
kubectl create secret generic openrouter-secret --from-literal=OPENROUTER_API_KEY=xxx -n 911-training
kubectl apply -f configmaps/
kubectl apply -f statefulsets/
kubectl apply -f deployments/
kubectl apply -f services/
kubectl apply -f ingress/
kubectl apply -f hpa/
```

### Option 3: Helm Chart (Production Recommended)
```bash
# Create secrets first
kubectl create namespace 911-training
kubectl create secret generic openrouter-secret --from-literal=OPENROUTER_API_KEY=xxx -n 911-training
kubectl create secret generic database-secret --from-literal=POSTGRES_PASSWORD=xxx -n 911-training
kubectl create secret generic s3-secret --from-literal=S3_ACCESS_KEY=xxx --from-literal=S3_SECRET_KEY=xxx -n 911-training

# Install Helm chart
helm install 911-training ./helm-chart \
  --set frontend.image.repository=your-registry/frontend \
  --set backend.image.repository=your-registry/backend \
  --set ingress.hosts[0].host=your-domain.com
```

## Configuration Required

Before deployment, you must configure:

### 1. Container Images
Update image references in:
- `deployments/frontend-deployment.yaml`
- `deployments/backend-deployment.yaml`
- `helm-chart/values.yaml`

### 2. Domain Name
Update domain in:
- `configmaps/frontend-config.yaml`
- `ingress/ingress.yaml`
- `helm-chart/values.yaml`

### 3. Secrets
Create the following secrets:
- `openrouter-secret`: OpenRouter API key
- `database-secret`: PostgreSQL credentials
- `s3-secret`: S3/MinIO credentials
- `redis-secret`: (Optional) Redis password

### 4. Storage
Configure storage class if needed:
- `statefulsets/postgresql-statefulset.yaml`
- `helm-chart/values.yaml`

## Resource Requirements

### Minimum Cluster Requirements
- **Nodes**: 3 worker nodes
- **Total CPU**: 8 cores
- **Total RAM**: 16 GB
- **Storage**: 200 GB

### Recommended Production Setup
- **Nodes**: 5+ worker nodes
- **Total CPU**: 16+ cores
- **Total RAM**: 32+ GB
- **Storage**: 500+ GB (SSD for database)

### Per-Component Resources

| Component | Replicas | CPU Request | CPU Limit | Memory Request | Memory Limit |
|-----------|----------|-------------|-----------|----------------|--------------|
| Frontend  | 2        | 100m        | 250m      | 128Mi          | 256Mi        |
| Backend   | 3-10     | 500m        | 2000m     | 1Gi            | 3Gi          |
| Coqui TTS | 2        | 1000m       | 2000m     | 2Gi            | 4Gi          |
| PostgreSQL| 1        | 1000m       | 4000m     | 2Gi            | 8Gi          |
| Redis     | 1        | 250m        | 1000m     | 512Mi          | 2Gi          |

## Documentation

### Comprehensive Guides
1. **README.md** - Complete documentation with all deployment methods
2. **DEPLOYMENT_GUIDE.md** - Detailed step-by-step deployment instructions
3. **KUBECTL_CHEATSHEET.md** - Quick reference for common operations
4. **helm-chart/README.md** - Helm-specific documentation
5. **secrets/README.md** - Secret management instructions

### What Each Guide Covers

#### README.md
- Directory structure overview
- Both deployment options (kubectl and Helm)
- Accessing the application
- Scaling instructions
- Monitoring and maintenance
- Troubleshooting
- Production best practices

#### DEPLOYMENT_GUIDE.md
- Prerequisites checklist
- Pre-deployment configuration
- Three deployment methods (automated, manual, Helm)
- Post-deployment configuration
- Verification steps
- Common issues and solutions

#### KUBECTL_CHEATSHEET.md
- Quick reference for all kubectl operations
- Pod, deployment, service operations
- ConfigMap and secret management
- Monitoring and troubleshooting commands
- Database and Redis operations
- Useful aliases

## Quick Start Summary

1. **Build images** and push to registry
2. **Update image references** in manifests
3. **Create secrets** with actual credentials
4. **Update domain name** in ingress configuration
5. **Deploy** using one of three methods
6. **Verify** deployment status
7. **Access** via ingress or port-forward

## Production Checklist

Before going to production:

- [ ] Images built and pushed to registry
- [ ] All secrets created with strong passwords
- [ ] Domain name configured with DNS
- [ ] TLS/SSL certificates configured
- [ ] Resource limits adjusted based on testing
- [ ] Storage class configured for production use
- [ ] Monitoring and alerting set up
- [ ] Backup strategy implemented
- [ ] Disaster recovery plan documented
- [ ] Security scan completed on images
- [ ] Network policies configured
- [ ] RBAC configured
- [ ] Load testing completed
- [ ] Documentation reviewed and updated

## Support and Maintenance

### Regular Tasks
- Monitor resource usage and adjust limits
- Review logs for errors
- Check HPA behavior under load
- Backup database regularly
- Update images with security patches
- Rotate secrets periodically

### Monitoring
```bash
# Check pod status
kubectl get pods -n 911-training

# Check resource usage
kubectl top pods -n 911-training
kubectl top nodes

# View logs
kubectl logs -n 911-training -l component=backend -f

# Check HPA
kubectl get hpa -n 911-training
```

### Common Operations
```bash
# Scale manually
kubectl scale deployment backend --replicas=5 -n 911-training

# Update image
kubectl set image deployment/backend backend=registry/backend:v2 -n 911-training

# Restart deployment
kubectl rollout restart deployment/backend -n 911-training

# Check rollout status
kubectl rollout status deployment/backend -n 911-training
```

## Next Steps

After successful deployment:

1. **Set up monitoring** - Install Prometheus and Grafana
2. **Configure logging** - Set up centralized logging (ELK stack or Loki)
3. **Enable backups** - Automated database backups
4. **Security hardening** - Network policies, Pod Security Policies
5. **Load testing** - Test with realistic traffic
6. **Documentation** - Document your specific configuration
7. **Alerting** - Set up alerts for critical issues
8. **Disaster recovery** - Test backup and restore procedures

## Troubleshooting Quick Links

- Pods not starting? → Check `kubectl describe pod <name>`
- Service not accessible? → Check `kubectl get endpoints`
- Database connection failed? → Check secrets and service DNS
- Ingress not working? → Check ingress controller logs
- High memory usage? → Review resource limits and usage

## Additional Resources

- Kubernetes Documentation: https://kubernetes.io/docs/
- Helm Documentation: https://helm.sh/docs/
- Nginx Ingress: https://kubernetes.github.io/ingress-nginx/
- cert-manager: https://cert-manager.io/

## Notes

- All sensitive data is in example files with `.example` suffix
- Never commit actual secrets to version control
- Update image tags for production deployments
- Adjust resource limits based on your workload
- Test thoroughly in a staging environment first

## Success Criteria

Deployment is successful when:
- [ ] All pods show status `Running`
- [ ] All services have valid endpoints
- [ ] Health checks return `200 OK`
- [ ] Frontend is accessible via browser
- [ ] Backend API responds at `/api/health`
- [ ] WebSocket connections work
- [ ] Database is accessible and initialized
- [ ] HPA shows current metrics
- [ ] Ingress has an IP/hostname assigned

---

**Created**: December 2025
**Version**: 1.0.0
**Kubernetes Version**: 1.19+
**Helm Version**: 3.0+
