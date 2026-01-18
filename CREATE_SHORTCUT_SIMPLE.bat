@echo off
REM ============================================
REM GharMitra - Create Desktop Shortcut (Simple Method)
REM ============================================
REM This uses PowerShell to create the shortcut directly

echo.
echo ============================================
echo   GharMitra - Creating Desktop Shortcut
echo ============================================
echo.

set "SCRIPT_DIR=%~dp0"
set "BATCH_FILE=%SCRIPT_DIR%START_GHARMITRA.bat"

if not exist "%BATCH_FILE%" (
    set "BATCH_FILE=%SCRIPT_DIR%start_gharmitra.bat"
    if not exist "%BATCH_FILE%" (
        echo [ERROR] Could not find START_GHARMITRA.bat or start_gharmitra.bat
        pause
        exit /b 1
    )
)

echo Script directory: %SCRIPT_DIR%
echo Batch file: %BATCH_FILE%
echo.

REM Create shortcut using PowerShell
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\GharMitra.lnk'); $Shortcut.TargetPath = '%BATCH_FILE%'; $Shortcut.WorkingDirectory = '%SCRIPT_DIR%'; $Shortcut.Description = 'Launch GharMitra'; $Shortcut.IconLocation = 'shell32.dll,137'; $Shortcut.WindowStyle = 1; $Shortcut.Save(); Write-Host 'Shortcut created successfully!'"

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to create shortcut using PowerShell.
    echo Trying VBScript method...
    echo.
    cscript //nologo "%~dp0CREATE_SHORTCUT_IMPROVED.vbs"
    
    if errorlevel 1 (
        echo.
        echo [ERROR] Both methods failed.
        echo.
        echo Manual method:
        echo 1. Right-click on START_GHARMITRA.bat
        echo 2. Select "Create Shortcut"
        echo 3. Move the shortcut to your Desktop
        echo 4. Rename it to "GharMitra"
        pause
        exit /b 1
    )
)

echo.
echo ============================================
echo   Shortcut Created Successfully!
echo ============================================
echo.
echo Location: %USERPROFILE%\Desktop\GharMitra.lnk
echo Target: %BATCH_FILE%
echo.
echo You can now double-click "GharMitra" on your desktop.
echo.
pause
