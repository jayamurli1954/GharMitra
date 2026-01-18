@echo off
REM ============================================
REM GharMitra - Stop All Servers
REM ============================================

echo.
echo ============================================
echo   GharMitra - Stopping All Servers
echo ============================================
echo.

REM Use the KILL_PORTS.bat script for comprehensive cleanup
set "SCRIPT_DIR=%~dp0"
call "%SCRIPT_DIR%KILL_PORTS.bat"

echo.
echo ============================================
echo   All GharMitra servers have been stopped.
echo ============================================
echo.
timeout /t 2 /nobreak >nul
