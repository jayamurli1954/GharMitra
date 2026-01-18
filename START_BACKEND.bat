@echo off
REM ============================================
REM GharMitra - Start Backend Server Only
REM ============================================

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%backend"

echo.
echo ============================================
echo   GharMitra - Starting Backend Server
echo ============================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Try to use virtual environment if it exists and works
if exist "venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment...
    call venv\Scripts\activate.bat
    python --version >nul 2>&1
    if errorlevel 1 (
        echo [WARNING] Virtual environment has issues, using system Python
        echo [INFO] Run FIX_VENV.bat to fix the virtual environment
    ) else (
        echo [OK] Using virtual environment
    )
) else (
    echo [INFO] No virtual environment found, using system Python
)

echo.
echo Starting backend server on http://127.0.0.1:8001
echo.
echo Press Ctrl+C to stop the server
echo.

python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload

pause
