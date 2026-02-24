# Unified AI Portal Deployment Guide for Healthcare

## Deploying a Consolidated On-Premises AI Platform Across All Healthcare Use Cases

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture Summary](#architecture-summary)
3. [Prerequisites](#prerequisites)
4. [Portal Components & Use Case Modules](#portal-components--use-case-modules)
   - [Patient Monitoring & Fine-Tuned Model Service](#1-patient-monitoring--fine-tuned-model-service)
   - [Medication Adherence (Computer Vision)](#2-medication-adherence-computer-vision)
   - [Security & Safety Detection](#3-security--safety-detection)
   - [Vision Capabilities Hub](#4-vision-capabilities-hub)
5. [Infrastructure Setup (On-Prem AOS Clusters)](#infrastructure-setup-on-prem-aos-clusters)
6. [One-Click NKP/NAI Deployment](#one-click-nkpnai-deployment)
7. [Local Model Hosting & Image Registry](#local-model-hosting--image-registry)
8. [Unified Portal UI](#unified-portal-ui)
9. [GPU/CPU Operator Configuration](#gpucpu-operator-configuration)
10. [Monitoring & Alerting](#monitoring--alerting)
11. [Security & Access Control](#security--access-control)
12. [Optimization & Latency Tuning](#optimization--latency-tuning)
13. [Operational Runbook](#operational-runbook)
14. [Troubleshooting](#troubleshooting)

---

## Overview

This guide describes how to deploy a **Unified AI Portal** that consolidates all healthcare AI use cases—patient monitoring, medication adherence tracking, security/safety detection, and vision-based analytics—into a single, self-service on-premises platform. The portal is designed to be stood up in under 30 minutes by engineers without deep Kubernetes expertise, eliminating the need for prolonged consulting engagements.

### Goals

| Goal | Target |
|------|--------|
| Deployment time (default environment) | < 30 minutes |
| Operator skill level required | General software engineer (no Kubernetes specialization) |
| Model upload time (Gemma, Mistral, etc.) | < 10 minutes post-environment setup |
| External internet dependency | None (fully air-gapped capable) |
| Professional services requirement | Zero for standard use cases |

---

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────────────┐
│                        UNIFIED AI PORTAL                            │
│                    (Single Web Entry Point)                         │
├───────────────┬───────────────┬───────────────┬─────────────────────┤
│   Patient     │  Medication   │  Security &   │   Vision            │
│  Monitoring   │  Adherence    │  Safety       │   Capabilities      │
│  Module       │  Module       │  Module       │   Hub               │
│  (LLM/NLP)   │  (CV)         │  (CV)         │   (Tracking/Seg)    │
├───────────────┴───────────────┴───────────────┴─────────────────────┤
│                    API Gateway / Service Mesh                        │
├───────────────┬───────────────┬───────────────┬─────────────────────┤
│  Model Server │  Video        │  Alert        │  Model              │
│  (Ollama /    │  Inference    │  Engine       │  Registry           │
│   vLLM)       │  Pipeline     │               │  (Local Harbor)     │
├───────────────┴───────────────┴───────────────┴─────────────────────┤
│              NKP / NAI (Nutanix Kubernetes Platform)                │
├─────────────────────────────────────────────────────────────────────┤
│              AOS On-Prem Cluster (GPU + CPU Nodes)                  │
└─────────────────────────────────────────────────────────────────────┘
```

**Key design principles:**
- All services communicate over an internal service mesh (Istio or Linkerd).
- The portal presents a single HTTPS endpoint to end-users.
- Each use case is an independently deployable Helm chart, activated via a feature-flag toggle in the portal UI.
- No workload requires an outbound internet connection after the initial seed pull.

---

## Prerequisites

### Hardware

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| AOS Cluster nodes | 3 (1 control, 2 worker) | 5+ nodes |
| GPU per worker node | 1x NVIDIA A30 or equivalent | 2x A100 80GB |
| CPU cores per worker | 16 | 32+ |
| RAM per worker | 64 GB | 128 GB |
| Storage (NVM e/SSD) | 2 TB | 8 TB |
| Network | 10 GbE | 25 GbE |

### Software

- **Nutanix AOS** 6.5+ with AHV hypervisor
- **NKP** (Nutanix Kubernetes Platform) 2.x or **NAI** (Nutanix AI)
- **Harbor** (local OCI image registry) — deployed via Helm
- **Helm** 3.10+
- **kubectl** 1.27+
- **NVIDIA GPU Operator** (bundled in NKP add-on catalog)

### Credentials & Certificates

- Internal CA certificate for TLS (wildcard or SAN cert for `*.ai.hospital.local`)
- LDAP/AD service account for SSO integration (optional but recommended)
- NKP admin credentials

---

## Portal Components & Use Case Modules

### 1. Patient Monitoring & Fine-Tuned Model Service

**Purpose:** Augments existing COTS patient monitoring software with specialized language models (Gemma, Mistral) for clinical note summarization, early deterioration alerting, and care-team communication.

#### Services Deployed

| Service | Image | Port |
|---------|-------|------|
| `model-server` | `harbor.local/ai/ollama:latest` | 11434 |
| `patient-monitor-api` | `harbor.local/ai/pm-api:1.0` | 8080 |
| `pm-frontend` | `harbor.local/ai/pm-ui:1.0` | 3000 |

#### Helm Chart Installation

```bash
# Add the local chart repo (seeded during infrastructure setup)
helm repo add ai-portal http://harbor.local/chartrepo/ai-platform
helm repo update

# Install the patient monitoring module
helm upgrade --install patient-monitoring ai-portal/patient-monitoring \
  --namespace ai-patient \
  --create-namespace \
  --set modelServer.model=gemma:7b \
  --set modelServer.gpuLimit=1 \
  --set api.cotsEndpoint="http://cots-ehr.hospital.local/api" \
  --set ingress.host="patient.ai.hospital.local" \
  --wait --timeout=10m
```

#### Model Upload (Gemma / Mistral)

If the model is not pre-cached in Harbor, upload it using the portal's **Model Library** tab:

1. Navigate to `https://portal.ai.hospital.local` → **Models** → **Upload**.
2. Select the GGUF or SafeTensors file from a local drive.
3. Choose target module: `Patient Monitoring`.
4. Click **Deploy**. The portal streams the upload directly to the model server's volume — no CLI required.

CLI alternative:

```bash
# Copy model file to the model-server pod directly
kubectl -n ai-patient cp ./gemma-7b.gguf \
  $(kubectl -n ai-patient get pod -l app=model-server -o name | head -1):/models/gemma-7b.gguf

# Trigger hot-reload
kubectl -n ai-patient rollout restart deployment/model-server
```

#### Integration with COTS Software

The `patient-monitor-api` exposes a REST webhook receiver. Configure your COTS EHR/monitoring system to `POST` patient events to:

```
http://patient-monitoring-api.ai-patient.svc.cluster.local/webhook/event
```

The API will enrich the event with model inference results and push enriched data back via a configurable callback URL.

---

### 2. Medication Adherence (Computer Vision)

**Purpose:** Uses computer vision to verify whether patients actually swallow medication or conceal it ("pocketing"). Camera feeds from medication administration areas are processed in real-time.

#### Services Deployed

| Service | Image | Port |
|---------|-------|------|
| `cv-inference-server` | `harbor.local/ai/triton:23.10` | 8000 / 8001 / 8002 |
| `med-adherence-api` | `harbor.local/ai/med-adherence:1.0` | 8080 |
| `rtsp-ingestor` | `harbor.local/ai/rtsp-bridge:1.0` | 8554 |
| `alert-dispatcher` | `harbor.local/ai/alerter:1.0` | 9090 |

#### Camera Feed Requirements

- RTSP-compatible IP cameras (H.264 or H.265 stream)
- Minimum resolution: 720p @ 15 fps
- Camera placement: direct line-of-sight to patient mouth, < 2m distance

#### Helm Chart Installation

```bash
helm upgrade --install med-adherence ai-portal/medication-adherence \
  --namespace ai-medication \
  --create-namespace \
  --set rtsp.streamUrl="rtsp://10.0.1.50:554/live" \
  --set inference.modelRepository="harbor.local/ai/models/med-adherence" \
  --set inference.gpuLimit=1 \
  --set alerts.nursePagerEndpoint="http://nursecall.hospital.local/api/alert" \
  --set ingress.host="medication.ai.hospital.local" \
  --wait --timeout=10m
```

#### Inference Pipeline

```
Camera (RTSP) → rtsp-ingestor → Frame Buffer → cv-inference-server
                                                       │
                              ┌────────────────────────┘
                              ▼
                   med-adherence-api (post-processing)
                              │
                 ┌────────────┴────────────┐
                 ▼                         ▼
          Confidence ≥ 0.85          Confidence < 0.85
       (Swallowed — log OK)    (Suspected Pocketing — alert)
                                          │
                                  alert-dispatcher
                                  (Nurse Call / EHR note)
```

#### CV Model Details

The default model is a fine-tuned **YOLOv8** variant trained on de-identified medication administration footage. Model files are stored in the Harbor registry under `harbor.local/ai/models/med-adherence`.

To upload a custom or updated model via the portal:

1. Navigate to **Models** → **Medication Adherence** → **Replace Model**.
2. Upload the `.onnx` or TensorRT `.plan` file.
3. The Triton inference server performs a live model reload with zero downtime.

---

### 3. Security & Safety Detection

**Purpose:** Computer vision to detect group arrivals (e.g., intoxicated or aggressive groups) at facility entry points, automatically dispatching security alerts and reducing unnecessary nursing interventions.

#### Services Deployed

| Service | Image | Port |
|---------|-------|------|
| `security-cv-server` | `harbor.local/ai/triton:23.10` | 8000 |
| `group-detection-api` | `harbor.local/ai/group-detect:1.0` | 8080 |
| `rtsp-ingestor-security` | `harbor.local/ai/rtsp-bridge:1.0` | 8554 |
| `security-alert-engine` | `harbor.local/ai/security-alerter:1.0` | 9091 |

#### Detection Capabilities

| Detection Type | Model | Trigger Threshold |
|----------------|-------|-------------------|
| Group size (≥ 3 persons) | YOLOv8-pose | 3+ bounding boxes |
| Erratic/unstable movement | Action recognition (SlowFast) | Confidence ≥ 0.80 |
| Aggressive posture | Pose estimation + classifier | Confidence ≥ 0.75 |
| Unattended bags/objects | YOLOv8-seg | Configurable |

#### Helm Chart Installation

```bash
helm upgrade --install security-safety ai-portal/security-safety \
  --namespace ai-security \
  --create-namespace \
  --set rtsp.cameraFeeds[0]="rtsp://10.0.2.10:554/entrance-main" \
  --set rtsp.cameraFeeds[1]="rtsp://10.0.2.11:554/entrance-er" \
  --set inference.gpuLimit=1 \
  --set alerts.securityDispatchEndpoint="http://security.hospital.local/api/dispatch" \
  --set alerts.nurseCallEndpoint="http://nursecall.hospital.local/api/alert" \
  --set thresholds.groupSize=3 \
  --set ingress.host="security.ai.hospital.local" \
  --wait --timeout=10m
```

#### Alert Routing Logic

```
Detection Event
      │
      ├─ Group ≥ 3 + Erratic Movement → Security Dispatch (Priority HIGH)
      │
      ├─ Group ≥ 3, Calm → Log + Notify charge nurse (Priority MEDIUM)
      │
      ├─ Single Person + Erratic → Nursing Alert (Priority MEDIUM)
      │
      └─ Normal → Log only (no alert)
```

All alert routing rules are configurable via the portal's **Security** → **Alert Rules** panel without requiring a redeployment.

---

### 4. Vision Capabilities Hub

**Purpose:** A centralized hub for shared vision pipeline primitives—object tracking, object identification, and image segmentation—that can be consumed by the other modules or extended for new use cases over time.

#### Services Deployed

| Service | Image | Port | Description |
|---------|-------|------|-------------|
| `vision-tracker` | `harbor.local/ai/bytetrack:1.0` | 8080 | Multi-object tracking (ByteTrack) |
| `vision-identifier` | `harbor.local/ai/triton:23.10` | 8000 | Object identification (CLIP, DINO) |
| `vision-segmentor` | `harbor.local/ai/sam2:1.0` | 8082 | Instance segmentation (SAM2) |
| `vision-hub-api` | `harbor.local/ai/vision-hub:1.0` | 9000 | Unified REST/gRPC API |

#### Helm Chart Installation

```bash
helm upgrade --install vision-hub ai-portal/vision-hub \
  --namespace ai-vision \
  --create-namespace \
  --set tracker.enabled=true \
  --set identifier.enabled=true \
  --set segmentor.enabled=true \
  --set inference.gpuLimit=2 \
  --set ingress.host="vision.ai.hospital.local" \
  --wait --timeout=10m
```

#### API Usage Example

```bash
# Object tracking — submit a video frame
curl -X POST http://vision-hub-api.ai-vision.svc.cluster.local/track \
  -H "Content-Type: application/json" \
  -d '{"frame_base64": "<BASE64_ENCODED_FRAME>", "session_id": "ward-cam-01"}'

# Segmentation — identify regions in an image
curl -X POST http://vision-hub-api.ai-vision.svc.cluster.local/segment \
  -H "Content-Type: application/json" \
  -d '{"image_base64": "<BASE64_ENCODED_IMAGE>", "prompts": ["medication cup", "hand"]}'
```

#### Extending with New Use Cases

The Vision Hub is designed as a shared service. New use cases can call it via its REST or gRPC interface without deploying additional GPU workloads. This maximizes GPU utilization across the cluster.

---

## Infrastructure Setup (On-Prem AOS Clusters)

### Step 1: Prepare AOS Cluster

```bash
# Verify AOS cluster health from Prism Central
# Navigate to: Prism Central → Infrastructure → Clusters
# All CVM services should show GREEN status

# Reserve dedicated VMs for NKP control plane and worker nodes
# Minimum worker node VM spec: 16 vCPU, 64 GB RAM, 500 GB disk, GPU passthrough enabled
```

### Step 2: Enable GPU Passthrough on AHV

```bash
# From Prism Element (per node), enable SR-IOV or GPU passthrough:
# Prism Element → Host → GPU Settings → Enable Virtual GPU

# Verify GPU visibility in the worker VM:
nvidia-smi
```

### Step 3: Seed the Local Image Registry (Harbor)

Harbor must be populated with all required container images and Helm charts before cluster bootstrap to avoid internet dependency.

```bash
# On a machine with temporary internet access and Docker installed:

# Pull required images
docker pull nvcr.io/nvidia/tritonserver:23.10-py3
docker pull ollama/ollama:latest
docker pull goharbor/harbor-core:v2.10.0
# ... (full image list provided in scripts/seed-registry.sh)

# Retag and push to Harbor
docker tag ollama/ollama:latest harbor.local/ai/ollama:latest
docker push harbor.local/ai/ollama:latest

# OR use the provided seed script:
bash scripts/seed-registry.sh --harbor-url harbor.local --username admin --password <PASSWORD>
```

### Step 4: Configure DNS

Add the following records to your internal DNS server:

```
portal.ai.hospital.local      → <LoadBalancer-VIP>
patient.ai.hospital.local     → <LoadBalancer-VIP>
medication.ai.hospital.local  → <LoadBalancer-VIP>
security.ai.hospital.local    → <LoadBalancer-VIP>
vision.ai.hospital.local      → <LoadBalancer-VIP>
harbor.local                  → <Harbor-VM-IP>
```

---

## One-Click NKP/NAI Deployment

To meet the < 30-minute deployment target, the portal ships with a **bootstrapper script** that provisions NKP, installs all operators, and deploys all use case modules with pre-configured defaults.

### Run the Bootstrapper

```bash
# Clone the AI portal repo from Harbor's integrated Git (Gitea) or your internal SCM
git clone http://git.hospital.local/ai-platform/ai-portal.git
cd ai-portal

# Edit site-specific values (takes ~2 minutes)
cp configs/values-template.yaml configs/values-site.yaml
# Fill in: cluster VIP, Harbor URL, DNS suffix, GPU node count, camera RTSP URLs

# Execute one-click bootstrap
bash scripts/bootstrap.sh --values configs/values-site.yaml
```

### What the Bootstrapper Does

```
bootstrap.sh execution flow:
─────────────────────────────────────────────────────
 1. Validates prerequisites (kubectl context, Harbor reachability)    [~1 min]
 2. Installs NKP via pre-staged offline bundle                        [~8 min]
 3. Deploys NVIDIA GPU Operator from local Harbor                     [~3 min]
 4. Deploys cert-manager + issues internal TLS certs                  [~2 min]
 5. Deploys MetalLB (LoadBalancer) with pre-configured VIP pool       [~1 min]
 6. Deploys Harbor (if not pre-existing)                              [~3 min]
 7. Deploys Ingress Controller (ingress-nginx)                        [~1 min]
 8. Deploys Unified Portal frontend + API gateway                     [~2 min]
 9. Deploys all enabled use case modules (per values-site.yaml)       [~5 min]
10. Runs smoke tests and prints access URL                            [~2 min]
─────────────────────────────────────────────────────
 Total:                                                               ~28 min
```

### Enable/Disable Use Case Modules

In `configs/values-site.yaml`, toggle modules on or off:

```yaml
modules:
  patientMonitoring:
    enabled: true
    model: "gemma:7b"
    gpuLimit: 1

  medicationAdherence:
    enabled: true
    cameraRtspUrl: "rtsp://10.0.1.50:554/live"
    gpuLimit: 1

  securitySafety:
    enabled: true
    cameraFeeds:
      - "rtsp://10.0.2.10:554/entrance-main"
      - "rtsp://10.0.2.11:554/entrance-er"
    gpuLimit: 1

  visionHub:
    enabled: true
    gpuLimit: 2
```

---

## Local Model Hosting & Image Registry

### Harbor Registry Layout

```
harbor.local/
├── ai/                         ← Runtime images
│   ├── ollama:latest
│   ├── triton:23.10
│   ├── med-adherence:1.0
│   ├── group-detect:1.0
│   ├── vision-hub:1.0
│   └── ...
├── models/                     ← Model weight files (OCI artifacts)
│   ├── gemma-7b/
│   ├── mistral-7b/
│   ├── med-adherence-yolo/
│   └── security-detection/
└── chartrepo/
    └── ai-platform/            ← Helm charts
        ├── patient-monitoring/
        ├── medication-adherence/
        ├── security-safety/
        └── vision-hub/
```

### Uploading a New LLM via Portal UI

1. Log in to `https://portal.ai.hospital.local`.
2. Go to **Models** → **LLM Library** → **+ Add Model**.
3. Select upload source: **Local File** or **Harbor OCI Pull**.
4. For local file: drag and drop the `.gguf` / `.safetensors` file.
5. Choose target module and GPU allocation.
6. Click **Deploy**. Monitor progress in the **Tasks** panel.

### Uploading a New CV Model via Portal UI

1. Go to **Models** → **Computer Vision** → **+ Add Model**.
2. Select the framework: `ONNX`, `TensorRT`, or `PyTorch TorchScript`.
3. Upload the model file and provide a name and version.
4. Assign the model to a module (Medication Adherence, Security, or Vision Hub).
5. The Triton server performs a live reload — no downtime.

---

## Unified Portal UI

The portal is a single-page React application served behind the ingress controller.

### Access

```
URL:      https://portal.ai.hospital.local
Default credentials (first login):
  Username: admin
  Password: (set during bootstrap via values-site.yaml → portal.adminPassword)
```

### Portal Navigation

| Section | Description |
|---------|-------------|
| **Dashboard** | Live status of all modules, GPU utilization, active alerts |
| **Patient Monitoring** | Model status, inference logs, EHR integration config |
| **Medication Adherence** | Live camera feed thumbnails, adherence event log, confidence threshold tuning |
| **Security & Safety** | Multi-camera grid view, alert history, routing rule editor |
| **Vision Hub** | API explorer, active tracking sessions, segmentation playground |
| **Models** | Upload, version, and deploy LLM and CV models |
| **Settings** | SSO, TLS certs, DNS, alert endpoints, GPU quotas |
| **Tasks** | Background job queue (model uploads, deployments, reloads) |

### Role-Based Access Control (RBAC)

| Role | Access |
|------|--------|
| `portal-admin` | Full access including Settings and Model management |
| `clinical-staff` | View dashboards, acknowledge alerts, view logs |
| `security-staff` | Security module only — camera feeds and alert history |
| `model-ops` | Models section only — upload, deploy, version |

RBAC roles map to LDAP/AD groups configured in **Settings** → **Identity Provider**.

---

## GPU/CPU Operator Configuration

### NVIDIA GPU Operator

The GPU Operator is deployed automatically by the bootstrapper. To verify:

```bash
kubectl get pods -n gpu-operator
# All pods should be in Running state

# Verify GPU is available in the cluster
kubectl get nodes -o custom-columns='NAME:.metadata.name,GPU:.status.allocatable.nvidia\.com/gpu'
```

### GPU Resource Quotas per Namespace

```bash
# Apply GPU quota per module namespace
kubectl apply -f - <<EOF
apiVersion: v1
kind: ResourceQuota
metadata:
  name: gpu-quota
  namespace: ai-patient
spec:
  hard:
    requests.nvidia.com/gpu: "1"
    limits.nvidia.com/gpu: "1"
EOF
```

Repeat for `ai-medication`, `ai-security`, `ai-vision` (adjust limits per module config).

### Multi-Instance GPU (MIG) — Optional

For A100 GPUs, enable MIG to share a single GPU across multiple modules:

```bash
# Enable MIG on a node
ssh worker-node-01 "sudo nvidia-smi -mig 1"

# Configure MIG profiles (e.g., 3x 3g.40gb slices on A100 80GB)
ssh worker-node-01 "sudo nvidia-smi mig -cgi 3g.40gb,3g.40gb -C"

# The GPU Operator will automatically expose MIG slices as schedulable resources
kubectl get nodes -o json | jq '.items[].status.allocatable | with_entries(select(.key | startswith("nvidia")))'
```

---

## Monitoring & Alerting

### Deployed Monitoring Stack

The bootstrapper installs a lightweight monitoring stack:

| Component | Purpose | Access |
|-----------|---------|--------|
| **Prometheus** | Metrics collection | `http://prometheus.ai.hospital.local` |
| **Grafana** | Dashboards | `http://grafana.ai.hospital.local` |
| **Loki** | Log aggregation | Internal only |
| **Alertmanager** | Alert routing | `http://alertmanager.ai.hospital.local` |

### Pre-Built Dashboards

| Dashboard | Metrics Shown |
|-----------|--------------|
| AI Platform Overview | GPU utilization, pod health, inference throughput |
| Patient Monitoring | Model inference latency, EHR webhook success rate |
| Medication Adherence | Frame processing FPS, adherence event rate, alert count |
| Security & Safety | Detection events/hour, alert response time, camera feed health |
| Vision Hub | API request rate, tracking session count, segmentation latency |

### Key Alerts (Pre-Configured in Alertmanager)

```yaml
# Sample alert: GPU memory pressure
- alert: GPUMemoryHigh
  expr: nvidia_gpu_memory_used_bytes / nvidia_gpu_memory_total_bytes > 0.90
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "GPU memory above 90% on {{ $labels.instance }}"

# Sample alert: Camera feed offline
- alert: RTSPFeedOffline
  expr: rtsp_ingestor_frames_received_total{job="rtsp-ingestor"} == 0
  for: 2m
  labels:
    severity: critical
  annotations:
    summary: "Camera feed offline: {{ $labels.stream_url }}"
```

---

## Security & Access Control

### TLS Everywhere

All inter-service communication uses mutual TLS (mTLS) enforced by the service mesh. The portal and all ingress endpoints require TLS. Certificates are automatically rotated by cert-manager.

### Network Policies

Each module namespace has a default-deny network policy. Only explicitly declared traffic flows are permitted:

```yaml
# Example: Only the portal API gateway can reach the patient-monitoring API
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-portal-to-pm-api
  namespace: ai-patient
spec:
  podSelector:
    matchLabels:
      app: patient-monitor-api
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ai-portal
```

### PHI / PII Considerations

- No patient-identifiable data is stored by the AI modules. All inference is stateless.
- Video frames are processed in-memory and not persisted unless explicitly configured.
- Audit logs for all portal actions (model uploads, alert acknowledgments, config changes) are written to Loki and retained for 90 days by default.
- Ensure the AOS cluster itself complies with your facility's HIPAA/HITRUST policies at the hypervisor and storage layer.

---

## Optimization & Latency Tuning

### Reducing NKP Default Deployment Time

The stock NKP deployment downloads images from the internet, which causes the >1-hour deployment time. The bootstrapper eliminates this by:

1. **Pre-staging all images in Harbor** before cluster creation.
2. **Configuring NKP to use Harbor as a mirror** via `containerd` registry config applied at node bootstrap time.
3. **Disabling unnecessary NKP add-ons** (only the required add-ons are enabled per `values-site.yaml`).

```bash
# values-site.yaml — disable unused NKP add-ons
nkp:
  addons:
    enabled:
      - gpu-operator
      - metallb
      - ingress-nginx
      - cert-manager
    disabled:
      - kommander        # enterprise management (not needed for single cluster)
      - velero           # backup (optional, enable if needed)
      - prometheus       # we deploy our own monitoring stack
```

### Inference Latency Tuning

```yaml
# Triton server — enable dynamic batching for higher throughput
modelConfig:
  dynamicBatching:
    preferredBatchSize: [4, 8]
    maxQueueDelayMicroseconds: 50000   # 50ms max queue wait

# Ollama — pin model to GPU, disable CPU offload
ollamaEnv:
  OLLAMA_FLASH_ATTENTION: "1"
  OLLAMA_GPU_LAYERS: "999"            # All layers on GPU
```

---

## Operational Runbook

### Adding a New Camera Feed (No Redeployment Required)

1. Log in to the portal → **Security & Safety** (or **Medication Adherence**).
2. Click **Cameras** → **+ Add Camera**.
3. Enter the RTSP URL and a display name.
4. Click **Save**. The `rtsp-ingestor` picks up the new feed within 30 seconds.

### Upgrading a Model In-Place

1. Portal → **Models** → Select the model to upgrade.
2. Click **Upload New Version** and provide the new file.
3. Set **Rollout Strategy**: `BlueGreen` (zero-downtime) or `Immediate`.
4. Click **Deploy**.

### Scaling a Module to Handle More Cameras

```bash
# Scale the CV inference server replicas (requires additional GPU capacity)
helm upgrade med-adherence ai-portal/medication-adherence \
  --namespace ai-medication \
  --reuse-values \
  --set inference.replicaCount=2 \
  --set inference.gpuLimit=1
```

### Removing a Module

```bash
helm uninstall med-adherence --namespace ai-medication
kubectl delete namespace ai-medication
```

---

## Troubleshooting

### Bootstrap script fails at NKP installation

```bash
# Check NKP bundle integrity
sha256sum nkp-bundle.tar.gz
# Compare against the expected checksum in scripts/checksums.sha256

# Re-run with verbose logging
bash scripts/bootstrap.sh --values configs/values-site.yaml --verbose
```

### GPU not detected in cluster

```bash
# Verify GPU passthrough is enabled in AHV
# Prism Element → Hosts → Select host → GPU settings

# Check GPU Operator pod logs
kubectl logs -n gpu-operator -l app=nvidia-device-plugin-daemonset --tail=50

# Force re-detection
kubectl rollout restart daemonset/nvidia-device-plugin-daemonset -n gpu-operator
```

### Camera feed not appearing in portal

```bash
# Test RTSP stream reachability from within the cluster
kubectl run rtsp-test --image=harbor.local/ai/ffprobe:latest --rm -it --restart=Never -- \
  ffprobe -v quiet -print_format json -show_streams rtsp://10.0.1.50:554/live

# Check ingestor logs
kubectl logs -n ai-medication -l app=rtsp-ingestor --tail=100
```

### Model inference returning errors

```bash
# Check model server health
curl http://model-server.ai-patient.svc.cluster.local:11434/api/health

# View model server logs
kubectl logs -n ai-patient -l app=model-server --tail=100

# Verify model file is present
kubectl exec -n ai-patient deploy/model-server -- ls -lh /models/
```

### Alert notifications not reaching nurse call system

```bash
# Test the nurse call endpoint directly
curl -X POST http://nursecall.hospital.local/api/alert \
  -H "Content-Type: application/json" \
  -d '{"type":"test","priority":"LOW","message":"AI portal connectivity test"}'

# Check alert dispatcher logs
kubectl logs -n ai-medication -l app=alert-dispatcher --tail=50
```

---

## Summary

| Use Case | Namespace | Ingress Host | GPU Required |
|----------|-----------|--------------|--------------|
| Patient Monitoring | `ai-patient` | `patient.ai.hospital.local` | Yes (LLM) |
| Medication Adherence | `ai-medication` | `medication.ai.hospital.local` | Yes (CV) |
| Security & Safety | `ai-security` | `security.ai.hospital.local` | Yes (CV) |
| Vision Hub | `ai-vision` | `vision.ai.hospital.local` | Yes (CV) |
| Portal UI | `ai-portal` | `portal.ai.hospital.local` | No |

All use cases are accessible from a single login at `https://portal.ai.hospital.local`. The bootstrapper provisions the entire stack in under 30 minutes with a single command, requiring no Kubernetes expertise beyond editing the `values-site.yaml` configuration file.
