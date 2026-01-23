# 🚀 GharMitra Cloud Hosting - Step-by-Step Guide

Complete guide to deploy GharMitra on **Railway (Backend) + Vercel (Frontend) + Supabase (Database)** - All Free Tier!

---

## 📋 Prerequisites

Before starting, ensure you have:
- ✅ GitHub account (free)
- ✅ Email address for account creation
- ✅ Your GharMitra code pushed to GitHub repository

---

## 🗄️ STEP 1: Setup Supabase Database (PostgreSQL)

### 1.1 Create Supabase Account

1. Go to [https://supabase.com](https://supabase.com)
2. Click **"Start your project"** or **"Sign up"**
3. Sign up with GitHub (recommended) or email
4. Verify your email if required

### 1.2 Create New Project

1. Click **"New Project"** button
2. Fill in the details:
   - **Name**: `gharmitra-db` (or any name you prefer)
   - **Database Password**: ⚠️ **IMPORTANT** - Create a strong password and **SAVE IT** (you'll need it later)
   - **Region**: Choose closest to your users (e.g., `Southeast Asia (Mumbai)` for India)
   - **Pricing Plan**: Select **"Free"** tier
3. Click **"Create new project"**
4. Wait 2-3 minutes for database provisioning

### 1.3 Get Database Connection String

**EASIEST METHOD - Use the "Connect" Button:**

1. **Look at the top-right of your Supabase dashboard**
   - You should see a **"Connect"** button next to "gharmitra-db / main PRODUCTION"
   - Click on this **"Connect"** button

2. **A popup dialog will open** titled "Connect to your project"
   - Make sure you're on the **"Connection String"** tab (it should be selected by default)
   - You'll see dropdowns: Type: "URI", Source: "Primary Database", Method: "Direct connection"

3. **Find the connection string field**
   - Look for the connection string in a text field
   - It will look like: `postgresql://postgres:xxxxx@db.xxxxx.supabase.co:5432/postgres`
   - ⚠️ **Note:** The password is already included in the string (it's the long string of characters after `postgres:`)

4. **Copy the connection string**
   - Click on the connection string field to select it
   - Or click the copy icon if available
   - **Copy the entire string** - it already contains your password!

5. **⚠️ IMPORTANT:** 
   - The connection string you see **already has your password** in it
   - You don't need to replace anything - just copy it as-is
   - **Save this connection string** somewhere safe (like a text file) - you'll need it for Railway

6. **Close the dialog** - Click the "X" button in the top-right corner

---

**What the connection string looks like:**
```
postgresql://postgres:your_actual_password_here@db.qmpmdsojnqllidbuvsoo.supabase.co:5432/postgres
```

**Note:** 
- The password is the long string between `postgres:` and `@`
- For Railway, use the **"Direct connection"** method (which you're already viewing)
- You'll paste this entire string into Railway's `DATABASE_URL` environment variable in the next step

---

**⚠️ IPv4 Warning:**
If you see a warning about "Not IPv4 compatible", that's okay for Railway. Railway supports IPv6. If you encounter connection issues later, you can use the "Session Pooler" method instead, but try Direct connection first.

---

## 🚂 STEP 2: Deploy Backend to Railway

### 2.1 Create Railway Account

1. Go to [https://railway.app](https://railway.app)
2. Click **"Start a New Project"**
3. Sign up with **GitHub** (recommended)
4. Authorize Railway to access your GitHub repositories

### 2.2 Create New Project

1. Click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Select your **GharMitra repository**
4. Railway will start detecting your project

### 2.3 Configure Backend Service

1. **Click on the service** (e.g., "gharkhata-backend" or your service name)
   - This opens the **Service** page (not Project Settings)
   - You should see tabs: "Deployments", "Variables", "Metrics", "Settings"

2. **Go to the "Settings" tab** (of the SERVICE, not the project)
   - This is the service-level settings, not project-level

3. **Configure the following:**

   **Root Directory:**
   - Find the **"Root Directory"** field (it might be under "Build" section)
   - Set to: `backend`
   - ⚠️ **Important**: This tells Railway to ignore root `package.json` files and use Python from `backend/` directory

   **Build Command:**
   ```
   pip install -r requirements.txt
   ```
   - Or leave it empty - Railway will auto-detect from `requirements.txt` in the `backend/` directory

   **Start Command:**
   ```
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

4. **Save changes** - Railway will automatically redeploy

### 2.4 Add Environment Variables

1. Go to **"Variables"** tab in Railway
2. Click **"New Variable"** and add each of these:

   **Required Variables:**

   ```
   DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@db.xxxxx.supabase.co:5432/postgres
   ```
   ⚠️ Replace `YOUR_PASSWORD` and the host with your actual Supabase connection string (use `psycopg2` driver)

   ```
   SECRET_KEY=your-super-secret-key-min-32-characters-change-this
   ```
   💡 Generate a random secret key (you can use: `python -c "import secrets; print(secrets.token_urlsafe(32))"`)

   ```
   ALGORITHM=HS256
   ```

   ```
   ACCESS_TOKEN_EXPIRE_MINUTES=43200
   ```

   ```
   ALLOWED_ORIGINS=https://gharmitra.vercel.app,https://your-custom-domain.vercel.app
   ```
   ⚠️ We'll update this after deploying frontend with the actual Vercel URL

   ```
   DEBUG=False
   ```

   ```
   ENV=production
   ```

   ```
   LOG_LEVEL=INFO
   ```

   **Optional Variables (can add later):**
   ```
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   FROM_EMAIL=noreply@gharmitra.com
   ```

### 2.5 Deploy Backend

1. Railway will automatically deploy when you save changes
2. Wait for deployment to complete (2-5 minutes)
3. Once deployed, Railway will show you a URL like:
   ```
   https://gharmitra-production.up.railway.app
   ```
4. **Copy this URL** - this is your backend API URL
5. Test the backend:
   - Visit: `https://your-backend-url.railway.app/health`
   - You should see: `{"status":"healthy","database":"connected","version":"v1"}`

### 2.6 Get Backend URL

1. Go to **"Settings"** → **"Networking"**
2. Copy the **"Public Domain"** URL
3. **Save this URL** - you'll need it for frontend configuration

---

## 🎨 STEP 3: Deploy Frontend to Vercel

### 3.1 Create Vercel Account

1. Go to [https://vercel.com](https://vercel.com)
2. Click **"Sign Up"**
3. Sign up with **GitHub** (recommended)
4. Authorize Vercel to access your repositories

### 3.2 Import Project

1. Click **"Add New..."** → **"Project"**
2. Select your **GharMitra repository**
3. Vercel will auto-detect settings

### 3.3 Configure Build Settings

1. In the project configuration:

   **Framework Preset:**
   - Select: **"Other"** or **"Vite"** (if available)

   **Root Directory:**
   - Click **"Edit"** and set to: `web`

   **Build Command:**
   ```
   npm install && npm run build
   ```

   **Output Directory:**
   ```
   dist
   ```

   **Install Command:**
   ```
   npm install
   ```

### 3.4 Add Environment Variables

1. Scroll down to **"Environment Variables"** section
2. Click **"Add"** and add:

   ```
   REACT_APP_API_URL=https://your-backend-url.railway.app/api
   ```
   ⚠️ Replace `your-backend-url.railway.app` with your actual Railway backend URL

   **Example:**
   ```
   REACT_APP_API_URL=https://gharmitra-production.up.railway.app/api
   ```

### 3.5 Deploy Frontend

1. Click **"Deploy"** button
2. Wait for build to complete (2-5 minutes)
3. Once deployed, Vercel will show you a URL like:
   ```
   https://gharmitra.vercel.app
   ```
4. **Copy this URL** - this is your frontend URL

### 3.6 Update Backend CORS

1. Go back to **Railway** → Your backend service → **Variables**
2. Update `ALLOWED_ORIGINS` to include your Vercel URL:
   ```
   ALLOWED_ORIGINS=https://gharmitra.vercel.app,https://gharmitra-git-main.vercel.app
   ```
   ⚠️ Vercel creates multiple URLs (main branch, preview branches) - add all that you need
3. Railway will automatically redeploy with new CORS settings

---

## 🔄 STEP 4: Run Database Migrations

### 4.1 Connect to Supabase Database

Your database tables will be created automatically when the backend starts, but you may need to run migrations for existing data.

### 4.2 Verify Database Connection

1. Go to **Supabase** → Your project → **Table Editor**
2. After backend deployment, you should see tables being created automatically
3. If tables don't appear, check Railway logs for errors

### 4.3 (Optional) Migrate Existing SQLite Data

If you have existing SQLite data to migrate:

1. **Export from SQLite:**
   ```bash
   sqlite3 gharmitra.db .dump > backup.sql
   ```

2. **Convert and Import to PostgreSQL:**
   - Use a migration script (we can create one if needed)
   - Or use Supabase SQL Editor to run converted SQL

---

## ✅ STEP 5: Test Your Deployment

### 5.1 Test Backend

1. Visit: `https://your-backend-url.railway.app/health`
   - Should return: `{"status":"healthy","database":"connected","version":"v1"}`

2. Visit: `https://your-backend-url.railway.app/docs`
   - Should show FastAPI documentation (if DEBUG is enabled)

### 5.2 Test Frontend

1. Visit your Vercel URL: `https://gharmitra.vercel.app`
2. You should see the GharMitra login page
3. Try logging in (if you have test users)
4. Check browser console (F12) for any errors

### 5.3 Test Database Connection

1. Go to **Supabase** → **Table Editor**
2. You should see tables like:
   - `users`
   - `societies`
   - `flats`
   - `transactions`
   - etc.

---

## 🔧 STEP 6: Troubleshooting

### Backend Not Starting

**Check Railway Logs:**
1. Go to Railway → Your service → **"Deployments"** tab
2. Click on the latest deployment
3. Check **"Build Logs"** and **"Deploy Logs"** for errors

**Common Issues:**
- ❌ **Database connection error**: Check `DATABASE_URL` is correct
- ❌ **Module not found**: Check `requirements.txt` includes all packages
- ❌ **Port error**: Ensure start command uses `$PORT` variable

### Frontend Not Connecting to Backend

**Check:**
1. Browser console (F12) for CORS errors
2. `REACT_APP_API_URL` environment variable in Vercel
3. Backend `ALLOWED_ORIGINS` includes your Vercel URL
4. Backend is running (check Railway status)

### Database Connection Issues

**Check:**
1. Supabase project is active (not paused)
2. Database password is correct in `DATABASE_URL`
3. Connection string format is correct
4. Railway can reach Supabase (check network settings)

---

## 📝 STEP 7: Post-Deployment Checklist

- [ ] Backend is accessible at Railway URL
- [ ] Frontend is accessible at Vercel URL
- [ ] Database tables are created in Supabase
- [ ] Can login to frontend
- [ ] API calls from frontend work
- [ ] CORS is properly configured
- [ ] Environment variables are set correctly
- [ ] Logs show no errors

---

## 🔐 STEP 8: Security Best Practices

### 8.1 Generate Strong Secret Key

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 8.2 Update CORS Origins

Only allow your actual frontend domains:
```
ALLOWED_ORIGINS=https://gharmitra.vercel.app
```

### 8.3 Database Security

- ✅ Never commit database passwords to Git
- ✅ Use environment variables for all secrets
- ✅ Enable Supabase database backups (available in paid tier)

---

## 📊 STEP 9: Monitor Your Deployment

### Railway Monitoring

1. Go to Railway → Your service → **"Metrics"**
2. Monitor:
   - CPU usage
   - Memory usage
   - Network traffic
   - Request count

### Vercel Monitoring

1. Go to Vercel → Your project → **"Analytics"**
2. Monitor:
   - Page views
   - Build times
   - Error rates

### Supabase Monitoring

1. Go to Supabase → Your project → **"Database"** → **"Usage"**
2. Monitor:
   - Database size
   - Connection count
   - Query performance

---

## 💰 Cost Summary (Free Tier)

| Service | Free Tier Limit | Your Usage |
|---------|----------------|------------|
| **Railway** | $5 credit/month | ~₹400/month |
| **Vercel** | Unlimited (within limits) | ₹0 |
| **Supabase** | 500MB database, 2GB bandwidth | ₹0 |
| **Total** | | **₹0-400/month** |

---

## 🚀 Next Steps

1. **Custom Domain** (Optional):
   - Add custom domain in Vercel
   - Update CORS in Railway
   - Update `REACT_APP_API_URL` in Vercel

2. **Enable Backups**:
   - Supabase: Automatic backups (paid tier)
   - Railway: Manual backups via database exports

3. **Scale Up** (When needed):
   - Railway: Upgrade to paid plan
   - Supabase: Upgrade for more storage
   - Vercel: Usually no need to upgrade

---

## 📞 Support & Resources

- **Railway Docs**: [https://docs.railway.app](https://docs.railway.app)
- **Vercel Docs**: [https://vercel.com/docs](https://vercel.com/docs)
- **Supabase Docs**: [https://supabase.com/docs](https://supabase.com/docs)

---

## ✅ Success!

Your GharMitra application is now live on the cloud! 🎉

**Your URLs:**
- Frontend: `https://gharmitra.vercel.app`
- Backend: `https://your-backend.railway.app`
- Database: Managed by Supabase

**Next:** Share your frontend URL with users and start using GharMitra!

---

## 🔄 Updating Your Deployment

### Update Backend:
1. Push changes to GitHub
2. Railway auto-deploys on push
3. Check deployment status in Railway

### Update Frontend:
1. Push changes to GitHub
2. Vercel auto-deploys on push
3. Check deployment status in Vercel

### Update Environment Variables:
1. Update in Railway/Vercel dashboard
2. Service will automatically restart/redeploy

---

**Happy Hosting! 🚀**
