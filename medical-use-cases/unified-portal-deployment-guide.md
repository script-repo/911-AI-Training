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

This guide describes how to deploy a **Unified AI Portal** that consolidates all healthcare AI use cases — patient monitoring, medication adherence tracking, security/safety detection, and vision-based analytics — into a single, self-service on-premises platform. The portal is designed to be stood up in under 30 minutes by engineers without deep Kubernetes expertise, eliminating the need for prolonged consulting engagements.

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
| Storage (NVMe/SSD) | 2 TB | 8 TB |
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
helm repo add ai-portal http://harbor.local/chartrepo/ai-platform
helm repo update

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

Upload via the portal **Models** tab (no CLI required), or via CLI:

```bash
kubectl -n ai-patient cp ./gemma-7b.gguf \
  $(kubectl -n ai-patient get pod -l app=model-server -o name | head -1):/models/gemma-7b.gguf

kubectl -n ai-patient rollout restart deployment/model-server
```

#### Integration with COTS Software

Configure your COTS EHR to POST patient events to:

```
http://patient-monitoring-api.ai-patient.svc.cluster.local/webhook/event
```

The API enriches events with model inference results and pushes back via a configurable callback URL.

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
Camera (RTSP) --> rtsp-ingestor --> Frame Buffer --> cv-inference-server
                                                           |
                              ┌────────────────────────────┘
                              v
                   med-adherence-api (post-processing)
                              |
                 ┌────────────┴────────────┐
                 v                         v
          Confidence >= 0.85          Confidence < 0.85
       (Swallowed — log OK)    (Suspected Pocketing — alert)
                                          |
                                  alert-dispatcher
                                  (Nurse Call / EHR note)
```

The default model is a fine-tuned **YOLOv8** variant trained on de-identified medication administration footage.

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
| Group size (>= 3 persons) | YOLOv8-pose | 3+ bounding boxes |
| Erratic/unstable movement | Action recognition (SlowFast) | Confidence >= 0.80 |
| Aggressive posture | Pose estimation + classifier | Confidence >= 0.75 |
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
      |
      +-- Group >= 3 + Erratic Movement --> Security Dispatch      [Priority HIGH]
      |
      +-- Group >= 3, Calm             --> Notify charge nurse     [Priority MEDIUM]
      |
      +-- Single Person + Erratic      --> Nursing Alert           [Priority MEDIUM]
      |
      +-- Normal                       --> Log only                [No alert]
```

All alert routing rules are configurable via the portal's **Security > Alert Rules** panel without redeployment.

---

### 4. Vision Capabilities Hub

**Purpose:** A centralized hub for shared vision pipeline primitives — object tracking, object identification, and image segmentation — consumable by other modules or extended for new use cases.

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
# Object tracking
curl -X POST http://vision-hub-api.ai-vision.svc.cluster.local/track \
  -H "Content-Type: application/json" \
  -d '{"frame_base64": "<BASE64_FRAME>", "session_id": "ward-cam-01"}'

# Segmentation
curl -X POST http://vision-hub-api.ai-vision.svc.cluster.local/segment \
  -H "Content-Type: application/json" \
  -d '{"image_base64": "<BASE64_IMAGE>", "prompts": ["medication cup", "hand"]}'
```

---

## Infrastructure Setup (On-Prem AOS Clusters)

### Step 1: Prepare AOS Cluster

Verify cluster health in Prism Central: **Infrastructure > Clusters**. All CVM services must show GREEN status.

Reserve dedicated VMs for NKP control plane and worker nodes:
- Minimum worker node: 16 vCPU, 64 GB RAM, 500 GB disk, GPU passthrough enabled.

### Step 2: Enable GPU Passthrough on AHV

```bash
# Prism Element > Host > GPU Settings > Enable Virtual GPU

# Verify inside worker VM:
nvidia-smi
```

### Step 3: Seed the Local Image Registry (Harbor)

```bash
# On a machine with temporary internet access:
docker pull nvcr.io/nvidia/tritonserver:23.10-py3
docker pull ollama/ollama:latest

# Retag and push to Harbor
docker tag ollama/ollama:latest harbor.local/ai/ollama:latest
docker push harbor.local/ai/ollama:latest

