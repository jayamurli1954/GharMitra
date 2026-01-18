@echo off
REM ============================================
REM GharMitra - Create Desktop Shortcut
REM ============================================
REM This script creates a desktop shortcut using VBScript
REM Works on all Windows versions

echo.
echo ============================================
echo   GharMitra - Create Desktop Shortcut
echo ============================================
echo.

REM Check if START_GHARMITRA.bat exists
if not exist "START_GHARMITRA.bat" (
    if not exist "start_gharmitra.bat" (
        echo [ERROR] START_GHARMITRA.bat not found!
        echo Please ensure you're running this from the GharMitra root directory.
        pause
        exit /b 1
    )
)

REM Run the VBScript to create shortcut
echo Creating desktop shortcut...
cscript //nologo "%~dp0CREATE_SHORTCUT.vbs"

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to create shortcut.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Shortcut Created Successfully!
echo ============================================
echo.
echo A shortcut named "GharMitra" has been created on your desktop.
echo Double-click it to start the application.
echo.
pause
