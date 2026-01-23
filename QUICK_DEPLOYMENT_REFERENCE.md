# 🚀 Quick Deployment Reference

Quick checklist for deploying GharMitra to Railway + Vercel + Supabase.

---

## ⚡ Quick Steps

### 1. Supabase (Database) - 5 minutes
- [ ] Sign up at [supabase.com](https://supabase.com)
- [ ] Create new project → Name: `gharmitra-db`
- [ ] Save database password
- [ ] Copy connection string from "Connect" button or Project Settings → Database
- [ ] Format: `postgresql://postgres:PASSWORD@db.xxxxx.supabase.co:5432/postgres`
- [ ] Replace `[YOUR-PASSWORD]` placeholder with actual password

### 2. Railway (Backend) - 10 minutes
- [ ] Sign up at [railway.app](https://railway.app) with GitHub
- [ ] New Project → Deploy from GitHub → Select GharMitra repo
- [ ] Settings → Root Directory: `backend`
- [ ] Settings → Build Command: `pip install -r requirements.txt`
- [ ] Settings → Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- [ ] Variables → Add:
  ```
  DATABASE_URL=postgresql+psycopg2://postgres:PASSWORD@db.xxxxx.supabase.co:5432/postgres
  SECRET_KEY=generate-random-32-char-string
  ALLOWED_ORIGINS=https://gharmitra.vercel.app
  DEBUG=False
  ```
- [ ] Copy backend URL (e.g., `https://gharmitra-production.up.railway.app`)

### 3. Vercel (Frontend) - 10 minutes
- [ ] Sign up at [vercel.com](https://vercel.com) with GitHub
- [ ] Add New Project → Select GharMitra repo
- [ ] Framework: Other
- [ ] Root Directory: `web`
- [ ] Build Command: `npm install && npm run build`
- [ ] Output Directory: `dist`
- [ ] Environment Variables → Add:
  ```
  REACT_APP_API_URL=https://your-backend-url.railway.app/api
  ```
- [ ] Deploy → Copy frontend URL
- [ ] Update Railway `ALLOWED_ORIGINS` with Vercel URL

---

## 🔑 Environment Variables Cheat Sheet

### Railway (Backend)
```env
DATABASE_URL=postgresql+psycopg2://postgres:PASSWORD@db.xxxxx.supabase.co:5432/postgres
SECRET_KEY=your-32-char-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200
ALLOWED_ORIGINS=https://gharmitra.vercel.app
DEBUG=False
ENV=production
LOG_LEVEL=INFO
```

### Vercel (Frontend)
```env
REACT_APP_API_URL=https://your-backend.railway.app/api
```

---

## 🧪 Test URLs

After deployment, test these:

- **Backend Health**: `https://your-backend.railway.app/health`
- **Frontend**: `https://gharmitra.vercel.app`
- **API Docs**: `https://your-backend.railway.app/docs` (if DEBUG=True)

---

## 🐛 Common Issues

| Issue | Solution |
|-------|----------|
| Backend won't start | Check Railway logs, verify DATABASE_URL |
| Frontend can't connect | Check REACT_APP_API_URL and CORS settings |
| Database connection error | Verify password in DATABASE_URL |
| CORS error | Update ALLOWED_ORIGINS in Railway |

---

## 📞 Quick Links

- **Railway Dashboard**: [railway.app](https://railway.app)
- **Vercel Dashboard**: [vercel.com](https://vercel.com)
- **Supabase Dashboard**: [supabase.com](https://supabase.com)

---

**Full guide**: See `DEPLOYMENT_STEP_BY_STEP.md` for detailed instructions.
