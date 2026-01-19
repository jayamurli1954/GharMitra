@echo off
echo ===================================================
echo   GharMitra - Push to GitHub
echo ===================================================

echo.
echo [1/3] Adding files to staging (Selectively)...

REM Add specific modified files
git add backend/app/routes/reports.py
git add start_gharmitra.bat

REM Add new documentation and scripts
git add USER_MANUAL.md
git add DEPLOYMENT_GUIDE_FULL.md
git add CLOUD_COMPARISON.md
git add ARCHITECTURE.md
git add FINAL_BACKUP.bat
git add PUSH_TO_GITHUB.bat
git add SAFE_KILL.bat
git add docs/images/

echo.
echo [2/3] Committing changes...
git commit -m "Final Update: Member Dues Fix, User Manual, architecture docs"

echo.
echo [3/3] Pushing to remote...
git push origin main

echo.
echo ===================================================
echo   Push Complete!
echo ===================================================
