@echo off
REM ============================================
REM GharMitra - Test Backend Connection
REM ============================================
REM This script tests if the backend is responding

echo.
echo ============================================
echo   Testing Backend Connection
echo ============================================
echo.

REM Check if port 8001 is listening
echo [1/2] Checking if port 8001 is listening...
netstat -ano | findstr :8001 | findstr LISTENING >nul
if errorlevel 1 (
    echo   [ERROR] No process is listening on port 8001
    echo   Backend is NOT running!
    echo.
    echo   Solution: Start the backend using START_BACKEND.bat
    pause
    exit /b 1
) else (
    echo   [OK] Port 8001 is listening
)

REM Try to connect to the backend
echo.
echo [2/2] Testing HTTP connection to backend...
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:8001/health' -UseBasicParsing -TimeoutSec 3; Write-Host '  [SUCCESS] Backend is responding!'; Write-Host '  Status Code:' $response.StatusCode; Write-Host '  Response:' $response.Content } catch { Write-Host '  [ERROR] Backend is NOT responding'; Write-Host '  Error:' $_.Exception.Message; Write-Host ''; Write-Host '  The backend process exists but is not responding.'; Write-Host '  Solution: Restart the backend using START_BACKEND.bat' }"

echo.
echo ============================================
echo   Test Complete
echo ============================================
echo.
pause
