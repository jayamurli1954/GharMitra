# Deployment Guide - Free Tier Hosting

Complete guide for deploying GharMitra backend on free tier hosting services.

## Quick Overview

| Service | Database | Backend | Total Cost | Best For |
|---------|----------|---------|------------|----------|
| Railway | SQLite (embedded) | $5 credit/month | **FREE** (first month) | Easy deployment |
| Render | SQLite (embedded) | Free tier | **FREE** | Long-term free hosting |
| Fly.io | SQLite (embedded) | Free tier | **FREE** | Global deployment |

**Note**: SQLite database is embedded in the application - no separate database hosting required!

---

## Option 1: Railway (Recommended for Beginners) ⭐

**Pros**: Easiest deployment, automatic HTTPS, GitHub integration, SQLite embedded (no database setup needed)
**Cons**: $5/month credit (runs out quickly under heavy use)

### Deploy to Railway

1. **Create Account**
   - Go to [Railway](https://railway.app/)
   - Sign up with GitHub

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Authorize Railway to access your GitHub
   - Select your repository

3. **Configure Environment Variables**
   - Go to your project → Variables
   - Add the following:
   ```
   DATABASE_URL=sqlite+aiosqlite:///./GharMitra.db
   SECRET_KEY=generate-random-32-character-string
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=43200
   ALLOWED_ORIGINS=*
   DEBUG=False
   ```

4. **Configure Build**
   - Railway auto-detects Python
   - It will use `requirements.txt`
   - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

5. **Deploy**
   - Railway will automatically deploy
   - You'll get a URL like: `https://your-app.railway.app`

6. **Custom Domain (Optional)**
   - Settings → Domains
   - Add your custom domain

---

## Option 2: Render (Best for Long-term Free) ⭐⭐

**Pros**: Completely free tier, no credit card required, SQLite embedded (no database setup)
**Cons**: Spins down after 15 min inactivity (slower cold starts)

### Deploy to Render

1. **Create Account**
   - Go to [Render](https://render.com/)
   - Sign up with GitHub

2. **Create Web Service**
   - Dashboard → New → Web Service
   - Connect your GitHub repository
   - Select the repository

3. **Configure Service**
   - Name: `GharMitra-api`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Plan: **Free**

4. **Environment Variables**
   - Add environment variables (same as Railway)
   - DATABASE_URL will point to SQLite database file

5. **Deploy**
   - Click "Create Web Service"
   - Render will build and deploy
   - You'll get a URL like: `https://GharMitra-api.onrender.com`

**Important**: Free tier spins down after 15 minutes of inactivity. First request after spin-down takes 30-60 seconds.

---

## Option 3: Fly.io (Advanced)

**Pros**: Global deployment, persistent storage
**Cons**: Requires credit card (not charged on free tier)

### Step 1: Install Fly CLI

```bash
# macOS
brew install flyctl

# Linux
curl -L https://fly.io/install.sh | sh

# Windows
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
```

### Step 2: Login and Launch

```bash
# Login
flyctl auth login

# Navigate to backend folder
cd backend

# Launch app
flyctl launch

# Follow prompts:
# - App name: GharMitra-api
# - Region: Choose closest to you
# - PostgreSQL: No
# - Redis: No
# - Deploy: Yes
```

### Step 3: Set Environment Variables

```bash
flyctl secrets set DATABASE_URL="sqlite+aiosqlite:///./GharMitra.db"
flyctl secrets set SECRET_KEY="your-secret-key"
flyctl secrets set ALLOWED_ORIGINS="*"
```

### Step 4: Deploy

```bash
flyctl deploy
```

---

## Local Development Setup

For testing before deployment:

### Run Backend Locally

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your settings

# Run server
python run.py
```

Visit: http://localhost:8000/docs

---

## Testing Your Deployment

### 1. Health Check
```bash
curl https://your-app-url.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "version": "v1"
}
```

### 2. Test Registration
```bash
curl -X POST https://your-app-url.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123",
    "name": "Test User",
    "apartment_number": "101",
    "role": "member"
  }'
