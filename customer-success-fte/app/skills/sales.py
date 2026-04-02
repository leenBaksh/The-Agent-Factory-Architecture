"""
Sales Support Skill Implementation

Handles pre-sales inquiries, pricing, upgrades, and enterprise sales assistance.
"""

import logging
from typing import Any

from app.skills import BaseSkill, SkillContext, SkillPriority, SkillResult, SkillTrigger

logger = logging.getLogger(__name__)


class SalesSkill(BaseSkill):
    """Sales Support skill for pre-sales and upgrade inquiries"""
    
    def __init__(self):
        super().__init__()
        self.skill_id = "sales-support"
        self.version = "1.0.0"
        self.priority = SkillPriority.MEDIUM
        self.description = "Handles pre-sales inquiries, pricing, and upgrade assistance"
        self.tools = [
            "get_pricing_info",
            "compare_plans",
            "check_upgrade_options",
            "get_enterprise_info",
            "extend_trial",
            "create_sales_lead",
            "schedule_demo",
            "escalate_to_sales",
        ]
    
    def get_trigger(self) -> SkillTrigger:
        return SkillTrigger(
            keywords=[
                "pricing",
                "cost",
                "upgrade",
                "enterprise",
                "demo",
                "trial",
                "features",
                "plans",
                "subscription",
                "buy",
                "purchase",
                "quote",
                "proposal",
                "contract",
                "volume discount",
                "team plan",
                "seats",
                "users",
            ],
            intents=[
                "pre_sales_inquiry",
                "upgrade_consideration",
                "feature_comparison",
                "enterprise_requirements",
                "trial_extension",
            ],
            patterns=[
                "how much does",
                "what's the price",
                "i want to upgrade",
                "difference between",
                "enterprise features",
                "can i get a demo",
            ],
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute sales support skill"""
        try:
            logger.info(f"Executing sales skill: conversation={context.conversation_id}")
            
            # Step 1: Identify sales intent
            intent = self._identify_intent(context.content)
            
            # Step 2: Get customer info if existing customer
            customer_info = await self._get_customer_info(context.customer_id)
            
            # Step 3: Handle based on intent
            if intent == "pricing_inquiry":
                return await self._handle_pricing(context, customer_info)
            elif intent == "upgrade":
                return await self._handle_upgrade(context, customer_info)
            elif intent == "enterprise":
                return await self._handle_enterprise(context, customer_info)
            elif intent == "demo":
                return await self._handle_demo(context, customer_info)
            elif intent == "trial":
                return await self._handle_trial(context, customer_info)
            elif intent == "comparison":
                return await self._handle_comparison(context, customer_info)
            else:
                return await self._handle_general_sales(context, customer_info)
                
        except Exception as e:
            logger.exception("Sales skill failed")
            return SkillResult(
                success=False,
                skill_id=self.skill_id,
                output="",
                error=str(e),
            )
    
    def _identify_intent(self, content: str) -> str:
        """Identify the sales intent from content"""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ["enterprise", "custom", "volume", "100+"]):
            return "enterprise"
        elif any(word in content_lower for word in ["demo", "walkthrough", "show me"]):
            return "demo"
        elif any(word in content_lower for word in ["trial", "trialing", "testing"]):
            return "trial"
        elif any(word in content_lower for word in ["upgrade", "switch", "move to"]):
            return "upgrade"
        elif any(word in content_lower for word in ["vs", "versus", "difference", "compare"]):
            return "comparison"
        elif any(word in content_lower for word in ["price", "cost", "how much", "pricing"]):
            return "pricing_inquiry"
        else:
            return "general_sales"
    
    async def _handle_pricing(self, context: SkillContext, customer_info: dict) -> SkillResult:
        """Handle pricing inquiry"""
        pricing = await self._get_pricing_info()
        
        return SkillResult(
            success=True,
            skill_id=self.skill_id,
            output="Here are our current plans:\n\n"
                   f"• **Free**: $0/month - {pricing['free']}\n"
                   f"• **Pro**: $29/month - {pricing['pro']}\n"
                   f"• **Business**: $99/month - {pricing['business']}\n"
                   f"• **Enterprise**: Custom - {pricing['enterprise']}\n\n"
                   "All plans include a 14-day free trial. Annual billing saves 20%!\n\n"
                   "Which plan sounds right for your needs?",
            metadata={"intent": "pricing"},
        )
    
    async def _handle_upgrade(self, context: SkillContext, customer_info: dict) -> SkillResult:
        """Handle upgrade inquiry"""
        current_plan = customer_info.get("plan", "free")
        
        if current_plan == "free":
            return SkillResult(
                success=True,
                skill_id=self.skill_id,
                output="Great choice! Upgrading from Free to Pro unlocks:\n\n"
                       "✓ Unlimited projects\n"
                       "✓ Advanced analytics\n"
                       "✓ Priority support\n"
                       "✓ API access\n\n"
                       "Would you like to upgrade to Pro ($29/month) or Business ($99/month)?\n\n"
                       "I can process the upgrade right away if you'd like!",
                metadata={"intent": "upgrade", "current_plan": current_plan},
            )
        elif current_plan == "pro":
            return SkillResult(
                success=True,
                skill_id=self.skill_id,
                output="Looking to upgrade to Business? You'll get:\n\n"
                       "✓ Everything in Pro\n"
                       "✓ Team collaboration (up to 10 users)\n"
                       "✓ Advanced integrations\n"
                       "✓ Dedicated support\n"
                       "✓ Custom reporting\n\n"
                       "Shall I process the upgrade to Business ($99/month)?",
                metadata={"intent": "upgrade", "current_plan": current_plan},
            )
        else:
            return SkillResult(
                success=True,
                skill_id=self.skill_id,
                output="I see you're on our Business plan. For Enterprise features like:\n\n"
                       "✓ Unlimited users\n"
                       "✓ Custom integrations\n"
                       "✓ Dedicated account manager\n"
                       "✓ SLA guarantees\n"
                       "✓ On-premise deployment\n\n"
                       "Let me connect you with our enterprise team for a custom quote.",
                handoff_to="sales_team",
                handoff_reason="Enterprise upgrade inquiry",
                metadata={"intent": "enterprise_upgrade"},
            )
    
    async def _handle_enterprise(self, context: SkillContext, customer_info: dict) -> SkillResult:
        """Handle enterprise inquiry"""
        # Qualify the lead
        qualification = await self._qualify_enterprise_lead(context.content)
        
        if qualification["high_value"]:
            # High-value lead - escalate to sales
            lead_id = await self._create_sales_lead(context, qualification)
            return SkillResult(
                success=True,
                skill_id=self.skill_id,
                output="Thank you for your interest in Enterprise! Based on your requirements, "
                       "I'd like to connect you with our enterprise sales team.\n\n"
                       "They'll provide:\n"
                       "• Custom pricing based on your needs\n"
                       "• Technical architecture review\n"
                       "• Security and compliance documentation\n"
                       "• Implementation planning\n\n"
                       f"Your reference ID: {lead_id}\n\n"
                       "A specialist will reach out within 24 hours.",
                handoff_to="sales_team",
                handoff_reason="High-value enterprise lead",
                metadata={"lead_id": lead_id, "qualification": qualification},
            )
        else:
            # Provide enterprise info
            return SkillResult(
                success=True,
                skill_id=self.skill_id,
                output="Our Enterprise plan includes:\n\n"
                       "✓ Unlimited users and projects\n"
                       "✓ Custom integrations and API access\n"
                       "✓ Dedicated account manager\n"
                       "✓ 99.9% SLA guarantee\n"
                       "✓ Priority 24/7 support\n"
                       "✓ Advanced security (SSO, SAML)\n"
                       "✓ On-premise deployment option\n"
                       "✓ Custom training and onboarding\n\n"
                       "Pricing is customized based on your needs. Would you like to schedule "
                       "a demo with our enterprise team?",
                metadata={"intent": "enterprise_info"},
            )
    
    async def _handle_demo(self, context: SkillContext, customer_info: dict) -> SkillResult:
        """Handle demo request"""
        demo_scheduled = await self._schedule_demo(context)
        
        if demo_scheduled:
            return SkillResult(
                success=True,
                skill_id=self.skill_id,
                output="Perfect! I've scheduled a demo for you.\n\n"
                       "You'll receive a calendar invite shortly with:\n"
                       "• Meeting link\n"
                       "• Agenda\n"
                       "• Pre-demo questionnaire\n\n"
                       "Our product specialist will tailor the demo to your specific use case. "
                       "Is there anything specific you'd like to see during the demo?",
                metadata={"demo_scheduled": True},
            )
        else:
            return SkillResult(
                success=True,
                skill_id=self.skill_id,
                output="I'd be happy to arrange a demo! Please use this link to schedule "
                       "at your convenience: [DEMO_SCHEDULING_LINK]\n\n"
                       "Demos typically last 30 minutes and cover:\n"
                       "• Product overview\n"
                       "• Features relevant to your use case\n"
                       "• Q&A session\n\n"
                       "What's the best email to send the invite to?",
                metadata={"demo_requested": True},
            )
    
    async def _handle_trial(self, context: SkillContext, customer_info: dict) -> SkillResult:
        """Handle trial inquiry"""
        if customer_info.get("on_trial"):
            # Trial extension request
            eligible = await self._check_trial_extension_eligibility(context.customer_id)
            if eligible:
                extended = await self._extend_trial(context.customer_id)
                return SkillResult(
                    success=True,
                    skill_id=self.skill_id,
                    output=f"Good news! I've extended your trial by 7 days. "
                           f"You now have access until {extended['new_end_date']}.\n\n"
                           "Would you like to see what features you haven't tried yet?",
                    metadata={"trial_extended": True},
                )
            else:
                return SkillResult(
                    success=True,
                    skill_id=self.skill_id,
                    output="I see you've already had a trial extension. Let me connect you "
                           "with our sales team to discuss plan options.",
                    handoff_to="sales_team",
                    handoff_reason="Trial extension - repeat request",
                )
        else:
            # New trial inquiry
            return SkillResult(
                success=True,
                skill_id=self.skill_id,
                output="Our 14-day free trial includes:\n\n"
                       "✓ Full access to Pro features\n"
                       "✓ No credit card required\n"
                       "✓ Cancel anytime\n\n"
                       "Would you like to start your trial now? I can set it up in seconds!",
                metadata={"trial_inquiry": True},
            )
    
    async def _handle_comparison(self, context: SkillContext, customer_info: dict) -> SkillResult:
        """Handle plan comparison request"""
        comparison = await self._get_plan_comparison()
        
        return SkillResult(
            success=True,
            skill_id=self.skill_id,
            output="Here's a comparison of our plans:\n\n"
                   f"{comparison}\n\n"
                   "Based on your needs, I'd recommend the **Pro** plan for most teams. "
                   "However, if you need team collaboration features, **Business** is worth it.\n\n"
                   "What's most important to you in a plan?",
            metadata={"intent": "comparison"},
        )
    
    async def _handle_general_sales(self, context: SkillContext, customer_info: dict) -> SkillResult:
        """Handle general sales inquiry"""
        return SkillResult(
            success=True,
            skill_id=self.skill_id,
            output="Thanks for your interest! I can help with:\n\n"
                   "• Pricing information\n"
                   "• Plan comparisons\n"
                   "• Upgrade assistance\n"
                   "• Enterprise inquiries\n"
                   "• Demo scheduling\n"
                   "• Trial information\n\n"
                   "What would you like to know?",
        )
    
    async def _get_pricing_info(self) -> dict[str, str]:
        """Get pricing information"""
        return {
            "free": "Basic features, 3 projects, community support",
            "pro": "Full features, unlimited projects, priority support, API access",
            "business": "Pro + team collaboration, advanced integrations, custom reporting",
            "enterprise": "Custom features, dedicated support, SLA, on-premise option",
        }
    
    async def _get_customer_info(self, customer_id: str) -> dict[str, Any]:
        """Get customer information"""
        # In production, query CRM
        return {
            "customer_id": customer_id,
            "plan": "free",
            "on_trial": False,
            "trial_end_date": None,
        }
    
    async def _qualify_enterprise_lead(self, content: str) -> dict[str, Any]:
        """Qualify enterprise lead"""
        # Simple qualification based on content
        high_value_indicators = ["100+", "1000+", "enterprise", "global", "fortune"]
        is_high_value = any(indicator in content.lower() for indicator in high_value_indicators)
        
        return {
            "high_value": is_high_value,
            "indicators": [i for i in high_value_indicators if i in content.lower()],
        }
    
    async def _create_sales_lead(self, context: SkillContext, qualification: dict) -> str:
        """Create sales lead in CRM"""
        import uuid
        lead_id = f"LEAD-{uuid.uuid4().hex[:8].upper()}"
        logger.info(f"Created sales lead {lead_id} for customer {context.customer_id}")
        return lead_id
    
    async def _schedule_demo(self, context: SkillContext) -> bool:
        """Schedule product demo"""
        # In production, integrate with calendar system
        return True
    
    async def _check_trial_extension_eligibility(self, customer_id: str) -> bool:
        """Check if customer is eligible for trial extension"""
        # In production, check database
        return True
    
    async def _extend_trial(self, customer_id: str) -> dict[str, Any]:
        """Extend customer trial"""
        from datetime import datetime, timedelta
        new_end = datetime.now() + timedelta(days=7)
        return {"new_end_date": new_end.strftime("%Y-%m-%d")}
    
    async def _get_plan_comparison(self) -> str:
        """Get plan comparison table"""
        return (
            "| Feature | Free | Pro | Business | Enterprise |\n"
            "|---------|------|-----|----------|------------|\n"
            "| Projects | 3 | ∞ | ∞ | ∞ |\n"
            "| Users | 1 | 3 | 10 | ∞ |\n"
            "| API Access | ✗ | ✓ | ✓ | ✓ |\n"
            "| Support | Community | Priority | Dedicated | 24/7 |\n"
            "| Analytics | Basic | Advanced | Custom | Custom |\n"
            "| Integrations | 3 | 10 | ∞ | Custom |"
        )
