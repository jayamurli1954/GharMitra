# ============================================
# GharMitra - Create Desktop Shortcut
# ============================================
# This PowerShell script creates a desktop shortcut
# that launches GharMitra with one click

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  GharMitra - Create Desktop Shortcut" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Get the script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$StartScript = Join-Path $ScriptDir "START_GHARMITRA.bat"

# Check if START_GHARMITRA.bat exists
if (-not (Test-Path $StartScript)) {
    Write-Host "[ERROR] START_GHARMITRA.bat not found!" -ForegroundColor Red
    Write-Host "Expected location: $StartScript" -ForegroundColor Yellow
    pause
    exit 1
}

# Get desktop path
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $DesktopPath "GharMitra.lnk"

# Create shortcut
try {
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut($ShortcutPath)
    $Shortcut.TargetPath = $StartScript
    $Shortcut.WorkingDirectory = $ScriptDir
    $Shortcut.Description = "Launch GharMitra - Apartment Accounting & Management System"
    $Shortcut.IconLocation = "shell32.dll,137"  # Application icon
    
    # Try to use GharMitra logo if available
    $LogoPath = Join-Path $ScriptDir "GharMitra_Logo.png"
    if (Test-Path $LogoPath) {
        # For PNG, we'd need to convert to ICO, but for now use default
        # You can manually change the icon later if needed
    }
    
    $Shortcut.Save()
    
    Write-Host "[SUCCESS] Desktop shortcut created!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Shortcut location: $ShortcutPath" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "You can now double-click 'GharMitra' on your desktop" -ForegroundColor Yellow
    Write-Host "to start the application." -ForegroundColor Yellow
    Write-Host ""
    
} catch {
    Write-Host "[ERROR] Failed to create shortcut: $_" -ForegroundColor Red
    pause
    exit 1
}

Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
