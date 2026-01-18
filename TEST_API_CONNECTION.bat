@echo off
REM ============================================
REM GharMitra - Test API Connection
REM ============================================
REM This script tests if the backend API is accessible

echo.
echo ============================================
echo   Testing Backend API Connection
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

REM Test health endpoint
echo Testing health endpoint...
curl -s http://localhost:8001/health
if errorlevel 1 (
    echo [ERROR] Cannot connect to backend
    echo.
    echo Please check:
    echo 1. Backend is running: python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
    echo 2. No firewall is blocking port 8001
    echo 3. Backend logs for any errors
) else (
    echo.
    echo [OK] Backend is responding
)

echo.
echo Testing root endpoint...
curl -s http://localhost:8001/
if errorlevel 1 (
    echo [ERROR] Root endpoint not accessible
) else (
    echo.
    echo [OK] Root endpoint is accessible
)

echo.
echo ============================================
echo   Connection Test Complete
echo ============================================
echo.
echo If both tests passed, the backend is working.
echo If you still get connection errors in the frontend:
echo 1. Check browser console (F12) for detailed errors
echo 2. Check backend terminal for error messages
echo 3. Verify CORS is enabled (it should be in DEBUG mode)
echo.
pause
