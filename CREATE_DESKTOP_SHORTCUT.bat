@echo off
REM ============================================
REM GharMitra - Create Desktop Shortcut (Batch Wrapper)
REM ============================================

echo.
echo ============================================
echo   GharMitra - Create Desktop Shortcut
echo ============================================
echo.

REM Check if PowerShell is available
powershell -Command "Get-Host" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] PowerShell is not available on this system.
    echo Please use the PowerShell script directly or install PowerShell.
    pause
    exit /b 1
)

REM Run the PowerShell script
powershell -ExecutionPolicy Bypass -File "%~dp0CREATE_DESKTOP_SHORTCUT.ps1"

pause
