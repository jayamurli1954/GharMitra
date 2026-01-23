# 🔧 Railway Environment Variables Fix

## Error You're Seeing

```
ERROR: failed to build: failed to solve: secret ACCESS_TOKEN_EXPIRE_MINUTES: not found
```

## Problem

Railway is trying to use `ACCESS_TOKEN_EXPIRE_MINUTES` as a **secret reference** (like `secret:ACCESS_TOKEN_EXPIRE_MINUTES`), but it should be a **regular environment variable**.

## Solution

### Step 1: Check Your Environment Variables in Railway

1. Go to your Railway project dashboard
2. Click on your service
3. Go to **"Variables"** tab
4. Check if `ACCESS_TOKEN_EXPIRE_MINUTES` exists

### Step 2: Add/Update the Variable Correctly

Make sure `ACCESS_TOKEN_EXPIRE_MINUTES` is set as a **regular variable**, not a secret:

1. In Railway Variables tab:
   - **Variable Name**: `ACCESS_TOKEN_EXPIRE_MINUTES`
   - **Value**: `43200` (just the number, no quotes, no `secret:` prefix)
   - **Type**: Should be "Variable" (not "Secret")

2. If it exists but is marked as a secret, delete it and recreate it as a regular variable

### Step 3: Ensure All Required Variables Are Set

Make sure you have ALL these variables set as **regular variables** (not secrets):

```
DATABASE_URL=postgresql+psycopg2://postgres:0pzNPoHFKncaeOYD@db.qmpmdsojnqllidbuvsoo.supabase.co:5432/postgres
SECRET_KEY=your-32-character-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200
ALLOWED_ORIGINS=https://gharmitra.vercel.app
DEBUG=False
ENV=production
LOG_LEVEL=INFO
```

### Step 4: Check for Secret References

If you see any variable with `secret:` prefix in Railway, remove that prefix. Variables should be:
- ✅ `ACCESS_TOKEN_EXPIRE_MINUTES=43200` (correct)
- ❌ `secret:ACCESS_TOKEN_EXPIRE_MINUTES` (wrong)

### Step 5: Redeploy

After fixing the variables:
1. Railway will automatically redeploy
2. Or manually trigger a redeploy from the Deployments tab
3. Check the build logs to verify it works

## Quick Fix Checklist

- [ ] `ACCESS_TOKEN_EXPIRE_MINUTES` exists in Variables tab
- [ ] It's set to `43200` (just the number)
- [ ] It's NOT marked as a secret
- [ ] All other required variables are set
- [ ] No variables have `secret:` prefix
- [ ] Redeploy triggered

## Alternative: Delete and Recreate

If the issue persists:

1. **Delete** the `ACCESS_TOKEN_EXPIRE_MINUTES` variable
2. **Create a new one** with:
   - Name: `ACCESS_TOKEN_EXPIRE_MINUTES`
   - Value: `43200`
   - Make sure it's a regular variable (not secret)
3. **Save** and let Railway redeploy

---

**After fixing, the build should succeed!** ✅
