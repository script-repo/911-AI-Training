# kubectl Cheatsheet for 911 Training Simulator

Quick reference for common kubectl commands for managing the 911 Operator Training Simulator.

## Namespace Operations

```bash
# Switch to 911-training namespace
kubectl config set-context --current --namespace=911-training

# List all resources in namespace
kubectl get all -n 911-training

# Delete namespace (WARNING: deletes everything)
kubectl delete namespace 911-training
```

## Pod Operations

```bash
# List all pods
kubectl get pods -n 911-training

# List pods with more details
kubectl get pods -n 911-training -o wide

# Watch pods in real-time
kubectl get pods -n 911-training -w

# Describe a pod
kubectl describe pod <pod-name> -n 911-training

# Get pod logs
kubectl logs <pod-name> -n 911-training

# Follow logs in real-time
kubectl logs -f <pod-name> -n 911-training

# Get logs from previous pod instance
kubectl logs <pod-name> -n 911-training --previous

# Get logs from specific container
kubectl logs <pod-name> -c <container-name> -n 911-training

# Get logs from all pods with a label
kubectl logs -l component=backend -n 911-training --all-containers=true

# Execute command in pod
kubectl exec -it <pod-name> -n 911-training -- /bin/sh

# Copy files from/to pod
kubectl cp <pod-name>:/path/to/file ./local-file -n 911-training
kubectl cp ./local-file <pod-name>:/path/to/file -n 911-training
```

## Deployment Operations

```bash
# List deployments
kubectl get deployments -n 911-training

# Describe deployment
kubectl describe deployment backend -n 911-training

# Scale deployment
kubectl scale deployment backend --replicas=5 -n 911-training

# Update image
kubectl set image deployment/backend backend=your-registry/backend:v2.0.0 -n 911-training

# Rollout status
kubectl rollout status deployment/backend -n 911-training

# Rollout history
kubectl rollout history deployment/backend -n 911-training

# Rollback to previous version
kubectl rollout undo deployment/backend -n 911-training

# Rollback to specific revision
kubectl rollout undo deployment/backend --to-revision=2 -n 911-training

# Restart deployment
kubectl rollout restart deployment/backend -n 911-training

# Pause rollout
kubectl rollout pause deployment/backend -n 911-training

# Resume rollout
kubectl rollout resume deployment/backend -n 911-training
```

## Service Operations

```bash
# List services
kubectl get services -n 911-training

# Describe service
kubectl describe service backend-service -n 911-training

# Get service endpoints
kubectl get endpoints backend-service -n 911-training

# Port forward to service
kubectl port-forward service/backend-service 8000:8000 -n 911-training

# Port forward to pod
kubectl port-forward <pod-name> 8000:8000 -n 911-training
```

## ConfigMap and Secret Operations

```bash
# List ConfigMaps
kubectl get configmaps -n 911-training

# Describe ConfigMap
kubectl describe configmap backend-config -n 911-training

# Edit ConfigMap
kubectl edit configmap backend-config -n 911-training

# List Secrets
kubectl get secrets -n 911-training

# Describe Secret
kubectl describe secret openrouter-secret -n 911-training

# Get Secret value (base64 encoded)
kubectl get secret openrouter-secret -n 911-training -o yaml

# Decode Secret value
kubectl get secret openrouter-secret -n 911-training -o jsonpath='{.data.OPENROUTER_API_KEY}' | base64 -d

# Create Secret
kubectl create secret generic my-secret \
  --from-literal=key1=value1 \
  --from-literal=key2=value2 \
  -n 911-training

# Create Secret from file
kubectl create secret generic my-secret \
  --from-file=ssh-privatekey=~/.ssh/id_rsa \
  -n 911-training

# Delete Secret
kubectl delete secret my-secret -n 911-training
```

## StatefulSet Operations

```bash
# List StatefulSets
kubectl get statefulsets -n 911-training

# Describe StatefulSet
kubectl describe statefulset postgresql -n 911-training

# Scale StatefulSet
kubectl scale statefulset postgresql --replicas=3 -n 911-training

# Update StatefulSet
kubectl set image statefulset/postgresql postgresql=postgres:16-alpine -n 911-training

# Delete StatefulSet (keeps PVCs)
kubectl delete statefulset postgresql -n 911-training

# Delete StatefulSet and PVCs
kubectl delete statefulset postgresql -n 911-training --cascade=true
```

