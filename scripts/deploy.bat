@echo off
REM =============================================================================
REM BALASORE ALLOYS DASHBOARD - WINDOWS DEPLOYMENT SCRIPT
REM =============================================================================
REM
REM Usage:
REM   scripts\deploy.bat              - Build and deploy
REM   scripts\deploy.bat --rebuild    - Force rebuild
REM
REM =============================================================================

setlocal enabledelayedexpansion

set APP_NAME=bal-dashboard
set IMAGE_NAME=bal-dashboard

REM Get version
set /p VERSION=<VERSION

echo ======================================
echo   BAL DASHBOARD DEPLOYMENT v%VERSION%
echo ======================================

REM Check if .env exists
if not exist ".env" (
    echo ERROR: .env file not found!
    echo Copy .env.example to .env and configure it.
    exit /b 1
)

REM Check Docker
docker info >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not running!
    exit /b 1
)

echo.
echo [1/4] Building image...
if "%1"=="--rebuild" (
    docker-compose build --no-cache
) else (
    docker-compose build
)

echo.
echo [2/4] Stopping old container...
docker-compose down 2>nul

echo.
echo [3/4] Starting new container...
docker-compose up -d

echo.
echo [4/4] Checking health...
timeout /t 5 /nobreak >nul

docker ps --filter "name=%APP_NAME%" --format "{{.Status}}"

echo.
echo ======================================
echo   DEPLOYMENT COMPLETE!
echo ======================================
echo   Version: %VERSION%
echo   URL: http://localhost:5100
echo.
echo   Commands:
echo     Logs:    docker-compose logs -f
echo     Stop:    docker-compose down
echo     Restart: docker-compose restart
echo ======================================

endlocal
