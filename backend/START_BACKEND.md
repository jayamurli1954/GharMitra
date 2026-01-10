# Starting GharMitra Backend

## Quick Start

### Windows PowerShell:
```powershell
cd backend
.\start_standalone.bat
```

### Windows Command Prompt (CMD):
```cmd
cd backend
start_standalone.bat
```

### Linux/Mac:
```bash
cd backend
./start_standalone.sh
```

---

## Why PowerShell Needs `.\` Prefix?

PowerShell requires the `.\` prefix to run scripts in the current directory for security reasons. This prevents accidentally running malicious scripts.

**PowerShell:** `.\start_standalone.bat` ✅  
**Command Prompt:** `start_standalone.bat` ✅  
**Both work the same way!**

---

## Alternative: Manual Start

If the script doesn't work, you can start manually:

```bash
cd backend

# Activate virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1

# Windows CMD:
venv\Scripts\activate.bat

# Linux/Mac:
source venv/bin/activate

# Install dependencies (first time only)
pip install -r requirements.txt

# Start server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Troubleshooting

### "Execution Policy" Error in PowerShell?
```powershell
# Allow script execution (one time)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then run:
.\start_standalone.bat
```

### Still Not Working?
Use Command Prompt (CMD) instead of PowerShell:
```cmd
cd backend
start_standalone.bat
```

---

**The backend will start on:** `http://localhost:8000`



