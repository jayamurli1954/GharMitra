@echo off
REM Stop all backend processes

echo Stopping all GharMitra backend processes...

REM Kill processes on port 8001
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8001 ^| findstr LISTENING') do (
    echo Stopping process %%a on port 8001...
    taskkill /PID %%a /F
)

REM Kill processes on port 8002
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8002 ^| findstr LISTENING') do (
    echo Stopping process %%a on port 8002...
    taskkill /PID %%a /F
)

echo.
echo All backend processes stopped.
timeout /t 2 /nobreak >nul
