# 📤 Manual Push Instructions for Dockerfile Fix

## Quick Method: Use Batch File

**Run `PUSH_DOCKERFILE_FIX.bat`** - it will handle everything automatically.

---

## Manual Method: Git Commands

If the batch file doesn't work, run these commands manually:

### Step 1: Remove Lock Files

```powershell
cd D:\SanMitra_Tech\GharMitra
Remove-Item -Path .git\index.lock -Force -ErrorAction SilentlyContinue
```

### Step 2: Add Files

```bash
git add backend/Dockerfile
git add backend/.dockerignore
git add backend/requirements.txt
git add backend/nixpacks.toml
git add backend/runtime.txt
```

### Step 3: Commit

```bash
git commit -m "Add Dockerfile solution to fix Railway Python 3.13 build issue"
```

### Step 4: Push

```bash
git push origin main
```

---

## After Pushing

### Configure Railway to Use Dockerfile

1. **Go to Railway** → Your Service → **Settings** tab
2. **Find "Build Command"** field
3. **Clear it** (delete the current command, leave empty)
4. **Railway will automatically detect the Dockerfile**
5. **Save** - Railway will redeploy automatically

### Verify Start Command

Make sure **Start Command** is:
```
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Or leave it empty - the Dockerfile CMD will be used.

---

## What the Dockerfile Does

- ✅ Uses `python:3.11-slim` base image (forces Python 3.11)
- ✅ Installs packages using pre-built wheels only
- ✅ More reliable than Build Command
- ✅ Railway can't override the Python version

---

**Run `PUSH_DOCKERFILE_FIX.bat` or use the manual commands above!** ✅
