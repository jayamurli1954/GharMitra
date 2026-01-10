@echo off
REM GharMitra Standalone Backend Server
REM This script starts the backend in standalone mode for demo

echo ========================================
echo GharMitra Standalone Backend Server
echo ========================================
echo.

REM Check if Python is installed (try both 'python' and 'py')
python --version >nul 2>&1
if errorlevel 1 (
    py --version >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Python is not installed or not in PATH
        echo Please install Python 3.11+ and try again
        echo.
        echo TIP: If Python is installed, try using 'py' command instead
        echo      Or activate your virtual environment first, then run:
        echo      python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
        pause
        exit /b 1
    )
    REM Use 'py' command if 'python' doesn't work
    set PYTHON_CMD=py
) else (
    set PYTHON_CMD=python
)

REM Navigate to backend directory
cd /d "%~dp0"

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    %PYTHON_CMD% -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/upgrade dependencies
echo.
echo Installing dependencies...
%PYTHON_CMD% -m pip install --upgrade pip --quiet
%PYTHON_CMD% -m pip install -r requirements.txt

REM Setup .env file if it doesn't exist
if not exist ".env" (
    echo.
    echo Setting up .env file...
    %PYTHON_CMD% setup_standalone_env.py
    if errorlevel 1 (
        echo.
        echo Creating basic .env file...
        echo DEPLOYMENT_MODE=standalone > .env
        echo DATABASE_URL=sqlite+aiosqlite:///./GharMitra.db >> .env
        echo SECRET_KEY=CHANGE_THIS_IN_PRODUCTION >> .env
        echo ENCRYPTION_KEY=CHANGE_THIS_IN_PRODUCTION >> .env
        echo.
        echo WARNING: Please update .env with secure SECRET_KEY and ENCRYPTION_KEY!
        echo Run: python setup_standalone_env.py
        echo.
    )
)

REM Get local IP address
echo.
echo Getting local IP address...
%PYTHON_CMD% get_local_ip.py
echo.

REM Set default port (8001 to avoid conflict with other projects)
if not defined PORT set PORT=8001

REM Start the server
echo ========================================
echo Starting GharMitra Backend Server...
echo ========================================
echo.
echo Server will be available at:
echo   - Local: http://localhost:%PORT%
echo   - Network: http://[YOUR_IP]:%PORT%
echo.
echo API Documentation: http://localhost:%PORT%/docs
echo Health Check: http://localhost:%PORT%/health
echo.
echo NOTE: Using port %PORT% (to avoid conflict with other projects)
echo       To change port, set PORT environment variable or edit .env file
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

%PYTHON_CMD% -m uvicorn app.main:app --host 0.0.0.0 --port %PORT% --reload


