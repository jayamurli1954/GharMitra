# GharMitra - Desktop Shortcut Setup Guide

## Quick Start

### Option 1: Automatic Setup (Recommended)
1. Double-click **`CREATE_DESKTOP_SHORTCUT.bat`**
2. A desktop shortcut named **"GharMitra"** will be created
3. Double-click the desktop shortcut to start GharMitra

### Option 2: Manual Setup
1. Right-click on **`START_GHARMITRA.bat`**
2. Select **"Create Shortcut"**
3. Move the shortcut to your Desktop
4. Rename it to **"GharMitra"** (optional)

## What the Shortcut Does

When you double-click the desktop shortcut, it will:

1. ✅ Stop any existing GharMitra servers (if running)
2. ✅ Start the backend server on port 8001
3. ✅ Start the frontend server on port 3005
4. ✅ Automatically open your browser to http://localhost:3006

## Files Created

- **`START_GHARMITRA.bat`** - Main launcher script
- **`STOP_GHARMITRA.bat`** - Stops all GharMitra servers
- **`CREATE_DESKTOP_SHORTCUT.ps1`** - PowerShell script to create shortcut
- **`CREATE_DESKTOP_SHORTCUT.bat`** - Batch wrapper for the PowerShell script

## Requirements

- Python 3.x (for backend)
- Node.js (for frontend)
- Both should be in your system PATH

## Troubleshooting

### Shortcut doesn't work
- Make sure Python and Node.js are installed
- Check that the `backend` and `web` directories exist
- Run `START_GHARMITRA.bat` directly to see error messages

### Port already in use
- Run `STOP_GHARMITRA.bat` to stop existing servers
- Or manually close any running GharMitra processes

### Browser doesn't open automatically
- Manually navigate to http://localhost:3006
- Check that the frontend server started successfully (check minimized windows)

## Stopping the Application

- Close the minimized "GharMitra Backend" and "GharMitra Frontend" windows
- Or run **`STOP_GHARMITRA.bat`**
