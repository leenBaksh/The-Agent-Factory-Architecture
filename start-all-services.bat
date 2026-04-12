@echo off
REM ═══════════════════════════════════════════════════════════════════════════
REM  Start All Digital FTE Services (WhatsApp + Gmail + Dashboard)
REM ═══════════════════════════════════════════════════════════════════════════

echo.
echo ═══════════════════════════════════════════════════════════════
echo   🚀 Starting Digital FTE Services
echo ═══════════════════════════════════════════════════════════════
echo.

REM Check if .env exists
if not exist "customer-success-fte\.env" (
    echo ❌ ERROR: customer-success-fte\.env not found!
    echo.
    echo Please:
    echo   1. Copy .env.example to .env
    echo   2. Fill in your WhatsApp ^& Gmail credentials
    echo   3. Run this script again
    echo.
    pause
    exit /b 1
)

echo ✅ Starting services...
echo.

REM ── Service 1: Agent Factory Backend (Port 8003) ─────────────────
echo [1/4] Starting Agent Factory Backend on port 8003...
start "Agent Factory Backend" cmd /k "cd agent-factory-backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload"
timeout /t 3 /nobreak >nul

REM ── Service 2: Customer Success FTE (Port 8000) ──────────────────
echo [2/4] Starting Customer Success FTE on port 8000...
start "Customer Success FTE (WhatsApp + Gmail)" cmd /k "cd customer-success-fte && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 3 /nobreak >nul

REM ── Service 3: Next.js Dashboard (Port 3000) ─────────────────────
echo [3/4] Starting Dashboard on port 3000...
start "Dashboard" cmd /k "cd agent-factory-dashboard && npm run dev"
timeout /t 3 /nobreak >nul

REM ── Service 4: MCP Servers (Optional) ────────────────────────────
echo [4/4] MCP Servers (optional - run start-mcp-servers.bat if needed)
echo.

echo ═══════════════════════════════════════════════════════════════
echo   ✅ All services started!
echo ═══════════════════════════════════════════════════════════════
echo.
echo   📊 Dashboard:      http://localhost:3000
echo   🔧 Customer FTE:   http://localhost:8000
echo   🔧 Backend API:    http://localhost:8003
echo   📚 API Docs:       http://localhost:8000/docs
echo.
echo   🔐 Login Credentials:
echo      Email:    admin@agentfactory.com
echo      Password: Admin@123
echo.
echo   📱 WhatsApp Setup Required:
echo      - Get credentials from https://developers.facebook.com/
echo      - Fill in customer-success-fte\.env
echo.
echo   📧 Gmail Setup Required:
echo      - Create Google Cloud project
echo      - Run: cd customer-success-fte ^&^& python scripts/setup_gmail_auth.py
echo.
echo ═══════════════════════════════════════════════════════════════
echo.
echo Press any key to open the dashboard...
pause >nul

start http://localhost:3000/login
