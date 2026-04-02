"""
Technical Support Skill Implementation

Handles API issues, integrations, advanced troubleshooting, and developer inquiries.
"""

import logging
import re
from typing import Any, Optional

from app.skills import BaseSkill, SkillContext, SkillPriority, SkillResult, SkillTrigger

logger = logging.getLogger(__name__)


class TechnicalSkill(BaseSkill):
    """Technical Support skill for API and integration issues"""
    
    def __init__(self):
        super().__init__()
        self.skill_id = "technical-support"
        self.version = "1.0.0"
        self.priority = SkillPriority.HIGH
        self.description = "Handles API issues, integrations, and advanced troubleshooting"
        self.tools = [
            "search_api_docs",
            "get_error_code_info",
            "check_api_status",
            "analyze_logs",
            "get_rate_limit_info",
            "create_tech_ticket",
            "escalate_to_engineering",
            "get_integration_guide",
        ]
    
    def get_trigger(self) -> SkillTrigger:
        return SkillTrigger(
            keywords=[
                "api",
                "integration",
                "webhook",
                "sdk",
                "authentication",
                "token",
                "error code",
                "debug",
                "logs",
                "performance",
                "slow",
                "timeout",
                "developer",
                "code",
                "endpoint",
                "request",
                "response",
                "401",
                "403",
                "500",
                "rate limit",
            ],
            intents=[
                "api_help",
                "integration_issue",
                "performance_problem",
                "advanced_configuration",
                "developer_inquiry",
            ],
            patterns=[
                "i'm getting error",
                "api returns",
                "http 4",
                "http 5",
                "stack trace",
                "exception:",
                "traceback",
            ],
        )
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute technical support skill"""
        try:
            logger.info(f"Executing technical skill: conversation={context.conversation_id}")
            
            # Step 1: Identify technical issue type
            issue_type = self._identify_issue_type(context.content)
            
            # Step 2: Handle based on issue type
            if issue_type == "api_authentication":
                return await self._handle_auth_issue(context)
            elif issue_type == "api_error":
                return await self._handle_api_error(context)
            elif issue_type == "integration":
                return await self._handle_integration(context)
            elif issue_type == "performance":
                return await self._handle_performance(context)
            elif issue_type == "webhook":
                return await self._handle_webhook(context)
            elif issue_type == "rate_limit":
                return await self._handle_rate_limit(context)
            else:
                return await self._handle_general_technical(context)
                
        except Exception as e:
            logger.exception("Technical skill failed")
            return SkillResult(
                success=False,
                skill_id=self.skill_id,
                output="",
                error=str(e),
            )
    
    def _identify_issue_type(self, content: str) -> str:
        """Identify the type of technical issue"""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ["401", "403", "unauthorized", "authentication", "token", "api key"]):
            return "api_authentication"
        elif any(word in content_lower for word in ["500", "502", "503", "error code", "internal error"]):
            return "api_error"
        elif any(word in content_lower for word in ["integration", "connect", "third-party", "zapier"]):
            return "integration"
        elif any(word in content_lower for word in ["slow", "performance", "timeout", "latency"]):
            return "performance"
        elif "webhook" in content_lower:
            return "webhook"
        elif any(word in content_lower for word in ["rate limit", "429", "too many requests"]):
            return "rate_limit"
        else:
            return "general_technical"
    
    async def _handle_auth_issue(self, context: SkillContext) -> SkillResult:
        """Handle API authentication issues"""
        content = context.content.lower()
        
        # Check for common auth issues
        if "401" in content or "unauthorized" in content:
            return SkillResult(
                success=True,
                skill_id=self.skill_id,
                output="A 401 Unauthorized error typically means your API key is invalid or expired. "
                       "Please check:\n"
                       "1. Your API key is correctly copied (no extra spaces)\n"
                       "2. The API key hasn't expired\n"
                       "3. You're using the correct endpoint\n\n"
                       "Would you like me to help you regenerate your API key?",
                metadata={"issue": "auth_401"},
            )
        elif "403" in content or "forbidden" in content:
            return SkillResult(
                success=True,
                skill_id=self.skill_id,
                output="A 403 Forbidden error means your API key is valid but doesn't have "
                       "permission for this action. This could be due to:\n"
                       "1. Plan limitations\n"
                       "2. Endpoint restrictions\n"
                       "3. IP whitelist requirements\n\n"
                       "Let me check your account permissions.",
                metadata={"issue": "auth_403"},
            )
        else:
            return SkillResult(
                success=True,
                skill_id=self.skill_id,
                output="I can help with your authentication issue. Could you share:\n"
                       "1. The exact error message\n"
                       "2. The endpoint you're calling\n"
                       "3. Your authentication method (API key, OAuth, etc.)",
            )
    
    async def _handle_api_error(self, context: SkillContext) -> SkillResult:
        """Handle API error codes"""
        # Extract error code from content
        error_code = self._extract_error_code(context.content)
        
        if error_code:
            error_info = await self._get_error_info(error_code)
            return SkillResult(
                success=True,
                skill_id=self.skill_id,
                output=f"Error {error_code}: {error_info.get('description', 'Unknown error')}\n\n"
                       f"Solution: {error_info.get('solution', 'Please contact support')}",
                metadata={"error_code": error_code},
            )
        else:
            return SkillResult(
                success=True,
                skill_id=self.skill_id,
                output="I can help troubleshoot your API error. Could you share:\n"
                       "1. The exact error code or message\n"
                       "2. The endpoint you're calling\n"
                       "3. A sample of your request (with sensitive data removed)",
                handoff_to="engineering",
                handoff_reason="Specific error code not identified",
            )
    
    async def _handle_integration(self, context: SkillContext) -> SkillResult:
        """Handle integration issues"""
        # Identify integration platform
        platform = self._identify_platform(context.content)
        
        if platform:
            guide = await self._get_integration_guide(platform)
            return SkillResult(
                success=True,
                skill_id=self.skill_id,
                output=f"I can help with your {platform} integration.\n\n"
                       f"Here's our integration guide: {guide}\n\n"
                       f"Common issues:\n"
                       f"1. Verify your credentials\n"
                       f"2. Check webhook URLs are publicly accessible\n"
                       f"3. Ensure proper event subscriptions\n\n"
                       f"What specific issue are you encountering?",
                metadata={"platform": platform},
            )
        else:
            return SkillResult(
                success=True,
                skill_id=self.skill_id,
                output="I can help with your integration. Which platform are you integrating with? "
                       "(e.g., Slack, Zapier, custom webhook, etc.)",
            )
    
    async def _handle_performance(self, context: SkillContext) -> SkillResult:
        """Handle performance issues"""
        return SkillResult(
            success=True,
            skill_id=self.skill_id,
            output="I understand you're experiencing performance issues. Let me help:\n\n"
                   "1. Check our status page: status.example.com\n"
                   "2. Verify your network connection\n"
                   "3. Try implementing retry logic with exponential backoff\n"
                   "4. Consider using our CDN endpoints\n\n"
                   "Are you seeing slow responses consistently or intermittently?",
            metadata={"issue": "performance"},
        )
    
    async def _handle_webhook(self, context: SkillContext) -> SkillResult:
        """Handle webhook issues"""
        return SkillResult(
            success=True,
            skill_id=self.skill_id,
            output="For webhook issues, let's troubleshoot:\n\n"
                   "1. Verify your webhook URL is publicly accessible\n"
                   "2. Check that it returns 2xx status codes\n"
                   "3. Ensure SSL is properly configured\n"
                   "4. Review webhook delivery logs in your dashboard\n\n"
                   "Would you like me to check your webhook delivery logs?",
            metadata={"issue": "webhook"},
        )
    
    async def _handle_rate_limit(self, context: SkillContext) -> SkillResult:
        """Handle rate limit issues"""
        return SkillResult(
            success=True,
            skill_id=self.skill_id,
            output="You're hitting rate limits. Here's how to resolve this:\n\n"
                   "1. Implement exponential backoff in your retries\n"
                   "2. Cache responses where possible\n"
                   "3. Use bulk endpoints instead of individual calls\n"
                   "4. Consider upgrading your plan for higher limits\n\n"
                   "Your current limit: 100 requests/minute\n"
                   "Would you like information about our higher-tier plans?",
            metadata={"issue": "rate_limit"},
        )
    
    async def _handle_general_technical(self, context: SkillContext) -> SkillResult:
        """Handle general technical inquiry"""
        return SkillResult(
            success=True,
            skill_id=self.skill_id,
            output="I can help with your technical question. Could you provide more details:\n\n"
                   "1. What are you trying to accomplish?\n"
                   "2. What have you tried so far?\n"
                   "3. What's the expected vs actual behavior?\n\n"
                   "If you have code or error messages, please share them (with sensitive data removed).",
            handoff_to="engineering",
            handoff_reason="Complex technical issue requiring engineering review",
        )
    
    def _extract_error_code(self, content: str) -> Optional[str]:
        """Extract error code from content"""
        import re
        # Look for patterns like "Error 404", "HTTP 500", "401 Unauthorized"
        patterns = [
            r"[Ee]rror\s*(\d{3})",
            r"HTTP\s*(\d{3})",
            r"\b(\d{3})\b",
        ]
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        return None
    
    async def _get_error_info(self, error_code: str) -> dict[str, str]:
        """Get error code information"""
        # In production, query error database
        error_db = {
            "400": {"description": "Bad Request", "solution": "Check your request format and parameters"},
            "401": {"description": "Unauthorized", "solution": "Verify your API key"},
            "403": {"description": "Forbidden", "solution": "Check your permissions"},
            "404": {"description": "Not Found", "solution": "Verify the endpoint URL"},
            "429": {"description": "Too Many Requests", "solution": "Implement rate limiting"},
            "500": {"description": "Internal Server Error", "solution": "Contact support with request ID"},
            "502": {"description": "Bad Gateway", "solution": "Retry after a few seconds"},
            "503": {"description": "Service Unavailable", "solution": "Check status page"},
        }
        return error_db.get(error_code, {"description": "Unknown Error", "solution": "Contact support"})
    
    def _identify_platform(self, content: str) -> Optional[str]:
        """Identify integration platform from content"""
        platforms = ["slack", "zapier", "teams", "webhook", "salesforce", "hubspot"]
        content_lower = content.lower()
        for platform in platforms:
            if platform in content_lower:
                return platform
        return None
    
    async def _get_integration_guide(self, platform: str) -> str:
        """Get integration guide URL"""
        return f"https://docs.example.com/integrations/{platform}"
