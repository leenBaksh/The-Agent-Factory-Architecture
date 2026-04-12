"""
Jira Service

Provides programmatic access to Jira for:
- Creating Jira issues from customer tickets
- Syncing ticket status between FTE and Jira
- Querying Jira issue details and comments
- Receiving webhook updates from Jira
"""

import base64
import logging
from typing import Any, Optional

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


class JiraService:
    """Service for interacting with Jira REST API"""

    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.jira_url.rstrip("/")
        self.auth_header = self._build_auth_header()
        self.project_key = self.settings.jira_project_key
        self.enabled = self.settings.jira_enabled and bool(self.auth_header)

    def _build_auth_header(self) -> Optional[str]:
        """Build Basic Auth header for Jira API"""
        if not self.settings.jira_email or not self.settings.jira_api_token:
            return None
        
        credentials = f"{self.settings.jira_email}:{self.settings.jira_api_token}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    async def _request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[dict] = None,
    ) -> dict[str, Any]:
        """Make authenticated request to Jira API"""
        
        if not self.enabled:
            raise RuntimeError("Jira integration is not enabled")

        url = f"{self.base_url}/rest/api/3{endpoint}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=method,
                url=url,
                json=json_data,
                headers={
                    "Authorization": self.auth_header,
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            
            if response.text:
                return response.json()
            return {}

    async def create_issue(
        self,
        summary: str,
        description: str,
        issue_type: str = "Task",
        priority: str = "Medium",
        labels: Optional[list[str]] = None,
        assignee: Optional[str] = None,
        custom_fields: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Create a new Jira issue.
        
        Args:
            summary: Issue title
            description: Issue description (supports Atlassian Document Format)
            issue_type: Type of issue (Task, Bug, Story, etc.)
            priority: Priority level (Highest, High, Medium, Low, Lowest)
            labels: List of labels/tags
            assignee: Account ID of assignee (optional)
            custom_fields: Additional custom fields
            
        Returns:
            Jira issue data including key and self URL
        """
        
        # Build description in ADF format
        adf_description = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": description,
                        }
                    ],
                }
            ],
        }

        # Map priority names to Jira priority IDs
        priority_map = {
            "Highest": 1,
            "High": 2,
            "Medium": 3,
            "Low": 4,
            "Lowest": 5,
        }

        fields: dict[str, Any] = {
            "project": {"key": self.project_key},
            "summary": summary,
            "description": adf_description,
            "issuetype": {"name": issue_type},
            "priority": {"id": str(priority_map.get(priority, 3))},
        }

        if labels:
            fields["labels"] = labels

        if assignee:
            fields["assignee"] = {"id": assignee}
        elif self.settings.jira_default_assignee:
            fields["assignee"] = {"accountId": self.settings.jira_default_assignee}

        if custom_fields:
            fields.update(custom_fields)

        response = await self._request(
            "POST",
            "/issue",
            json_data={"fields": fields},
        )

        logger.info(f"Created Jira issue: {response.get('key', 'unknown')}")
        return response

    async def get_issue(self, issue_key: str) -> dict[str, Any]:
        """Get a Jira issue by key (e.g., SCRUM-4)"""
        
        return await self._request(
            "GET",
            f"/issue/{issue_key}?expand=renderedFields",
        )

    async def update_issue(
        self,
        issue_key: str,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        assignee: Optional[str] = None,
        labels: Optional[list[str]] = None,
    ) -> None:
        """Update an existing Jira issue"""
        
        fields: dict[str, Any] = {}

        if summary:
            fields["summary"] = summary

        if description:
            fields["description"] = {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": description}],
                    }
                ],
            }

        if labels:
            fields["labels"] = labels

        if fields:
            await self._request(
                "PUT",
                f"/issue/{issue_key}",
                json_data={"fields": fields},
            )

        if assignee:
            await self._request(
                "PUT",
                f"/issue/{issue_key}/assignee",
                json_data={"accountId": assignee},
            )

        if status:
            await self.transition_issue(issue_key, status)

        logger.info(f"Updated Jira issue: {issue_key}")

    async def add_comment(self, issue_key: str, comment: str) -> dict[str, Any]:
        """Add a comment to a Jira issue"""
        
        return await self._request(
            "POST",
            f"/issue/{issue_key}/comment",
            json_data={
                "body": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": comment}],
                        }
                    ],
                }
            },
        )

    async def transition_issue(self, issue_key: str, transition_name: str) -> dict[str, Any]:
        """
        Transition an issue to a new status.
        
        Common transitions:
        - "To Do" → "In Progress"
        - "In Progress" → "Done"
        - "Done" → "To Do" (reopened)
        """
        
        # Get available transitions
        transitions_response = await self._request(
            "GET",
            f"/issue/{issue_key}/transitions",
        )

        transitions = transitions_response.get("transitions", [])
        
        # Find matching transition
        transition_id = None
        for t in transitions:
            if t["name"].lower() == transition_name.lower():
                transition_id = t["id"]
                break

        if not transition_id:
            available = [t["name"] for t in transitions]
            raise ValueError(
                f"Transition '{transition_name}' not found. "
                f"Available: {', '.join(available)}"
            )

        return await self._request(
            "POST",
            f"/issue/{issue_key}/transitions",
            json_data={"transition": {"id": transition_id}},
        )

    async def search_issues(
        self,
        jql: str,
        max_results: int = 50,
        start_at: int = 0,
    ) -> dict[str, Any]:
        """
        Search for Jira issues using JQL.
        
        Example JQL:
        - "project = SCRUM AND status = 'To Do'"
        - "assignee = currentUser()"
        - "created >= -7d"
        """
        
        return await self._request(
            "GET",
            f"/search?jql={jql}&maxResults={max_results}&startAt={start_at}",
        )

    async def get_project_info(self) -> dict[str, Any]:
        """Get information about the configured Jira project"""
        
        return await self._request(
            "GET",
            f"/project/{self.project_key}",
        )


# Module-level singleton
jira_service = JiraService()
