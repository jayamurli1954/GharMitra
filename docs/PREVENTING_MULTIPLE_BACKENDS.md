# Preventing Multiple Backend Processes

## What Happened?

The backend server process on port 8001 (PID 67632) became unresponsive to termination commands but continued serving old cached code. This created a situation where:

1. The old process wouldn't die despite multiple kill attempts
2. A new process was started on port 8002 with updated code
3. This led to confusion about which backend was serving the frontend

## Root Causes

### 1. **Windows Process Management Issues**
- Windows processes can enter a state where they ignore termination signals
- Git Bash on Windows interferes with PowerShell process termination
- Socket handles remain in `LISTENING` state even after process termination fails

### 2. **No Graceful Shutdown Mechanism**
- The backend was started manually without proper process management
- No PID file tracking
- No cleanup on restart

### 3. **Manual Code Updates Without Reload**
- Updated `reports.py` code wasn't loaded by the existing process
- Uvicorn's `--reload` only watches for file changes in the same process
- Stale Python module imports remained in memory

## Solutions Implemented

### 1. **Startup Script** (`start_backend.bat`)
Located at: `backend/start_backend.bat`

This script:
- Checks for existing processes on port 8001
- Forcefully terminates them
- Waits for the port to be released
- Starts a fresh backend server

**Usage:**
```batch
cd D:\SanMitra_Tech\GharMitra\backend
start_backend.bat
```

### 2. **Cleanup Script** (`stop_backend.bat`)
Located at: `backend/stop_backend.bat`

This script:
- Stops all backend processes on ports 8001 and 8002
- Ensures clean shutdown before starting new instances

**Usage:**
```batch
cd D:\SanMitra_Tech\GharMitra\backend
stop_backend.bat
```

### 3. **Frontend Port Configuration**
The frontend now uses a configurable `TEMP_PORT` variable in `web/src/services/api.js`:

```javascript
const TEMP_PORT = '8002';  // Change to '8001' after restart
```

## Best Practices Going Forward

### 1. **Always Use the Startup Script**
Never start the backend manually with `python -m uvicorn`. Always use:
```batch
backend\start_backend.bat
```

### 2. **Stop Before Starting**
If you need to restart the backend:
```batch
backend\stop_backend.bat
backend\start_backend.bat
```

### 3. **After System Restart**
When you restart your computer:

1. **Update the frontend port back to 8001:**
   - Edit `web/src/services/api.js`
   - Change `const TEMP_PORT = '8002';` to `const TEMP_PORT = '8001';`
   - Rebuild: `cd web && npm run build`

2. **Start the backend:**
   ```batch
   cd backend
   start_backend.bat
   ```

### 4. **Verify Single Backend**
Check that only one backend is running:
```cmd
netstat -ano | findstr ":800"
```

You should see ONLY one LISTENING entry on port 8001.

### 5. **Use Uvicorn's Auto-Reload**
The startup script includes `--reload` flag, which automatically reloads when you modify Python files. You don't need to restart the server for code changes.

## Current State

### Temporary Configuration (Until Restart)
- **Backend Port**: 8002 (because 8001 is blocked)
- **Frontend**: Configured to use port 8002
- **Status**: Working correctly with updated flat_id code

### After System Restart
- **Backend Port**: 8001 (normal configuration)
- **Frontend**: Change TEMP_PORT to '8001' and rebuild
- **Status**: Will work normally

## Monitoring for Multiple Backends

Run this command periodically to check:
```cmd
netstat -ano | findstr ":800" | findstr "LISTENING"
```

**Expected output** (only ONE line):
```
TCP    0.0.0.0:8001           0.0.0.0:0              LISTENING       12345
```

**Problem indicators:**
- Multiple LISTENING entries
- Entries on both 8001 and 8002

## Emergency Cleanup

If you ever have multiple backends running:

1. Run the stop script:
   ```batch
   backend\stop_backend.bat
   ```

2. If that doesn't work, restart your computer

3. After restart, use `start_backend.bat` to start fresh

## Key Lesson

**Never manually kill and restart Python processes on Windows.** Always use the provided scripts that handle:
- Port cleanup
- Process termination
- Graceful startup
- Error handling

## Technical Details

### Why Process 67632 Wouldn't Die

1. **Windows Socket Linger**: The socket handle remained open even after termination attempts
2. **Git Bash Path Translation**: `/F` and `/PID` flags were interpreted as file paths by Git Bash
3. **Process State**: The process entered a zombie-like state where it continued functioning but was unresponsive to signals

### Why Port 8002 Solution Worked

- Fresh Python interpreter instance with no cached modules
- No socket conflicts
- Clean process startup
- Updated code loaded from disk

### Why Restart Fixes Everything

- Clears all process states
- Releases all socket handles
- Flushes Python module caches
- Resets Windows networking stack
