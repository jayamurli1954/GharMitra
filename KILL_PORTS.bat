@echo off
echo Killing processes on ports 8001 and 3006...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8001"') do (
    echo Killing process %%a on port 8001
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3006"') do (
    echo Killing process %%a on port 3006
    taskkill /F /PID %%a >nul 2>&1
)
echo Done. Ports should be free now.
pause
