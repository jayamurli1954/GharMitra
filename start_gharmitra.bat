@echo off
REM ============================================
REM GharMitra - One-Click Desktop Launcher
REM ============================================

setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo.
echo ============================================
echo   GharMitra - Starting Application
echo ============================================
echo.

REM Kill existing processes
call "%~dp0SAFE_KILL.bat"

REM Start Backend
echo [1/3] Starting Backend Server...
start "GharMitra Backend" /min "%~dp0START_BACKEND.bat"

REM Wait for backend initialization
echo Waiting for backend...
timeout /t 5 /nobreak >nul

REM Start Frontend
echo [2/3] Starting Frontend Server...
start "GharMitra Frontend" /min "%~dp0START_FRONTEND.bat"

REM Wait for frontend initialization
echo Waiting for frontend...
timeout /t 8 /nobreak >nul

REM Open Browser
echo [3/3] Opening Browser...
start http://localhost:3006

echo.
echo ============================================
echo   Application Started!
echo ============================================
echo.
echo Servers are running in the background.
echo Close the minimized windows to stop them.
echo.
timeout /t 5 /nobreak >nul
exit
