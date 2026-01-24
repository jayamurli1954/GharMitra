@echo off
echo ========================================
echo Pushing Render Setup Changes to GitHub
echo ========================================
echo.

REM Remove git lock file if it exists
echo [1/4] Removing git lock file...
if exist .git\index.lock (
    del /F /Q .git\index.lock
    echo Lock file removed.
) else (
    echo No lock file found.
)
echo.

REM Add files
echo [2/4] Staging files...
git add backend/requirements.txt RENDER_SETUP_GUIDE.md RENDER_SETUP_REVIEW.md
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to stage files!
    pause
    exit /b 1
)
echo Files staged successfully.
echo.

REM Commit
echo [3/4] Committing changes...
git commit -m "Add asyncpg driver for PostgreSQL and Render setup guides

- Updated requirements.txt to use asyncpg instead of psycopg2-binary for async FastAPI
- Added RENDER_SETUP_GUIDE.md with complete Render deployment steps
- Added RENDER_SETUP_REVIEW.md summarizing key findings from Render_Cloudsetup.txt"
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to commit!
    pause
    exit /b 1
)
echo Commit successful.
echo.

REM Push
echo [4/4] Pushing to GitHub...
git push origin main
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo WARNING: Push failed. This might be a network issue.
    echo Please check your internet connection and try again.
    echo.
    echo You can manually push later with:
    echo   git push origin main
    pause
    exit /b 1
)

echo.
echo ========================================
echo SUCCESS! Changes pushed to GitHub.
echo ========================================
echo.
pause
