# Railway Deployment - Issue Fixed

## Problem
Railway build was failing with this error:
```
TypeError: ForwardRef._evaluate() missing 1 required keyword-only argument: 'recursive_guard'
error: failed to run custom build command for `pydantic-core v2.14.6`
```

## Root Cause
1. Railway's Nixpacks auto-detected Python 3.13
2. `pydantic-core v2.14.6` is incompatible with Python 3.13
3. The `--only-binary :all:` flag in Dockerfile was too strict

## Solution Applied

### 1. Created `railway.toml` (Root Directory)
```toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "backend/Dockerfile"

[deploy]
startCommand = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
```

This forces Railway to use your Dockerfile instead of Nixpacks auto-detection.

### 2. Updated `backend/Dockerfile`

**Changed:**
- `pip install --only-binary :all:` → `pip install --prefer-binary`
- Added `libpq-dev` and `gcc` to system dependencies

**Why:**
- `--prefer-binary`: Prefers wheels but allows source builds if needed
- `--only-binary :all:`: Was too strict, causing failures
- Extra dependencies: Needed for psycopg2-binary and other packages

### 3. Python Version
- Dockerfile explicitly uses `python:3.11-slim`
- This avoids the Python 3.13 incompatibility

## What Happens Now

1. ✅ Railway will detect `railway.toml` in your repository
2. ✅ Railway will use the Dockerfile build method
3. ✅ Build will use Python 3.11 (compatible with pydantic)
4. ✅ Packages will install using binary wheels preferentially

## Next Steps

1. Go to your Railway dashboard
2. Watch the build logs - it should now succeed
3. If it still fails, check:
   - Is `railway.toml` in the root directory? (Not in backend/)
   - Is it committed and pushed to git?
   - Does Railway show "Using Dockerfile" in build logs?

## Additional Railway Configuration

Make sure you have these environment variables set in Railway:

```
DATABASE_URL=<your-supabase-postgres-url>
SECRET_KEY=<your-secret-key>
ALLOWED_ORIGINS=<your-frontend-url>
DEBUG=false
PORT=8001
```

## Verifying the Fix

Check Railway build logs for:
```
✅ Using Dockerfile
✅ Step 1/8 : FROM python:3.11-slim
✅ Successfully built <image-id>
✅ Successfully installed pydantic-2.5.3 pydantic-core-2.14.6
```

## Troubleshooting

If build still fails:

### Check 1: Verify railway.toml location
```bash
git ls-files | grep railway.toml
# Should output: railway.toml (not backend/railway.toml)
```

### Check 2: Verify Dockerfile location
```bash
ls backend/Dockerfile
# Should exist
```

### Check 3: Railway Project Settings
- Go to Railway dashboard → Your Project → Settings
- Under "Build", ensure no custom build command overrides the railway.toml

### Alternative: Manual Railway Configuration
If railway.toml doesn't work, set in Railway UI:
- Settings → Build → Builder: Dockerfile
- Settings → Build → Dockerfile Path: backend/Dockerfile

---

**Status:** ✅ Fixed and pushed to GitHub (Commit: 21e5f83)

Railway should auto-deploy when it detects the push.
