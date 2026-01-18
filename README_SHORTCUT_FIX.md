# GharMitra - Desktop Shortcut Troubleshooting Guide

## Quick Fix

1. **Run `CREATE_SHORTCUT_SIMPLE.bat`** - This uses PowerShell to create the shortcut directly
2. **Or run `FIX_SHORTCUT.bat`** - This removes old shortcut and creates a new one

## If Shortcut Still Doesn't Work

### Method 1: Manual Creation (Most Reliable)

1. Navigate to: `D:\SanMitra_Tech\GharMitra`
2. Right-click on `START_GHARMITRA.bat`
3. Select **"Create Shortcut"**
4. A shortcut will be created in the same folder
5. **Cut** (Ctrl+X) the shortcut
6. Go to your Desktop
7. **Paste** (Ctrl+V) the shortcut
8. Rename it to **"GharMitra"** (optional)

### Method 2: Check Shortcut Properties

1. Right-click the "GharMitra" shortcut on your desktop
2. Select **"Properties"**
3. Verify:
   - **Target**: Should be `D:\SanMitra_Tech\GharMitra\START_GHARMITRA.bat`
   - **Start in**: Should be `D:\SanMitra_Tech\GharMitra`
   - **Run**: Should be "Normal window"
4. Click **"OK"**

### Method 3: Run Diagnostic

1. Run `DIAGNOSE_SHORTCUT.bat`
2. This will check:
   - If shortcut exists
   - If batch file exists
   - Shortcut properties
   - Test if batch file runs directly

## Common Issues

### Issue: Shortcut does nothing when clicked
**Solution**: Check if the batch file path is correct in shortcut properties

### Issue: "Windows cannot find the file"
**Solution**: The target path is wrong. Recreate the shortcut using Method 1 above.

### Issue: Window opens and closes immediately
**Solution**: This might be normal if there's an error. Check if Python and Node.js are installed.

### Issue: "Access Denied" or "Blocked"
**Solution**: 
1. Right-click shortcut → Properties
2. Click "Unblock" if available
3. Or run as Administrator

## Testing

To test if the batch file works:
1. Open Command Prompt
2. Navigate to: `cd D:\SanMitra_Tech\GharMitra`
3. Run: `START_GHARMITRA.bat`
4. If this works, the shortcut should work too

## Files Available

- `CREATE_SHORTCUT_SIMPLE.bat` - Creates shortcut using PowerShell
- `CREATE_SHORTCUT.bat` - Creates shortcut using VBScript
- `FIX_SHORTCUT.bat` - Removes old and creates new shortcut
- `DIAGNOSE_SHORTCUT.bat` - Diagnoses shortcut issues
- `TEST_SHORTCUT.bat` - Tests if shortcut works
