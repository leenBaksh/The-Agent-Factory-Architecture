"""
MCP Server Initialization and Configuration

This module provides utilities to automatically initialize MCP servers
based on the MCP_SERVER_IDS environment variable.
"""

import logging
from typing import Optional

from app.config import get_settings
from app.mcp.client import (
    MCPConnectionConfig,
    MCPManager,
    create_filesystem_mcp,
    create_github_mcp,
    create_mcp_manager,
    create_postgres_mcp,
    create_slack_mcp,
)

try:
    from app.mcp.jira_server import create_jira_mcp
    JIRA_MCP_AVAILABLE = True
except ImportError:
    JIRA_MCP_AVAILABLE = False
    logger.warning("Jira MCP module not available")

logger = logging.getLogger(__name__)

# Global MCP manager instance
_mcp_manager: Optional[MCPManager] = None


def get_mcp_manager() -> Optional[MCPManager]:
    """Get the global MCP manager instance"""
    return _mcp_manager


def create_server_config(server_id: str) -> Optional[MCPConnectionConfig]:
    """
    Create an MCP server configuration based on the server ID.

    Args:
        server_id: The server identifier (filesystem, postgres, github, slack, jira)

    Returns:
        MCPConnectionConfig if the server is properly configured, None otherwise
    """
    settings = get_settings()

    if server_id == "filesystem":
        if not settings.mcp_filesystem_path:
            logger.warning("Filesystem MCP requested but MCP_FILESYSTEM_PATH not set")
            return None
        return create_filesystem_mcp(settings.mcp_filesystem_path)

    elif server_id == "postgres":
        if not settings.mcp_postgres_connection_string:
            logger.warning("PostgreSQL MCP requested but MCP_POSTGRES_CONNECTION_STRING not set")
            return None
        return create_postgres_mcp(settings.mcp_postgres_connection_string)

    elif server_id == "github":
        if not settings.mcp_github_token:
            logger.warning("GitHub MCP requested but MCP_GITHUB_TOKEN not set")
            return None
        return create_github_mcp(settings.mcp_github_token)

    elif server_id == "slack":
        if not settings.mcp_slack_bot_token:
            logger.warning("Slack MCP requested but MCP_SLACK_BOT_TOKEN not set")
            return None
        return create_slack_mcp(settings.mcp_slack_bot_token)

    elif server_id == "jira":
        if not JIRA_MCP_AVAILABLE:
            logger.warning("Jira MCP requested but module not available")
            return None
        if not settings.jira_enabled:
            logger.warning("Jira MCP requested but JIRA_ENABLED is false")
            return None
        if not settings.jira_url or not settings.jira_email or not settings.jira_api_token:
            logger.warning("Jira MCP requested but missing credentials (URL, email, or token)")
            return None
        return create_jira_mcp()

    else:
        logger.error(f"Unknown MCP server ID: {server_id}")
        return None


async def initialize_mcp_servers() -> Optional[MCPManager]:
    """
    Initialize all MCP servers specified in MCP_SERVER_IDS.

    This function:
    1. Reads the MCP_SERVER_IDS environment variable
    2. Creates configurations for each requested server
    3. Connects to all servers
    4. Returns an MCPManager with all connected servers

    Returns:
        MCPManager instance if MCP is enabled and servers connected successfully,
        None if MCP is disabled or no servers were configured
    """
    global _mcp_manager

    settings = get_settings()

    # Check if MCP is enabled
    if not settings.mcp_enabled:
        logger.info("MCP is disabled (set MCP_ENABLED=true to enable)")
        return None

    # Get list of server IDs
    server_ids = settings.mcp_server_ids_list
    if not server_ids:
        logger.warning("MCP is enabled but no server IDs configured (MCP_SERVER_IDS is empty)")
        return None

    logger.info(f"Initializing {len(server_ids)} MCP server(s): {', '.join(server_ids)}")

    # Create manager
    manager = create_mcp_manager()

    # Configure and connect each server
    connected_count = 0
    for server_id in server_ids:
        try:
            # Create server configuration
            server_config = create_server_config(server_id)
            if server_config is None:
                logger.warning(f"Skipping {server_id} - missing required configuration")
                continue

            # Add server to manager
            manager.add_server(server_config)

            logger.info(f"Configured MCP server: {server_id}")

        except Exception as e:
            logger.error(f"Failed to configure MCP server {server_id}: {e}")
            continue

    # Connect to all configured servers
    if manager.clients:
        logger.info("Connecting to MCP servers...")
        results = await manager.connect_all()

        # Log results
        for server_id, success in results.items():
            if success:
                connected_count += 1
                client = manager.get_client(server_id)
                tool_count = len(client.tools) if client else 0
                logger.info(
                    f"MCP server '{server_id}' connected successfully "
                    f"({tool_count} tools available)"
                )
            else:
                logger.error(f"MCP server '{server_id}' failed to connect")

        logger.info(
            f"MCP initialization complete: {connected_count}/{len(manager.clients)} server(s) connected"
        )
    else:
        logger.warning("No MCP servers were successfully configured")
        return None

    # Store global reference
    _mcp_manager = manager

    return manager


async def shutdown_mcp_servers():
    """Disconnect from all MCP servers"""
    global _mcp_manager

    if _mcp_manager:
        logger.info("Shutting down MCP servers...")
        await _mcp_manager.disconnect_all()
        _mcp_manager = None
        logger.info("MCP servers shutdown complete")