## PersistentVolume and PVC Operations

```bash
# List PVCs
kubectl get pvc -n 911-training

# Describe PVC
kubectl describe pvc postgresql-data-postgresql-0 -n 911-training

# List PVs
kubectl get pv

# Describe PV
kubectl describe pv <pv-name>

# Delete PVC
kubectl delete pvc postgresql-data-postgresql-0 -n 911-training
```

## Ingress Operations

```bash
# List Ingress
kubectl get ingress -n 911-training

# Describe Ingress
kubectl describe ingress 911-training-ingress -n 911-training

# Get Ingress YAML
kubectl get ingress 911-training-ingress -n 911-training -o yaml

# Edit Ingress
kubectl edit ingress 911-training-ingress -n 911-training
```

## HorizontalPodAutoscaler Operations

```bash
# List HPA
kubectl get hpa -n 911-training

# Describe HPA
kubectl describe hpa backend-hpa -n 911-training

# Watch HPA in real-time
kubectl get hpa -n 911-training -w

# Edit HPA
kubectl edit hpa backend-hpa -n 911-training

# Delete HPA
kubectl delete hpa backend-hpa -n 911-training
```

## Resource Monitoring

```bash
# Get resource usage for pods
kubectl top pods -n 911-training

# Get resource usage for nodes
kubectl top nodes

# Get resource usage for specific pod
kubectl top pod <pod-name> -n 911-training

# Get resource usage sorted by CPU
kubectl top pods -n 911-training --sort-by=cpu

# Get resource usage sorted by memory
kubectl top pods -n 911-training --sort-by=memory
```

## Events

```bash
# List all events
kubectl get events -n 911-training

# List events sorted by timestamp
kubectl get events -n 911-training --sort-by='.lastTimestamp'

# Watch events in real-time
kubectl get events -n 911-training -w

# Get events for specific resource
kubectl get events --field-selector involvedObject.name=<pod-name> -n 911-training
```

## Labels and Selectors

```bash
# Show labels
kubectl get pods -n 911-training --show-labels

# Filter by label
kubectl get pods -l component=backend -n 911-training

# Filter by multiple labels
kubectl get pods -l component=backend,app=911-training-simulator -n 911-training

# Add label to pod
kubectl label pod <pod-name> environment=production -n 911-training

# Remove label from pod
kubectl label pod <pod-name> environment- -n 911-training

# Update existing label
kubectl label pod <pod-name> environment=staging --overwrite -n 911-training
```

## Troubleshooting

```bash
# Check cluster info
kubectl cluster-info

# Check component status
kubectl get componentstatuses

# List all resources
kubectl api-resources

# Explain resource
kubectl explain pod
kubectl explain deployment.spec

# Validate YAML without applying
kubectl apply -f deployment.yaml --dry-run=client

# Server-side dry run
kubectl apply -f deployment.yaml --dry-run=server

# Diff changes before applying
kubectl diff -f deployment.yaml

# Debug pod that won't start
kubectl run -it --rm debug --image=busybox --restart=Never -n 911-training -- sh

# Test DNS resolution
kubectl run -it --rm debug --image=busybox --restart=Never -n 911-training -- nslookup backend-service

# Test service connectivity
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -n 911-training -- curl http://backend-service:8000/health

# Test PostgreSQL connection
kubectl run -it --rm psql-test --image=postgres:15-alpine --restart=Never -n 911-training -- psql -h postgresql-service -U postgres -d training_db
```

## Database Operations

```bash
# Access PostgreSQL shell
kubectl exec -it postgresql-0 -n 911-training -- psql -U postgres -d training_db

# Run SQL query
kubectl exec -it postgresql-0 -n 911-training -- psql -U postgres -d training_db -c "SELECT * FROM users;"

# Backup database
kubectl exec -n 911-training postgresql-0 -- pg_dump -U postgres training_db > backup-$(date +%Y%m%d).sql

# Restore database
cat backup.sql | kubectl exec -i -n 911-training postgresql-0 -- psql -U postgres training_db

# Check database size
kubectl exec -it postgresql-0 -n 911-training -- psql -U postgres -d training_db -c "SELECT pg_size_pretty(pg_database_size('training_db'));"
```

