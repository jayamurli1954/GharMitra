# GharMitra Backup & Restore Guide

## Overview

GharMitra provides **three layers of backup protection** to ensure your data is never lost:

1. **Automatic Backups** - Created every time backend starts
2. **Manual Backups** - Create on-demand via UI
3. **Logout Backups** - Created when admin logs out

All backups are **verified for integrity** before being saved.

---

## 🔄 Automatic Backups

### When They Happen
- **Every time the backend starts**
- Runs before any database operations
- Takes ~1-2 seconds for typical database

### What Gets Backed Up
- Complete database snapshot using SQLite's native backup API
- All tables, indexes, and data
- Preserves database integrity

### Storage Location
```
backend/
  └── backups/
      ├── gharmitra_backup_20260113_154951.db
      ├── gharmitra_backup_20260113_152727.db
      └── ... (keeps last 10 backups)
```

### Automatic Cleanup
- System automatically keeps **last 10 backups**
- Older backups are deleted to save disk space
- Each backup is verified before old ones are removed

### Verification Process
Every backup is checked with:
```sql
PRAGMA quick_check
```
If verification fails, the backup is **deleted automatically** and an error is logged.

---

## 💾 Manual Backups

### How to Create

#### Via API:
```bash
POST /api/database/backup
Authorization: Bearer <admin-token>
```

Response:
```json
{
  "message": "Backup created successfully"
}
```

#### Via Frontend UI:
1. Go to **Settings** → **Data & Security**
2. Click **"Create Backup"** button
3. Wait for confirmation message
4. Backup appears in the list below

### When to Use Manual Backups

**Before:**
- Major data entry (bulk imports)
- System upgrades
- Configuration changes
- Financial year closing
- Testing new features

**Best Practice:**
- Create a backup before any risky operation
- Label backups mentally (e.g., "before bulk import")
- Keep at least 1-2 manual backups per month

---

## 🚪 Logout Backups

### Automatic Protection
When an **admin user logs out**, the system automatically triggers a backup in the background.

### How It Works
```javascript
// On logout
POST /api/database/backup-on-logout
```

The backup runs **asynchronously** so logout is instant, but data is protected.

### Why This Matters
- Protects against unexpected shutdowns
- Ensures you have a recent backup
- No extra effort required
- Runs in background

---

## 📋 Viewing Available Backups

### API Endpoint:
```bash
GET /api/database/backups
Authorization: Bearer <admin-token>
```

### Response Example:
```json
[
  {
    "filename": "gharmitra_backup_20260113_154951.db",
    "size_kb": 1331.2,
    "created_at": "2026-01-13T15:49:51"
  },
  {
    "filename": "gharmitra_backup_20260113_152727.db",
    "size_kb": 1328.5,
    "created_at": "2026-01-13T15:27:27"
  }
]
```

### Frontend UI:
1. Go to **Settings** → **Data & Security**
2. Scroll to **"Database Backups"** section
3. View list of all backups with:
   - Filename
   - Size
   - Creation date/time

---

## 🔄 Restoring from Backup

### ⚠️ IMPORTANT WARNINGS

**Before Restoring:**
1. ✅ **Create a fresh backup** of current data
2. ✅ **Notify all users** to log out
3. ✅ **Stop any ongoing transactions**
4. ✅ **Have a plan** to test the restored data

**After Restoring:**
1. ⚠️ **Restart the backend server** (required!)
2. ⚠️ **Verify data** before allowing user access
3. ⚠️ **Check recent transactions** weren't lost

### Restore Process

#### Step 1: Create Safety Backup
The system automatically creates a "pre-restore safety backup" before overwriting.

#### Step 2: Stop Backend (Recommended)
```bash
# Stop backend gracefully
taskkill /IM python.exe

# Or use the stop script
backend/stop_backend.bat
```

#### Step 3: Restore via API
```bash
POST /api/database/restore
Authorization: Bearer <admin-token>
Content-Type: application/json

{
  "filename": "gharmitra_backup_20260113_154951.db"
}
```

Response:
```json
{
  "message": "Restore completed. Please restart the backend server.",
  "safety_backup": "pre_restore_safety_20260113_160000.db"
}
```

