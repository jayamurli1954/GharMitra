# Force Restart GharMitra Backend
Write-Host "Stopping all Python/Uvicorn processes..." -ForegroundColor Yellow
Get-Process -Name "python" -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process -Name "uvicorn" -ErrorAction SilentlyContinue | Stop-Process -Force

Write-Host "Backend processes stopped." -ForegroundColor Green
Write-Host "Please start the backend again from the 'backend' directory using:" -ForegroundColor Cyan
Write-Host "python -m uvicorn app.main:app --reload --port 8001 --host 0.0.0.0" -ForegroundColor White
