# SQLite to PostgreSQL Migration Guide for GharMitra

## Executive Summary

**Current State**: GharMitra uses SQLite (`sqlite+aiosqlite:///./gharmitra.db`) with extensive SQLite-specific features.

**Migration Complexity**: **HIGH** - Requires significant code changes across multiple files.

**Estimated Effort**: 2-3 days for a developer familiar with both databases.

---

## Key Challenges Identified

### 1. **SQLite-Specific Code Throughout Codebase**

The codebase has **175+ references** to SQLite, including:

#### A. Database Connection (`backend/app/database.py`)
- Uses `aiosqlite` driver
- SQLite-specific PRAGMA statements (WAL mode, optimizations)
- SQLite backup API (`sqlite3.backup()`)
- SQLite-specific table info queries (`PRAGMA table_info()`)

#### B. Migration Functions
- All migration functions use `PRAGMA table_info()` to check columns
- SQLite-specific `sqlite_master` queries
- SQLite-specific ALTER TABLE syntax

#### C. Backup System
- Custom SQLite backup API implementation
- SQLite integrity checks (`PRAGMA quick_check`)

#### D. Scripts & Utilities
- 30+ utility scripts directly use `sqlite3` module
- Hardcoded SQLite connection strings

---

## Required Changes

### 1. **Database Driver & Connection**

**Current** (`backend/app/database.py`):
```python
DATABASE_URL: str = "sqlite+aiosqlite:///./gharmitra.db"
engine = create_async_engine(settings.DATABASE_URL, ...)
```

**PostgreSQL**:
```python
DATABASE_URL: str = "postgresql+asyncpg://user:password@host:5432/gharmitra"
# OR for production:
DATABASE_URL: str = "postgresql+asyncpg://user:password@host:5432/gharmitra?ssl=require"
```

**Required Package Change**:
```bash
# Remove from requirements.txt:
aiosqlite==0.19.0

# Add to requirements.txt:
asyncpg==0.29.0
psycopg2-binary==2.9.9  # For sync operations if needed
```

---

### 2. **Remove SQLite-Specific PRAGMA Statements**

**Current** (`backend/app/database.py`, lines 106-122):
```python
await conn.execute(text("PRAGMA journal_mode=WAL"))
await conn.execute(text("PRAGMA synchronous=NORMAL"))
await conn.execute(text("PRAGMA wal_autocheckpoint=1000"))
# ... 10+ more PRAGMA statements
```

**PostgreSQL**: Remove all PRAGMA statements. PostgreSQL handles these automatically.

**Action**: Wrap in conditional:
```python
if "sqlite" in settings.DATABASE_URL:
    # SQLite PRAGMA statements
    await conn.execute(text("PRAGMA journal_mode=WAL"))
    # ...
elif "postgresql" in settings.DATABASE_URL:
    # PostgreSQL-specific initialization (if any)
    pass
```

---

### 3. **Replace Table Info Queries**

**Current** (used in 15+ migration functions):
```python
result = await db.execute(text("PRAGMA table_info(societies)"))
columns = {row[1]: row for row in result.fetchall()}
```

**PostgreSQL**:
```python
# Option 1: Use SQLAlchemy introspection
from sqlalchemy import inspect
inspector = inspect(engine)
columns = {col['name']: col for col in inspector.get_columns('societies')}

# Option 2: Query information_schema
result = await db.execute(text("""
    SELECT column_name, data_type, is_nullable, column_default
    FROM information_schema.columns
    WHERE table_name = 'societies'
"""))
columns = {row[0]: row for row in result.fetchall()}
```

**Files to Update**: All migration functions in `backend/app/database.py`:
- `migrate_society_fields()`
- `migrate_user_consent_fields()`
- `migrate_member_privacy_fields()`
- `migrate_vendor_schema()`
- `migrate_physical_documents()`
- `migrate_meeting_management()`
- `migrate_template_system()`
- `migrate_flats_bedrooms()`

---

### 4. **Replace sqlite_master Queries**

**Current** (used in 10+ places):
```python
result = await db.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='vendors'"))
```

**PostgreSQL**:
```python
result = await db.execute(text("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' AND table_name = 'vendors'
"""))
```

---

### 5. **Fix ALTER TABLE Syntax**

**Current**:
```python
await db.execute(text("ALTER TABLE societies ADD COLUMN registration_no VARCHAR(100)"))
```

