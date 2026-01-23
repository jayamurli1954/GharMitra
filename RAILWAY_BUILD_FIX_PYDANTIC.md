# 🔧 Fix Railway Build Error: pydantic-core

## Error You're Seeing

```
ERROR: Failed building wheel for pydantic-core
Failed to build pydantic-core
error: failed-wheel-build-for-install
```

## Problem

`pydantic-core` requires Rust to build from source, but Railway's build environment may not have Rust installed or configured properly. Railway is trying to build it from source instead of using pre-built wheels.

## Solution 1: Update requirements.txt (Recommended)

Update your `backend/requirements.txt` to use versions that have pre-built wheels available:

1. **Open `backend/requirements.txt`**

2. **Update pydantic and related packages** to versions with pre-built wheels:

```txt
# Update these lines in requirements.txt
pydantic==2.5.3  # This version has pre-built wheels
pydantic-core==2.14.6  # Explicitly specify version with wheels
```

Or use the latest stable versions that definitely have wheels:

```txt
pydantic>=2.5.0,<3.0.0
```

3. **Commit and push to GitHub**
   - Railway will automatically redeploy with updated requirements

## Solution 2: Add Build Dependencies

If Solution 1 doesn't work, we can add Rust build tools. Create or update `backend/nixpacks.toml`:

```toml
[phases.setup]
nixPkgs = ["python311", "pip", "rustc", "cargo"]

[phases.install]
cmds = ["pip install -r requirements.txt"]

[start]
cmd = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
```

## Solution 3: Use Pre-built Wheels Only

Force pip to only use pre-built wheels (no building from source):

1. **Update Build Command in Railway:**
   - Go to Service → Settings → Build Command
   - Change to:
   ```
   pip install --only-binary :all: -r requirements.txt
   ```
   - This forces pip to only use pre-built wheels

2. **If that fails**, try:
   ```
   pip install --prefer-binary -r requirements.txt
   ```

## Solution 4: Pin Compatible Versions

Update `backend/requirements.txt` with versions known to work:

```txt
# Core Framework
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6

# Database
sqlalchemy==2.0.25
aiosqlite==0.19.0
psycopg2-binary==2.9.9

# Authentication & Security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
bcrypt==4.1.2
pydantic==2.5.3  # Use version with pre-built wheels
pydantic-settings==2.1.0
cryptography==42.0.0

# Environment & Configuration
python-dotenv==1.0.0

# CORS
fastapi-cors==0.0.6

# PDF Generation
reportlab==4.0.9
weasyprint==60.2

# Excel Export
openpyxl==3.1.2

# Date/Time
python-dateutil==2.8.2

# HTTP Client
requests==2.31.0

# Validation
email-validator==2.1.0

# Development
pytest==7.4.4
pytest-asyncio==0.23.3
httpx==0.26.0
black==24.1.1
flake8==7.0.0

# Optional: Email
aiosmtplib==3.0.1

# Optional: WebSockets
websockets==12.0

# Production
gunicorn==21.2.0
alembic==1.13.1
```

## Quick Fix (Try This First)

1. **Update Build Command in Railway:**
   - Service → Settings → Build Command
   - Change to:
   ```
   pip install --upgrade pip setuptools wheel && pip install -r requirements.txt
   ```

2. **Or try:**
   ```
   pip install --prefer-binary -r requirements.txt
   ```

## Recommended Action Plan

1. ✅ **First**: Try updating Build Command to use `--prefer-binary`
2. ✅ **If that fails**: Update `pydantic` version in `requirements.txt` to `2.5.3`
3. ✅ **If still failing**: Add `nixpacks.toml` with Rust build tools
4. ✅ **Commit and push** changes
5. ✅ **Railway will auto-redeploy**

---

**The quickest fix is usually updating the Build Command to prefer binary wheels!** ✅
