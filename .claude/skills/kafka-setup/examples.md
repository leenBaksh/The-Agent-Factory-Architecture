# Kafka Setup Examples

## Example 1: Strimzi Kafka Cluster for Minikube

```yaml
# kafka/kafka-cluster-minikube.yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: Kafka
metadata:
  name: todo-kafka
  namespace: kafka
spec:
  kafka:
    version: 3.6.0
    replicas: 1
    listeners:
      - name: plain
        port: 9092
        type: internal
        tls: false
    config:
      offsets.topic.replication.factor: 1
      transaction.state.log.replication.factor: 1
      transaction.state.log.min.isr: 1
      default.replication.factor: 1
      min.insync.replicas: 1
    storage:
      type: ephemeral
    resources:
      requests:
        memory: 512Mi
        cpu: "250m"
      limits:
        memory: 1Gi
        cpu: "500m"
  zookeeper:
    replicas: 1
    storage:
      type: ephemeral
    resources:
      requests:
        memory: 256Mi
        cpu: "100m"
      limits:
        memory: 512Mi
        cpu: "250m"
  entityOperator:
    topicOperator: {}
```

## Example 2: Production Kafka Cluster

```yaml
# kafka/kafka-cluster-production.yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: Kafka
metadata:
  name: todo-kafka
  namespace: kafka
spec:
  kafka:
    version: 3.6.0
    replicas: 3
    listeners:
      - name: plain
        port: 9092
        type: internal
        tls: false
      - name: tls
        port: 9093
        type: internal
        tls: true
    config:
      offsets.topic.replication.factor: 3
      transaction.state.log.replication.factor: 3
      transaction.state.log.min.isr: 2
      default.replication.factor: 3
      min.insync.replicas: 2
    storage:
      type: jbod
      volumes:
        - id: 0
          type: persistent-claim
          size: 50Gi
          deleteClaim: false
    resources:
      requests:
        memory: 2Gi
        cpu: "1"
      limits:
        memory: 4Gi
        cpu: "2"
  zookeeper:
    replicas: 3
    storage:
      type: persistent-claim
      size: 10Gi
      deleteClaim: false
    resources:
      requests:
        memory: 1Gi
        cpu: "500m"
      limits:
        memory: 2Gi
        cpu: "1"
  entityOperator:
    topicOperator: {}
    userOperator: {}
```

## Example 3: Kafka Topics

```yaml
# kafka/kafka-topics.yaml
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaTopic
metadata:
  name: task-events
  namespace: kafka
  labels:
    strimzi.io/cluster: todo-kafka
spec:
  partitions: 3
  replicas: 1
  config:
    retention.ms: 604800000  # 7 days
    cleanup.policy: delete
    segment.bytes: 1073741824  # 1GB
---
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaTopic
metadata:
  name: reminder-events
  namespace: kafka
  labels:
    strimzi.io/cluster: todo-kafka
spec:
  partitions: 3
  replicas: 1
  config:
    retention.ms: 604800000
    cleanup.policy: delete
---
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaTopic
metadata:
  name: audit-events
  namespace: kafka
  labels:
    strimzi.io/cluster: todo-kafka
spec:
  partitions: 3
  replicas: 1
  config:
    retention.ms: 2592000000  # 30 days
    cleanup.policy: compact
---
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaTopic
metadata:
  name: task-updates
  namespace: kafka
  labels:
    strimzi.io/cluster: todo-kafka
spec:
  partitions: 3
  replicas: 1
  config:
    retention.ms: 86400000  # 1 day
    cleanup.policy: delete
```

## Example 4: Docker Compose Kafka

```yaml
# docker-compose.kafka.yaml
version: '3.9'

services:
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    container_name: zookeeper
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    ports:
      - "2181:2181"
    networks:
      - kafka-network
    volumes:
      - zookeeper-data:/var/lib/zookeeper/data
      - zookeeper-logs:/var/lib/zookeeper/log

  kafka:
    image: confluentinc/cp-kafka:7.5.0
    container_name: kafka
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
      - "29092:29092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092,PLAINTEXT_HOST://localhost:29092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1
      KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1
      KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS: 0
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true"
    networks:
      - kafka-network
    volumes:
      - kafka-data:/var/lib/kafka/data

  kafka-ui:
    image: provectuslabs/kafka-ui:latest
    container_name: kafka-ui
    depends_on:
      - kafka
    ports:
      - "8080:8080"
    environment:
      KAFKA_CLUSTERS_0_NAME: local
      KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS: kafka:9092
      KAFKA_CLUSTERS_0_ZOOKEEPER: zookeeper:2181
    networks:
      - kafka-network

networks:
  kafka-network:
    driver: bridge

volumes:
  zookeeper-data:
  zookeeper-logs:
  kafka-data:
```

