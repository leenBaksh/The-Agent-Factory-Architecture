"""
Skills FastAPI Router

Exposes skills endpoints for:
- Listing available skills
- Executing specific skills
- Skill health checks
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from app.skills import (
    SkillContext,
    SkillResult,
    get_registry,
    initialize_skills,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/skills", tags=["Skills"])


@router.get("")
async def list_skills() -> dict[str, Any]:
    """List all available skills"""
    registry = get_registry()
    skills = registry.list_skills()
    
    return {
        "skills": skills,
        "total": len(skills),
    }


@router.get("/initialize")
async def initialize_skills_endpoint() -> dict[str, Any]:
    """Initialize/reload skills registry"""
    registry = initialize_skills()
    
    return {
        "status": "initialized",
        "skills_count": len(registry.skills),
    }


@router.post("/execute")
async def execute_skill(
    skill_id: str,
    conversation_id: str,
    customer_id: str,
    message_id: str,
    channel: str,
    content: str,
    sentiment_score: float = 0.5,
    ticket_id: str | None = None,
) -> dict[str, Any]:
    """
    Execute a specific skill.
    
    Args:
        skill_id: ID of the skill to execute
        conversation_id: Conversation identifier
        customer_id: Customer identifier
        message_id: Message identifier
        channel: Communication channel
        content: Message content
        sentiment_score: Message sentiment (0-1)
        ticket_id: Optional ticket ID
        
    Returns:
        Skill execution result
    """
    registry = get_registry()
    
    context = SkillContext(
        conversation_id=conversation_id,
        customer_id=customer_id,
        message_id=message_id,
        channel=channel,
        content=content,
        sentiment_score=sentiment_score,
        ticket_id=ticket_id,
    )
    
    result = await registry.execute_skill(skill_id, context)
    
    return {
        "success": result.success,
        "skill_id": result.skill_id,
        "output": result.output,
        "handoff_to": result.handoff_to,
        "handoff_reason": result.handoff_reason,
        "error": result.error,
        "metadata": result.metadata,
    }


@router.post("/auto-execute")
async def auto_execute_skill(
    conversation_id: str,
    customer_id: str,
    message_id: str,
    channel: str,
    content: str,
    sentiment_score: float = 0.5,
    ticket_id: str | None = None,
    exclude_skills: list[str] | None = None,
) -> dict[str, Any]:
    """
    Automatically find and execute the best matching skill.
    
    Args:
        conversation_id: Conversation identifier
        customer_id: Customer identifier
        message_id: Message identifier
        channel: Communication channel
        content: Message content
        sentiment_score: Message sentiment (0-1)
        ticket_id: Optional ticket ID
        exclude_skills: Skills to exclude from matching
        
    Returns:
        Skill execution result
    """
    registry = get_registry()
    
    context = SkillContext(
        conversation_id=conversation_id,
        customer_id=customer_id,
        message_id=message_id,
        channel=channel,
        content=content,
        sentiment_score=sentiment_score,
        ticket_id=ticket_id,
    )
    
    result = await registry.auto_execute(content, context, exclude_skills)
    
    return {
        "success": result.success,
        "skill_id": result.skill_id,
        "output": result.output,
        "handoff_to": result.handoff_to,
        "handoff_reason": result.handoff_reason,
        "error": result.error,
        "metadata": result.metadata,
    }


@router.get("/health")
async def skills_health() -> dict[str, Any]:
    """Skills system health check"""
    registry = get_registry()
    
    return {
        "status": "healthy",
        "skills_loaded": len(registry.skills),
        "initialized": registry._initialized,
    }
