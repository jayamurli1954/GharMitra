# 📤 Manual Push Instructions - Render Setup Changes

Due to persistent git lock file issues, please follow these **manual steps** to commit and push the changes.

---

## ✅ Files to Commit

1. `backend/requirements.txt` - Updated with `asyncpg` driver
2. `RENDER_SETUP_GUIDE.md` - Complete Render deployment guide
3. `RENDER_SETUP_REVIEW.md` - Review summary
4. `PUSH_RENDER_SETUP.bat` - Helper script

---

## 🔧 Step-by-Step Instructions

### Step 1: Remove Git Lock File

**Open PowerShell** in the project directory and run:

```powershell
cd D:\SanMitra_Tech\GharMitra
Remove-Item -Path .git\index.lock -Force -ErrorAction SilentlyContinue
```

**OR** manually delete the file:
- Navigate to: `D:\SanMitra_Tech\GharMitra\.git\`
- Delete: `index.lock` (if it exists)

---

### Step 2: Close All Git Processes

**In PowerShell**, run:

```powershell
Get-Process | Where-Object {$_.ProcessName -like "*git*"} | Stop-Process -Force
```

**OR** check Task Manager:
- Press `Ctrl + Shift + Esc`
- Look for any `git.exe` processes
- End them if found

---

### Step 3: Stage Files

**In PowerShell**, run:

```powershell
cd D:\SanMitra_Tech\GharMitra
git add backend/requirements.txt
git add RENDER_SETUP_GUIDE.md
git add RENDER_SETUP_REVIEW.md
git add PUSH_RENDER_SETUP.bat
```

---

### Step 4: Commit

```powershell
git commit -m "Add asyncpg driver for PostgreSQL and Render setup guides" -m "- Updated requirements.txt to use asyncpg instead of psycopg2-binary for async FastAPI" -m "- Added RENDER_SETUP_GUIDE.md with complete Render deployment steps" -m "- Added RENDER_SETUP_REVIEW.md summarizing key findings from Render_Cloudsetup.txt" -m "- Added PUSH_RENDER_SETUP.bat for easy deployment"
```

---

### Step 5: Push to GitHub

```powershell
git push origin main
```

**Note:** If push fails due to network issues, try again later or check your internet connection.

---

## 🚀 Alternative: Use Git GUI

If command line continues to have issues:

1. **Open Git GUI** or **GitHub Desktop**
2. **Stage** the files:
   - `backend/requirements.txt`
   - `RENDER_SETUP_GUIDE.md`
   - `RENDER_SETUP_REVIEW.md`
   - `PUSH_RENDER_SETUP.bat`
3. **Commit** with message:
   ```
   Add asyncpg driver for PostgreSQL and Render setup guides
   
   - Updated requirements.txt to use asyncpg instead of psycopg2-binary for async FastAPI
   - Added RENDER_SETUP_GUIDE.md with complete Render deployment steps
   - Added RENDER_SETUP_REVIEW.md summarizing key findings from Render_Cloudsetup.txt
   - Added PUSH_RENDER_SETUP.bat for easy deployment
   ```
4. **Push** to `origin/main`

---

## ✅ Verification

After pushing, verify on GitHub:

1. Go to: `https://github.com/jayamurli1954/GharMitra`
2. Check that `backend/requirements.txt` shows `asyncpg==0.29.0`
3. Verify new files appear:
   - `RENDER_SETUP_GUIDE.md`
   - `RENDER_SETUP_REVIEW.md`
   - `PUSH_RENDER_SETUP.bat`

---

## 🎯 Summary of Changes

### ✅ Updated `backend/requirements.txt`

**Added:**
```txt
asyncpg==0.29.0
```

**Commented out:**
```txt
# psycopg2-binary==2.9.9  # Commented - use asyncpg for async FastAPI
```

**Why:** `asyncpg` is required for async FastAPI with PostgreSQL. `psycopg2` blocks the event loop.

### ✅ New Files Created

1. **RENDER_SETUP_GUIDE.md** - Complete step-by-step guide for deploying to Render
2. **RENDER_SETUP_REVIEW.md** - Summary of findings from `Render_Cloudsetup.txt`
3. **PUSH_RENDER_SETUP.bat** - Helper script for future pushes

---

**Once pushed, Railway will automatically redeploy with the updated `asyncpg` driver!** ✅
