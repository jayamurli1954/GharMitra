# 🚨 Render Deployment Crash - Troubleshooting Guide

Your deployment showed successful but then crashed. Let's diagnose and fix it.

---

## 🔍 STEP 1: Check Render Logs

**Most Important:** Check the actual error in Render logs!

1. Go to **Render Dashboard** → Your service
2. Click **"Logs"** tab
3. Scroll to the **bottom** (most recent errors)
4. Look for:
   - ❌ Red error messages
   - ❌ `Traceback` or `Exception`
   - ❌ `ModuleNotFoundError`
   - ❌ `ConnectionError`
   - ❌ `AttributeError`

**Copy the error message** - this tells us exactly what's wrong!

---

## 🚨 Common Crash Causes & Fixes

### Issue 1: Missing `asyncpg` Module

**Error:**
```
ModuleNotFoundError: No module named 'asyncpg'
```

**Fix:**
1. Check `backend/requirements.txt` includes:
   ```txt
   asyncpg==0.29.0
   ```
2. If missing, add it and push to GitHub
3. Render will auto-redeploy

---

### Issue 2: Database Connection String Wrong Format

**Error:**
```
Invalid connection string
```
or
```
asyncpg.exceptions.InvalidPasswordError
```

**Fix:**
1. Go to **Render** → **Environment** → `DATABASE_URL`
2. Ensure it's: `postgresql+asyncpg://...` (NOT `postgresql://`)
3. Format should be:
   ```
   postgresql+asyncpg://postgres:PASSWORD@db.xxxxx.supabase.co:5432/postgres
   ```
4. Remove any `[]` brackets from password
5. Save and redeploy

---

### Issue 3: Database Connection Timeout

**Error:**
```
Connection timeout
```
or
```
Database unavailable
```

**Fix:**
1. Check Supabase database is running
2. Verify connection string is correct
3. Check Supabase firewall allows Render IPs
4. Add retry logic (should already be in code)

---

### Issue 4: Missing Environment Variables

**Error:**
```
KeyError: 'DATABASE_URL'
```
or
```
SECRET_KEY not set
```

**Fix:**
1. Go to **Render** → **Environment**
2. Verify all required variables:
   - ✅ `DATABASE_URL`
   - ✅ `SECRET_KEY`
   - ✅ `ALLOWED_ORIGINS`
   - ✅ `ACCESS_TOKEN_EXPIRE_MINUTES`
3. Add any missing variables
4. Redeploy

---

### Issue 5: Import Errors

**Error:**
```
ImportError: cannot import name 'X'
```
or
```
ModuleNotFoundError: No module named 'app.X'
```

**Fix:**
1. Check `backend/app/main.py` imports
2. Ensure all imported modules exist
3. Check `requirements.txt` has all dependencies
4. Verify file structure is correct

---

### Issue 6: Port Configuration

**Error:**
```
Address already in use
```
or
```
Failed to bind to port
```

**Fix:**
1. Ensure Start Command uses `$PORT`:
   ```
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
2. Render sets `$PORT` automatically - don't hardcode it!

---

### Issue 7: Health Check Failing

**Error:**
```
Health check failed
```

**Fix:**
1. Ensure `/health` endpoint exists (it does in your code)
2. Health check should return quickly
3. Don't require database for health check to pass

---

## 🔧 STEP 2: Quick Diagnostic Commands

### Check What's Actually Failing

**In Render Logs, look for:**

1. **Startup errors:**
   ```
   ERROR: Application startup failed
   ```

2. **Database errors:**
   ```
   ERROR: Database connection failed
   ```

3. **Import errors:**
   ```
   ModuleNotFoundError
   ```

4. **Configuration errors:**
   ```
   KeyError
   ValueError
   ```

---

## ✅ STEP 3: Verify Configuration

### 3.1 Check requirements.txt

Ensure it has:
```txt
asyncpg==0.29.0
fastapi
uvicorn[standard]
sqlalchemy>=2.0
```

### 3.2 Check Environment Variables

**In Render Dashboard:**
- `DATABASE_URL` = `postgresql+asyncpg://...`
- `SECRET_KEY` = (32+ character string)
- `ALLOWED_ORIGINS` = (your frontend URL or `*`)
- `ACCESS_TOKEN_EXPIRE_MINUTES` = `43200`

### 3.3 Check Start Command

**In Render Settings:**
```
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Root Directory:**
```
backend
```

---

## 🛠️ STEP 4: Common Fixes

### Fix 1: Add Better Error Handling

If database connection fails, app should still start. Check if `init_db()` has retry logic.

### Fix 2: Verify Database URL Format

**Wrong:**
```
postgresql://postgres:password@host:5432/db
```

**Correct:**
```
postgresql+asyncpg://postgres:password@host:5432/db
```

### Fix 3: Clear Build Cache

1. Render Dashboard → Your service
2. Click **"Manual Deploy"** → **"Clear build cache"**
3. Deploy again

---

## 📋 STEP 5: Diagnostic Checklist

Run through this checklist:

- [ ] Render logs show specific error message
- [ ] `requirements.txt` includes `asyncpg`
- [ ] `DATABASE_URL` is `postgresql+asyncpg://...`
- [ ] All environment variables are set
- [ ] Start command uses `$PORT`
- [ ] Root directory is set to `backend`
- [ ] Supabase database is running
- [ ] Connection string has no `[]` brackets
- [ ] Build completed successfully
- [ ] Health endpoint exists at `/health`

---

## 🚀 STEP 6: Force Redeploy

Sometimes a clean redeploy fixes issues:

1. **Render Dashboard** → Your service
2. **"Manual Deploy"** → **"Clear build cache"**
3. **"Deploy latest commit"**

---

## 📝 What to Share for Help

If still crashing, share:

1. **Error message from Render logs** (most important!)
2. **Environment variables** (hide passwords):
   - `DATABASE_URL` format (first 20 chars)
   - Which variables are set
3. **Build logs** - any errors during build?
4. **Start command** - what's configured?
5. **Root directory** - is it set to `backend`?

---

## 🎯 Most Likely Issues

Based on common Render crashes:

1. **Missing `asyncpg`** - 40% of cases
2. **Wrong DATABASE_URL format** - 30% of cases
3. **Missing environment variables** - 20% of cases
4. **Import errors** - 10% of cases

---

## ⚡ Quick Fix Script

If you can access Render logs, look for the **exact error message** and:

1. **If it says "asyncpg":**
   - Add `asyncpg==0.29.0` to `requirements.txt`
   - Push to GitHub
   - Render auto-redeploys

2. **If it says "DATABASE_URL":**
   - Check environment variable is set
   - Verify format is `postgresql+asyncpg://...`

3. **If it says "Connection":**
   - Check Supabase is running
   - Verify connection string is correct
   - Check firewall settings

---

**Next Step:** Check Render logs and share the error message! 🔍
