# GharMitra - Quick Start Guide

## 🚀 One-Click Desktop Shortcut

### Create Desktop Shortcut

**Option 1: Double-click `CREATE_SHORTCUT.bat`** (Easiest)

**Option 2: Double-click `create_desktop_shortcut.vbs`**

**Option 3: Right-click `START_GHARMITRA.bat` → Create Shortcut → Move to Desktop**

### Start GharMitra

1. **Double-click the "GharMitra" shortcut on your desktop**
2. The application will automatically:
   - ✅ Stop any running servers
   - ✅ Start backend server (port 8001)
   - ✅ Start frontend server (port 3006)
   - ✅ Open your browser to http://localhost:3006

### Stop GharMitra

- **Option 1:** Close the minimized "GharMitra Backend" and "GharMitra Frontend" windows
- **Option 2:** Double-click `STOP_GHARMITRA.bat`

## 📋 Manual Start (If Shortcut Doesn't Work)

1. Open Command Prompt or PowerShell
2. Navigate to the GharMitra folder:
   ```
   cd D:\SanMitra_Tech\GharMitra
   ```
3. Run the launcher:
   ```
   START_GHARMITRA.bat
   ```

## 🔧 Requirements

- **Python 3.x** (for backend)
- **Node.js** (for frontend)
- Both should be in your system PATH

## 🌐 Access URLs

- **Frontend:** http://localhost:3006
- **Backend API:** http://localhost:8001
- **API Docs:** http://localhost:8001/docs

## ❓ Troubleshooting

### "Python is not installed"
- Install Python from https://www.python.org/
- Make sure to check "Add Python to PATH" during installation

### "Node.js is not installed"
- Install Node.js from https://nodejs.org/
- Restart your computer after installation

### "Port already in use"
- Run `STOP_GHARMITRA.bat` to stop existing servers
- Or manually close any running GharMitra processes

### Browser doesn't open automatically
- Manually navigate to http://localhost:3006
- Check that both servers started successfully (check minimized windows)

## 📁 Important Files

- `START_GHARMITRA.bat` - Main launcher script
- `STOP_GHARMITRA.bat` - Stop all servers
- `CREATE_SHORTCUT.bat` - Create desktop shortcut
- `create_desktop_shortcut.vbs` - VBScript to create shortcut

---

**Enjoy using GharMitra! 🏠**
