# 🚀 Render Setup Guide for GharMitra

Based on `Render_Cloudsetup.txt` review - Complete step-by-step guide for deploying GharMitra on Render.

---

## ⚠️ Important Note

Since you mentioned Render's free tier is already used for LegalMitra, this guide is for **reference** or if you decide to use Render's paid tier for GharMitra.

**Alternative Free Tier Options:**
- Railway + Supabase (recommended - see `DEPLOYMENT_STEP_BY_STEP.md`)
- Fly.io + Neon

---

## 📋 Prerequisites

- ✅ GitHub repository with GharMitra code
- ✅ Render account (or plan to create one)
- ✅ Supabase account (for PostgreSQL database)

---

## 🗄️ STEP 1: Setup Supabase PostgreSQL Database

### 1.1 Create Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Create new project: `gharmitra-db`
3. Save database password securely
4. Wait for provisioning (2-3 minutes)

### 1.2 Get Connection String

1. Click **"Connect"** button in Supabase dashboard
2. Go to **"Connection String"** tab
3. Select **"URI"** format
4. Copy the connection string:
   ```
   postgresql://postgres:PASSWORD@db.xxxxx.supabase.co:5432/postgres
   ```

### 1.3 Convert to Async Format

**For FastAPI (async), you MUST use `asyncpg` driver:**

Change from:
```
postgresql://postgres:PASSWORD@db.xxxxx.supabase.co:5432/postgres
```

To:
```
postgresql+asyncpg://postgres:PASSWORD@db.xxxxx.supabase.co:5432/postgres
```

**Key Point:** Just add `+asyncpg` after `postgresql` - nothing else changes!

---

## 🚀 STEP 2: Deploy Backend to Render

### 2.1 Create Render Account

