"""
Jira Webhook Router

Handles incoming webhooks from Jira to sync status updates back to the FTE system.

Endpoints:
    POST /webhooks/jira
        Receives Jira issue updates (status changes, comments, assignments)
    GET /api/jira/projects
        Get Jira project information
    GET /api/jira/issues/{issue_key}
        Get specific Jira issue details
    POST /api/jira/issues
        Create a new Jira issue
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.jira_service import jira_service

router = APIRouter(prefix="/webhooks", tags=["Jira"])
api_router = APIRouter(prefix="/api/jira", tags=["Jira"])

logger = logging.getLogger(__name__)


# ── Pydantic Models ──────────────────────────────────────────────────────────


class JiraCreateIssueRequest(BaseModel):
    """Request body for creating a Jira issue"""
    summary: str = Field(..., description="Issue title")
    description: str = Field(..., description="Issue description")
    issue_type: str = Field(default="Task", description="Issue type (Task, Bug, Story, etc.)")
    priority: str = Field(default="Medium", description="Priority level")
    labels: Optional[list[str]] = Field(default=None, description="Labels/tags")
    assignee: Optional[str] = Field(default=None, description="Assignee account ID")


class JiraUpdateIssueRequest(BaseModel):
    """Request body for updating a Jira issue"""
    summary: Optional[str] = Field(default=None, description="New summary")
    description: Optional[str] = Field(default=None, description="New description")
    status: Optional[str] = Field(default=None, description="New status")
    assignee: Optional[str] = Field(default=None, description="New assignee")
    labels: Optional[list[str]] = Field(default=None, description="New labels")


class JiraAddCommentRequest(BaseModel):
    """Request body for adding a comment"""
    comment: str = Field(..., description="Comment text")


# ── Webhook Handler ───────────────────────────────────────────────────────────


@router.post("/jira")
async def handle_jira_webhook(payload: dict):
    """
    Receive webhook notifications from Jira.
    
    This endpoint is called when Jira issues are updated.
    Currently logs the update - can be extended to sync with internal tickets.
    """
    logger.info(f"Received Jira webhook: {payload}")
    
    # Extract useful information from the webhook
    issue_key = payload.get("issue", {}).get("key", "unknown")
    issue_event = payload.get("issue_event", {})
    user = payload.get("user", {}).get("displayName", "unknown")
    
    # Log the event
    logger.info(
        f"Jira update: {issue_key} by {user} - {issue_event.get('type', 'unknown')}"
    )
    
    # TODO: Sync with internal ticket system
    # - Find matching FTE ticket
    # - Update status/comments based on Jira changes
    # - Notify relevant stakeholders
    
    return {
        "success": True,
        "message": f"Received Jira update for {issue_key}",
        "issue_key": issue_key,
    }


# ── API Endpoints ─────────────────────────────────────────────────────────────


@api_router.get("/projects")
async def get_project_info():
    """Get information about the configured Jira project"""
    
    if not jira_service.enabled:
        raise HTTPException(status_code=503, detail="Jira integration is not enabled")
    
    try:
        project = await jira_service.get_project_info()
        return {
            "success": True,
            "project": project,
        }
    except Exception as e:
        logger.error(f"Failed to get Jira project info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/issues/{issue_key}")
async def get_issue(issue_key: str):
    """Get a specific Jira issue by key"""
    
    if not jira_service.enabled:
        raise HTTPException(status_code=503, detail="Jira integration is not enabled")
    
    try:
        issue = await jira_service.get_issue(issue_key)
        return {
            "success": True,
            "issue": issue,
        }
    except Exception as e:
        logger.error(f"Failed to get Jira issue {issue_key}: {e}")
        raise HTTPException(status_code=404, detail=f"Issue {issue_key} not found")


@api_router.post("/issues")
async def create_issue(request: JiraCreateIssueRequest):
    """Create a new Jira issue"""
    
    if not jira_service.enabled:
        raise HTTPException(status_code=503, detail="Jira integration is not enabled")
    
    try:
        issue = await jira_service.create_issue(
            summary=request.summary,
            description=request.description,
            issue_type=request.issue_type,
            priority=request.priority,
            labels=request.labels,
            assignee=request.assignee,
        )
        return {
            "success": True,
            "issue": issue,
        }
    except Exception as e:
        logger.error(f"Failed to create Jira issue: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.put("/issues/{issue_key}")
async def update_issue(issue_key: str, request: JiraUpdateIssueRequest):
    """Update an existing Jira issue"""
    
    if not jira_service.enabled:
        raise HTTPException(status_code=503, detail="Jira integration is not enabled")
    
    try:
        await jira_service.update_issue(
            issue_key=issue_key,
            summary=request.summary,
            description=request.description,
            status=request.status,
            assignee=request.assignee,
            labels=request.labels,
        )
        return {
            "success": True,
            "message": f"Issue {issue_key} updated",
        }
    except Exception as e:
        logger.error(f"Failed to update Jira issue {issue_key}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/issues/{issue_key}/comments")
async def add_comment(issue_key: str, request: JiraAddCommentRequest):
    """Add a comment to a Jira issue"""
    
    if not jira_service.enabled:
        raise HTTPException(status_code=503, detail="Jira integration is not enabled")
    
    try:
        comment = await jira_service.add_comment(issue_key, request.comment)
        return {
            "success": True,
            "comment": comment,
        }
    except Exception as e:
        logger.error(f"Failed to add comment to {issue_key}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/search")
async def search_issues(
    jql: str = Query(..., description="JQL query string"),
    max_results: int = Query(default=50, le=100),
    start_at: int = Query(default=0, ge=0),
):
    """Search for Jira issues using JQL"""
    
    if not jira_service.enabled:
        raise HTTPException(status_code=503, detail="Jira integration is not enabled")
    
    try:
        results = await jira_service.search_issues(
            jql=jql,
            max_results=max_results,
            start_at=start_at,
        )
        return {
            "success": True,
            "results": results,
            "total": results.get("total", 0),
        }
    except Exception as e:
        logger.error(f"Failed to search Jira issues: {e}")
        raise HTTPException(status_code=500, detail=str(e))
