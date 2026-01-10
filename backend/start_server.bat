@echo off
echo ============================================================
echo Starting GharMitra API Server
echo ============================================================
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Get local IP
echo Getting local IP address...
python get_local_ip.py
echo.

REM Start server
echo Starting server on http://0.0.0.0:8000
echo.
echo IMPORTANT:
echo - Make sure phone and laptop are on SAME WiFi
echo - Test from phone browser: http://YOUR_IP:8000/health
echo.
echo Press Ctrl+C to stop the server
echo ============================================================
echo.

python run.py

pause


