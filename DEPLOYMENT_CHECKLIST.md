# ✅ GharMitra Deployment Checklist

Use this checklist to ensure you complete all deployment steps correctly.

---

## 📋 Pre-Deployment

- [ ] Code is pushed to GitHub repository
- [ ] All local changes are committed
- [ ] You have GitHub account ready
- [ ] You have email address for account creation

---

## 🗄️ Step 1: Supabase Database Setup

- [ ] Created Supabase account at [supabase.com](https://supabase.com)
- [ ] Created new project named `gharmitra-db`
- [ ] Saved database password securely
- [ ] Found connection string (via "Connect" button or Project Settings → Database)
- [ ] Copied connection string
- [ ] Replaced `[YOUR-PASSWORD]` placeholder with actual password
- [ ] Connection string format: `postgresql://postgres:PASSWORD@db.xxxxx.supabase.co:5432/postgres`
- [ ] Tested connection (optional - can verify later)

**Connection String Saved:** `_________________________________________________`

---

## 🚂 Step 2: Railway Backend Setup

- [ ] Created Railway account at [railway.app](https://railway.app)
- [ ] Connected GitHub account
- [ ] Created new project from GitHub repository
- [ ] Set Root Directory to: `backend`
- [ ] Set Build Command to: `pip install -r requirements.txt`
- [ ] Set Start Command to: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Environment Variables Added:

- [ ] `DATABASE_URL` = `postgresql+psycopg2://postgres:PASSWORD@db.xxxxx.supabase.co:5432/postgres`
- [ ] `SECRET_KEY` = Generated 32+ character secret key
- [ ] `ALGORITHM` = `HS256`
- [ ] `ACCESS_TOKEN_EXPIRE_MINUTES` = `43200`
- [ ] `ALLOWED_ORIGINS` = (will update after frontend deployment)
- [ ] `DEBUG` = `False`
- [ ] `ENV` = `production`
- [ ] `LOG_LEVEL` = `INFO`

**Backend URL:** `https://________________________________.railway.app`

**Deployment Status:**
- [ ] Build successful
- [ ] Deployment successful
- [ ] Health check passed: `/health` endpoint returns `{"status":"healthy"}`

---

## 🎨 Step 3: Vercel Frontend Setup

- [ ] Created Vercel account at [vercel.com](https://vercel.com)
- [ ] Connected GitHub account
- [ ] Imported GharMitra project
- [ ] Set Framework to: `Other` or `Vite`
- [ ] Set Root Directory to: `web`
- [ ] Set Build Command to: `npm install && npm run build`
- [ ] Set Output Directory to: `dist`

### Environment Variables Added:

- [ ] `REACT_APP_API_URL` = `https://your-backend-url.railway.app/api`

**Frontend URL:** `https://________________________________.vercel.app`

**Deployment Status:**
- [ ] Build successful
- [ ] Deployment successful
- [ ] Frontend loads without errors

---

## 🔄 Step 4: Connect Frontend & Backend

- [ ] Updated Railway `ALLOWED_ORIGINS` with Vercel URL
- [ ] Added all Vercel URLs (main + preview branches if needed)
- [ ] Railway automatically redeployed with new CORS settings
- [ ] Verified CORS is working (no errors in browser console)

**CORS Origins Added:**
- `https://________________________________.vercel.app`
- `https://________________________________.vercel.app` (if preview branch)

---

## 🧪 Step 5: Testing

### Backend Tests:

- [ ] Health endpoint: `https://your-backend.railway.app/health` ✅
- [ ] API docs: `https://your-backend.railway.app/docs` (if enabled) ✅
- [ ] Database connection verified in logs ✅

### Frontend Tests:

- [ ] Frontend loads: `https://your-frontend.vercel.app` ✅
- [ ] Login page displays correctly ✅
- [ ] No console errors (F12 → Console) ✅
- [ ] API calls work (check Network tab) ✅

### Database Tests:

- [ ] Supabase tables created automatically ✅
- [ ] Can view tables in Supabase Table Editor ✅
- [ ] Database connection stable (check Railway logs) ✅

---

## 🔐 Step 6: Security Verification

- [ ] `SECRET_KEY` is strong (32+ characters, random) ✅
- [ ] `DEBUG` is set to `False` in production ✅
- [ ] Database password is not in code (only in environment variables) ✅
- [ ] CORS only allows your frontend domains ✅
- [ ] No sensitive data in Git repository ✅

---

## 📊 Step 7: Monitoring Setup

- [ ] Railway metrics dashboard accessible ✅
- [ ] Vercel analytics accessible ✅
- [ ] Supabase usage dashboard accessible ✅
- [ ] Set up alerts (optional) ✅

---

## 📝 Step 8: Documentation

- [ ] Saved all URLs (backend, frontend, database) ✅
- [ ] Saved all passwords/keys securely ✅
- [ ] Documented any custom configurations ✅
- [ ] Shared deployment info with team (if applicable) ✅

---

## ✅ Final Verification

- [ ] **Backend**: Accessible and healthy ✅
- [ ] **Frontend**: Accessible and functional ✅
- [ ] **Database**: Connected and tables created ✅
- [ ] **CORS**: Properly configured ✅
- [ ] **Environment Variables**: All set correctly ✅
- [ ] **Logs**: No critical errors ✅
- [ ] **User Access**: Can login and use application ✅

---

## 🎉 Deployment Complete!

**Your Live URLs:**
- Frontend: `https://________________________________.vercel.app`
- Backend: `https://________________________________.railway.app`
- Database: Managed by Supabase

**Next Steps:**
- [ ] Share frontend URL with users
- [ ] Monitor usage and performance
- [ ] Set up custom domain (optional)
- [ ] Configure backups (optional)

---

## 📞 Support Resources

- **Railway Docs**: [docs.railway.app](https://docs.railway.app)
- **Vercel Docs**: [vercel.com/docs](https://vercel.com/docs)
- **Supabase Docs**: [supabase.com/docs](https://supabase.com/docs)
- **Full Guide**: See `DEPLOYMENT_STEP_BY_STEP.md`

---

**Deployment Date:** `_________________`

**Deployed By:** `_________________`

**Notes:**
```
_________________________________________________
_________________________________________________
_________________________________________________
```