#### Step 4: Restart Backend
```bash
# Start backend
backend/start_backend.bat

# Or manually
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### Step 5: Verify Data
1. Log in as admin
2. Check recent transactions
3. Verify member count
4. Test critical features

---

## 🛡️ Best Practices

### Regular Backups
- ✅ System does this automatically (10 backups)
- ✅ Create manual backups before major changes
- ✅ Export monthly backups to external storage

### External Storage
**Recommended:** Copy backups to external location weekly

```bash
# Windows
xcopy backend\backups\*.db "E:\GharMitra_Backups\" /Y /D

# Or use OneDrive/Google Drive/Dropbox
# Copy to: C:\Users\<Name>\OneDrive\GharMitra_Backups\
```

### Backup Retention
- **System:** Last 10 automatic backups
- **Manual:** Keep monthly backups indefinitely
- **External:** Keep yearly backups for 7 years (legal requirement)

### Testing Restores
**Test your backups quarterly:**

1. Copy production DB to test location
2. Restore from backup to test location
3. Verify data integrity
4. Document any issues

---

## 🔧 Manual Backup (Advanced)

### Via Command Line

#### 1. Using SQLite Backup API (Recommended)
```python
import sqlite3

# Connect to source
source = sqlite3.connect('gharmitra.db')
backup = sqlite3.connect('manual_backup.db')

# Perform backup
with backup:
    source.backup(backup)

source.close()
backup.close()

# Verify
verify = sqlite3.connect('manual_backup.db')
cursor = verify.cursor()
cursor.execute("PRAGMA integrity_check")
print(cursor.fetchone()[0])  # Should print "ok"
verify.close()
```

#### 2. Using File Copy (Quick but Less Safe)
```bash
# Stop backend first!
taskkill /IM python.exe

# Copy database
copy gharmitra.db gharmitra_manual_backup.db

# Restart backend
python -m uvicorn app.main:app
```

### Via SQLite Command Line
```bash
# Install sqlite3 CLI if needed
# Download from: https://www.sqlite.org/download.html

# Backup
sqlite3 gharmitra.db ".backup gharmitra_backup.db"

# Verify
sqlite3 gharmitra_backup.db "PRAGMA integrity_check"
```

---

## 🚨 Emergency Recovery

### If Backend Won't Start

1. **Check Database Integrity**
```bash
cd backend
python -c "
import sqlite3
conn = sqlite3.connect('gharmitra.db')
cursor = conn.cursor()
cursor.execute('PRAGMA integrity_check')
print(cursor.fetchone()[0])
conn.close()
"
```

2. **If Corrupted, Restore from Backup**
```bash
# Use most recent backup
copy backups\gharmitra_backup_YYYYMMDD_HHMMSS.db gharmitra.db

