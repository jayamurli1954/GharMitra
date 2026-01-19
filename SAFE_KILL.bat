@echo off
REM Safe port killing script
setlocal enabledelayedexpansion

echo Checking ports 8001 and 3006...

REM Kill by port 8001
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8001') do (
    echo Killing PID %%a on port 8001...
    taskkill /PID %%a /F >nul 2>&1
)

REM Kill by port 3006
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3006') do (
    echo Killing PID %%a on port 3006...
    taskkill /PID %%a /F >nul 2>&1
)

timeout /t 2 /nobreak >nul
exit /b 0
