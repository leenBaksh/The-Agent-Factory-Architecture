"""
Dapr configuration for Customer Success FTE

This module provides Dapr client configuration and utilities.
"""

import os
from dataclasses import dataclass

import dapr.clients


@dataclass
class DaprConfig:
    """Dapr configuration"""

    grpc_endpoint: str = os.getenv("DAPR_GRPC_ENDPOINT", "localhost:50001")
    http_endpoint: str = os.getenv("DAPR_HTTP_ENDPOINT", "http://localhost:3500")
    pubsub_name: str = os.getenv("DAPR_PUBSUB_NAME", "cs-pubsub")
    state_store_name: str = os.getenv("DAPR_STATE_STORE", "cs-state")
    workflow_runtime_id: str = os.getenv("DAPR_WORKFLOW_RUNTIME", "workflow-runtime")


def get_dapr_client() -> dapr.clients.DaprClient:
    """Get a Dapr client instance"""
    config = DaprConfig()
    return dapr.clients.DaprClient(
        grpc_endpoint=config.grpc_endpoint,
        http_endpoint=config.http_endpoint,
    )


def publish_event(
    pubsub_name: str, topic: str, data: dict, metadata: dict | None = None
) -> bool:
    """Publish an event to a Dapr pubsub topic"""
    client = get_dapr_client()

    try:
        client.publish_event(
            pubsub_name=pubsub_name,
            topic_name=topic,
            data=data,
            data_content_type="application/json",
            metadata=metadata,
        )
        return True
    except Exception as e:
        print(f"Failed to publish event: {e}")
        return False


def save_state(store_name: str, key: str, value: dict) -> bool:
    """Save state to a Dapr state store"""
    client = get_dapr_client()

    try:
        client.save_state(store_name=store_name, key=key, value=value)
        return True
    except Exception as e:
        print(f"Failed to save state: {e}")
        return False


def get_state(store_name: str, key: str) -> dict | None:
    """Get state from a Dapr state store"""
    client = get_dapr_client()

    try:
        result = client.get_state(store_name=store_name, key=key)
        if result.data:
            import json

            return json.loads(result.data)
        return None
    except Exception as e:
        print(f"Failed to get state: {e}")
        return None


def invoke_binding(
    binding_name: str, operation: str, data: dict | None = None
) -> bytes | None:
    """Invoke a Dapr binding"""
    client = get_dapr_client()

    try:
        result = client.invoke_binding(
            binding_name=binding_name,
            operation=operation,
            data=data,
        )
        return result.data
    except Exception as e:
        print(f"Failed to invoke binding: {e}")
        return None
