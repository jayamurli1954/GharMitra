@echo off
REM ============================================
REM GharMitra - Start Frontend Server Only
REM ============================================

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%web"

echo.
echo ============================================
echo   GharMitra - Starting Frontend Server
echo ============================================
echo.

REM Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed or not in PATH
    pause
    exit /b 1
)

echo [INFO] Starting frontend server on http://localhost:3006
echo.
echo Press Ctrl+C to stop the server
echo.

npm run dev

pause
