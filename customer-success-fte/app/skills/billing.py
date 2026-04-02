"""
Billing Support Skill Implementation

Handles payment, subscription, invoicing, and refund-related inquiries.
"""

import logging
from typing import Any

from app.skills import BaseSkill, SkillContext, SkillPriority, SkillResult, SkillTrigger

logger = logging.getLogger(__name__)


class BillingSkill(BaseSkill):
    """Billing Support skill for payment and subscription inquiries"""
    
    def __init__(self):
        super().__init__()
        self.skill_id = "billing-support"
        self.version = "1.0.0"
        self.priority = SkillPriority.HIGH
        self.description = "Handles payment, subscription, invoicing, and refund inquiries"
        self.tools = [
            "get_billing_info",
            "get_subscription_status",
            "update_payment_method",
            "process_refund",
            "change_subscription",
            "send_invoice",
            "create_billing_ticket",
            "escalate_to_billing_team",
        ]
    
    def get_trigger(self) -> SkillTrigger:
        return SkillTrigger(
            keywords=[
                "billing",
                "payment",
                "invoice",
                "refund",
                "charge",
                "subscription",
                "cancel",
                "upgrade",
                "downgrade",
                "plan",
                "pricing",
                "cost",
                "price",
                "credit card",
                "failed payment",
            ],
            intents=[
                "payment_issue",
                "refund_request",
                "subscription_change",
                "invoice_request",
                "pricing_inquiry",
            ],
            patterns=[
                "i want to cancel",
                "how do i upgrade",
                "where is my invoice",
                "i was charged",
                "refund my",
                "payment failed",
            ],
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute billing support skill"""
        try:
            logger.info(f"Executing billing skill: conversation={context.conversation_id}")
            
            # Step 1: Get billing information
            billing_info = await self._get_billing_info(context.customer_id)
            
            # Step 2: Identify the billing intent
            intent = self._identify_intent(context.content)
            
            # Step 3: Handle based on intent
            if intent == "refund_request":
                return await self._handle_refund(context, billing_info)
            elif intent == "subscription_change":
                return await self._handle_subscription_change(context, billing_info)
            elif intent == "payment_issue":
                return await self._handle_payment_issue(context, billing_info)
            elif intent == "invoice_request":
                return await self._handle_invoice_request(context, billing_info)
            elif intent == "pricing_inquiry":
                return await self._handle_pricing_inquiry(context, billing_info)
            else:
                return await self._handle_general_billing(context, billing_info)
                
        except Exception as e:
            logger.exception("Billing skill failed")
            return SkillResult(
                success=False,
                skill_id=self.skill_id,
                output="",
                error=str(e),
            )
    
    async def _get_billing_info(self, customer_id: str) -> dict[str, Any]:
        """Get customer billing information"""
        # In production, this would query the billing system
        return {
            "customer_id": customer_id,
            "plan": "pro",
            "status": "active",
            "next_billing_date": "2024-02-15",
            "payment_method": "card_ending_4242",
        }
    
    def _identify_intent(self, content: str) -> str:
        """Identify the billing intent from content"""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ["refund", "money back", "chargeback"]):
            return "refund_request"
        elif any(word in content_lower for word in ["upgrade", "downgrade", "cancel", "change plan"]):
            return "subscription_change"
        elif any(word in content_lower for word in ["payment failed", "declined", "card error"]):
            return "payment_issue"
        elif any(word in content_lower for word in ["invoice", "receipt", "billing statement"]):
            return "invoice_request"
        elif any(word in content_lower for word in ["pricing", "cost", "how much", "price"]):
            return "pricing_inquiry"
        else:
            return "general_billing"
    
    async def _handle_refund(self, context: SkillContext, billing_info: dict) -> SkillResult:
        """Handle refund request"""
        # Check refund eligibility
        eligible = await self._check_refund_eligibility(context.customer_id)
        
        if eligible:
            # Process refund
            refund_id = await self._process_refund(context.customer_id)
            return SkillResult(
                success=True,
                skill_id=self.skill_id,
                output=f"Your refund has been processed. Reference ID: {refund_id}. "
                       f"You should see the credit in 5-7 business days.",
                metadata={"refund_id": refund_id},
            )
        else:
            # Escalate for exception review
            return SkillResult(
                success=True,
                skill_id=self.skill_id,
                output="I understand you're requesting a refund. Let me connect you with "
                       "our billing team who can review your specific situation.",
                handoff_to="billing_team",
                handoff_reason="Refund exception review required",
            )
    
    async def _handle_subscription_change(
        self, context: SkillContext, billing_info: dict
    ) -> SkillResult:
        """Handle subscription change request"""
        content = context.content.lower()
        
        if "cancel" in content:
            # Handle cancellation
            return await self._handle_cancellation(context, billing_info)
        elif "upgrade" in content:
            # Handle upgrade
            return await self._handle_upgrade(context, billing_info)
        else:
            # General subscription change
            return SkillResult(
                success=True,
                skill_id=self.skill_id,
                output="I can help you change your subscription. What specific change "
                       "would you like to make? You can upgrade, downgrade, or cancel your plan.",
            )
    
    async def _handle_payment_issue(
        self, context: SkillContext, billing_info: dict
    ) -> SkillResult:
        """Handle payment issue"""
        # Update payment method or retry payment
        return SkillResult(
            success=True,
            skill_id=self.skill_id,
            output="I can help you resolve the payment issue. Please use this secure link "
                   "to update your payment method: [SECURE_PAYMENT_LINK]",
            metadata={"action_required": "update_payment"},
        )
    
    async def _handle_invoice_request(
        self, context: SkillContext, billing_info: dict
    ) -> SkillResult:
        """Handle invoice request"""
        # Send invoice
        invoice_sent = await self._send_invoice(context.customer_id)
        return SkillResult(
            success=True,
            skill_id=self.skill_id,
            output=f"Your invoice has been sent to your registered email address.",
            metadata={"invoice_sent": invoice_sent},
        )
    
    async def _handle_pricing_inquiry(
        self, context: SkillContext, billing_info: dict
    ) -> SkillResult:
        """Handle pricing inquiry"""
        # Provide pricing information
        return SkillResult(
            success=True,
            skill_id=self.skill_id,
            output="Here are our current plans:\n"
                   "- Free: Basic features\n"
                   "- Pro: $29/month - Full features\n"
                   "- Business: $99/month - Advanced features + priority support\n"
                   "- Enterprise: Custom pricing\n\n"
                   "Would you like to upgrade your current plan?",
        )
    
    async def _handle_general_billing(
        self, context: SkillContext, billing_info: dict
    ) -> SkillResult:
        """Handle general billing inquiry"""
        return SkillResult(
            success=True,
            skill_id=self.skill_id,
            output=f"Your current plan is {billing_info.get('plan', 'unknown')}. "
                   f"Next billing date: {billing_info.get('next_billing_date', 'unknown')}. "
                   f"How can I help you with your billing?",
        )
    
    async def _check_refund_eligibility(self, customer_id: str) -> bool:
        """Check if customer is eligible for refund"""
        # In production, check billing system
        # For now, return mock result
        return True
    
    async def _process_refund(self, customer_id: str) -> str:
        """Process refund"""
        import uuid
        return f"REF-{uuid.uuid4().hex[:8].upper()}"
    
    async def _handle_cancellation(
        self, context: SkillContext, billing_info: dict
    ) -> SkillResult:
        """Handle cancellation request"""
        return SkillResult(
            success=True,
            skill_id=self.skill_id,
            output="I understand you'd like to cancel. Before you go, is there anything "
                   "we can help with? Your access will continue until the end of your "
                   "billing period. Would you like to proceed with cancellation?",
            metadata={"action": "cancellation_requested"},
        )
    
    async def _handle_upgrade(
        self, context: SkillContext, billing_info: dict
    ) -> SkillResult:
        """Handle upgrade request"""
        return SkillResult(
            success=True,
            skill_id=self.skill_id,
            output="Great! I can help you upgrade. Based on your current plan, "
                   "I recommend our Business plan. Would you like me to process the upgrade?",
            metadata={"action": "upgrade_requested"},
        )
    
    async def _send_invoice(self, customer_id: str) -> bool:
        """Send invoice to customer"""
        # In production, send via email
        return True
