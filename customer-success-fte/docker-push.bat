@echo off
REM ═══════════════════════════════════════════════════════════════════════════
REM  Build & Push Customer Success FTE to Docker Hub
REM  
REM  Usage:
REM    1. Make sure Docker Desktop is running (green whale icon in tray)
REM    2. Run: docker-push.bat
REM ═══════════════════════════════════════════════════════════════════════════

echo.
echo ========================================
echo   Docker Build & Push
echo ========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not running!
    echo.
    echo Please start Docker Desktop and wait for it to be ready
    echo (Look for the green whale icon in the system tray)
    echo.
    pause
    exit /b 1
)

echo Docker is running. Building image...
echo.

REM Build the image
cd /d "%~dp0"
docker build -t leenbaksh1529/customer-success-fte:latest .

if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo.
echo Build successful! Logging in to Docker Hub...
echo.

REM Login to Docker Hub
docker login

if errorlevel 1 (
    echo.
    echo ERROR: Login failed!
    pause
    exit /b 1
)

echo.
echo Pushing to Docker Hub...
echo.

docker push leenbaksh1529/customer-success-fte:latest

if errorlevel 1 (
    echo.
    echo ERROR: Push failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo   SUCCESS!
echo ========================================
echo.
echo   Image pushed to:
echo   docker.io/leenbaksh1529/customer-success-fte:latest
echo.
echo   To run:
echo     docker run -p 8000:8000 --env-file .env leenbaksh1529/customer-success-fte
echo.
pause