## Redis Operations

```bash
# Access Redis CLI
kubectl exec -it $(kubectl get pod -n 911-training -l component=redis -o jsonpath='{.items[0].metadata.name}') -n 911-training -- redis-cli

# Get Redis info
kubectl exec -n 911-training $(kubectl get pod -n 911-training -l component=redis -o jsonpath='{.items[0].metadata.name}') -- redis-cli INFO

# Check Redis memory usage
kubectl exec -n 911-training $(kubectl get pod -n 911-training -l component=redis -o jsonpath='{.items[0].metadata.name}') -- redis-cli INFO memory

# Flush Redis (WARNING: deletes all data)
kubectl exec -n 911-training $(kubectl get pod -n 911-training -l component=redis -o jsonpath='{.items[0].metadata.name}') -- redis-cli FLUSHALL
```

## Batch Operations

```bash
# Delete all pods with label
kubectl delete pods -l component=backend -n 911-training

# Delete all resources from file
kubectl delete -f deployments/ -n 911-training

# Apply all files in directory
kubectl apply -f deployments/ -n 911-training

# Apply all YAML files recursively
kubectl apply -R -f kubernetes/ -n 911-training

# Get all pods and format output
kubectl get pods -n 911-training -o custom-columns=NAME:.metadata.name,STATUS:.status.phase,NODE:.spec.nodeName

# Get all container images
kubectl get pods -n 911-training -o jsonpath='{range .items[*]}{.spec.containers[*].image}{"\n"}{end}'
```

## JSON/YAML Operations

```bash
# Get resource in JSON
kubectl get pod <pod-name> -n 911-training -o json

# Get resource in YAML
kubectl get pod <pod-name> -n 911-training -o yaml

# Get specific field with jsonpath
kubectl get pod <pod-name> -n 911-training -o jsonpath='{.status.podIP}'

# Get multiple fields
kubectl get pods -n 911-training -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.podIP}{"\n"}{end}'

# Output to file
kubectl get deployment backend -n 911-training -o yaml > backend-deployment.yaml
```

## Helm Operations (if using Helm)

```bash
# List releases
helm list -n 911-training

# Get release status
helm status 911-training -n 911-training

# Get release values
helm get values 911-training -n 911-training

# Get all release info
helm get all 911-training -n 911-training

# Upgrade release
helm upgrade 911-training ./helm-chart -f values.yaml

# Rollback release
helm rollback 911-training -n 911-training

# Rollback to specific revision
helm rollback 911-training 1 -n 911-training

# Uninstall release
helm uninstall 911-training -n 911-training

# History
helm history 911-training -n 911-training
```

## Context and Configuration

```bash
# List contexts
kubectl config get-contexts

# Switch context
kubectl config use-context <context-name>

# Set default namespace for current context
kubectl config set-context --current --namespace=911-training

# View current config
kubectl config view

# Get cluster info
kubectl cluster-info
```

## Quick Fixes

```bash
# Restart all backend pods
kubectl rollout restart deployment/backend -n 911-training

# Force delete stuck pod
kubectl delete pod <pod-name> -n 911-training --grace-period=0 --force

# Clear failed pods
kubectl delete pods --field-selector status.phase=Failed -n 911-training

# Get pod on specific node
kubectl get pods -n 911-training --field-selector spec.nodeName=<node-name>

# Cordon node (prevent new pods)
kubectl cordon <node-name>

# Uncordon node
kubectl uncordon <node-name>

# Drain node (evict all pods)
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data
```

## Useful Aliases

Add these to your `~/.bashrc` or `~/.zshrc`:

```bash
alias k='kubectl'
alias kn='kubectl config set-context --current --namespace'
alias kg='kubectl get'
alias kd='kubectl describe'
alias kdel='kubectl delete'
alias kl='kubectl logs'
alias kex='kubectl exec -it'
alias kpf='kubectl port-forward'
alias ka='kubectl apply -f'

# 911 Training specific
alias k911='kubectl -n 911-training'
alias k911logs='kubectl logs -n 911-training'
alias k911pods='kubectl get pods -n 911-training'
```
