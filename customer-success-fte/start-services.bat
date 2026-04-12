@echo off
REM ═══════════════════════════════════════════════════════════════════
REM Start all services + ngrok tunnel for WhatsApp webhook
REM ═══════════════════════════════════════════════════════════════════

echo [1/3] Starting Docker services...
cd /d "%~dp0customer-success-fte"
docker compose up -d fastapi
if %errorlevel% neq 0 (
    echo ERROR: Docker failed to start
    pause
    exit /b 1
)
echo.

echo [2/3] Waiting for FastAPI to be healthy...
timeout /t 5 /nobreak >nul
curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: FastAPI may not be healthy yet
    docker ps --filter name=cs-fte-api --format "table {{.Names}}\t{{.Status}}"
) else (
    echo FastAPI is healthy on http://localhost:8000
)
echo.

echo [3/3] Starting ngrok tunnel...
echo -------------------------------------------
echo Your webhook URL will be shown below.
echo Copy it and use in the Meta dashboard:
echo   https://YOUR-NGROK-URL.ngrok-free.dev/webhooks/whatsapp
echo -------------------------------------------
echo.
ngrok http 8000 --bypass-tunnel-reminder
