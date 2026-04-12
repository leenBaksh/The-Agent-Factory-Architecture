@echo off
REM MCP Servers Startup Script
REM This script starts all MCP servers for Digital FTEs

echo =========================================
echo   Agent Factory - MCP Servers
echo =========================================
echo.

REM Check if virtual environment exists
if not exist "mcp-venv" (
    echo Creating MCP virtual environment...
    python -m venv mcp-venv
    echo.
    echo Installing MCP server dependencies...
    mcp-venv\Scripts\pip install -r mcp-servers\requirements-mcp.txt
    echo.
)

echo Starting MCP Servers...
echo.
echo Available Servers:
echo   1. Slack MCP Server       (Team communication)
echo   2. PostgreSQL MCP Server  (Database queries)
echo   3. Web Search MCP Server  (Research & fact-checking)
echo.
echo Note: Set environment variables before starting:
echo   - SLACK_BOT_TOKEN         (for Slack server)
echo   - DATABASE_URL            (for PostgreSQL server)
echo   - SEARCH_API_KEY          (for Web Search server)
echo   - SEARCH_ENGINE_ID        (for Web Search server)
echo   - NEWS_API_KEY            (for Web Search server)
echo.

echo To start a specific server:
echo   mcp-venv\Scripts\python mcp-servers\slack_mcp.py
echo   mcp-venv\Scripts\python mcp-servers\postgresql_mcp.py
echo   mcp-venv\Scripts\python mcp-servers\web_search_mcp.py
echo.
pause
