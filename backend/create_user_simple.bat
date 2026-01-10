@echo off
REM Simple script to create admin user
REM Make sure backend virtual environment is activated first!

echo ========================================
echo Creating Admin User for GharMitra
echo ========================================
echo.

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Run the Python script
python create_admin_user.py

pause