# OR use the provided seed script:
bash scripts/seed-registry.sh --harbor-url harbor.local --username admin --password <PASSWORD>
```

### Step 4: Configure DNS

```
portal.ai.hospital.local      --> <LoadBalancer-VIP>
patient.ai.hospital.local     --> <LoadBalancer-VIP>
medication.ai.hospital.local  --> <LoadBalancer-VIP>
security.ai.hospital.local    --> <LoadBalancer-VIP>
vision.ai.hospital.local      --> <LoadBalancer-VIP>
harbor.local                  --> <Harbor-VM-IP>
```

---

## One-Click NKP/NAI Deployment

```bash
git clone http://git.hospital.local/ai-platform/ai-portal.git
cd ai-portal

cp configs/values-template.yaml configs/values-site.yaml
# Fill in: cluster VIP, Harbor URL, DNS suffix, GPU node count, camera RTSP URLs

bash scripts/bootstrap.sh --values configs/values-site.yaml
```

### Bootstrap Execution Flow (~28 minutes total)

| Step | Action | Duration |
|------|--------|----------|
| 1 | Validate prerequisites | ~1 min |
| 2 | Install NKP via offline bundle | ~8 min |
| 3 | Deploy NVIDIA GPU Operator | ~3 min |
| 4 | Deploy cert-manager + TLS certs | ~2 min |
| 5 | Deploy MetalLB (LoadBalancer) | ~1 min |
| 6 | Deploy Harbor (if not pre-existing) | ~3 min |
| 7 | Deploy ingress-nginx | ~1 min |
| 8 | Deploy Unified Portal frontend + API gateway | ~2 min |
| 9 | Deploy enabled use case modules | ~5 min |
| 10 | Smoke tests + print access URL | ~2 min |

### values-site.yaml Module Toggles

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
├── ai/                         <- Runtime images
│   ├── ollama:latest
│   ├── triton:23.10
│   ├── med-adherence:1.0
│   ├── group-detect:1.0
│   └── vision-hub:1.0
├── models/                     <- Model weight files (OCI artifacts)
│   ├── gemma-7b/
│   ├── mistral-7b/
│   ├── med-adherence-yolo/
│   └── security-detection/
└── chartrepo/
    └── ai-platform/            <- Helm charts
        ├── patient-monitoring/
        ├── medication-adherence/
        ├── security-safety/
        └── vision-hub/
```

### Uploading Models via Portal UI

**LLM Models:**
1. Portal > **Models** > **LLM Library** > **+ Add Model**
2. Drag and drop `.gguf` / `.safetensors` file
3. Choose target module and GPU allocation, click **Deploy**

**CV Models:**
1. Portal > **Models** > **Computer Vision** > **+ Add Model**
2. Select framework: `ONNX`, `TensorRT`, or `TorchScript`
3. Assign to module — Triton performs a live reload with zero downtime

---

## Unified Portal UI

```
URL:      https://portal.ai.hospital.local
Username: admin
Password: (set in values-site.yaml -> portal.adminPassword)
```

### Navigation

| Section | Description |
|---------|-------------|
| **Dashboard** | Live status of all modules, GPU utilization, active alerts |
| **Patient Monitoring** | Model status, inference logs, EHR integration config |
| **Medication Adherence** | Live camera thumbnails, event log, confidence threshold tuning |
| **Security & Safety** | Multi-camera grid, alert history, routing rule editor |
| **Vision Hub** | API explorer, tracking sessions, segmentation playground |
| **Models** | Upload, version, and deploy LLM and CV models |
| **Settings** | SSO, TLS certs, DNS, alert endpoints, GPU quotas |
| **Tasks** | Background job queue (uploads, deployments, reloads) |

### RBAC Roles

| Role | Access |
|------|--------|
| `portal-admin` | Full access including Settings and Model management |
| `clinical-staff` | View dashboards, acknowledge alerts, view logs |
| `security-staff` | Security module only |
| `model-ops` | Models section only |

---

## GPU/CPU Operator Configuration

```bash
# Verify GPU Operator is healthy
kubectl get pods -n gpu-operator

# Verify GPU availability
kubectl get nodes -o custom-columns='NAME:.metadata.name,GPU:.status.allocatable.nvidia\.com/gpu'

# Apply GPU quota per namespace
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

### MIG (Multi-Instance GPU) — Optional for A100

```bash
# Enable MIG on a node
ssh worker-node-01 "sudo nvidia-smi -mig 1"

