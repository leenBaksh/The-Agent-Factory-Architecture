"""
FTE Router - Manage FTE instances.
"""

import logging
from typing import Any

from app.services.fte_registry import fte_registry

logger = logging.getLogger(__name__)


async def list_all_ftes() -> list[dict[str, Any]]:
    """List all registered FTE instances."""
    return list(fte_registry.instances.values())


async def create_new_fte(fte_data: dict) -> dict[str, Any]:
    """Create a new FTE instance."""
    fte_id = fte_data.get("id")
    if not fte_id:
        return {"error": "FTE ID is required"}
    
    await fte_registry.register(fte_data)
    return {"status": "created", "fte_id": fte_id}


async def get_fte_by_id(fte_id: str) -> dict[str, Any]:
    """Get a specific FTE instance."""
    fte = fte_registry.instances.get(fte_id)
    if not fte:
        return {"error": f"FTE {fte_id} not found"}
    return fte


async def delete_fte_by_id(fte_id: str) -> dict[str, Any]:
    """Delete an FTE instance."""
    if fte_id in fte_registry.instances:
        await fte_registry.unregister(fte_id)
        return {"status": "deleted", "fte_id": fte_id}
    return {"error": f"FTE {fte_id} not found"}