# Restart
python -m uvicorn app.main:app
```

3. **If No Backups Available**
```bash
# Try SQLite recovery
sqlite3 gharmitra_corrupted.db ".recover" | sqlite3 gharmitra_recovered.db
copy gharmitra_recovered.db gharmitra.db
```

### If Restore Fails

1. **Check Backup Integrity**
```bash
sqlite3 backups\gharmitra_backup_YYYYMMDD.db "PRAGMA integrity_check"
```

2. **Try Different Backup**
- List all backups
- Try second-most-recent
- Work backwards until you find a good one

3. **Check Disk Space**
```bash
# Windows
dir backend\
fsutil volume diskfree c:
```

4. **Contact Support**
- Email: support@gharmitra.com
- Include: Error messages, last successful backup date
- Attach: Diagnostic logs from `backend/logs/`

---

## 📊 Monitoring Backups

### Check Backup Health

#### Via API:
```bash
GET /api/database/health
```

Response:
```json
{
  "status": "healthy",
  "journal_mode": "wal",
  "size_mb": 1.3,
  "fragmentation_percent": 2.5,
  "last_backup": "2026-01-13T15:49:51",
  "backup_count": 10,
  "integrity": "ok"
}
```

#### Via Script:
```bash
cd backend
python app/utils/db_health.py
```

### Backup Alerts

**Set up alerts for:**
- Backup failures (check logs)
- Low disk space (< 1GB)
- Database size growth (> 100MB)
- Fragmentation (> 10%)

---

## 📝 Backup Checklist

### Daily (Automatic)
- [x] Backend startup creates backup
- [x] Logout triggers backup (for admins)
- [x] System maintains 10 recent backups

### Weekly (Manual)
- [ ] Create manual backup on Friday
- [ ] Copy backup to external drive
- [ ] Verify external backup integrity

### Monthly (Maintenance)
- [ ] Create labeled backup (e.g., "Dec_2025_Closing")
- [ ] Archive to long-term storage
- [ ] Test restore on test database
- [ ] Review backup storage space

### Quarterly (Compliance)
- [ ] Test full disaster recovery
- [ ] Document recovery time
- [ ] Update backup procedures
- [ ] Train staff on restore process

### Annually (Audit)
- [ ] Create end-of-year backup
- [ ] Store for 7 years (legal requirement)
- [ ] Review backup strategy
- [ ] Upgrade backup infrastructure

---

## 🔐 Security Considerations

### Backup Encryption (Future Enhancement)
Currently backups are **not encrypted**. For sensitive data:

**Recommended:**
- Store backups on encrypted drives (BitLocker)
- Use encrypted cloud storage (OneDrive with encryption)
- Limit access to backup folder (Windows permissions)

### Access Control
- Only **admin users** can create/restore backups
- Backup API requires authentication token
- Restore requires explicit admin confirmation

### Audit Trail
All backup/restore operations are logged:
- `backend/logs/app.log` - Backup creation/verification
- `backend/logs/audit.log` - Restore operations

---

## 💡 Tips & Tricks

### Naming Conventions
Backups use timestamp format: `gharmitra_backup_YYYYMMDD_HHMMSS.db`

Example:
- `gharmitra_backup_20260113_154951.db` = Jan 13, 2026, 3:49:51 PM

### Quick Commands

**List backups:**
```bash
dir backend\backups\gharmitra_backup_*.db
```

**Find latest backup:**
```bash
dir backend\backups\gharmitra_backup_*.db /O-D | findstr /R "gharmitra" | head -1
```

**Copy latest backup to desktop:**
```bash
copy backend\backups\gharmitra_backup_*.db %USERPROFILE%\Desktop\ /Y
```

### Backup Before:
- ✅ Software updates
- ✅ Database migrations
- ✅ Bulk data imports
- ✅ Financial year closing
- ✅ Changing critical settings
- ✅ Testing new features

---

## ❓ FAQ

### Q: How long does a backup take?
**A:** 1-2 seconds for typical database (< 10MB). Scales linearly with DB size.

### Q: Can I restore while users are logged in?
**A:** Not recommended. Always log out all users and restart backend after restore.

### Q: What if I restore the wrong backup?
**A:** The system creates a "pre-restore safety backup" automatically. Just restore from that.

### Q: Can I download backups?
**A:** Yes, backups are stored in `backend/backups/`. Copy them to any location.

### Q: How do I restore a very old backup?
**A:** Place the backup file in `backend/backups/` and use the restore API.

### Q: What if all backups are corrupted?
**A:** Use SQLite's `.recover` command (see Emergency Recovery section).

### Q: Can I schedule backups?
**A:** Automatic backups happen on backend start. For scheduled backups, use Windows Task Scheduler to call the backup API.

### Q: How do I backup just one table?
**A:** Use `sqlite3` CLI: `.dump <table_name>` or export to CSV from the UI.

---

## 📞 Support

For backup/restore issues:
- **Email:** support@gharmitra.com
- **Documentation:** docs/DATABASE_CORRUPTION_PREVENTION.md
- **Health Check:** `python backend/app/utils/db_health.py`

---

## ✅ Summary

**Your Data is Protected By:**
1. ✅ WAL mode (99.99% crash protection)
2. ✅ Automatic backups (10 recent copies)
3. ✅ Manual backups (on-demand)
4. ✅ Logout backups (admin safety net)
5. ✅ Integrity verification (every backup checked)
6. ✅ Pre-restore safety backups (rollback protection)

**Remember:**
- 🔄 Backups happen automatically
- 💾 Create manual backups before major changes
- 🔐 Store monthly backups externally
- ✅ Test restores quarterly
- 📝 Document your recovery process

**Your society's financial data is safe!** 🎉
