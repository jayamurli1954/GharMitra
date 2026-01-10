# Windows Firewall Setup Script for GharMitra API
# Run this as Administrator to allow mobile device access

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "GharMitra API - Firewall Setup" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

Write-Host "Adding firewall rule for port 8000..." -ForegroundColor Yellow

# Remove existing rule if it exists
netsh advfirewall firewall delete rule name="GharMitra API" 2>$null

# Add new rule
netsh advfirewall firewall add rule name="GharMitra API" dir=in action=allow protocol=TCP localport=8000

if ($LASTEXITCODE -eq 0) {
    Write-Host "SUCCESS: Firewall rule added!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Port 8000 is now accessible from your network" -ForegroundColor Green
    Write-Host "Mobile devices on the same WiFi can now connect" -ForegroundColor Green
} else {
    Write-Host "ERROR: Failed to add firewall rule" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "1. Start backend: python run.py" -ForegroundColor White
Write-Host "2. Test from mobile browser: http://YOUR_IP:8000/health" -ForegroundColor White
Write-Host "3. Try login from mobile app" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Cyan


