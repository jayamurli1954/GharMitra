@echo off
echo ========================================
echo Pushing Railway Build Fix to GitHub
echo ========================================
echo.

REM Remove git lock file
if exist .git\index.lock del .git\index.lock

echo Adding files...
git add backend/runtime.txt
git add backend/nixpacks.toml
git add backend/requirements.txt
git add PYTHON_VERSION_FIX.md

echo.
echo Committing changes...
git commit -m "Fix Railway build: Use Python 3.11 and prefer binary wheels

- Add runtime.txt to force Python 3.11 (compatible with pydantic-core wheels)
- Update nixpacks.toml to prefer binary wheels
- Remove explicit pydantic-core version from requirements.txt
- Fixes build failure with Python 3.13 and pydantic-core compilation"

echo.
echo Pushing to GitHub...
git push origin main

echo.
echo ========================================
if %ERRORLEVEL% EQU 0 (
    echo SUCCESS! Changes pushed to GitHub.
    echo Railway will automatically redeploy with Python 3.11.
) else (
    echo ERROR: Push failed. Check your internet connection and try again.
)
echo ========================================
pause
