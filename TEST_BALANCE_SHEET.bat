@echo off
REM ============================================
REM GharMitra - Test Balance Sheet Endpoint
REM ============================================
REM This script tests if the Balance Sheet endpoint is working

echo.
echo ============================================
echo   Testing Balance Sheet Endpoint
echo ============================================
echo.

REM Check if backend is running
netstat -ano | findstr :8001 >nul
if errorlevel 1 (
    echo [ERROR] Backend is not running on port 8001
    echo Please start the backend first using START_BACKEND.bat
    pause
    exit /b 1
)

echo [OK] Backend is running on port 8001
echo.

REM Test the endpoint (requires authentication token)
echo Testing Balance Sheet endpoint...
echo.
echo Note: This requires a valid authentication token.
echo You can test it manually by:
echo 1. Opening browser to http://localhost:8001/docs
echo 2. Going to /reports/balance-sheet endpoint
echo 3. Clicking "Try it out"
echo 4. Entering as_on_date (e.g., 2026-01-17)
echo 5. Clicking "Execute"
echo.
pause
