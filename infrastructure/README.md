# Agent Factory Infrastructure Configuration

This directory contains infrastructure configurations for Dapr, Kafka, and Kubernetes deployments.

## Directory Structure

```
infrastructure/
├── dapr/                          # Dapr components
│   ├── components/
│   │   ├── pubsub-kafka.yaml      # Kafka pub/sub component
│   │   ├── state-redis.yaml       # Redis state store
│   │   ├── secrets-local.yaml     # Local secrets (dev only)
│   │   └── workflow.yaml          # Dapr workflow configuration
│   └── configurations/
│       └── config.yaml            # Dapr sidecar configuration
│
├── kafka/                         # Kafka configuration
│   ├── topics.yaml                # Kubernetes topic definitions
│   └── docker-compose.yml         # Local Kafka (dev environment)
│
├── kubernetes/                    # K8s manifests
│   ├── agent-sandbox/             # Agent Sandbox (gVisor)
│   │   ├── sandbox-pool.yaml
│   │   └── sandbox-template.yaml
│   ├── deployments/
│   │   ├── customer-success-fte.yaml
│   │   ├── sales-support-fte.yaml
│   │   └── technical-support-fte.yaml
│   ├── services/
│   │   └── fte-services.yaml
│   └── monitoring/
│       ├── prometheus-rules.yaml
│       └── grafana-dashboard.yaml
│
└── docker/                        # Docker configs
    ├── Dockerfile.fte             # Digital FTE base image
    └── docker-compose.dev.yml     # Local dev environment
```
