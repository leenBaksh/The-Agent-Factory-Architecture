"""
FTE Registry Service - Manages registered FTE instances.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class FTERegistry:
    """Registry for FTE instances."""
    
    def __init__(self):
        self.instances: dict[str, dict[str, Any]] = {}
    
    async def register(self, fte_data: dict[str, Any]) -> bool:
        """Register an FTE instance."""
        fte_id = fte_data.get("id")
        if not fte_id:
            logger.error("FTE registration failed: missing ID")
            return False
        
        self.instances[fte_id] = fte_data
        logger.info(f"Registered FTE: {fte_id}")
        return True
    
    async def unregister(self, fte_id: str) -> bool:
        """Unregister an FTE instance."""
        if fte_id in self.instances:
            del self.instances[fte_id]
            logger.info(f"Unregistered FTE: {fte_id}")
            return True
        return False
    
    async def clear(self) -> None:
        """Clear all registered FTEs."""
        self.instances.clear()
        logger.info("Cleared all FTE registrations")
    
    def get(self, fte_id: str) -> dict[str, Any] | None:
        """Get an FTE by ID."""
        return self.instances.get(fte_id)
    
    @property
    def count(self) -> int:
        """Get count of registered FTEs."""
        return len(self.instances)


# Global registry instance
fte_registry = FTERegistry()
