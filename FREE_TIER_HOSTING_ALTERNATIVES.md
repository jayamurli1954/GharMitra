# Free Tier Cloud Hosting Alternatives for GharMitra

Since Render's free tier is already used for LegalMitra, here are the best **free tier alternatives** for hosting GharMitra.

---

## 🎯 Recommended Free Tier Stack

### **Option 1: Railway (Backend) + Vercel (Frontend) + Supabase (Database)** ⭐ **BEST CHOICE**

**Why this combination:**
- ✅ Railway: $5/month free credit (enough for small apps)
- ✅ Vercel: Unlimited free tier for React apps
- ✅ Supabase: Free PostgreSQL (500MB, perfect for pilot)

**Monthly Cost: ₹0** (within free tier limits)

---

### **Option 2: Fly.io (Backend) + Netlify (Frontend) + Neon (Database)** ⭐⭐ **MOST GENEROUS**

**Why this combination:**
- ✅ Fly.io: 3 shared VMs free (160GB outbound/month)
- ✅ Netlify: 100GB bandwidth free
- ✅ Neon: Free PostgreSQL (3GB storage, serverless)

**Monthly Cost: ₹0** (within free tier limits)

---

## 📋 Detailed Breakdown

### 🔹 Backend Hosting (Python/FastAPI)

#### **1. Railway** ⭐ **Recommended**

**Free Tier:**
- $5 credit/month (≈₹400)
- Auto-deploys from GitHub
- HTTPS included
- No credit card required initially

**Limitations:**
- Credits expire monthly
- Usage-based billing (can exceed free tier)
- App sleeps after inactivity (wakes on request)

