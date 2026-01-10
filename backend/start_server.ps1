# PowerShell script to start the backend server
Write-Host "Starting GharMitra Backend Server..." -ForegroundColor Green
Write-Host ""

# Change to backend directory
Set-Location $PSScriptRoot

# Activate virtual environment
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & "venv\Scripts\Activate.ps1"
} else {
    Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please create a virtual environment first:" -ForegroundColor Yellow
    Write-Host "  python -m venv venv" -ForegroundColor Cyan
    Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor Cyan
    Write-Host "  pip install -r requirements.txt" -ForegroundColor Cyan
    Read-Host "Press Enter to exit"
    exit 1
}

# Ensure pydantic-settings is installed
Write-Host "Checking dependencies..." -ForegroundColor Yellow
try {
    python -c "import pydantic_settings" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Installing pydantic-settings..." -ForegroundColor Yellow
        pip install pydantic-settings
    }
} catch {
    Write-Host "Installing pydantic-settings..." -ForegroundColor Yellow
    pip install pydantic-settings
}

# Check if FastAPI is installed
try {
    python -c "import fastapi" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Installing required packages..." -ForegroundColor Yellow
        pip install -r requirements.txt
    }
} catch {
    Write-Host "Installing required packages..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

# Start the server
Write-Host ""
Write-Host "Starting FastAPI server on http://0.0.0.0:8000" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""
python run.py

