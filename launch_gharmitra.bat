@echo off
REM GharMitra - One-Click Launcher
REM This script starts all required services and opens the application

echo ========================================
echo   GharMitra - Starting Application
echo ========================================
echo.

REM Get the script directory
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Stop any existing processes on required ports
echo [1/5] Stopping existing processes...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8001 ^| findstr LISTENING') do (
    echo   - Stopping process %%a on port 8001...
    taskkill /PID %%a /F >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3001 ^| findstr LISTENING') do (
    echo   - Stopping process %%a on port 3001...
    taskkill /PID %%a /F >nul 2>&1
)

REM Wait for ports to be released
echo [2/5] Waiting for ports to be released...
timeout /t 2 /nobreak >nul

REM Start backend in minimized window
echo [3/5] Starting backend server...
cd /d "%SCRIPT_DIR%backend"
start "GharMitra Backend" /min cmd /c "python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload"

REM Wait for backend to start
echo [4/5] Waiting for backend to initialize...
timeout /t 5 /nobreak >nul

REM Check if desktop app should be used or web
if exist "%SCRIPT_DIR%desktop\node_modules\electron" (
    echo [5/5] Starting desktop application...
    cd /d "%SCRIPT_DIR%desktop"
    start "" npm start
) else (
    echo [5/5] Starting web frontend...
    cd /d "%SCRIPT_DIR%web"
    start "GharMitra Frontend" /min cmd /c "npm run dev"
    timeout /t 3 /nobreak >nul
    echo.
    echo Opening browser...
    start http://localhost:3001
)

echo.
echo ========================================
echo   GharMitra is starting!
echo ========================================
echo.
echo Backend:  http://localhost:8001
if exist "%SCRIPT_DIR%desktop\node_modules\electron" (
    echo Desktop app is launching...
) else (
    echo Frontend: http://localhost:3001
    echo.
    echo Browser should open automatically.
)
echo.
echo To stop the application, close the minimized windows
echo or run stop_gharmitra.bat
echo.
timeout /t 3 /nobreak >nul
exit
