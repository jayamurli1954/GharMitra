# GharMitra Full Deployment Guide

This guide details how to deploy the **entire** GharMitra application (Backend API + Frontend Web App) to the cloud.

## 🏗️ Architecture Overview

*   **Backend**: Python (FastAPI) + SQLite Database.
    *   *Hosting*: Railway, Render, or Fly.io.
*   **Frontend**: React (Web Version).
    *   *Hosting*: Netlify, Vercel, or any static site host.

---

## Part 1: Backend Deployment (API)

First, we need to get the API running so we have a URL to give to the frontend.

### Option A: Railway (Recommended)

1.  **Sign Up**: Go to [Railway.app](https://railway.app/) and sign up with GitHub.
2.  **New Project**: Click "New Project" -> "Deploy from GitHub repo".
3.  **Select Repository**: Choose your GharMitra repository.
4.  **Add Variables**:
    *   Go to the "Variables" tab.
    *   Add `DATABASE_URL` = `sqlite+aiosqlite:///./GharMitra.db`
    *   Add `SECRET_KEY` = (Generate a random string)
    *   Add `ALLOWED_ORIGINS` = `*` (or your frontend URL later)
5.  **Settings**:
    *   Set the **Root Directory** to `/` (default) or `/backend` if your repo structure requires it. *Note: Based on current structure, `requirements.txt` is in `backend/`, so set Root Directory to `backend`.*
    *   Set **Build Command**: `pip install -r requirements.txt`
    *   Set **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6.  **Deploy**: Railway will deploy. Once done, it will give you a URL (e.g., `https://gharmitra-production.up.railway.app`).
    *   **Copy this URL**. You will need it for Part 2.

---

## Part 2: Frontend Deployment (Web)

Now we deploy the React frontend and connect it to your new backend.

### Option A: Netlify (Easiest)

1.  **Sign Up**: Go to [Netlify.com](https://www.netlify.com/) and login.
2.  **Import**: Click "Add new site" -> "Import an existing project".
3.  **Connect GitHub**: Authorize and select your repo.
4.  **Build Settings**:
    *   **Base directory**: `web`
    *   **Build command**: `npm run build`
    *   **Publish directory**: `web/dist`
5.  **Environment Variables**:
    *   Click "Show advanced" -> "New Variable".
    *   Key: `REACT_APP_API_URL`
    *   Value: `https://your-backend-url.railway.app/api` (Paste the URL from Part 1 and append `/api`).
6.  **Deploy**: Click "Deploy site".

### Handling Page Refreshes (SPA Redirects)
Since this is a Single Page App, reloading a page like `/members` might give a 404 error on Netlify.
To fix this, create a file named `_redirects` inside `web/public/` with this content:
```
/*  /index.html  200
```
Netlify will then route all requests to your app.

---

## Part 3: Connecting & Verifying

1.  Open your **Frontend URL** (e.g., `https://gharmitra.netlify.app`).
2.  Try to **Login** using your admin credentials.
3.  If it works, your Frontend is successfully talking to your Backend in the cloud!

## 💾 Important Note on Database (SQLite)

GharMitra uses **SQLite**, which is a file-based database (`GharMitra.db`).
*   **On Railway/Render**: The file system is often *ephemeral* (reset on redeploy).
*   **Consequence**: If you redeploy the backend, you might lose data unless you use a "Volume" or "Persistent Disk".
*   **Recommendation**:
    *   **Railway**: Add a Volume and point your `DATABASE_URL` to a path on that volume.
    *   **Production**: Eventually, consider switching to PostgreSQL (Railway provides this easily) for better data safety.

---

## Troubleshooting

*   **Login fails?** Check the Browser Console (F12). If you see "CORS error", ensure your Backend Variable `ALLOWED_ORIGINS` includes your Netlify URL (e.g., `https://gharmitra.netlify.app`).
*   **White screen?** Check if you set the `Base directory` correctly to `web`.
