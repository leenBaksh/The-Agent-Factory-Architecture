@echo off
REM ═══════════════════════════════════════════════════════════════════════════
REM  Build & Push Docker Images - Customer Success Digital FTE
REM ═══════════════════════════════════════════════════════════════════════════

echo.
echo ═══════════════════════════════════════════════════════════════
echo   🐳 Building & Pushing Docker Images
echo ═══════════════════════════════════════════════════════════════
echo.

REM ── Configuration ──────────────────────────────────────────────────
set IMAGE_NAME=customer-success-fte
set DOCKER_USERNAME=%DOCKER_USERNAME%
set TAG=latest

if "%DOCKER_USERNAME%"=="" (
    echo ⚠️  DOCKER_USERNAME environment variable not set
    echo.
    set /p DOCKER_USERNAME="Enter your Docker Hub username: "
    if "!DOCKER_USERNAME!"=="" (
        echo ❌ Docker Hub username is required!
        pause
        exit /b 1
    )
)

set FULL_IMAGE=%DOCKER_USERNAME%/%IMAGE_NAME%:%TAG%

echo 📦 Image: %FULL_IMAGE%
echo.

REM ── Check Docker ───────────────────────────────────────────────────
echo [1/5] Checking Docker...
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not running!
    echo.
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)
echo ✅ Docker is running
echo.

REM ── Login to Docker Hub ────────────────────────────────────────────
echo [2/5] Logging in to Docker Hub...
docker login
if errorlevel 1 (
    echo ❌ Docker login failed!
    pause
    exit /b 1
)
echo.

REM ── Build Docker Image ─────────────────────────────────────────────
echo [3/5] Building Docker image...
echo.
cd customer-success-fte
docker build -t %FULL_IMAGE% .
if errorlevel 1 (
    echo ❌ Docker build failed!
    cd ..
    pause
    exit /b 1
)
echo.
echo ✅ Image built successfully!
echo.

REM ── Test Image ─────────────────────────────────────────────────────
echo [4/5] Testing image...
docker run --rm %FULL_IMAGE% uvicorn app.main:app --host 0.0.0.0 --port 8000 --help >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Image test had issues, but continuing...
) else (
    echo ✅ Image test passed
)
echo.

REM ── Push to Docker Hub ─────────────────────────────────────────────
echo [5/5] Pushing to Docker Hub...
docker push %FULL_IMAGE%
if errorlevel 1 (
    echo ❌ Docker push failed!
    cd ..
    pause
    exit /b 1
)

cd ..

echo.
echo ═══════════════════════════════════════════════════════════════
echo   ✅ Successfully pushed to Docker Hub!
echo ═══════════════════════════════════════════════════════════════
echo.
echo   📦 Image: %FULL_IMAGE%
echo.
echo   To pull and run:
echo     docker pull %FULL_IMAGE%
echo     docker run -p 8000:8000 --env-file .env %FULL_IMAGE%
echo.
echo   To run with Docker Compose:
echo     docker-compose up -d
echo.
echo ═══════════════════════════════════════════════════════════════
echo.
pause
