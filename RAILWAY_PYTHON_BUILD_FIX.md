# 🔧 Railway Python Build Fix

## Error You're Seeing

```
sh: 1: pip: not found
ERROR: failed to build: failed to solve: process "sh -c cd backend && pip install -r requirements.txt" did not complete successfully: exit code: 127
```

## Problem

Railway is detecting Node.js (from root `package.json` files) and using a Node.js buildpack, but your backend is Python. When it tries to run `pip install`, `pip` is not available in the Node.js environment.

## Solution

### Method 1: Set Root Directory in Railway Settings (Recommended)

1. **Go to Railway Dashboard**
   - Open your project
   - Click on your service

2. **Go to Settings Tab**
   - Click on **"Settings"** tab

3. **Set Root Directory**
   - Find **"Root Directory"** field
   - Set it to: `backend`
   - This tells Railway to ignore the root `package.json` files and focus on the `backend/` directory

4. **Verify Build Command**
   - **Build Command** should be empty or: `pip install -r requirements.txt`
   - Railway will auto-detect Python if `requirements.txt` is in the root directory (which will be `backend/` after setting root)

5. **Verify Start Command**
   - **Start Command** should be: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

6. **Save and Redeploy**
   - Railway will automatically redeploy
   - The build should now use Python instead of Node.js

### Method 2: Add Python Detection File

If Method 1 doesn't work, add a `runtime.txt` file to force Python:

1. **Create `backend/runtime.txt`**
   ```
   python-3.11
   ```
   Or whatever Python version you need (check `requirements.txt` or use `python-3.11`)

2. **Commit and push to GitHub**
   - Railway will auto-detect Python from `runtime.txt`

### Method 3: Use Nixpacks Configuration

Create or update `backend/nixpacks.toml`:

```toml
[phases.setup]
nixPkgs = ["python311", "pip"]

[phases.install]
cmds = ["pip install -r requirements.txt"]

[start]
cmd = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
```

## Quick Fix Steps

1. ✅ Go to Railway → Your Service → **Settings**
2. ✅ Set **Root Directory** to: `backend`
3. ✅ Set **Build Command** to: `pip install -r requirements.txt` (or leave empty for auto-detect)
4. ✅ Set **Start Command** to: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. ✅ Save changes
6. ✅ Railway will redeploy automatically

## Verify It's Working

After redeploying, check the build logs. You should see:
- ✅ Python being detected
- ✅ `pip install -r requirements.txt` running successfully
- ✅ No Node.js build steps
- ✅ Build completes successfully

## If Still Not Working

1. **Check for `requirements.txt` in `backend/` directory**
   - Railway needs this to detect Python

2. **Check Python version**
   - Add `backend/runtime.txt` with: `python-3.11`

3. **Clear build cache**
   - In Railway Settings → Advanced → Clear build cache
   - Redeploy

4. **Check build logs**
   - Look for what buildpack Railway is using
   - Should say "Python" not "Node"

---

**After setting Root Directory to `backend`, Railway should correctly detect Python and build successfully!** ✅
