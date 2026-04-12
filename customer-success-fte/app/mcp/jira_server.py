"""
Jira MCP Server Configuration

Creates MCP server configuration for Jira integration.
Uses the official @modelcontextprotocol/server-jira package.
"""

import logging
from app.config import get_settings
from app.mcp.client import MCPConnectionConfig

logger = logging.getLogger(__name__)


def create_jira_mcp() -> MCPConnectionConfig:
    """
    Create MCP server configuration for Jira.
    
    Uses the official Jira MCP server package.
    Requires: JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN
    """
    settings = get_settings()
    
    # Validate required fields
    if not settings.jira_url:
        raise ValueError("JIRA_URL is required for Jira MCP server")
    if not settings.jira_email:
        raise ValueError("JIRA_EMAIL is required for Jira MCP server")
    if not settings.jira_api_token:
        raise ValueError("JIRA_API_TOKEN is required for Jira MCP server")
    
    logger.info(f"Creating Jira MCP server config: {settings.jira_url}")
    
    return MCPConnectionConfig(
        server_id="jira",
        server_type="stdio",
        command="npx",
        args=[
            "-y",
            "@modelcontextprotocol/server-jira",
            settings.jira_url,
            settings.jira_email,
            settings.jira_api_token,
        ],
        timeout=60.0,  # Longer timeout for npx package download
    )
