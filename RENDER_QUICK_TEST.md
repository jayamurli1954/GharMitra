# 🧪 Quick Test Guide - Render Deployment

Quick verification steps for your Render deployment.

---

## ✅ 1. Test Backend Health (30 seconds)

**Open in browser:**
```
https://your-backend-name.onrender.com/health
```

**Expected:**
```json
{
  "status": "healthy",
  "database": "connected",
  "version": "v1"
}
```

✅ **If you see this:** Backend is working!

---

## ✅ 2. Test API Documentation (30 seconds)

**Open in browser:**
```
https://your-backend-name.onrender.com/docs
```

**Expected:** FastAPI Swagger UI with all endpoints

✅ **If you see this:** API is accessible!

---

## ✅ 3. Check Render Logs (1 minute)

1. Go to **Render Dashboard** → Your service
2. Click **"Logs"** tab
3. Look for:
   - ✅ `Application startup complete`
   - ✅ `Database connected`
   - ✅ No red error messages

✅ **If you see these:** Everything is running!

---

## ✅ 4. Test Database Connection (1 minute)

1. Go to **Supabase Dashboard** → Your project
2. Click **"Table Editor"**
3. Check if tables exist:
   - `users`
   - `societies`
   - `flats`

✅ **If tables exist:** Database is connected!

---

## ✅ 5. Test Frontend (If Deployed) (1 minute)

**Open in browser:**
```
https://your-frontend-name.vercel.app
```

**Expected:** GharMitra login page

**Check browser console (F12):**
- ✅ No red errors
- ✅ API calls working

---

## 🎯 All Tests Passed?

**Congratulations! Your deployment is successful!** 🎉

**Next Steps:**
1. Test user registration
2. Test login
3. Create a test society
4. Add test members
5. Test payment tracking

---

## 🚨 If Tests Fail

**Check:**
1. `RENDER_DEPLOYMENT_VERIFICATION.md` - Detailed troubleshooting
2. Render logs for specific errors
3. Environment variables in Render dashboard
4. Supabase connection string format

---

**Quick Reference:**
- Backend: `https://your-backend-name.onrender.com`
- Health: `/health`
- Docs: `/docs`
- Database: Supabase PostgreSQL
