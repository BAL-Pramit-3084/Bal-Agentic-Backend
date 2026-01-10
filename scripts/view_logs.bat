@echo off
REM =============================================================================
REM VIEW LOGS - Quick access to container logs
REM =============================================================================

echo.
echo BAL Dashboard Logs
echo ==================
echo.
echo Choose an option:
echo   1. Live logs (follow mode)
echo   2. Last 100 lines
echo   3. Error logs only
echo   4. Search logs
echo   5. Exit
echo.

set /p choice="Enter choice (1-5): "

if "%choice%"=="1" (
    docker-compose logs -f bal-dashboard
) else if "%choice%"=="2" (
    docker-compose logs --tail=100 bal-dashboard
) else if "%choice%"=="3" (
    docker-compose logs bal-dashboard 2>&1 | findstr /i "error exception failed"
) else if "%choice%"=="4" (
    set /p search="Enter search term: "
    docker-compose logs bal-dashboard 2>&1 | findstr /i "!search!"
) else (
    echo Exiting...
)
