# GharMitra - Manual Start Commands

## Quick Start

**Option 1: Use the batch file**
```
Double-click: START_MANUAL.bat
```

**Option 2: Run commands manually (see below)**

---

## Manual Commands

### Step 1: Open Command Prompt
Press `Win + R`, type `cmd`, press Enter

### Step 2: Navigate to GharMitra folder
```cmd
cd D:\SanMitra_Tech\GharMitra
```

### Step 3: Start Backend Server

**Open a NEW Command Prompt window** and run:

```cmd
cd D:\SanMitra_Tech\GharMitra\backend

REM If you have a virtual environment:
venv\Scripts\activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload

REM OR if no virtual environment:
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

**Keep this window open!** The backend will run here.

### Step 4: Start Frontend Server

**Open ANOTHER NEW Command Prompt window** and run:

```cmd
cd D:\SanMitra_Tech\GharMitra\web
npm run dev
```

**Keep this window open too!** The frontend will run here.

### Step 5: Open Browser

Once both servers are running, open your browser and go to:
```
http://localhost:3006
```

---

## One-Line Commands (Copy & Paste)

### Backend (in one command):
```cmd
cd /d D:\SanMitra_Tech\GharMitra\backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

### Frontend (in one command):
```cmd
cd /d D:\SanMitra_Tech\GharMitra\web && npm run dev
```

---

## Stop Servers

### Method 1: Close the Command Windows
Simply close the command prompt windows where the servers are running.

### Method 2: Use the Stop Script
```
Double-click: STOP_GHARMITRA.bat
```

### Method 3: Kill Ports Manually
```cmd
REM Kill backend (port 8001)
netstat -ano | findstr :8001
taskkill /PID <PID_NUMBER> /F

REM Kill frontend (port 3006)
netstat -ano | findstr :3006
taskkill /PID <PID_NUMBER> /F
```

---

## Troubleshooting

### "Python is not recognized"
- Install Python from https://www.python.org/
- Make sure to check "Add Python to PATH" during installation

### "npm is not recognized"
- Install Node.js from https://nodejs.org/
- Restart your computer after installation

### "Port already in use"
- Run `STOP_GHARMITRA.bat` first
- Or use `KILL_PORTS.bat` to kill all processes

### Backend won't start
- Check if Python is installed: `python --version`
- Check if you're in the correct directory: `cd D:\SanMitra_Tech\GharMitra\backend`
- Check if uvicorn is installed: `pip install uvicorn fastapi`

### Frontend won't start
- Check if Node.js is installed: `node --version`
- Check if you're in the correct directory: `cd D:\SanMitra_Tech\GharMitra\web`
- Install dependencies: `npm install`

---

## URLs

- **Frontend**: http://localhost:3006
- **Backend API**: http://localhost:8001
- **API Docs**: http://localhost:8001/docs

---

## Quick Reference Card

```
┌─────────────────────────────────────────┐
│  BACKEND (Terminal 1)                   │
├─────────────────────────────────────────┤
│  cd D:\SanMitra_Tech\GharMitra\backend │
│  python -m uvicorn app.main:app         │
│       --host 127.0.0.1                  │
│       --port 8001 --reload              │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  FRONTEND (Terminal 2)                  │
├─────────────────────────────────────────┤
│  cd D:\SanMitra_Tech\GharMitra\web     │
│  npm run dev                            │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  BROWSER                                 │
├─────────────────────────────────────────┤
│  http://localhost:3006                  │
└─────────────────────────────────────────┘
```