**PostgreSQL**: Mostly compatible, but:
- `VARCHAR` → `VARCHAR` (same)
- `INTEGER` → `INTEGER` or `BIGINT` (same)
- `REAL` → `REAL` or `DOUBLE PRECISION` (same)
- `BOOLEAN` → `BOOLEAN` (same)
- `DATETIME` → `TIMESTAMP` (different!)
- `TEXT` → `TEXT` (same)

**Critical Change**:
```python
# SQLite:
"created_at DATETIME DEFAULT CURRENT_TIMESTAMP"

# PostgreSQL:
"created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
```

---

### 6. **Update Backup System**

**Current** (`backend/app/database.py`, `perform_automated_backup()`):
- Uses SQLite's native backup API
- File-based backups

**PostgreSQL**: Replace with:
```python
async def perform_automated_backup():
    """Create PostgreSQL backup using pg_dump"""
    if "postgresql" not in settings.DATABASE_URL:
        return
    
    import subprocess
    from datetime import datetime
    
    # Parse connection string
    # Extract host, port, database, user, password
    # Run: pg_dump -h host -U user -d database > backup.sql
    
    # OR use Python library like pg_dump
    # OR use cloud provider's backup API (Railway, Render, etc.)
```

**Alternative**: Use cloud provider's automated backups (Railway, Render, Neon all provide this).

---

### 7. **Update Utility Scripts**

**30+ scripts** in `backend/scripts/` use:
```python
import sqlite3
conn = sqlite3.connect('gharmitra.db')
```

**PostgreSQL**: Replace with:
```python
import psycopg2
# OR
from sqlalchemy import create_engine
engine = create_engine(settings.DATABASE_URL)
```

**Scripts to Update**:
- `check_*.py` (10+ files)
- `fix_*.py` (10+ files)
- `verify_*.py` (5+ files)
- `recover_db.py`
- `optimize_database.py`
- `manual_flat_sync.py`
- And many more...

---

### 8. **Data Type Mapping**

| SQLite | PostgreSQL | Notes |
|--------|------------|-------|
| `INTEGER` | `INTEGER` or `BIGINT` | Same |
| `REAL` | `REAL` or `DOUBLE PRECISION` | Same |
| `TEXT` | `TEXT` or `VARCHAR` | Same |
| `BLOB` | `BYTEA` | Different |
| `DATETIME` | `TIMESTAMP` | **Different** |
| `DATE` | `DATE` | Same |
| `BOOLEAN` | `BOOLEAN` | Same (but SQLite stores as 0/1) |

**Critical**: All `DATETIME` columns must become `TIMESTAMP`.

---

### 9. **Boolean Handling**

**SQLite**: Stores booleans as `0`/`1` (INTEGER)
**PostgreSQL**: Native `BOOLEAN` type

**Migration**: Ensure data conversion:
```sql
-- During migration:
UPDATE table_name SET boolean_column = (boolean_column = 1);
```

---

### 10. **Auto-increment Primary Keys**

**SQLite**:
```sql
id INTEGER PRIMARY KEY AUTOINCREMENT
```

**PostgreSQL**:
```sql
id SERIAL PRIMARY KEY
-- OR (preferred for PostgreSQL 10+):
id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY
```

**Action**: Update all model definitions in `backend/app/models_db.py`.

---

### 11. **Foreign Key Constraints**

**SQLite**: Foreign keys are optional (must enable with `PRAGMA foreign_keys=ON`)
**PostgreSQL**: Foreign keys are always enforced

**Action**: Ensure all foreign key relationships are properly defined in models.

---

### 12. **Index Creation**

**SQLite**:
```sql
CREATE INDEX IF NOT EXISTS idx_name ON table(column)
```

**PostgreSQL**: Same syntax, but PostgreSQL has more index types:
- B-tree (default)
- GIN (for JSONB)
- GiST (for full-text search)

**Action**: Mostly compatible, but consider PostgreSQL-specific optimizations.

---

### 13. **JSON Support**

**SQLite**: `TEXT` with JSON functions
**PostgreSQL**: Native `JSON` and `JSONB` types

**Action**: Consider migrating JSON columns to `JSONB` for better performance.

---

### 14. **Connection Pooling**

**SQLite**: Single file, limited concurrency
**PostgreSQL**: Proper connection pooling required

