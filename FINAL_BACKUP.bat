@echo off
echo ===================================================
echo   GharMitra - Final Data Backup
echo ===================================================

set "BACKEND_DIR=%~dp0\backend"
set "BACKUP_DIR=%~dp0\backups"

REM Create backup directory if it doesn't exist
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

REM Generate timestamp
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set "TIMESTAMP=%datetime:~0,4%-%datetime:~4,2%-%datetime:~6,2%_%datetime:~8,2%-%datetime:~10,2%"

echo.
echo [1/2] Backing up Database...
if exist "%BACKEND_DIR%\GharMitra.db" (
    copy "%BACKEND_DIR%\GharMitra.db" "%BACKUP_DIR%\GharMitra_FINAL_%TIMESTAMP%.db"
    echo    Success: Database backed up to backups\GharMitra_FINAL_%TIMESTAMP%.db
) else (
    echo    Error: Database file not found in %BACKEND_DIR%!
)

echo.
echo [2/2] Backing up Uploads...
if exist "%BACKEND_DIR%\uploads" (
    xcopy "%BACKEND_DIR%\uploads" "%BACKUP_DIR%\uploads_%TIMESTAMP%" /E /I /Q
    echo    Success: Uploads folder backed up.
) else (
    echo    Note: No uploads folder found to backup.
)

echo.
echo ===================================================
echo   Backup Complete!
echo ===================================================
pause
