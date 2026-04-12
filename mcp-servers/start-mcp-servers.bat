@echo off
REM ═══════════════════════════════════════════════════════════════════
REM Start all MCP servers for Digital FTEs
REM ═══════════════════════════════════════════════════════════════════

setlocal
cd /d "%~dp0"

REM ── Environment from customer-success-fte .env ─────────────────────
for /f "tokens=*" %%a in ('type "..\customer-success-fte\.env"') do set %%a

REM ── Database URL fix for MCP (sync asyncpg driver) ─────────────────
set DATABASE_URL=postgresql://postgres:changeme@localhost:5432/customer_success

echo ============================================================
echo  MCP Servers — Digital FTEs
echo ============================================================
echo.
echo [1/3] PostgreSQL MCP Server  — port 5432
echo [2/3] WhatsApp MCP Server   — Meta Cloud API
echo [3/3] Gmail MCP Server      — OAuth2
echo.
echo Press Ctrl+C in any window to stop a server.
echo ============================================================
echo.

REM ── PostgreSQL MCP ────────────────────────────────────────────────
start "MCP: PostgreSQL" cmd /k "set DATABASE_URL=postgresql://postgres:changeme@localhost:5432/customer_success && python postgresql_mcp.py"
timeout /t 2 /nobreak >nul

REM ── WhatsApp MCP ──────────────────────────────────────────────────
start "MCP: WhatsApp" cmd /k "python whatsapp_mcp.py"
timeout /t 2 /nobreak >nul

REM ── Gmail MCP ─────────────────────────────────────────────────────
start "MCP: Gmail" cmd /k "python gmail_mcp.py"

echo.
echo All MCP servers launched in separate windows.
