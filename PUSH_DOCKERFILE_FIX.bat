@echo off
echo ========================================
echo Pushing Dockerfile Fix to GitHub
echo ========================================
echo.

REM Remove git lock files
if exist .git\index.lock del .git\index.lock /F /Q
if exist .git\objects\cc\tmp_obj_* del .git\objects\cc\tmp_obj_* /F /Q 2>nul

echo Adding files...
git add backend/Dockerfile
git add backend/.dockerignore
git add backend/requirements.txt
git add backend/nixpacks.toml
git add backend/runtime.txt
git add DOCKERFILE_SOLUTION.md
git add URGENT_RAILWAY_FIX.md
git add FINAL_RAILWAY_BUILD_FIX.md
git add FORCE_PYTHON_311_FIX.md
git add PYTHON_VERSION_FIX.md

echo.
echo Committing changes...
git commit -m "Add Dockerfile solution to fix Railway Python 3.13 build issue

- Add Dockerfile to force Python 3.11 (explicit base image)
- Add .dockerignore to exclude unnecessary files
- Update requirements.txt to pin pydantic version
- Add nixpacks.toml and runtime.txt as fallback
- Fixes pydantic-core build failure with Python 3.13"

echo.
echo Pushing to GitHub...
git push origin main

echo.
echo ========================================
if %ERRORLEVEL% EQU 0 (
    echo SUCCESS! Changes pushed to GitHub.
    echo.
    echo NEXT STEPS:
    echo 1. Go to Railway -^> Your Service -^> Settings
    echo 2. Clear the Build Command field (leave empty)
    echo 3. Railway will automatically use the Dockerfile
    echo 4. Save and wait for redeploy
) else (
    echo ERROR: Push failed.
    echo Check your internet connection and try again.
    echo.
    echo You can also push manually using:
    echo   git push origin main
)
echo ========================================
pause
