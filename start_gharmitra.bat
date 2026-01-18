@echo off
REM ============================================
REM GharMitra - One-Click Desktop Launcher
REM ============================================
REM This script starts the backend and frontend servers
REM and automatically opens the application in your browser

setlocal enabledelayedexpansion

REM Get the script directory
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo.
echo ============================================
echo   GharMitra - Starting Application
echo ============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python and try again.
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed or not in PATH
    echo Please install Node.js and try again.
    pause
    exit /b 1
)

REM Step 1: Kill all processes on required ports (clean slate)
echo [1/6] Killing all processes on required ports...
call "%~dp0KILL_PORTS.bat"

REM Step 2: Wait for ports to be released (already done in KILL_PORTS.bat)
echo [2/6] Ports cleared, ready to start servers...

REM Step 3: Start backend server
echo [3/6] Starting backend server (port 8001)...
cd /d "%SCRIPT_DIR%backend"
if not exist "app\main.py" (
    echo [ERROR] Backend files not found!
    pause
    exit /b 1
)

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

start "GharMitra Backend" /min cmd /c "python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload"

REM Wait for backend to start
echo [4/6] Waiting for backend to initialize...
timeout /t 5 /nobreak >nul

REM Check if backend is running
set "BACKEND_RUNNING=0"
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8001 ^| findstr LISTENING') do (
    set "BACKEND_RUNNING=1"
)

if !BACKEND_RUNNING!==0 (
    echo [WARNING] Backend may not have started properly. Continuing anyway...
)

REM Step 5: Start frontend server
echo [5/6] Starting frontend server (port 3006)...
cd /d "%SCRIPT_DIR%web"

if not exist "package.json" (
    echo [ERROR] Web frontend files not found!
    echo Please ensure the web directory exists and has package.json
    pause
    exit /b 1
)

REM Check if node_modules exists
if not exist "node_modules" (
    echo [INFO] Installing frontend dependencies...
    call npm install
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies!
        pause
        exit /b 1
    )
)

start "GharMitra Frontend" /min cmd /c "npm run dev"

REM Wait for frontend to start
echo.
echo Waiting for frontend to initialize...
timeout /t 8 /nobreak >nul

REM Open browser
echo.
echo ============================================
echo   GharMitra is Starting!
echo ============================================
echo.
echo Backend:  http://localhost:8001
echo Frontend: http://localhost:3006
echo.
echo Opening browser...
timeout /t 2 /nobreak >nul
start http://localhost:3006

echo.
echo ============================================
echo   Application Started Successfully!
echo ============================================
echo.
echo Both servers are running in minimized windows.
echo.
echo To stop the application:
echo   - Close the minimized "GharMitra Backend" and "GharMitra Frontend" windows
echo   - Or run STOP_GHARMITRA.bat
echo.
echo The application will open in your default browser.
echo.
echo This window will close automatically in 5 seconds...
echo (You can close it manually if needed)
timeout /t 5 /nobreak >nul
exit
