# Kubernetes Secrets

This directory contains example secret files with placeholders. **DO NOT** commit actual secrets to version control.

## Creating Secrets

### Option 1: Using kubectl create secret

```bash
# OpenRouter API Secret
kubectl create secret generic openrouter-secret \
  --from-literal=OPENROUTER_API_KEY=your_actual_api_key_here \
  --namespace=911-training

# Database Secret
kubectl create secret generic database-secret \
  --from-literal=POSTGRES_USER=postgres \
  --from-literal=POSTGRES_PASSWORD=your_secure_password_here \
  --from-literal=DATABASE_URL=postgresql://postgres:your_secure_password_here@postgresql-service:5432/training_db \
  --namespace=911-training

# Redis Secret (if using password)
kubectl create secret generic redis-secret \
  --from-literal=REDIS_PASSWORD=your_redis_password_here \
  --namespace=911-training

# S3/MinIO Secret
kubectl create secret generic s3-secret \
  --from-literal=S3_ACCESS_KEY=your_access_key_here \
  --from-literal=S3_SECRET_KEY=your_secret_key_here \
  --namespace=911-training
```

### Option 2: Using the example YAML files

1. Copy the example files and remove the `.example` suffix
2. Replace all placeholder values with actual secrets
3. Base64 encode the values:
   ```bash
   echo -n "your_secret_value" | base64
   ```
4. Update the YAML files with the base64-encoded values
5. Apply the secrets:
   ```bash
   kubectl apply -f openrouter-secret.yaml
   kubectl apply -f database-secret.yaml
   kubectl apply -f redis-secret.yaml
   kubectl apply -f s3-secret.yaml
   ```

### Option 3: Using Sealed Secrets (Recommended for GitOps)

If you're using a GitOps workflow, consider using [Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets):

```bash
# Install sealed-secrets controller
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.0/controller.yaml

# Create a secret and seal it
kubectl create secret generic openrouter-secret \
  --from-literal=OPENROUTER_API_KEY=your_actual_api_key_here \
  --dry-run=client -o yaml | \
  kubeseal -o yaml > openrouter-sealed-secret.yaml

# Commit the sealed secret to git
git add openrouter-sealed-secret.yaml
```

### Option 4: Using External Secrets Operator

For production environments, consider using [External Secrets Operator](https://external-secrets.io/) with your secret management solution (HashiCorp Vault, AWS Secrets Manager, etc.).

## Verification

Verify your secrets are created correctly:

```bash
# List all secrets
kubectl get secrets -n 911-training

# View secret (values will be base64 encoded)
kubectl describe secret openrouter-secret -n 911-training

# Decode a secret value (for debugging)
kubectl get secret openrouter-secret -n 911-training -o jsonpath='{.data.OPENROUTER_API_KEY}' | base64 --decode
```

## Security Best Practices

1. **Never commit unencrypted secrets to version control**
2. Use RBAC to restrict access to secrets
3. Enable encryption at rest for etcd
4. Rotate secrets regularly
5. Use separate secrets for different environments
6. Consider using a dedicated secret management solution for production
7. Audit secret access regularly
