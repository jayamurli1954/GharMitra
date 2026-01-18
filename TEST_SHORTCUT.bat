@echo off
REM ============================================
REM GharMitra - Test Desktop Shortcut
REM ============================================
REM This script tests if the desktop shortcut works

echo.
echo ============================================
echo   GharMitra - Testing Desktop Shortcut
echo ============================================
echo.

set "DESKTOP=%USERPROFILE%\Desktop"
set "SHORTCUT=%DESKTOP%\GharMitra.lnk"

if not exist "%SHORTCUT%" (
    echo [ERROR] Shortcut not found at: %SHORTCUT%
    echo.
    echo Please run CREATE_SHORTCUT.bat or FIX_SHORTCUT.bat first.
    pause
    exit /b 1
)

echo [OK] Shortcut found at: %SHORTCUT%
echo.

REM Check shortcut properties using PowerShell
echo Checking shortcut properties...
powershell -Command "$sh = (New-Object -ComObject WScript.Shell).CreateShortcut('%SHORTCUT%'); Write-Host 'Target:' $sh.TargetPath; Write-Host 'Working Directory:' $sh.WorkingDirectory; Write-Host 'Arguments:' $sh.Arguments"

echo.
echo ============================================
echo   Testing Batch File Directly
echo ============================================
echo.

if exist "START_GHARMITRA.bat" (
    echo [OK] START_GHARMITRA.bat exists
    echo.
    echo Testing if batch file can be executed...
    echo (This will start the application - you can close it after testing)
    echo.
    pause
    call "START_GHARMITRA.bat"
) else if exist "start_gharmitra.bat" (
    echo [OK] start_gharmitra.bat exists
    echo.
    echo Testing if batch file can be executed...
    echo (This will start the application - you can close it after testing)
    echo.
    pause
    call "start_gharmitra.bat"
) else (
    echo [ERROR] No launcher batch file found!
    echo Expected: START_GHARMITRA.bat or start_gharmitra.bat
    pause
    exit /b 1
)
