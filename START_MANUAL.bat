@echo off
REM ============================================
REM GharMitra - Manual Start Commands
REM ============================================
REM Run this file to start both servers in separate windows
REM Or copy the commands below to run manually

setlocal enabledelayedexpansion

REM Get the script directory
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo.
echo ============================================
echo   GharMitra - Manual Start
echo ============================================
echo.
echo This will open two command windows:
echo   1. Backend server (port 8001)
echo   2. Frontend server (port 3006)
echo.
echo Close the windows to stop the servers.
echo.
pause

REM Kill existing processes first
echo.
echo [1/2] Stopping existing processes...
call "%SCRIPT_DIR%KILL_PORTS.bat"

echo.
echo [2/2] Starting servers...
echo.

REM Start backend in a new window
echo Starting Backend Server (port 8001)...
cd /d "%SCRIPT_DIR%backend"
REM Use the START_BACKEND.bat which handles venv issues
start "GharMitra Backend - Port 8001" cmd /k "%~dp0START_BACKEND.bat"

REM Wait a bit
timeout /t 3 /nobreak >nul

REM Start frontend in a new window
echo Starting Frontend Server (port 3006)...
cd /d "%SCRIPT_DIR%web"
REM Use the START_FRONTEND.bat
start "GharMitra Frontend - Port 3006" cmd /k "%~dp0START_FRONTEND.bat"

echo.
echo ============================================
echo   Servers Starting!
echo ============================================
echo.
echo Backend:  http://localhost:8001
echo Frontend: http://localhost:3006
echo.
echo Two command windows have opened.
echo Close those windows to stop the servers.
echo.
echo Opening browser in 5 seconds...
timeout /t 5 /nobreak >nul
start http://localhost:3006

echo.
echo Done! Check the command windows for server status.
echo.
pause
