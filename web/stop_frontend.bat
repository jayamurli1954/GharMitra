@echo off
REM Stop all frontend development servers

echo Stopping all GharMitra frontend processes...

REM Kill processes on port 3006
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3006 ^| findstr LISTENING') do (
    echo Stopping process %%a on port 3006...
    taskkill /PID %%a /F
)

echo.
echo All frontend processes stopped.
timeout /t 2 /nobreak >nul