## Example 5: Python Kafka Producer

```python
from aiokafka import AIOKafkaProducer
import json
import asyncio
from datetime import datetime

class TaskEventProducer:
    """Produce task events to Kafka."""

    def __init__(self, bootstrap_servers: str = "localhost:29092"):
        self.bootstrap_servers = bootstrap_servers
        self.producer = None

    async def start(self):
        """Start the producer."""
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None
        )
        await self.producer.start()

    async def stop(self):
        """Stop the producer."""
        if self.producer:
            await self.producer.stop()

    async def publish_task_event(self, event_type: str, task: dict, user_id: str):
        """Publish a task event."""
        event = {
            "event_type": event_type,
            "task_id": task["id"],
            "user_id": user_id,
            "task": task,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.producer.send_and_wait(
            topic="task-events",
            key=str(task["id"]),
            value=event
        )

# Usage
producer = TaskEventProducer()
await producer.start()
await producer.publish_task_event("task.created", task_data, user_id)
await producer.stop()
```

## Example 6: Python Kafka Consumer

```python
from aiokafka import AIOKafkaConsumer
import json
import asyncio

class TaskEventConsumer:
    """Consume task events from Kafka."""

    def __init__(
        self,
        bootstrap_servers: str = "localhost:29092",
        group_id: str = "notification-service"
    ):
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.consumer = None

    async def start(self):
        """Start the consumer."""
        self.consumer = AIOKafkaConsumer(
            "task-events",
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.group_id,
            value_deserializer=lambda v: json.loads(v.decode('utf-8')),
            auto_offset_reset="earliest"
        )
        await self.consumer.start()

    async def stop(self):
        """Stop the consumer."""
        if self.consumer:
            await self.consumer.stop()

    async def consume(self, handler):
        """Consume messages and pass to handler."""
        async for msg in self.consumer:
            await handler(msg.topic, msg.value)

# Usage
async def handle_event(topic: str, event: dict):
    print(f"Received {event['event_type']} from {topic}")
    if event["event_type"] == "task.created":
        # Send notification
        pass

consumer = TaskEventConsumer()
await consumer.start()
await consumer.consume(handle_event)
```

## Example 7: Installation Commands

```bash
# Install Strimzi operator
kubectl create namespace kafka
kubectl create -f 'https://strimzi.io/install/latest?namespace=kafka' -n kafka

# Wait for operator
kubectl wait deployment/strimzi-cluster-operator \
  --for=condition=available \
  --timeout=300s \
  -n kafka

# Apply Kafka cluster
kubectl apply -f kafka/kafka-cluster-minikube.yaml

# Wait for Kafka to be ready
kubectl wait kafka/todo-kafka \
  --for=condition=Ready \
  --timeout=300s \
  -n kafka

# Apply topics
kubectl apply -f kafka/kafka-topics.yaml

# Verify
kubectl get kafka -n kafka
kubectl get kafkatopic -n kafka
```

## Example 8: Redpanda Cloud Configuration

```yaml
# dapr-components/pubsub-redpanda.yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: taskpubsub
  namespace: todo-app
spec:
  type: pubsub.kafka
  version: v1
  metadata:
    - name: brokers
      secretKeyRef:
        name: redpanda-secrets
        key: brokers
    - name: authType
      value: "password"
    - name: saslUsername
      secretKeyRef:
        name: redpanda-secrets
        key: username
    - name: saslPassword
      secretKeyRef:
        name: redpanda-secrets
        key: password
    - name: saslMechanism
      value: "SCRAM-SHA-256"
    - name: tls
      value: "true"
    - name: consumerGroup
      value: "todo-consumer-group"
```
