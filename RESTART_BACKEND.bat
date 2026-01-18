@echo off
REM ============================================
REM GharMitra - Restart Backend Server
REM ============================================
REM This script kills the backend process and restarts it cleanly

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo.
echo ============================================
echo   GharMitra - Restarting Backend Server
echo ============================================
echo.

REM Step 1: Kill all processes on port 8001
echo [1/3] Stopping existing backend processes...
call "%SCRIPT_DIR%KILL_PORTS.bat"

REM Wait a moment
timeout /t 2 /nobreak >nul

REM Step 2: Start backend
echo.
echo [2/3] Starting backend server...
cd /d "%SCRIPT_DIR%backend"

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo [INFO] Using system Python (no virtual environment)
)

echo.
echo [3/3] Backend server starting on http://127.0.0.1:8001
echo.
echo Press Ctrl+C to stop the server
echo.

python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload

pause
