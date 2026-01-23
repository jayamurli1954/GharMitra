# 🔍 How to Find Root Directory Setting in Railway

## The Issue

You're looking at **Project Settings**, but **Root Directory** is in **Service Settings**.

## Step-by-Step Instructions

### Step 1: Go to Your Service (Not Project Settings)

1. **From the Railway dashboard**, you should see your services listed
   - Look for the service card named something like "gharkhata-backend" or "GharMitra-backend"
   - It will have a GitHub icon (Octocat)

2. **Click on that service card** (not the project name)
   - This opens the **Service** page

### Step 2: Navigate to Service Settings

1. **You should now see tabs at the top:**
   - "Deployments"
   - "Variables" 
   - "Metrics"
   - **"Settings"** ← Click this one

2. **This is the SERVICE Settings** (different from Project Settings)

### Step 3: Find Root Directory

1. **Scroll down** in the Settings page
2. **Look for a section called "Build"** or "Configuration"
3. **Find the field labeled "Root Directory"**
   - It might be empty or set to `/` or `.`
   - This is where you need to set it to `backend`

### Step 4: Set Root Directory

1. **Click on the "Root Directory" field**
2. **Type or select:** `backend`
3. **Save the changes**

## Visual Guide

```
Railway Dashboard
├── Your Project
    ├── [Service Card: gharkhata-backend] ← CLICK HERE
    │   ├── Deployments tab
    │   ├── Variables tab
    │   ├── Metrics tab
    │   └── Settings tab ← THEN CLICK HERE
    │       └── Root Directory field ← FIND THIS
    └── [Postgres Service]
```

## Alternative: If You Still Can't Find It

### Method 1: Check Build Settings

1. Go to your service → **Settings** tab
2. Look for **"Build"** section
3. Root Directory should be there

### Method 2: Use Railway CLI

If the UI doesn't show it, you can use Railway CLI:

```bash
railway service
railway variables
```

### Method 3: Check railway.json

The Root Directory can also be set in `railway.json` file in your repository:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
  }
}
```

But the easiest way is through the UI.

## Quick Checklist

- [ ] Clicked on the **service** (not project)
- [ ] Went to **Settings** tab of the service
- [ ] Found **Root Directory** field
- [ ] Set it to: `backend`
- [ ] Saved changes
- [ ] Railway redeployed automatically

## Still Can't Find It?

1. **Make sure you're in the SERVICE settings**, not Project Settings
   - Project Settings = Settings for the entire project (members, webhooks, etc.)
   - Service Settings = Settings for one specific service (build, deploy, etc.)

2. **Try refreshing the page**

3. **Check if you have the right permissions**
   - You need to be the project owner or have admin access

4. **Look for "Build Configuration" or "Deploy Configuration"** section
   - Root Directory might be under one of these

---

**The key is: Service Settings, not Project Settings!** ✅
