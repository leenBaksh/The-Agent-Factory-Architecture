"""
Customer Support Skill Implementation

Handles general customer inquiries, product questions, and support requests.
"""

import logging
from typing import Any

from app.skills import BaseSkill, SkillContext, SkillPriority, SkillResult, SkillTrigger

logger = logging.getLogger(__name__)


class CustomerSupportSkill(BaseSkill):
    """Customer Support skill for general inquiries and support"""
    
    def __init__(self):
        super().__init__()
        self.skill_id = "customer-support"
        self.version = "1.0.0"
        self.priority = SkillPriority.MEDIUM
        self.description = "Handles general customer inquiries, product questions, and support requests"
        self.tools = [
            "search_knowledge_base",
            "get_customer_history",
            "create_ticket",
            "send_response",
            "resolve_ticket",
            "escalate_to_human",
        ]
    
    def get_trigger(self) -> SkillTrigger:
        return SkillTrigger(
            keywords=[
                "help",
                "support",
                "question",
                "issue",
                "problem",
                "how to",
                "cannot",
                "can't",
                "error",
                "not working",
                "confused",
                "stuck",
            ],
            intents=[
                "product_inquiry",
                "technical_assistance",
                "account_help",
                "feature_request",
                "bug_report",
            ],
            patterns=[
                "how do i",
                "i need help",
                "can you help",
                "i'm trying to",
                "where can i",
            ],
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute customer support skill"""
        try:
            logger.info(
                f"Executing customer support skill: conversation={context.conversation_id}"
            )
            
            # Step 1: Search knowledge base
            kb_results = await self._search_knowledge_base(context.content)
            
            # Step 2: Get customer history
            history = await self._get_customer_history(context.customer_id)
            
            # Step 3: Determine if ticket is needed
            needs_ticket = self._requires_ticket(context.content, kb_results)
            
            # Step 4: Generate response
            response = await self._generate_response(
                content=context.content,
                kb_results=kb_results,
                history=history,
                needs_ticket=needs_ticket,
            )
            
            # Step 5: Create ticket if needed
            ticket_id = None
            if needs_ticket:
                ticket_id = await self._create_ticket(context, kb_results)
            
            # Step 6: Check if escalation is needed
            if self._requires_escalation(context.content, context.sentiment_score):
                return SkillResult(
                    success=True,
                    skill_id=self.skill_id,
                    output=response,
                    handoff_to="human_agent",
                    handoff_reason="Customer requires human assistance",
                    metadata={
                        "ticket_id": ticket_id,
                        "kb_results": len(kb_results),
                        "sentiment": context.sentiment_score,
                    },
                )
            
            return SkillResult(
                success=True,
                skill_id=self.skill_id,
                output=response,
                metadata={
                    "ticket_id": ticket_id,
                    "kb_results": len(kb_results),
                    "sentiment": context.sentiment_score,
                },
            )
            
        except Exception as e:
            logger.exception("Customer support skill failed")
            return SkillResult(
                success=False,
                skill_id=self.skill_id,
                output="",
                error=str(e),
            )
    
    async def _search_knowledge_base(self, query: str) -> list[dict[str, Any]]:
        """Search knowledge base for relevant articles"""
        # In production, this would call the actual KB service
        # For now, return mock results
        return [
            {"id": "KB-001", "title": "Getting Started Guide", "relevance": 0.95},
            {"id": "KB-002", "title": "Common Issues", "relevance": 0.85},
        ]
    
    async def _get_customer_history(self, customer_id: str) -> dict[str, Any]:
        """Get customer's interaction history"""
        # In production, this would query the database
        return {
            "customer_id": customer_id,
            "total_tickets": 3,
            "last_contact": "2024-01-10",
            "plan": "pro",
        }
    
    def _requires_ticket(self, content: str, kb_results: list) -> bool:
        """Determine if a ticket should be created"""
        # Create ticket if no good KB match or issue seems complex
        if not kb_results:
            return True
        
        best_match = max(kb_results, key=lambda x: x.get("relevance", 0))
        return best_match.get("relevance", 0) < 0.7
    
    async def _generate_response(
        self,
        content: str,
        kb_results: list,
        history: dict,
        needs_ticket: bool,
    ) -> str:
        """Generate a response to the customer"""
        response_parts = []
        
        # Acknowledge the inquiry
        response_parts.append("Thank you for contacting support.")
        
        # Provide KB-based guidance
        if kb_results:
            response_parts.append("\nBased on your inquiry, here are some helpful resources:")
            for article in kb_results[:3]:
                response_parts.append(f"- {article['title']}")
        
        # Mention ticket creation
        if needs_ticket:
            response_parts.append(
                "\nI've created a support ticket to track this issue. "
                "Our team will follow up shortly."
            )
        
        # Close with offer for further help
        response_parts.append("\nIs there anything else I can help you with?")
        
        return "\n".join(response_parts)
    
    async def _create_ticket(self, context: SkillContext, kb_results: list) -> str:
        """Create a support ticket"""
        # In production, this would call the ticket service
        import uuid
        ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"
        logger.info(f"Created ticket {ticket_id} for conversation {context.conversation_id}")
        return ticket_id
    
    def _requires_escalation(self, content: str, sentiment: float) -> bool:
        """Determine if escalation to human is needed"""
        # Escalate if:
        # - Customer is highly frustrated (low sentiment)
        # - Content contains escalation keywords
        escalation_keywords = [
            "speak to manager",
            "human agent",
            "real person",
            "complaint",
            "unacceptable",
            "terrible",
        ]
        
        content_lower = content.lower()
        if any(keyword in content_lower for keyword in escalation_keywords):
            return True
        
        if sentiment < 0.3:
            return True
        
        return False
