@echo off
REM ============================================
REM GharMitra - Kill All Port Processes
REM ============================================
REM This script kills all processes using ports 8001 and 3006
REM Can be run standalone or called from other scripts

setlocal enabledelayedexpansion

echo.
echo ============================================
echo   GharMitra - Killing Port Processes
echo ============================================
echo.

set "PORTS_KILLED=0"

REM Kill all processes on port 8001 (Backend)
echo Checking port 8001 (Backend)...
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr :8001') do (
    set "PID=%%a"
    if not "!PID!"=="" (
        echo   - Killing process !PID! on port 8001...
        taskkill /PID !PID! /F >nul 2>&1
        if !errorlevel!==0 (
            set /a PORTS_KILLED+=1
        )
    )
)

REM Kill all processes on port 3006 (Frontend)
echo Checking port 3006 (Frontend)...
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr :3006') do (
    set "PID=%%a"
    if not "!PID!"=="" (
        echo   - Killing process !PID! on port 3006...
        taskkill /PID !PID! /F >nul 2>&1
        if !errorlevel!==0 (
            set /a PORTS_KILLED+=1
        )
    )
)

REM Kill Python uvicorn processes (Backend)
echo Checking for Python uvicorn processes...
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq python.exe" /FO CSV 2^>nul ^| findstr /V "INFO:"') do (
    set "PID=%%a"
    set "PID=!PID:"=!"
    if not "!PID!"=="" (
        wmic process where "ProcessId=!PID!" get CommandLine /format:list 2^>nul | findstr /I uvicorn >nul
        if !errorlevel!==0 (
            echo   - Killing Python uvicorn process !PID!...
            taskkill /PID !PID! /F >nul 2>&1
            if !errorlevel!==0 (
                set /a PORTS_KILLED+=1
            )
        )
    )
)

REM Kill Node webpack processes (Frontend)
echo Checking for Node webpack processes...
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq node.exe" /FO CSV 2^>nul ^| findstr /V "INFO:"') do (
    set "PID=%%a"
    set "PID=!PID:"=!"
    if not "!PID!"=="" (
        wmic process where "ProcessId=!PID!" get CommandLine /format:list 2^>nul | findstr /I webpack >nul
        if !errorlevel!==0 (
            echo   - Killing Node webpack process !PID!...
            taskkill /PID !PID! /F >nul 2>&1
            if !errorlevel!==0 (
                set /a PORTS_KILLED+=1
            )
        )
    )
)

if !PORTS_KILLED!==0 (
    echo.
    echo No processes found on ports 8001 or 3006.
) else (
    echo.
    echo Successfully killed !PORTS_KILLED! process(es).
)

REM Wait for ports to be released
echo.
echo Waiting for ports to be released...
timeout /t 2 /nobreak >nul

REM Verify ports are free
set "PORT_8001_FREE=1"
set "PORT_3006_FREE=1"
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr :8001') do (
    set "PORT_8001_FREE=0"
)
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr :3006') do (
    set "PORT_3006_FREE=0"
)

if !PORT_8001_FREE!==0 (
    echo [WARNING] Port 8001 may still be in use. Retrying...
    timeout /t 1 /nobreak >nul
    for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr :8001') do (
        taskkill /PID %%a /F >nul 2>&1
    )
)

if !PORT_3006_FREE!==0 (
    echo [WARNING] Port 3006 may still be in use. Retrying...
    timeout /t 1 /nobreak >nul
    for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr :3006') do (
        taskkill /PID %%a /F >nul 2>&1
    )
)

echo.
echo Ports should now be free.
echo.
timeout /t 1 /nobreak >nul
