# Fix Virtual Environment Issue

## Problem
The virtual environment was created with a Python path that no longer exists:
- Old path: `C:\Users\Dell\anaconda3\python.exe`
- Current Python: `C:\Users\Muralidhar\AppData\Local\Programs\Python\Python311\python.exe`

## Solution

### Option 1: Use the Fix Script (Easiest)

1. **Deactivate current venv** (if active):
   ```powershell
   deactivate
   ```

2. **Run the fix script**:
   ```powershell
   .\fix_venv.bat
   ```

3. **Activate the new venv**:
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

4. **Start the server**:
   ```powershell
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
   ```

---

### Option 2: Manual Fix

1. **Deactivate current venv** (if active):
   ```powershell
   deactivate
   ```

2. **Delete old virtual environment**:
   ```powershell
   Remove-Item -Recurse -Force venv
   ```

3. **Create new virtual environment**:
   ```powershell
   python -m venv venv
   ```

4. **Activate new virtual environment**:
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

5. **Upgrade pip**:
   ```powershell
   python -m pip install --upgrade pip
   ```

6. **Install dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

7. **Start the server**:
   ```powershell
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
   ```

---

## Verification

After fixing, verify Python path:
```powershell
python --version
where.exe python
```

You should see:
- Python 3.11.9 (or similar)
- Path pointing to your current Python installation

---

## Notes

- The database (`gharmitra.db`) will NOT be affected by this fix
- All your data is safe
- Only the Python environment is being recreated