**Deployment Steps:**
1. Sign up at [railway.app](https://railway.app) (GitHub login)
2. New Project → Deploy from GitHub
3. Select your GharMitra repo
4. Set Root Directory: `backend`
5. Add Environment Variables:
   ```
   DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/db
   SECRET_KEY=your-secret-key
   ALLOWED_ORIGINS=https://your-frontend.vercel.app
   ```
6. Build Command: `pip install -r requirements.txt`
7. Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

**Best for:** Quick deployment, GitHub integration, beginner-friendly

---

#### **2. Fly.io** ⭐⭐ **Most Generous Free Tier**

**Free Tier:**
- 3 shared VMs (256MB RAM each)
- 160GB outbound data/month
- 3GB persistent volumes
- Global edge network

**Limitations:**
- Requires credit card (but won't charge if within limits)
- Slightly more complex setup
- Apps sleep after 5 min inactivity

**Deployment Steps:**
1. Install Fly CLI: `iwr https://fly.io/install.ps1 -useb | iex`
2. Sign up: `fly auth signup`
3. Create app: `fly launch` (in `backend/` directory)
4. Add PostgreSQL: `fly postgres create --name gharmitra-db`
5. Attach DB: `fly postgres attach --app gharmitra-api`
6. Deploy: `fly deploy`

**Best for:** More resources, global deployment, production-ready

---

#### **3. PythonAnywhere** ⭐ **Simplest**

**Free Tier:**
- 1 web app
- 512MB disk space
- 1 MySQL database (can use PostgreSQL via external service)
- Limited CPU time

**Limitations:**
- No custom domains on free tier
- Limited to Python 3.8/3.9
- No background tasks
- Can't install all packages

**Best for:** Learning, simple demos (not recommended for production)

---

### 🔹 Frontend Hosting (React)

#### **1. Vercel** ⭐⭐⭐ **Best for React**

**Free Tier:**
- Unlimited deployments
- 100GB bandwidth/month
- Automatic HTTPS
- Global CDN
- Preview deployments

**Deployment Steps:**
1. Sign up at [vercel.com](https://vercel.com) (GitHub login)
2. Import Project → Select GharMitra repo
3. Framework Preset: **Vite** or **React**
4. Root Directory: `web`
5. Build Command: `npm run build`
6. Output Directory: `dist`
7. Environment Variables:
   ```
   VITE_API_BASE_URL=https://your-backend.railway.app
   ```
8. Deploy!

**Best for:** React apps, best performance, zero config

---

#### **2. Netlify** ⭐⭐ **Great Alternative**

**Free Tier:**
- 100GB bandwidth/month
- 300 build minutes/month
- Automatic HTTPS
- Form handling included

**Deployment Steps:**
1. Sign up at [netlify.com](https://netlify.com) (GitHub login)
2. Add new site → Import from Git
3. Build settings:
   - Base directory: `web`
   - Build command: `npm run build`
   - Publish directory: `web/dist`
4. Environment Variables:
   ```
   VITE_API_BASE_URL=https://your-backend.railway.app
   ```
5. Deploy!

**Best for:** JAMstack, forms, functions

---

#### **3. Cloudflare Pages** ⭐ **Fastest CDN**

**Free Tier:**
- Unlimited bandwidth
- Unlimited requests
- Global CDN (fastest)
- Automatic HTTPS

**Best for:** Maximum performance, high traffic

---

### 🔹 Database (PostgreSQL)

#### **1. Supabase** ⭐⭐⭐ **Best Free Tier**

**Free Tier:**
- 500MB database storage
- 2GB bandwidth/month
- Unlimited API requests
- Real-time subscriptions
- Auto backups

**Setup:**
1. Sign up at [supabase.com](https://supabase.com)
2. New Project → Choose region
3. Copy connection string:
   ```
   postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres
   ```
4. Use in backend `DATABASE_URL`

**Best for:** Easiest setup, includes auth, real-time features

---

#### **2. Neon** ⭐⭐ **Serverless PostgreSQL**

**Free Tier:**
- 3GB storage
- Unlimited projects
- Serverless (scales to zero)
- Branching (like Git for DB)

**Setup:**
1. Sign up at [neon.tech](https://neon.tech)
2. Create Project
3. Copy connection string
4. Use in backend `DATABASE_URL`

**Best for:** Serverless architecture, modern features

---

#### **3. Railway PostgreSQL** ⭐ **Integrated**

**Free Tier:**
- Included with Railway account
- 1GB storage
- Auto-backups

**Setup:**
1. In Railway project → New → PostgreSQL
2. Copy `DATABASE_URL` from variables
3. Use in backend

**Best for:** One-vendor solution, simple setup

---

#### **4. ElephantSQL** ⭐ **Reliable**

**Free Tier:**
- 20MB storage (very limited)
- 5 connections
- Shared instance

**Best for:** Testing only (too small for production)

---

## 🏗️ Complete Setup Guide: Railway + Vercel + Supabase

### Step 1: Setup Supabase Database

1. Go to [supabase.com](https://supabase.com)
2. Create account → New Project
3. Project name: `gharmitra-db`
4. Database password: (save this!)
5. Region: Choose closest to your users
6. Wait for provisioning (2-3 minutes)
7. Go to **Settings → Database**
8. Copy **Connection String** (URI format)

---

### Step 2: Deploy Backend to Railway

1. **Sign up Railway:**
   - Go to [railway.app](https://railway.app)
   - Sign up with GitHub

2. **Create Project:**
   - New Project → Deploy from GitHub
   - Select GharMitra repository

3. **Configure Service:**
   - Root Directory: `backend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

4. **Add Environment Variables:**
   ```
   DATABASE_URL=postgresql+psycopg2://postgres:[PASSWORD]@[SUPABASE_HOST]:5432/postgres
   SECRET_KEY=generate-random-32-char-string-here
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=43200
   ALLOWED_ORIGINS=https://gharmitra.vercel.app
   ENV=production
   ```

5. **Deploy:**
   - Railway auto-deploys
   - Copy the URL: `https://gharmitra-api.up.railway.app`

---

### Step 3: Update Backend for PostgreSQL

**Update `backend/app/db.py`:**

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL")

# Convert postgresql:// to postgresql+psycopg2:// if needed
if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

# For async operations (if using async)
engine = create_async_engine(
    DATABASE_URL.replace("psycopg2", "asyncpg") if "postgresql" in DATABASE_URL else DATABASE_URL,
    echo=False,
    pool_pre_ping=True
)

# For sync operations
sync_engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(bind=sync_engine, class_=AsyncSession)
```

**Update `requirements.txt` to ensure PostgreSQL support:**
```
psycopg2-binary==2.9.9  # Already present
alembic==1.13.1  # For migrations
```

**Run migrations:**
```bash
cd backend
alembic upgrade head
```

---

### Step 4: Deploy Frontend to Vercel

1. **Sign up Vercel:**
   - Go to [vercel.com](https://vercel.com)
   - Sign up with GitHub

2. **Import Project:**
   - Add New Project → Import Git Repository
   - Select GharMitra repository

3. **Configure:**
   - Framework Preset: **Vite**
   - Root Directory: `web`
   - Build Command: `npm run build` (or `npm install && npm run build`)
   - Output Directory: `dist`
   - Install Command: `npm install`

4. **Environment Variables:**
   ```
   VITE_API_BASE_URL=https://gharmitra-api.up.railway.app
   ```

5. **Deploy:**
   - Click Deploy
   - Vercel builds and deploys
   - You get: `https://gharmitra.vercel.app`

---

### Step 5: Update CORS in Backend

**Update `backend/app/main.py`:**

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://gharmitra.vercel.app",
        "http://localhost:3006",  # For local dev
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 💰 Cost Comparison (Free Tier Limits)

| Component | Railway | Fly.io | Vercel | Netlify | Supabase | Neon |
|-----------|---------|--------|--------|---------|----------|------|
| **Backend** | $5 credit/mo | 3 VMs free | N/A | N/A | N/A | N/A |
| **Frontend** | N/A | N/A | Unlimited | 100GB/mo | N/A | N/A |
| **Database** | 1GB free | Add-on | N/A | N/A | 500MB free | 3GB free |
| **Total Cost** | ₹0-400/mo | ₹0 | ₹0 | ₹0 | ₹0 | ₹0 |

---

## 🎯 Final Recommendation

### **For GharMitra (Accounting Software):**

**Best Stack:**
- **Backend:** Railway (easiest) or Fly.io (more resources)
- **Frontend:** Vercel (best React support)
- **Database:** Supabase (easiest) or Neon (more storage)

**Why:**
1. ✅ All free tier
2. ✅ Production-ready
3. ✅ Easy migrations later
4. ✅ Good performance
5. ✅ Automatic HTTPS
6. ✅ GitHub integration

---

## ⚠️ Important Notes

### **Free Tier Limitations:**

1. **Railway:**
   - Credits expire monthly
   - App may sleep (wakes on request, ~30s delay)
   - Monitor usage to avoid charges

2. **Fly.io:**
   - Apps sleep after 5 min inactivity
   - Requires credit card (won't charge if within limits)

3. **Vercel/Netlify:**
   - Bandwidth limits (usually enough for small apps)
   - Build time limits (usually sufficient)

4. **Supabase/Neon:**
   - Storage limits (500MB-3GB)
   - Connection limits
   - Perfect for pilot/testing phase

### **When to Upgrade:**

- **Backend:** When traffic exceeds free tier or need 24/7 uptime
- **Database:** When data exceeds 3GB or need more connections
- **Frontend:** Rarely need to upgrade (Vercel free tier is generous)

---

## 🚀 Quick Start Commands

### **Railway Deployment:**
```bash
# Install Railway CLI (optional)
npm i -g @railway/cli

# Login
railway login

# Link project
railway link

# Deploy
railway up
```

### **Fly.io Deployment:**
```bash
# Install Fly CLI
iwr https://fly.io/install.ps1 -useb | iex

# Login
fly auth login

# Launch app
cd backend
fly launch

# Deploy
fly deploy
```

### **Vercel Deployment:**
```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy
cd web
vercel
```

---

## 📚 Additional Resources

- [Railway Docs](https://docs.railway.app)
- [Fly.io Docs](https://fly.io/docs)
- [Vercel Docs](https://vercel.com/docs)
- [Supabase Docs](https://supabase.com/docs)
- [Neon Docs](https://neon.tech/docs)

---

## ✅ Checklist

- [ ] Create Supabase project and get connection string
- [ ] Deploy backend to Railway/Fly.io
- [ ] Update backend `DATABASE_URL` environment variable
- [ ] Run database migrations (Alembic)
- [ ] Test backend API endpoints
- [ ] Deploy frontend to Vercel
- [ ] Update frontend `VITE_API_BASE_URL`
- [ ] Update CORS in backend
- [ ] Test full application flow
- [ ] Set up custom domains (optional)

---

**You're all set! GharMitra will be running on free tier hosting.** 🎉