# Create 3x 3g.40gb slices on A100 80GB
ssh worker-node-01 "sudo nvidia-smi mig -cgi 3g.40gb,3g.40gb,3g.40gb -C"
```

---

## Monitoring & Alerting

| Component | Purpose | Access |
|-----------|---------|--------|
| **Prometheus** | Metrics collection | `http://prometheus.ai.hospital.local` |
| **Grafana** | Dashboards | `http://grafana.ai.hospital.local` |
| **Loki** | Log aggregation | Internal only |
| **Alertmanager** | Alert routing | `http://alertmanager.ai.hospital.local` |

Pre-built dashboards: AI Platform Overview, Patient Monitoring, Medication Adherence, Security & Safety, Vision Hub.

Key pre-configured alerts include GPU memory pressure (>90%) and RTSP feed offline (0 frames for 2+ minutes).

---

## Security & Access Control

- **mTLS everywhere**: All inter-service communication is mutually authenticated via the service mesh. Certificates auto-rotate via cert-manager.
- **Default-deny network policies**: Only explicitly declared traffic flows between namespaces are permitted.
- **No PHI persistence**: All inference is stateless. Video frames are processed in-memory and not persisted unless explicitly configured.
- **Audit logging**: All portal actions are written to Loki, retained 90 days by default.

---

## Optimization & Latency Tuning

### Eliminating the >1-Hour NKP Deployment Time

1. Pre-stage all images in Harbor before cluster creation.
2. Configure NKP to use Harbor as a `containerd` mirror at node bootstrap time.
3. Disable unused NKP add-ons in `values-site.yaml`.

```yaml
nkp:
  addons:
    enabled: [gpu-operator, metallb, ingress-nginx, cert-manager]
    disabled: [kommander, velero, prometheus]
```

### Inference Latency Tuning

```yaml
# Triton — dynamic batching
modelConfig:
  dynamicBatching:
    preferredBatchSize: [4, 8]
    maxQueueDelayMicroseconds: 50000

# Ollama — pin all layers to GPU
ollamaEnv:
  OLLAMA_FLASH_ATTENTION: "1"
  OLLAMA_GPU_LAYERS: "999"
```

---

## Operational Runbook

### Add a New Camera Feed (No Redeployment)

Portal > **Security & Safety** > **Cameras** > **+ Add Camera** > enter RTSP URL > **Save**. Feed is live within 30 seconds.

### Upgrade a Model In-Place

Portal > **Models** > select model > **Upload New Version** > choose rollout strategy (`BlueGreen` or `Immediate`) > **Deploy**.

### Scale a Module

```bash
helm upgrade med-adherence ai-portal/medication-adherence \
  --namespace ai-medication \
  --reuse-values \
  --set inference.replicaCount=2
```

### Remove a Module

```bash
helm uninstall med-adherence --namespace ai-medication
kubectl delete namespace ai-medication
```

---

## Troubleshooting

| Symptom | Command |
|---------|---------|
| GPU not detected | `kubectl logs -n gpu-operator -l app=nvidia-device-plugin-daemonset` |
| Camera feed missing | `kubectl logs -n ai-medication -l app=rtsp-ingestor` |
| Model inference errors | `kubectl logs -n ai-patient -l app=model-server` |
| Alerts not reaching nurse call | `kubectl logs -n ai-medication -l app=alert-dispatcher` |

---

## Summary

| Use Case | Namespace | Ingress Host | GPU |
|----------|-----------|--------------|-----|
| Patient Monitoring | `ai-patient` | `patient.ai.hospital.local` | Yes (LLM) |
| Medication Adherence | `ai-medication` | `medication.ai.hospital.local` | Yes (CV) |
| Security & Safety | `ai-security` | `security.ai.hospital.local` | Yes (CV) |
| Vision Hub | `ai-vision` | `vision.ai.hospital.local` | Yes (CV) |
| Portal UI | `ai-portal` | `portal.ai.hospital.local` | No |

All use cases are accessible from a single login at `https://portal.ai.hospital.local`. The bootstrapper provisions the entire stack in under 30 minutes with a single command, requiring no Kubernetes expertise beyond editing `values-site.yaml`.
