@echo off
echo ========================================
echo Committing and Pushing Deployment Files
echo ========================================
echo.

REM Remove git lock file if it exists
if exist .git\index.lock del .git\index.lock

REM Add modified files
echo Adding modified files...
git add backend/.env.example
git add backend/app/database.py

REM Add new deployment files
echo Adding new deployment files...
git add backend/generate_secret_key.py
git add backend/railway.json
git add railway.json
git add vercel.json
git add DEPLOYMENT_STEP_BY_STEP.md
git add DEPLOYMENT_CHECKLIST.md
git add QUICK_DEPLOYMENT_REFERENCE.md
git add HOSTING_GUIDE_INDEX.md
git add FREE_TIER_HOSTING_ALTERNATIVES.md

echo.
echo Committing changes...
git commit -m "Add cloud hosting deployment guides and configurations

- Add comprehensive deployment guides for Railway + Vercel + Supabase
- Update database.py to support PostgreSQL connections
- Add Railway and Vercel configuration files
- Add deployment checklist and quick reference guides
- Update .env.example with PostgreSQL examples
- Add secret key generator script"

echo.
echo Pushing to GitHub...
git push origin main

echo.
echo ========================================
echo Done! Check GitHub to verify changes.
echo ========================================
pause
