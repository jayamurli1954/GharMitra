@echo off
REM Stop any existing backend process gracefully
echo Checking for existing backend processes...

REM Find and kill any python process using port 8001
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8001 ^| findstr LISTENING') do (
    echo Found process %%a on port 8001, stopping...
    taskkill /PID %%a /F
)

REM Wait for port to be released
timeout /t 2 /nobreak >nul

REM Start the backend
echo Starting GharMitra backend on port 8001...
cd /d "%~dp0"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

pause
