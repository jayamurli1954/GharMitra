@echo off
REM Stop any existing frontend process and start fresh

echo Checking for existing frontend processes...

REM Find and kill any process using port 3006
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3006 ^| findstr LISTENING') do (
    echo Found process %%a on port 3006, stopping...
    taskkill /PID %%a /F
)

REM Wait for port to be released
timeout /t 2 /nobreak >nul

REM Start the frontend development server
echo Starting GharMitra frontend on port 3006...
cd /d "%~dp0"
npm run dev
