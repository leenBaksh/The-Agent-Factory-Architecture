"""
Skills System for Customer Success Digital FTE

This module provides the skills registry and execution framework for domain-specific
capabilities. Skills extend the base agent functionality with specialized knowledge,
tools, and workflows.

Architecture:
- SkillRegistry: Central registry of all available skills
- BaseSkill: Abstract base class for all skills
- Skill instances: Concrete implementations for each domain
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class SkillPriority(Enum):
    """Skill priority levels"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


class SkillStatus(Enum):
    """Skill execution status"""
    INACTIVE = "inactive"
    ACTIVE = "active"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    HANDED_OFF = "handed_off"


@dataclass
class SkillTrigger:
    """Defines when a skill should be activated"""
    keywords: list[str] = field(default_factory=list)
    intents: list[str] = field(default_factory=list)
    min_sentiment: Optional[float] = None
    max_sentiment: Optional[float] = None
    patterns: list[str] = field(default_factory=list)
    
    def matches(self, text: str, sentiment: float = 0.5) -> bool:
        """Check if the trigger matches the input"""
        text_lower = text.lower()
        
        # Check keywords
        for keyword in self.keywords:
            if keyword.lower() in text_lower:
                return True
        
        # Check sentiment range
        if self.min_sentiment is not None and sentiment < self.min_sentiment:
            return True
        if self.max_sentiment is not None and sentiment > self.max_sentiment:
            return True
        
        # Check patterns (simple substring for now)
        for pattern in self.patterns:
            if pattern.lower() in text_lower:
                return True
        
        return False


@dataclass
class SkillContext:
    """Context passed to skill execution"""
    conversation_id: str
    customer_id: str
    message_id: str
    channel: str
    content: str
    sentiment_score: float = 0.5
    ticket_id: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SkillResult:
    """Result of skill execution"""
    success: bool
    skill_id: str
    output: str
    handoff_to: Optional[str] = None
    handoff_reason: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class BaseSkill(ABC):
    """
    Abstract base class for all skills.
    
    Each skill must implement:
    - get_trigger(): When this skill should activate
    - execute(): The skill's main logic
    """
    
    def __init__(self):
        self.skill_id: str = ""
        self.version: str = "1.0.0"
        self.priority: SkillPriority = SkillPriority.MEDIUM
        self.description: str = ""
        self.tools: list[str] = []
    
    @abstractmethod
    def get_trigger(self) -> SkillTrigger:
        """Return the trigger conditions for this skill"""
        pass
    
    @abstractmethod
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute the skill with the given context"""
        pass
    
    def should_handoff(self, result: SkillResult) -> bool:
        """Check if the result indicates a handoff is needed"""
        return result.handoff_to is not None
    
    def get_metadata(self) -> dict[str, Any]:
        """Get skill metadata"""
        return {
            "skill_id": self.skill_id,
            "version": self.version,
            "priority": self.priority.value,
            "description": self.description,
            "tools": self.tools,
        }


class SkillRegistry:
    """
    Central registry for all skills.
    
    Manages skill registration, discovery, and execution.
    """
    
    def __init__(self):
        self.skills: dict[str, BaseSkill] = {}
        self.triggers: list[tuple[str, BaseSkill]] = []
        self._initialized = False
    
    def register(self, skill: BaseSkill) -> None:
        """Register a skill"""
        if not skill.skill_id:
            raise ValueError("Skill must have a skill_id")
        
        self.skills[skill.skill_id] = skill
        self.triggers.append((skill.skill_id, skill))
        logger.info(f"Registered skill: {skill.skill_id} v{skill.version}")
    
    def unregister(self, skill_id: str) -> None:
        """Unregister a skill"""
        if skill_id in self.skills:
            del self.skills[skill_id]
            self.triggers = [(sid, s) for sid, s in self.triggers if sid != skill_id]
            logger.info(f"Unregistered skill: {skill_id}")
    
    def find_matching_skill(
        self,
        text: str,
        sentiment: float = 0.5,
        exclude: Optional[list[str]] = None,
    ) -> Optional[BaseSkill]:
        """
        Find the best matching skill for the input.
        
        Args:
            text: Input text to match
            sentiment: Sentiment score (0-1)
            exclude: Skill IDs to exclude from matching
            
        Returns:
            Best matching skill or None
        """
        exclude = exclude or []
        matches = []
        
        for skill_id, skill in self.triggers:
            if skill_id in exclude:
                continue
            
            trigger = skill.get_trigger()
            if trigger.matches(text, sentiment):
                matches.append((skill.priority.value, skill_id, skill))
        
        if not matches:
            return None
        
        # Sort by priority (lower value = higher priority)
        matches.sort(key=lambda x: x[0])
        return matches[0][2]
    
    def get_skill(self, skill_id: str) -> Optional[BaseSkill]:
        """Get a skill by ID"""
        return self.skills.get(skill_id)
    
    def list_skills(self) -> list[dict[str, Any]]:
        """List all registered skills"""
        return [skill.get_metadata() for skill in self.skills.values()]
    
    async def execute_skill(
        self,
        skill_id: str,
        context: SkillContext,
    ) -> SkillResult:
        """Execute a specific skill"""
        skill = self.get_skill(skill_id)
        
        if not skill:
            return SkillResult(
                success=False,
                skill_id=skill_id,
                output="",
                error=f"Skill not found: {skill_id}",
            )
        
        try:
            logger.info(f"Executing skill: {skill_id}")
            result = await skill.execute(context)
            return result
        except Exception as e:
            logger.exception(f"Skill execution failed: {skill_id}")
            return SkillResult(
                success=False,
                skill_id=skill_id,
                output="",
                error=str(e),
            )
    
    async def auto_execute(
        self,
        text: str,
        context: SkillContext,
        exclude: Optional[list[str]] = None,
    ) -> SkillResult:
        """
        Automatically find and execute the best matching skill.
        
        Args:
            text: Input text
            context: Skill context
            exclude: Skills to exclude
            
        Returns:
            Skill execution result
        """
        skill = self.find_matching_skill(text, context.sentiment_score, exclude)
        
        if not skill:
            return SkillResult(
                success=False,
                skill_id="none",
                output="",
                error="No matching skill found",
            )
        
        return await self.execute_skill(skill.skill_id, context)


# Global registry instance
_registry: Optional[SkillRegistry] = None


def get_registry() -> SkillRegistry:
    """Get the global skill registry"""
    global _registry
    if _registry is None:
        _registry = SkillRegistry()
    return _registry


def initialize_skills() -> SkillRegistry:
    """Initialize the skill registry with all available skills"""
    from .customer_support import CustomerSupportSkill
    from .billing import BillingSkill
    from .technical import TechnicalSkill
    from .sales import SalesSkill
    
    registry = get_registry()
    
    # Register all skills
    registry.register(CustomerSupportSkill())
    registry.register(BillingSkill())
    registry.register(TechnicalSkill())
    registry.register(SalesSkill())
    
    registry._initialized = True
    logger.info(f"Initialized {len(registry.skills)} skills")
    
    return registry
