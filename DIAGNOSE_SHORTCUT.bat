@echo off
REM ============================================
REM GharMitra - Diagnose Desktop Shortcut Issue
REM ============================================

echo.
echo ============================================
echo   GharMitra - Shortcut Diagnostic
echo ============================================
echo.

set "DESKTOP=%USERPROFILE%\Desktop"
set "SHORTCUT=%DESKTOP%\GharMitra.lnk"
set "SCRIPT_DIR=%~dp0"

echo [1/5] Checking if shortcut exists...
if exist "%SHORTCUT%" (
    echo   [OK] Shortcut found: %SHORTCUT%
) else (
    echo   [ERROR] Shortcut NOT found: %SHORTCUT%
    echo   Please run CREATE_SHORTCUT.bat first.
    pause
    exit /b 1
)

echo.
echo [2/5] Checking batch file...
if exist "%SCRIPT_DIR%START_GHARMITRA.bat" (
    echo   [OK] START_GHARMITRA.bat exists
    set "BATCH_FILE=%SCRIPT_DIR%START_GHARMITRA.bat"
) else if exist "%SCRIPT_DIR%start_gharmitra.bat" (
    echo   [OK] start_gharmitra.bat exists
    set "BATCH_FILE=%SCRIPT_DIR%start_gharmitra.bat"
) else (
    echo   [ERROR] No launcher batch file found!
    pause
    exit /b 1
)

echo.
echo [3/5] Reading shortcut properties...
powershell -NoProfile -Command "$sh = (New-Object -ComObject WScript.Shell).CreateShortcut('%SHORTCUT%'); Write-Host '  Target:' $sh.TargetPath; Write-Host '  Working Directory:' $sh.WorkingDirectory; Write-Host '  Arguments:' $sh.Arguments; Write-Host '  Description:' $sh.Description"

echo.
echo [4/5] Testing batch file directly...
echo   Running: %BATCH_FILE%
echo   (This will start GharMitra - you can close it after testing)
echo.
pause
call "%BATCH_FILE%"

echo.
echo [5/5] Diagnostic complete.
echo.
echo If the batch file worked above but the shortcut doesn't:
echo   1. The shortcut might have wrong target path
echo   2. The shortcut might have wrong working directory
echo   3. Windows might be blocking the shortcut
echo.
echo Solution: Run CREATE_SHORTCUT_SIMPLE.bat to recreate the shortcut
echo.
pause