```

### 3. Test Login
```bash
curl -X POST https://your-app-url.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'
```

---

## Cost Breakdown (Monthly)

### Completely Free Setup
- **SQLite Database**: FREE (embedded in application)
- **Render**: FREE (with limitations)
- **Total**: **$0/month** ✅

### Paid Alternative (Better Performance)
- **SQLite Database**: FREE (embedded)
- **Railway**: $5-10/month (pay as you go)
- **Total**: ~$5-10/month

### Production Setup
- **SQLite Database**: FREE (embedded) or migrate to PostgreSQL/MySQL for scale
- **DigitalOcean Droplet**: $6/month
- **Total**: ~$6/month

---

## Monitoring & Maintenance

### Railway
- Dashboard shows real-time metrics
- View logs in real-time
- Automatic deployments on Git push

### Render
- Dashboard → Logs
- Metrics tab for performance
- Manual deploys or auto-deploy on push

### SQLite Database
- Embedded in application
- Automatic database creation on first run
- Database file persists with application storage

---

## Troubleshooting

### "Could not connect to database"
- Verify DATABASE_URL environment variable is set correctly
- Check that SQLite database file has proper write permissions
- Ensure aiosqlite package is installed

### "Application Error" on deployment
- Check logs in hosting platform
- Verify all environment variables are set
- Check `requirements.txt` has all dependencies

### Slow cold starts (Render)
- Free tier spins down after inactivity
- Consider upgrading to paid tier for always-on
- Or use Railway/Fly.io

### CORS errors in React Native
- Add your mobile app origins to `ALLOWED_ORIGINS`
- Example: `ALLOWED_ORIGINS=*` (development) or specific domains (production)

---

## Security Checklist

Before going to production:

- [ ] Change `SECRET_KEY` to random 32+ character string
- [ ] Set `DEBUG=False`
- [ ] Use specific `ALLOWED_ORIGINS` (not `*`)
- [ ] Use environment variables for all secrets
- [ ] Enable HTTPS (automatic on all platforms)
- [ ] Set up regular SQLite database backups
- [ ] Ensure proper file permissions on SQLite database
- [ ] Monitor error logs regularly

---

## Scaling Up

When you outgrow free tier:

1. **Database**:
   - Keep SQLite for small-medium associations (< 100 units)
   - Migrate to PostgreSQL or MySQL for larger scale
   - Consider managed database services (DigitalOcean, AWS RDS)

2. **Backend**:
   - Railway: Increase resources ($5-20/month)
   - DigitalOcean: $6/month droplet
   - AWS/GCP: More expensive but highly scalable

3. **CDN**: Cloudflare (Free tier available)

---

## Backup Strategy

### SQLite Backups

**Manual Backup** (Simple file copy):
```bash
# Copy the database file
cp GharMitra.db GharMitra_backup_$(date +%Y%m%d).db
```

**Automated Backup Script**:
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
cp GharMitra.db "backups/GharMitra_$DATE.db"
# Keep only last 7 days of backups
find backups/ -name "GharMitra_*.db" -mtime +7 -delete
```

**Restore**:
```bash
# Simply replace the database file
cp GharMitra_backup_20250101.db GharMitra.db
```

**Important**:
- SQLite database is a single file - easy to backup
- Consider storing backups in cloud storage (S3, Google Drive, Dropbox)
- For production, use volume mounts to persist data

---

## Next Steps

1. Deploy backend using one of the options above
2. Update React Native app with your API URL
3. Test all features
4. Set up monitoring
5. Configure custom domain (optional)

## Support

- Railway: https://docs.railway.app
- Render: https://render.com/docs
- Fly.io: https://fly.io/docs
- SQLite: https://www.sqlite.org/docs.html
- SQLAlchemy: https://docs.sqlalchemy.org/

Good luck with your deployment! 🚀

