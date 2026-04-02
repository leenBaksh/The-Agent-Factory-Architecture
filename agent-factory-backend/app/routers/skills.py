"""
Skills Router - List available skills.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


async def list_all_skills() -> list[dict[str, Any]]:
    """List all available skills."""
    
    # Mock skills data
    return [
        {
            "id": "customer-support",
            "name": "Customer Support",
            "description": "Handle customer inquiries and support tickets",
            "version": "1.0.0",
        },
        {
            "id": "billing",
            "name": "Billing",
            "description": "Process billing inquiries and payment issues",
            "version": "1.0.0",
        },
        {
            "id": "technical",
            "name": "Technical Support",
            "description": "Handle technical issues and troubleshooting",
            "version": "1.0.0",
        },
        {
            "id": "sales",
            "name": "Sales",
            "description": "Process sales inquiries and lead qualification",
            "version": "1.0.0",
        },
    ]


async def get_skill_by_id(skill_id: str) -> dict[str, Any]:
    """Get a specific skill."""
    
    skills = await list_all_skills()
    for skill in skills:
        if skill["id"] == skill_id:
            return skill
    
    return {"error": f"Skill {skill_id} not found"}
