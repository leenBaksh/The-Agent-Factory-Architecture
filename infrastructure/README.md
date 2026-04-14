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
│   ├── topics.yaml                # Kubernetes topic definitions (Strimzi)
│   └── docker-compose.yml         # Local Kafka + Zookeeper + Redis (dev)
│
├── kubernetes/                    # K8s manifests
│   ├── namespace.yaml             # agent-factory namespace
│   ├── secrets.yaml               # FTE secrets (placeholder - update before deploy)
│   ├── service-account.yaml       # ServiceAccount + RBAC
│   ├── deployments/
│   │   └── digital-ftes.yaml      # Combined FTE deployments
│   └── services/
│       └── fte-services.yaml      # ClusterIP services
│
└── docker/                        # Docker configs
    └── Dockerfile.fte             # Digital FTE base image
```

## Quick Start

### Local Development

1. Start infrastructure:
   ```bash
   cd infrastructure/kafka
   docker-compose up -d
   ```

2. Create Kafka topics (auto-created on first use if `KAFKA_AUTO_CREATE_TOPICS_ENABLE=true`):
   ```bash
   # Topics are auto-created when first message is published
   # Or manually apply topics.yaml in Kubernetes:
   kubectl apply -f topics.yaml
   ```

### Kubernetes Deployment

1. Create namespace and secrets:
   ```bash
   kubectl apply -f kubernetes/namespace.yaml
   kubectl apply -f kubernetes/secrets.yaml  # Update placeholder values first!
   kubectl apply -f kubernetes/service-account.yaml
   ```

2. Deploy Dapr components:
   ```bash
   kubectl apply -f dapr/components/
   kubectl apply -f dapr/configurations/
   ```

3. Deploy FTEs:
   ```bash
   kubectl apply -f kubernetes/deployments/
   kubectl apply -f kubernetes/services/
   ```

## Important Notes

- **Secrets**: The `secrets.yaml` file contains placeholder values. Replace with actual secrets before deploying to production. Use a secrets manager (Vault, Sealed Secrets, etc.) for production.
- **Redis Password**: Currently set to empty for local development. Set a proper password in production and update the Dapr components accordingly.
- **Kafka Topics**: The `topics.yaml` file defines topics for both Customer Success FTE (matching `.env` configuration) and cross-FTE infrastructure topics.
- **Dapr Components**: All components are scoped to the three FTE apps (customer-success, sales-support, technical-support).