**Action**: Configure connection pool in SQLAlchemy:
```python
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verify connections before using
)
```

---

## Migration Strategy

### Phase 1: Preparation (1 day)
1. ✅ Create PostgreSQL database (local or cloud)
2. ✅ Update `requirements.txt` (remove `aiosqlite`, add `asyncpg`)
3. ✅ Create database abstraction layer
4. ✅ Write migration script to convert SQLite → PostgreSQL

### Phase 2: Code Updates (1-2 days)
1. ✅ Update `backend/app/database.py` (connection, PRAGMA removal)
2. ✅ Update all migration functions (table info queries)
3. ✅ Update backup system
4. ✅ Update utility scripts (30+ files)
5. ✅ Update model definitions (data types, auto-increment)

### Phase 3: Data Migration (0.5 day)
1. ✅ Export SQLite data
2. ✅ Transform data (data types, booleans, timestamps)
3. ✅ Import to PostgreSQL
4. ✅ Verify data integrity

### Phase 4: Testing (0.5 day)
1. ✅ Test all API endpoints
2. ✅ Test all reports
3. ✅ Test all utility scripts
4. ✅ Performance testing

---

## Recommended Approach

### Option A: **Gradual Migration** (Recommended)
1. Make database layer configurable (support both SQLite and PostgreSQL)
2. Test PostgreSQL in development
3. Migrate production data
4. Switch production to PostgreSQL
5. Remove SQLite support later

### Option B: **Big Bang Migration**
1. Do all changes at once
2. Test thoroughly
3. Deploy

**Risk**: Higher, but faster.

---

## Cloud Hosting Considerations

### Railway
- ✅ Easy PostgreSQL setup (one-click)
- ✅ Automatic backups
- ✅ Connection pooling handled
- ✅ SSL by default

### Render
- ✅ Free PostgreSQL tier (limited)
- ✅ Automatic backups (paid tier)
- ✅ Easy setup

### Neon.tech
- ✅ Serverless PostgreSQL
- ✅ Free tier (generous)
- ✅ Automatic backups
- ✅ Branching (dev/staging/prod)

**Recommendation**: Use **Neon.tech** for free tier, or **Railway** for simplicity.

---

## Cost Comparison

| Service | SQLite (Current) | PostgreSQL |
|---------|-------------------|------------|
| **Railway** | $5/mo (Volume) | $5/mo (PostgreSQL addon) |
| **Render** | Free (ephemeral) | Free tier (limited) |
| **Neon.tech** | N/A | Free tier (0.5GB) |

**Verdict**: PostgreSQL can be **FREE** on Neon.tech or Render, vs. SQLite requiring paid storage on Railway.

---

## Benefits of PostgreSQL

1. ✅ **Concurrent Writes**: Multiple users can write simultaneously
2. ✅ **Better Performance**: For complex queries and large datasets
3. ✅ **Advanced Features**: Full-text search, JSON queries, arrays
4. ✅ **Data Safety**: ACID compliance, replication, backups
5. ✅ **Scalability**: Can handle millions of rows
6. ✅ **Cloud-Native**: Better integration with cloud services

---

## Drawbacks of Migration

1. ❌ **Complexity**: More moving parts
2. ❌ **Cost**: May require paid database hosting
3. ❌ **Migration Risk**: Data loss if not done carefully
4. ❌ **Development Setup**: Requires PostgreSQL installation locally
5. ❌ **Deployment**: More configuration needed

---

## My Recommendation

### **For Production (Cloud Hosting)**:
✅ **Migrate to PostgreSQL** if:
- You expect >100 concurrent users
- You need better data safety
- You want free hosting (Neon.tech)
- You plan to scale

❌ **Stay with SQLite** if:
- You have <50 users
- You want simplest deployment
- You're okay with Railway's $5/mo for volumes
- You don't need advanced features

### **For Development**:
- Keep SQLite for local development (faster, simpler)
- Use PostgreSQL for staging/production

---

## Next Steps

1. **If you want to proceed with migration**:
   - I can create a detailed migration script
   - Update all database code
   - Create PostgreSQL-specific configurations

2. **If you want to stay with SQLite**:
   - Optimize current SQLite setup
   - Use Railway with volumes
   - Implement better backup strategy

**Please let me know which path you'd like to take!**