1. Go to [render.com](https://render.com)
2. Sign up with GitHub
3. Authorize Render to access your repositories

### 2.2 Create Web Service

1. **Dashboard** → **"New"** → **"Web Service"**
2. **Connect GitHub repository** → Select GharMitra repo
3. **Configure service:**

   **Name:** `gharmitra-backend`
   
   **Environment:** `Python 3`
   
   **Region:** Choose closest to your users
   
   **Branch:** `main`
   
   **Root Directory:** `backend`
   
   **Build Command:**
   ```
   pip install -r requirements.txt
   ```
   
   **Start Command:**
   ```
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
   
   **Plan:** Choose based on your needs (Free tier spins down after 15 min)

### 2.3 Add Environment Variables

In Render dashboard → Your service → **"Environment"** tab:

**Required Variables:**

```
DATABASE_URL=postgresql+asyncpg://postgres:PASSWORD@db.xxxxx.supabase.co:5432/postgres
```
⚠️ **CRITICAL:** Must use `postgresql+asyncpg://` (not `postgresql://`)

```
SECRET_KEY=your-32-character-secret-key-here
```
💡 Generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`

```
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200
ALLOWED_ORIGINS=https://gharmitra.vercel.app
DEBUG=False
ENV=production
LOG_LEVEL=INFO
```

### 2.4 Deploy

1. Click **"Create Web Service"**
2. Render will build and deploy automatically
3. Wait for deployment (3-5 minutes)
4. Copy your service URL: `https://gharmitra-backend.onrender.com`

---

## ✅ STEP 3: Verify Requirements.txt

Based on `Render_Cloudsetup.txt`, ensure `backend/requirements.txt` includes:

```txt
fastapi
uvicorn[standard]
sqlalchemy>=2.0
asyncpg  # CRITICAL - must be present
python-jose[cryptography]
passlib[bcrypt]
pydantic[email]
python-dotenv
pydantic-settings
# ... other dependencies
```

**⚠️ Important:**
- ✅ Must have `asyncpg` (for async PostgreSQL)
- ❌ Do NOT use `psycopg2` or `psycopg2-binary` (sync driver, blocks event loop)

---

## 🔧 STEP 4: Update Database Configuration

### 4.1 Verify database.py Uses Async Engine

Your `backend/app/database.py` should use:

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

engine = create_async_engine(
    DATABASE_URL,  # Should be postgresql+asyncpg://...
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)
```

### 4.2 Add Retry Logic (Production-Safe)

Based on `Render_Cloudsetup.txt`, add retry logic to handle Supabase cold starts:

```python
async def init_db(retries: int = 5, delay: int = 3):
    """Initialize DB with retry - never crashes app startup"""
    for attempt in range(1, retries + 1):
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("✅ Database connected")
            return
        except Exception as e:
            logger.warning(f"DB connection failed (attempt {attempt}/{retries}): {e}")
            if attempt < retries:
                await asyncio.sleep(delay)
    
    logger.error("❌ Database unavailable - app continues without DB")
```

---

## 🎨 STEP 5: Deploy Frontend to Vercel

1. Go to [vercel.com](https://vercel.com)
2. Import GitHub repository
3. Configure:
   - **Framework:** React / Vite
   - **Root Directory:** `web`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
4. **Environment Variable:**
   ```
   REACT_APP_API_URL=https://gharmitra-backend.onrender.com/api
   ```
5. Deploy

---

## 🔐 STEP 6: Multi-Society Isolation (Important)

Based on `Render_Cloudsetup.txt`, ensure every table has `society_id`:

### 6.1 Database Schema

Every table must include:
```sql
society_id UUID NOT NULL REFERENCES societies(id)
```

### 6.2 Query Filtering

Always filter by `society_id` in queries:
```python
# Get society_id from authenticated user
society_id = user.society_id

# Filter queries
members = await session.execute(
    select(Member).where(Member.society_id == society_id)
)
```

---

## ✅ STEP 7: Health Check Endpoint

Add a health check that doesn't require DB:

```python
@router.get("/health")
async def health_check():
    db_status = "unknown"
    if engine:
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            db_status = "ok"
        except Exception:
            db_status = "down"
    
    return {
        "status": "ok",
        "database": db_status,
    }
```

This ensures Render health checks pass even if DB is temporarily unavailable.

---

## 🧪 STEP 8: Test Deployment

1. **Backend Health:**
   ```
   https://gharmitra-backend.onrender.com/health
   ```
   Should return: `{"status":"ok","database":"ok"}`

2. **Frontend:**
   - Visit your Vercel URL
   - Should load without errors
   - API calls should work

---

## 📝 Key Takeaways from Render_Cloudsetup.txt

### ✅ DO's

1. **Use `asyncpg` driver** - Required for async FastAPI
2. **Convert Supabase URL** - Add `+asyncpg` to connection string
3. **Add retry logic** - Handle Supabase cold starts
4. **Multi-tenant isolation** - Every table needs `society_id`
5. **Health checks** - Don't require DB to be up

### ❌ DON'Ts

1. **Don't use `psycopg2`** - Blocks async event loop
2. **Don't skip retry logic** - Supabase can be slow on cold start
3. **Don't forget `society_id`** - Security risk without it
4. **Don't crash on DB errors** - App should start even if DB is down

---

## 🔄 Migration from SQLite to PostgreSQL

If you have existing SQLite data:

1. **Export from SQLite:**
   ```bash
   sqlite3 gharmitra.db .dump > backup.sql
   ```

2. **Convert and import to PostgreSQL:**
   - Use migration script
   - Or use Supabase SQL Editor

3. **Verify data:**
   - Check record counts
   - Verify trial balance
   - Test member data

---

## 💰 Cost Estimate (Render Paid Tier)

| Component | Plan | Monthly Cost |
|-----------|------|--------------|
| **Backend** | Starter ($7/mo) | ₹600 |
| **PostgreSQL** | Starter ($7/mo) | ₹600 |
| **Frontend** | Vercel (Free) | ₹0 |
| **Total** | | **₹1,200/month** |

**Note:** Free tier spins down after 15 min inactivity (slow cold starts).

---

## 🎯 Final Checklist

- [ ] Supabase PostgreSQL created
- [ ] Connection string converted to `postgresql+asyncpg://`
- [ ] `asyncpg` added to `requirements.txt`
- [ ] Render Web Service created
- [ ] Environment variables set correctly
- [ ] Database retry logic implemented
- [ ] Health check endpoint added
- [ ] Multi-society isolation verified
- [ ] Frontend deployed to Vercel
- [ ] CORS configured correctly
- [ ] Tested end-to-end

---

**This guide is based on `Render_Cloudsetup.txt` and ensures production-ready deployment!** ✅
