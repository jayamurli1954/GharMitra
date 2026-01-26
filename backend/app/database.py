"""
SQLite database connection using SQLAlchemy (async)
"""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator
from app.config import settings
from sqlalchemy import text
import logging
import shutil
import os
from datetime import datetime

logger = logging.getLogger(__name__)

async def perform_automated_backup():
    """
    Create a verified backup of the current database file using SQLite's backup API
    This is safer than file copy as it ensures consistency
    """
    try:
        # Get DB path from settings (e.g., sqlite+aiosqlite:///./gharmitra.db)
        db_url = settings.DATABASE_URL
        if "sqlite" not in db_url:
            logger.info("  ℹ Automated backup skipped (not using SQLite)")
            return

        db_path = db_url.split("///")[-1]
        if not os.path.exists(db_path):
            return

        backup_dir = os.path.join(os.path.dirname(db_path), "backups")
        os.makedirs(backup_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"gharmitra_backup_{timestamp}.db")

        # Use SQLite's backup API (better than file copy - ensures consistency)
        import sqlite3
        source = sqlite3.connect(db_path)
        backup = sqlite3.connect(backup_file)

        with backup:
            source.backup(backup, pages=100, progress=None)

        source.close()
        backup.close()

        # Verify backup integrity
        backup_conn = sqlite3.connect(backup_file)
        cursor = backup_conn.cursor()
        cursor.execute("PRAGMA quick_check")
        integrity = cursor.fetchone()[0]
        backup_conn.close()

        if integrity != "ok":
            logger.error(f"  ❌ Backup verification FAILED: {integrity}")
            os.remove(backup_file)  # Delete corrupted backup
            return

        logger.info(f"  ✓ Automated backup created & verified: {backup_file}")

        # Keep last 10 backups (increased from 5 for better safety)
        backups = sorted([f for f in os.listdir(backup_dir) if f.startswith("gharmitra_backup_")])
        if len(backups) > 10:
            for old_backup in backups[:-10]:
                try:
                    os.remove(os.path.join(backup_dir, old_backup))
                    logger.info(f"  ✓ Removed old backup: {old_backup}")
                except Exception as e:
                    logger.warning(f"  ⚠ Could not remove old backup {old_backup}: {e}")

    except Exception as e:
        logger.warning(f"  ⚠ Automated backup failed: {e}")

# Base class for models (must be defined before models are imported)
Base = declarative_base()

# Global engine and session factory (initialized lazily in init_db)
engine = None
AsyncSessionLocal = None

def get_database_url():
    """Get and normalize database URL - doesn't create connection"""
    database_url = settings.DATABASE_URL
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgresql://") and "+asyncpg" not in database_url:
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgresql+psycopg2://"):
        # Convert psycopg2 to asyncpg for async operations
        database_url = database_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
    return database_url

def create_engine_instance():
    """Create engine instance - called during init_db, not at import time"""
    global engine, AsyncSessionLocal
    if engine is not None:
        return engine  # Already created

    # Import here to avoid import-time crashes
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.pool import NullPool
    import ssl

    database_url = get_database_url()

    # Build engine kwargs
    engine_kwargs = {
        "echo": settings.DATABASE_ECHO,
        "future": True,
    }

    # PostgreSQL-specific settings (including Supabase/Neon)
    if "postgres" in database_url:
        # Use NullPool when connecting through external connection poolers (pgbouncer/Supabase)
        # This prevents SQLAlchemy from maintaining its own pool on top of pgbouncer,
        # which causes DuplicatePreparedStatementError
        engine_kwargs.update({
            "pool_pre_ping": True,
            "poolclass": NullPool,
        })
        # SSL + disable prepared statements for cloud PostgreSQL
        if "supabase" in database_url or "neon" in database_url:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            engine_kwargs["connect_args"] = {
                "ssl": ssl_context,
                "prepared_statement_cache_size": 0,  # asyncpg native param - disables prepared stmt cache
                "statement_cache_size": 0,  # Belt-and-suspenders: also set the older param name
            }
        else:
            # Force disable prepared statements for all Postgres connections
            engine_kwargs["connect_args"] = {
                "prepared_statement_cache_size": 0,
                "statement_cache_size": 0,
            }

    engine = create_async_engine(database_url, **engine_kwargs)

    # Create async session factory
    AsyncSessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    return engine

# Import models so they're registered with Base (must be after Base is defined)
# This ensures all tables are created when init_db() is called
def import_models():
    """Import all models to register them with Base"""
    from app import models_db  # noqa: F401
    from app.models import audit_adjustment  # noqa: F401


async def init_db(retries: int = 5, delay: int = 3):
    """
    Initialize database - create all tables and run migrations
    Includes retry logic for cloud deployments (Supabase cold starts)
    Never crashes app startup - logs errors but continues
    """
    import asyncio
    from sqlalchemy.exc import SQLAlchemyError
    
    # Create engine instance (lazy initialization - not at import time)
    create_engine_instance()
    
    for attempt in range(1, retries + 1):
        try:
            # 0. Perform automated backup before any operations (SQLite only)
            await perform_automated_backup()
            
            # 1. Test database connection first (important for cloud deployments)
            try:
                # Log the host we are trying to connect to (for debugging)
                from urllib.parse import urlparse
                try:
                    # Clean/safe parsing of the URL
                    db_url_parts = settings.DATABASE_URL.split("@")
                    if len(db_url_parts) > 1:
                        # Get user part (before @, after //)
                        user_pass = db_url_parts[0].split("//")[1]
                        if ":" in user_pass:
                            username = user_pass.split(":")[0]
                        else:
                            username = user_pass
                        
                        host_port = db_url_parts[1]
                        logger.info(f"Attempting DB connection as USER: '{username}'")
                        logger.info(f"Connecting to HOST: '{host_port}'")
                except Exception as parse_err:
                    logger.info(f"Attempting to connect to DB (url parsing failed: {parse_err})")

                async with engine.connect() as conn:
                    await conn.execute(text("SELECT 1"))
            except (OSError, Exception) as e:
                # Catch network unreachable errors common with Render -> Supabase IPv6 changes
                error_str = str(e)
                if "Network is unreachable" in error_str or "101" in error_str:
                    logger.error("🛑 NETWORK ERROR: Cannot reach database.")
                    logger.error("👉 SUGGESTION: If using Supabase, update DATABASE_URL to use the CONNECTION POOLER (port 6543).")
                    logger.error("   Example: postgresql://user.proj:pass@aws-0-ap-south-1.pooler.supabase.com:6543/postgres")
                raise e
            
            # 2. Database optimizations
            if "sqlite" in settings.DATABASE_URL:
                 # Enable WAL mode for crash resilience and optimize settings
                async with engine.connect() as conn:
                    await conn.execute(text("PRAGMA journal_mode=WAL"))
                    await conn.execute(text("PRAGMA synchronous=NORMAL"))

                    # Additional optimizations for corruption prevention
                    await conn.execute(text("PRAGMA wal_autocheckpoint=1000"))  # Checkpoint every 1000 pages
                    await conn.execute(text("PRAGMA cache_size=-8000"))  # 8MB cache (better performance)
                    await conn.execute(text("PRAGMA temp_store=MEMORY"))  # Use memory for temp tables
                    await conn.execute(text("PRAGMA foreign_keys=ON"))  # Enable foreign key constraints
                    await conn.execute(text("PRAGMA optimize"))  # Optimize the database

                    # Run initial checkpoint
                    await conn.execute(text("PRAGMA wal_checkpoint(PASSIVE)"))
                    await conn.execute(text("PRAGMA analysis_limit=1000"))  # Limit for query analysis
                    await conn.execute(text("PRAGMA automatic_index=ON"))  # Enable automatic indexing

                    logger.info("  ✓ SQLite WAL mode enabled with optimizations")
            else:
                 logger.info(f"  ✓ Connected to database: {settings.DATABASE_URL.split('@')[-1]}")

            # Import models first to register them
            import_models()
            logger.info(f"Initializing database at {settings.DATABASE_URL}")
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            # Seed default data (Society and Admin User) - MUST RUN BEFORE MIGRATIONS
            await seed_default_data()
            
            # Run migrations to add missing columns
            await migrate_society_fields()
            await migrate_physical_documents()
            await migrate_physical_documents()
            await migrate_user_consent_fields()
            await migrate_member_privacy_fields() 
            await migrate_vendor_schema() # Added vendor migration
            await migrate_meeting_management()
            await migrate_template_system()
            await migrate_flats_bedrooms()  # Add bedrooms column to flats table
            
            logger.info("✅ Database initialized successfully")
            return  # Success - exit function
            
        except SQLAlchemyError as e:
            logger.warning(f"⚠️ Database connection failed (attempt {attempt}/{retries}): {e}")
            if attempt < retries:
                logger.info(f"  Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
            else:
                logger.error(f"❌ Database unavailable after {retries} attempts - app will continue without DB")
                logger.error(f"   Error: {e}")
                # Don't raise - let app start without DB
                return
        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {e}")
            logger.error(f"   Error type: {type(e).__name__}")
            # For non-database errors, still don't crash - log and continue
            if attempt < retries:
                logger.info(f"  Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
            else:
                logger.error(f"❌ Database initialization failed after {retries} attempts")
                logger.error(f"   App will start but database features may not work")
                return


def is_postgresql() -> bool:
    """Check if we're using PostgreSQL"""
    return "postgresql" in settings.DATABASE_URL


def get_autoincrement_syntax() -> str:
    """Get the correct auto-increment primary key syntax for the database"""
    if is_postgresql():
        return "SERIAL PRIMARY KEY"
    return "INTEGER PRIMARY KEY AUTOINCREMENT"


async def get_table_columns(db, table_name: str) -> set:
    """Get column names for a table - works with both SQLite and PostgreSQL"""
    database_url = settings.DATABASE_URL
    if "postgresql" in database_url:
        # PostgreSQL - use information_schema
        result = await db.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = :table_name
        """), {"table_name": table_name})
        return {row[0] for row in result.fetchall()}
    else:
        # SQLite - use PRAGMA
        result = await db.execute(text(f"PRAGMA table_info({table_name})"))
        return {row[1] for row in result.fetchall()}


async def table_exists(db, table_name: str) -> bool:
    """Check if a table exists - works with both SQLite and PostgreSQL"""
    database_url = settings.DATABASE_URL
    if "postgresql" in database_url:
        result = await db.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = :table_name
            )
        """), {"table_name": table_name})
        return result.scalar()
    else:
        result = await db.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=:table_name"
        ), {"table_name": table_name})
        return result.fetchone() is not None


async def migrate_society_fields():
    """Add missing columns to societies table if they don't exist"""
    from sqlalchemy import text
    try:
        async with AsyncSessionLocal() as db:
            # Check existing columns (PostgreSQL/SQLite compatible)
            columns = await get_table_columns(db, "societies")
            
            # Columns to add
            new_columns = [
                ("registration_no", "VARCHAR(100)"),
                ("pan_no", "VARCHAR(20)"),
                ("reg_cert_url", "VARCHAR(500)"),
                ("pan_card_url", "VARCHAR(500)"),
                ("logo_url", "VARCHAR(500)"),
                ("financial_year_start", "DATE"),
                ("financial_year_end", "DATE"),
                ("accounting_type", "VARCHAR(20) DEFAULT 'cash'"),
                ("bank_name", "VARCHAR(200)"),
                ("bank_branch", "VARCHAR(200)"),
                ("bank_account_number", "VARCHAR(50)"),
                ("bank_ifsc_code", "VARCHAR(20)"),
                ("upi_qr_code_url", "VARCHAR(500)"),
            ]
            
            for col_name, col_type in new_columns:
                if col_name not in columns:
                    try:
                        await db.execute(text(f"ALTER TABLE societies ADD COLUMN {col_name} {col_type}"))
                        await db.commit()
                        logger.info(f"  ✓ Added {col_name} to societies table")
                    except Exception as e:
                        logger.warning(f"  ⚠ Could not add {col_name}: {e}")
            
            # Also check and add missing columns to maintenance_bills if needed
            try:
                bill_columns = await get_table_columns(db, "maintenance_bills")
                
                # Add bill_number if missing
                if "bill_number" not in bill_columns:
                    await db.execute(text("ALTER TABLE maintenance_bills ADD COLUMN bill_number VARCHAR(50)"))
                    await db.commit()
                    logger.info("  ✓ Added bill_number to maintenance_bills table")
                
                # Add maintenance_amount if missing
                if "maintenance_amount" not in bill_columns:
                    await db.execute(text("ALTER TABLE maintenance_bills ADD COLUMN maintenance_amount REAL NOT NULL DEFAULT 0.0"))
                    await db.commit()
                    logger.info("  ✓ Added maintenance_amount to maintenance_bills table")
                
                # Add water_amount if missing
                if "water_amount" not in bill_columns:
                    await db.execute(text("ALTER TABLE maintenance_bills ADD COLUMN water_amount REAL NOT NULL DEFAULT 0.0"))
                    await db.commit()
                    logger.info("  ✓ Added water_amount to maintenance_bills table")
                
                # Add fixed_amount if missing 
                if "fixed_amount" not in bill_columns:
                    await db.execute(text("ALTER TABLE maintenance_bills ADD COLUMN fixed_amount REAL NOT NULL DEFAULT 0.0"))
                    await db.commit()
                    logger.info("  ✓ Added fixed_amount to maintenance_bills table")
                
                # Add sinking_fund_amount if missing
                if "sinking_fund_amount" not in bill_columns:
                    await db.execute(text("ALTER TABLE maintenance_bills ADD COLUMN sinking_fund_amount REAL NOT NULL DEFAULT 0.0"))
                    await db.commit()
                    logger.info("  ✓ Added sinking_fund_amount to maintenance_bills table")
                
                # Add repair_fund_amount if missing 
                if "repair_fund_amount" not in bill_columns:
                    await db.execute(text("ALTER TABLE maintenance_bills ADD COLUMN repair_fund_amount REAL NOT NULL DEFAULT 0.0"))
                    await db.commit()
                    logger.info("  ✓ Added repair_fund_amount to maintenance_bills table")
                
                # Add corpus_fund_amount if missing 
                if "corpus_fund_amount" not in bill_columns:
                    await db.execute(text("ALTER TABLE maintenance_bills ADD COLUMN corpus_fund_amount REAL NOT NULL DEFAULT 0.0"))
                    await db.commit()
                    logger.info("  ✓ Added corpus_fund_amount to maintenance_bills table")
                
                # Add arrears_amount if missing
                if "arrears_amount" not in bill_columns:
                    await db.execute(text("ALTER TABLE maintenance_bills ADD COLUMN arrears_amount REAL NOT NULL DEFAULT 0.0"))
                    await db.commit()
                    logger.info("  ✓ Added arrears_amount to maintenance_bills table")
                
                # Add late_fee_amount if missing
                if "late_fee_amount" not in bill_columns:
                    await db.execute(text("ALTER TABLE maintenance_bills ADD COLUMN late_fee_amount REAL NOT NULL DEFAULT 0.0"))
                    await db.commit()
                    logger.info("  ✓ Added late_fee_amount to maintenance_bills table")
                
                # Add total_amount if missing
                if "total_amount" not in bill_columns:
                    await db.execute(text("ALTER TABLE maintenance_bills ADD COLUMN total_amount REAL NOT NULL DEFAULT 0.0"))
                    await db.commit()
                    logger.info("  ✓ Added total_amount to maintenance_bills table")
                
                # Add breakdown (JSON) if missing
                if "breakdown" not in bill_columns:
                    await db.execute(text("ALTER TABLE maintenance_bills ADD COLUMN breakdown TEXT"))
                    await db.commit()
                    logger.info("  ✓ Added breakdown to maintenance_bills table")
                
                # Add due_date if missing
                if "due_date" not in bill_columns:
                    await db.execute(text("ALTER TABLE maintenance_bills ADD COLUMN due_date DATE"))
                    await db.commit()
                    logger.info("  ✓ Added due_date to maintenance_bills table")
                
                # Add paid_date if missing
                if "paid_date" not in bill_columns:
                    await db.execute(text("ALTER TABLE maintenance_bills ADD COLUMN paid_date DATE"))
                    await db.commit()
                    logger.info("  ✓ Added paid_date to maintenance_bills table")
                
                # Add created_at if missing
                if "created_at" not in bill_columns:
                    await db.execute(text("ALTER TABLE maintenance_bills ADD COLUMN created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP"))
                    await db.commit()
                    logger.info("  ✓ Added created_at to maintenance_bills table")
                
                # Add updated_at if missing
                if "updated_at" not in bill_columns:
                    await db.execute(text("ALTER TABLE maintenance_bills ADD COLUMN updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP"))
                    await db.commit()
                    logger.info("  ✓ Added updated_at to maintenance_bills table")
                
                # Add society_id if missing
                if "society_id" not in bill_columns:
                    await db.execute(text("ALTER TABLE maintenance_bills ADD COLUMN society_id INTEGER NOT NULL DEFAULT 1"))
                    await db.commit()
                    logger.info("  ✓ Added society_id to maintenance_bills table")
            except Exception as e:
                logger.warning(f"  ⚠ Could not add columns to maintenance_bills: {e}")
            
            # Also check and add missing columns to water_expenses if needed
            try:
                water_columns = await get_table_columns(db, "water_expenses")
                
                # Add tanker_charges if missing
                if "tanker_charges" not in water_columns:
                    await db.execute(text("ALTER TABLE water_expenses ADD COLUMN tanker_charges REAL NOT NULL DEFAULT 0.0"))
                    await db.commit()
                    logger.info("  ✓ Added tanker_charges to water_expenses table")
                
                # Add government_charges if missing
                if "government_charges" not in water_columns:
                    await db.execute(text("ALTER TABLE water_expenses ADD COLUMN government_charges REAL NOT NULL DEFAULT 0.0"))
                    await db.commit()
                    logger.info("  ✓ Added government_charges to water_expenses table")
                
                # Add other_charges if missing
                if "other_charges" not in water_columns:
                    await db.execute(text("ALTER TABLE water_expenses ADD COLUMN other_charges REAL NOT NULL DEFAULT 0.0"))
                    await db.commit()
                    logger.info("  ✓ Added other_charges to water_expenses table")
                
                # Add total_amount if missing
                if "total_amount" not in water_columns:
                    await db.execute(text("ALTER TABLE water_expenses ADD COLUMN total_amount REAL NOT NULL DEFAULT 0.0"))
                    await db.commit()
                    logger.info("  ✓ Added total_amount to water_expenses table")
            except Exception as e:
                logger.warning(f"  ⚠ Could not add columns to water_expenses: {e}")
            
            # Also check and add document_number to transactions if needed
            try:
                transaction_columns = await get_table_columns(db, "transactions")
                if "document_number" not in transaction_columns:
                    await db.execute(text("ALTER TABLE transactions ADD COLUMN document_number VARCHAR(50)"))
                    await db.commit()
                    logger.info("  ✓ Added document_number to transactions table")
                    # Create index for document_number
                    try:
                        await db.execute(text("CREATE INDEX IF NOT EXISTS idx_transactions_document_number ON transactions(document_number)"))
                        await db.commit()
                    except Exception as e:
                        logger.warning(f"  ⚠ Could not create index on document_number: {e}")
            except Exception as e:
                logger.warning(f"  ⚠ Could not add document_number to transactions: {e}")
            
            # Also check and add is_fixed_expense to account_codes if needed
            try:
                account_columns = await get_table_columns(db, "account_codes")
                if "is_fixed_expense" not in account_columns:
                    await db.execute(text("ALTER TABLE account_codes ADD COLUMN is_fixed_expense BOOLEAN DEFAULT 0"))
                    await db.commit()
                    logger.info("  ✓ Added is_fixed_expense to account_codes table")
            except Exception as e:
                logger.warning(f"  ⚠ Could not add is_fixed_expense to account_codes: {e}")
            
            # Also check and add admin_guidelines_acknowledgments table if needed
            try:
                if not await table_exists(db, "admin_guidelines_acknowledgments"):
                    pk_syntax = get_autoincrement_syntax()
                    await db.execute(text(f"""
                        CREATE TABLE admin_guidelines_acknowledgments (
                            id {pk_syntax},
                            user_id INTEGER NOT NULL UNIQUE,
                            society_id INTEGER NOT NULL,
                            acknowledged_version VARCHAR(20) NOT NULL,
                            acknowledged_at TIMESTAMP NOT NULL,
                            created_at TIMESTAMP NOT NULL,
                            updated_at TIMESTAMP NOT NULL,
                            FOREIGN KEY (user_id) REFERENCES users(id),
                            FOREIGN KEY (society_id) REFERENCES societies(id)
                        )
                    """))
                    await db.commit()
                    logger.info("  ✓ Created admin_guidelines_acknowledgments table")
            except Exception as e:
                logger.warning(f"  ⚠ Could not create admin_guidelines_acknowledgments table: {e}")
            
            # Also check and add meetings and meeting_minutes tables if needed
            try:
                if not await table_exists(db, "meetings"):
                    pk_syntax = get_autoincrement_syntax()
                    await db.execute(text(f"""
                        CREATE TABLE meetings (
                            id {pk_syntax},
                            society_id INTEGER NOT NULL,
                            meeting_type VARCHAR(20) NOT NULL,
                            meeting_date DATE NOT NULL,
                            meeting_title VARCHAR(200) NOT NULL,
                            venue VARCHAR(200),
                            agenda TEXT,
                            attendees_count INTEGER,
                            chaired_by VARCHAR(100),
                            notice_sent BOOLEAN DEFAULT FALSE NOT NULL,
                            notice_sent_at TIMESTAMP,
                            notice_sent_by INTEGER,
                            created_by INTEGER NOT NULL,
                            created_at TIMESTAMP NOT NULL,
                            updated_at TIMESTAMP NOT NULL,
                            FOREIGN KEY (society_id) REFERENCES societies(id),
                            FOREIGN KEY (created_by) REFERENCES users(id),
                            FOREIGN KEY (notice_sent_by) REFERENCES users(id)
                        )
                    """))
                    await db.execute(text("CREATE INDEX idx_meetings_society ON meetings(society_id)"))
                    await db.execute(text("CREATE INDEX idx_meetings_type ON meetings(meeting_type)"))
                    await db.execute(text("CREATE INDEX idx_meetings_date ON meetings(meeting_date)"))
                    await db.commit()
                    logger.info("  ✓ Created meetings table")
            except Exception as e:
                logger.warning(f"  ⚠ Could not create meetings table: {e}")
            
            # Also check and add notice_sent columns to meetings table if needed
            try:
                meeting_columns = await get_table_columns(db, "meetings")
                if "notice_sent" not in meeting_columns:
                    await db.execute(text("ALTER TABLE meetings ADD COLUMN notice_sent BOOLEAN DEFAULT 0 NOT NULL"))
                    await db.execute(text("ALTER TABLE meetings ADD COLUMN notice_sent_at DATETIME"))
                    await db.execute(text("ALTER TABLE meetings ADD COLUMN notice_sent_by INTEGER"))
                    await db.execute(text("CREATE INDEX idx_meetings_notice_sent ON meetings(notice_sent)"))
                    await db.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_meetings_notice_sent ON meetings(notice_sent)
                    """))
                    await db.commit()
                    logger.info("  ✓ Added notice_sent columns to meetings table")
            except Exception as e:
                logger.warning(f"  ⚠ Could not add notice_sent columns to meetings: {e}")
    except Exception as e:
        logger.warning(f"Migration check failed (table may not exist yet): {e}")


async def migrate_user_consent_fields():
    """Add legal consent fields to users table (DPDP Act 2023 compliance)"""
    from sqlalchemy import text
    try:
        async with AsyncSessionLocal() as db:
            # Check existing columns (PostgreSQL/SQLite compatible)
            columns = await get_table_columns(db, "users")
            
            # Add consent fields if they don't exist
            consent_fields = [
                ("terms_accepted", "BOOLEAN NOT NULL DEFAULT 0"),
                ("privacy_accepted", "BOOLEAN NOT NULL DEFAULT 0"),
                ("consent_timestamp", "DATETIME"),
                ("consent_ip_address", "VARCHAR(45)"),
                ("consent_version", "VARCHAR(20)"),
            ]
            
            for col_name, col_type in consent_fields:
                if col_name not in columns:
                    try:
                        await db.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))
                        await db.commit()
                        logger.info(f"  ✓ Added {col_name} to users table")
                    except Exception as e:
                        logger.warning(f"  ⚠ Could not add {col_name}: {e}")
    except Exception as e:
        logger.warning(f"User consent fields migration check failed: {e}")


async def migrate_member_privacy_fields():
    """Add is_mobile_public and occupation columns to members table"""
    from sqlalchemy import text
    try:
        async with AsyncSessionLocal() as db:
            columns = await get_table_columns(db, "members")
            
            if "is_mobile_public" not in columns:
                try:
                    await db.execute(text("ALTER TABLE members ADD COLUMN is_mobile_public BOOLEAN NOT NULL DEFAULT 0"))
                    await db.commit()
                    logger.info("  ✓ Added is_mobile_public to members table")
                except Exception as e:
                    logger.warning(f"  ⚠ Could not add is_mobile_public: {e}")

            if "occupation" not in columns:
                try:
                    await db.execute(text("ALTER TABLE members ADD COLUMN occupation VARCHAR(100)"))
                    await db.commit()
                    logger.info("  ✓ Added occupation to members table")
                except Exception as e:
                    logger.warning(f"  ⚠ Could not add occupation: {e}")

    except Exception as e:
        logger.warning(f"Member privacy fields migration check failed: {e}")



async def migrate_vendor_schema():
    """Add vendors table and update transactions"""
    from sqlalchemy import text
    try:
        async with AsyncSessionLocal() as db:
            # 1. Create Vendors Table
            if not await table_exists(db, "vendors"):
                pk_syntax = get_autoincrement_syntax()
                await db.execute(text(f"""
                    CREATE TABLE vendors (
                        id {pk_syntax},
                        society_id INTEGER NOT NULL DEFAULT 1,
                        name VARCHAR(100) NOT NULL,
                        category VARCHAR(50),
                        contact_person VARCHAR(100),
                        phone_number VARCHAR(20),
                        email VARCHAR(100),
                        address TEXT,
                        tax_id VARCHAR(50),
                        opening_balance REAL DEFAULT 0.0,
                        current_balance REAL DEFAULT 0.0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (society_id) REFERENCES societies(id)
                    )
                """))
                logger.info("  ✓ Created vendors table")

            # 2. Add vendor_id to transactions
            columns = await get_table_columns(db, "transactions")
            
            if "vendor_id" not in columns:
                try:
                    await db.execute(text("ALTER TABLE transactions ADD COLUMN vendor_id INTEGER REFERENCES vendors(id)"))
                    logger.info("  ✓ Added vendor_id to transactions table")
                except Exception as e:
                    logger.warning(f"  ⚠ Could not add vendor_id: {e}")
            
            await db.commit()

    except Exception as e:
        logger.warning(f"Vendor schema migration failed: {e}")


async def migrate_physical_documents():
    """Create physical documents checklist tables if they don't exist"""
    from sqlalchemy import text
    try:
        async with AsyncSessionLocal() as db:
            # Check if table exists
            if not await table_exists(db, "physical_documents_checklist"):
                logger.info("Creating physical_documents_checklist tables...")
                
                # Create physical_documents_checklist table (PostgreSQL/SQLite compatible)
                database_url = settings.DATABASE_URL
                if "postgresql" in database_url:
                    await db.execute(text("""
                        CREATE TABLE IF NOT EXISTS physical_documents_checklist (
                          id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
                          society_id INTEGER NOT NULL,
                          member_id INTEGER NOT NULL,
                          flat_id INTEGER NOT NULL,
                          document_type TEXT NOT NULL CHECK (document_type IN (
                            'aadhaar', 'pan', 'passport', 'driving_license',
                            'rent_agreement', 'sale_deed', 'electricity_bill',
                            'water_bill', 'other'
                          )),
                          submitted INTEGER DEFAULT 0,
                          submission_date TEXT,
                          verified INTEGER DEFAULT 0,
                          verified_by INTEGER,
                          verification_date TEXT,
                          storage_location TEXT,
                          storage_location_encrypted TEXT,
                          verification_notes TEXT,
                          verification_notes_encrypted TEXT,
                          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                          UNIQUE(member_id, document_type),
                          FOREIGN KEY (society_id) REFERENCES societies(id) ON DELETE CASCADE,
                          FOREIGN KEY (member_id) REFERENCES users(id) ON DELETE CASCADE,
                          FOREIGN KEY (flat_id) REFERENCES flats(id) ON DELETE CASCADE,
                          FOREIGN KEY (verified_by) REFERENCES users(id)
                        )
                    """))
                else:
                    await db.execute(text("""
                        CREATE TABLE IF NOT EXISTS physical_documents_checklist (
                          id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                          society_id INTEGER NOT NULL,
                          member_id INTEGER NOT NULL,
                          flat_id INTEGER NOT NULL,
                          document_type TEXT NOT NULL CHECK (document_type IN (
                            'aadhaar', 'pan', 'passport', 'driving_license',
                            'rent_agreement', 'sale_deed', 'electricity_bill',
                            'water_bill', 'other'
                          )),
                          submitted INTEGER DEFAULT 0,
                          submission_date TEXT,
                          verified INTEGER DEFAULT 0,
                          verified_by INTEGER,
                          verification_date TEXT,
                          storage_location TEXT,
                          storage_location_encrypted TEXT,
                          verification_notes TEXT,
                          verification_notes_encrypted TEXT,
                          created_at TEXT DEFAULT (datetime('now')),
                          updated_at TEXT DEFAULT (datetime('now')),
                          UNIQUE(member_id, document_type),
                          FOREIGN KEY (society_id) REFERENCES societies(id) ON DELETE CASCADE,
                          FOREIGN KEY (member_id) REFERENCES users(id) ON DELETE CASCADE,
                          FOREIGN KEY (flat_id) REFERENCES flats(id) ON DELETE CASCADE,
                          FOREIGN KEY (verified_by) REFERENCES users(id)
                        )
                    """))
                
                # Create indexes
                await db.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_physical_docs_member 
                    ON physical_documents_checklist(member_id)
                """))
                await db.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_physical_docs_society 
                    ON physical_documents_checklist(society_id)
                """))
                await db.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_physical_docs_verification 
                    ON physical_documents_checklist(verified, verification_date)
                """))
                await db.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_physical_docs_submission 
                    ON physical_documents_checklist(submitted, submission_date)
                """))
                
                # Create document_access_logs table (PostgreSQL/SQLite compatible)
                if "postgresql" in database_url:
                    await db.execute(text("""
                        CREATE TABLE IF NOT EXISTS document_access_logs (
                          id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
                          document_id TEXT,
                          document_type TEXT NOT NULL CHECK (document_type IN ('physical', 'digital')),
                          accessed_by INTEGER,
                          access_type TEXT NOT NULL,
                          access_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                          ip_address TEXT,
                          user_agent TEXT,
                          FOREIGN KEY (accessed_by) REFERENCES users(id)
                        )
                    """))
                else:
                    await db.execute(text("""
                        CREATE TABLE IF NOT EXISTS document_access_logs (
                          id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                          document_id TEXT,
                          document_type TEXT NOT NULL CHECK (document_type IN ('physical', 'digital')),
                          accessed_by INTEGER,
                          access_type TEXT NOT NULL,
                          access_timestamp TEXT DEFAULT (datetime('now')),
                          ip_address TEXT,
                          user_agent TEXT,
                          FOREIGN KEY (accessed_by) REFERENCES users(id)
                        )
                    """))
                
                # Create access log indexes
                await db.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_access_logs_document 
                    ON document_access_logs(document_id)
                """))
                await db.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_access_logs_user 
                    ON document_access_logs(accessed_by)
                """))
                await db.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_access_logs_timestamp 
                    ON document_access_logs(access_timestamp)
                """))
                
                await db.commit()
                logger.info("  ✓ Created physical_documents_checklist tables")
            else:
                logger.info("  - physical_documents_checklist tables already exist")
    except Exception as e:
        logger.warning(f"Physical documents migration check failed: {e}")


async def migrate_meeting_management():
    """Add meeting management system columns and tables"""
    from sqlalchemy import text
    try:
        async with AsyncSessionLocal() as db:
            # Check if meetings table exists and add new columns
            if await table_exists(db, "meetings"):
                # Table exists, check and add new columns
                columns = await get_table_columns(db, "meetings")
                
                # Add new columns to meetings table
                new_columns = [
                    ("meeting_number", "VARCHAR(50)"),
                    ("meeting_time", "VARCHAR(20)"),
                    ("notice_sent_to", "VARCHAR(50)"),
                    ("status", "VARCHAR(20) DEFAULT 'scheduled'"),
                    ("total_members_eligible", "INTEGER"),
                    ("total_members_present", "INTEGER DEFAULT 0"),
                    ("quorum_required", "INTEGER"),
                    ("quorum_met", "BOOLEAN DEFAULT 0"),
                    ("minutes_text", "TEXT"),
                    ("minutes_approved", "BOOLEAN DEFAULT 0"),
                    ("minutes_approved_date", "DATE"),
                    ("recorded_by", "VARCHAR(100)"),
                    ("recorded_at", "DATETIME"),
                ]
                
                for col_name, col_type in new_columns:
                    if col_name not in columns:
                        try:
                            await db.execute(text(f"ALTER TABLE meetings ADD COLUMN {col_name} {col_type}"))
                            await db.commit()
                            logger.info(f"  ✓ Added {col_name} to meetings table")
                        except Exception as e:
                            logger.warning(f"  ⚠ Could not add {col_name}: {e}")
            
            # Create meeting_agenda_items table if it doesn't exist
            if not await table_exists(db, "meeting_agenda_items"):
                pk_syntax = get_autoincrement_syntax()
                await db.execute(text(f"""
                    CREATE TABLE meeting_agenda_items (
                        id {pk_syntax},
                        meeting_id INTEGER NOT NULL,
                        society_id INTEGER NOT NULL,
                        item_number INTEGER NOT NULL,
                        item_title VARCHAR(200) NOT NULL,
                        item_description TEXT,
                        discussion_summary TEXT,
                        status VARCHAR(20) DEFAULT 'pending',
                        resolution_id INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE,
                        FOREIGN KEY (society_id) REFERENCES societies(id) ON DELETE CASCADE,
                        FOREIGN KEY (resolution_id) REFERENCES meeting_resolutions(id)
                    )
                """))
                await db.execute(text("CREATE INDEX IF NOT EXISTS idx_agenda_meeting ON meeting_agenda_items(meeting_id)"))
                await db.commit()
                logger.info("  ✓ Created meeting_agenda_items table")
            
            # Create meeting_attendance table if it doesn't exist
            if not await table_exists(db, "meeting_attendance"):
                pk_syntax = get_autoincrement_syntax()
                await db.execute(text(f"""
                    CREATE TABLE meeting_attendance (
                        id {pk_syntax},
                        meeting_id INTEGER NOT NULL,
                        society_id INTEGER NOT NULL,
                        member_id INTEGER NOT NULL,
                        member_name VARCHAR(100) NOT NULL,
                        member_flat VARCHAR(50),
                        status VARCHAR(20) NOT NULL,
                        proxy_holder_id INTEGER,
                        proxy_holder_name VARCHAR(100),
                        arrival_time VARCHAR(20),
                        departure_time VARCHAR(20),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE,
                        FOREIGN KEY (society_id) REFERENCES societies(id) ON DELETE CASCADE,
                        FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE CASCADE,
                        FOREIGN KEY (proxy_holder_id) REFERENCES members(id)
                    )
                """))
                await db.execute(text("CREATE INDEX IF NOT EXISTS idx_attendance_meeting ON meeting_attendance(meeting_id)"))
                await db.execute(text("CREATE INDEX IF NOT EXISTS idx_attendance_member ON meeting_attendance(member_id)"))
                await db.commit()
                logger.info("  ✓ Created meeting_attendance table")
            
            # Create meeting_resolutions table if it doesn't exist
            if not await table_exists(db, "meeting_resolutions"):
                pk_syntax = get_autoincrement_syntax()
                await db.execute(text(f"""
                    CREATE TABLE meeting_resolutions (
                        id {pk_syntax},
                        meeting_id INTEGER NOT NULL,
                        society_id INTEGER NOT NULL,
                        resolution_number VARCHAR(50) NOT NULL UNIQUE,
                        resolution_type VARCHAR(20),
                        resolution_title VARCHAR(200) NOT NULL,
                        resolution_text TEXT NOT NULL,
                        proposed_by_id INTEGER,
                        proposed_by_name VARCHAR(100) NOT NULL,
                        seconded_by_id INTEGER,
                        seconded_by_name VARCHAR(100) NOT NULL,
                        votes_for INTEGER DEFAULT 0,
                        votes_against INTEGER DEFAULT 0,
                        votes_abstain INTEGER DEFAULT 0,
                        result VARCHAR(20) NOT NULL,
                        action_items TEXT,
                        assigned_to VARCHAR(100),
                        due_date DATE,
                        implementation_status VARCHAR(20) DEFAULT 'pending',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE,
                        FOREIGN KEY (society_id) REFERENCES societies(id) ON DELETE CASCADE,
                        FOREIGN KEY (proposed_by_id) REFERENCES members(id),
                        FOREIGN KEY (seconded_by_id) REFERENCES members(id)
                    )
                """))
                await db.execute(text("CREATE INDEX IF NOT EXISTS idx_resolutions_meeting ON meeting_resolutions(meeting_id)"))
                await db.execute(text("CREATE INDEX IF NOT EXISTS idx_resolutions_number ON meeting_resolutions(resolution_number)"))
                await db.execute(text("CREATE INDEX IF NOT EXISTS idx_resolutions_status ON meeting_resolutions(implementation_status)"))
                await db.commit()
                logger.info("  ✓ Created meeting_resolutions table")
            
            # Create meeting_votes table if it doesn't exist
            if not await table_exists(db, "meeting_votes"):
                pk_syntax = get_autoincrement_syntax()
                await db.execute(text(f"""
                    CREATE TABLE meeting_votes (
                        id {pk_syntax},
                        resolution_id INTEGER NOT NULL,
                        meeting_id INTEGER NOT NULL,
                        society_id INTEGER NOT NULL,
                        member_id INTEGER NOT NULL,
                        member_name VARCHAR(100) NOT NULL,
                        vote VARCHAR(20) NOT NULL,
                        voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (resolution_id) REFERENCES meeting_resolutions(id) ON DELETE CASCADE,
                        FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE,
                        FOREIGN KEY (society_id) REFERENCES societies(id) ON DELETE CASCADE,
                        FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE CASCADE
                    )
                """))
                await db.execute(text("CREATE INDEX IF NOT EXISTS idx_votes_resolution ON meeting_votes(resolution_id)"))
                await db.execute(text("CREATE INDEX IF NOT EXISTS idx_votes_member ON meeting_votes(member_id)"))
                await db.commit()
                logger.info("  ✓ Created meeting_votes table")
    except Exception as e:
        logger.warning(f"Meeting management migration check failed: {e}")


async def migrate_template_system():
    """Add template system tables for Resource Centre (NO storage approach)"""
    from sqlalchemy import text
    try:
        async with AsyncSessionLocal() as db:
            database_url = settings.DATABASE_URL
            is_postgres = "postgresql" in database_url

            # Create template_categories table if it doesn't exist
            if not await table_exists(db, "template_categories"):
                pk_syntax = get_autoincrement_syntax()
                await db.execute(text(f"""
                    CREATE TABLE template_categories (
                        id {pk_syntax},
                        category_code VARCHAR(50) NOT NULL UNIQUE,
                        category_name VARCHAR(100) NOT NULL,
                        category_description TEXT,
                        icon_name VARCHAR(50),
                        display_order INTEGER DEFAULT 0,
                        is_active BOOLEAN DEFAULT TRUE
                    )
                """))
                await db.execute(text("CREATE INDEX IF NOT EXISTS idx_categories_code ON template_categories(category_code)"))
                await db.commit()
                logger.info("  ✓ Created template_categories table")
                
                # Insert default categories
                categories = [
                    ('moveout', 'Move-In / Move-Out', 'Forms for tenant and owner transitions', 'home-export-outline', 1),
                    ('maintenance', 'Maintenance & Payments', 'Bills, receipts, and payment forms', 'wrench-outline', 2),
                    ('complaints', 'Complaints & Requests', 'Report issues and make requests', 'alert-circle-outline', 3),
                    ('permissions', 'Permissions & Approvals', 'Request approvals for various activities', 'check-circle-outline', 4),
                    ('governance', 'Society Governance', 'Meeting notices, resolutions, elections', 'gavel', 5),
                    ('legal', 'Legal & Compliance', 'Legal documents and compliance forms', 'scale-balance', 6),
                    ('communication', 'Communication', 'Notices, circulars, announcements', 'email-outline', 7),
                    ('administrative', 'Administrative', 'Member updates and registrations', 'folder-outline', 8),
                    ('financial', 'Financial', 'Financial requests and reports', 'currency-inr', 9),
                    ('emergency', 'Emergency & Safety', 'Emergency contacts and safety forms', 'alert-outline', 10),
                ]
                
                for cat_code, cat_name, cat_desc, icon, order in categories:
                    await db.execute(text("""
                        INSERT INTO template_categories (category_code, category_name, category_description, icon_name, display_order, is_active)
                        VALUES (:code, :name, :desc, :icon, :order, :active)
                    """), {"code": cat_code, "name": cat_name, "desc": cat_desc, "icon": icon, "order": order, "active": True})
                await db.commit()
                logger.info("  ✓ Inserted default template categories")
            
            # Create document_templates table if it doesn't exist
            if not await table_exists(db, "document_templates"):
                pk_syntax = get_autoincrement_syntax()
                await db.execute(text(f"""
                    CREATE TABLE document_templates (
                        id {pk_syntax},
                        society_id INTEGER NOT NULL DEFAULT 1,
                        template_name VARCHAR(200) NOT NULL,
                        template_code VARCHAR(50) NOT NULL UNIQUE,
                        category VARCHAR(50) NOT NULL,
                        template_html TEXT NOT NULL,
                        template_variables TEXT,
                        description TEXT,
                        instructions TEXT,
                        template_type VARCHAR(20) NOT NULL,
                        can_autofill INTEGER DEFAULT 0,
                        autofill_fields TEXT,
                        available_to VARCHAR(20) DEFAULT 'all',
                        icon_name VARCHAR(50),
                        display_order INTEGER DEFAULT 0,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (society_id) REFERENCES societies(id) ON DELETE CASCADE
                    )
                """))
                await db.execute(text("CREATE INDEX IF NOT EXISTS idx_templates_category ON document_templates(category)"))
                await db.execute(text("CREATE INDEX IF NOT EXISTS idx_templates_code ON document_templates(template_code)"))
                await db.execute(text("CREATE INDEX IF NOT EXISTS idx_templates_type ON document_templates(template_type)"))
                await db.execute(text("CREATE INDEX IF NOT EXISTS idx_templates_active ON document_templates(is_active)"))
                await db.commit()
                logger.info("  ✓ Created document_templates table")
            
            # Create template_usage_log table if it doesn't exist
            if not await table_exists(db, "template_usage_log"):
                pk_syntax = get_autoincrement_syntax()
                await db.execute(text(f"""
                    CREATE TABLE template_usage_log (
                        id {pk_syntax},
                        template_id INTEGER NOT NULL,
                        template_code VARCHAR(50) NOT NULL,
                        society_id INTEGER NOT NULL,
                        member_id INTEGER NOT NULL,
                        generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        platform VARCHAR(20),
                        FOREIGN KEY (template_id) REFERENCES document_templates(id) ON DELETE CASCADE,
                        FOREIGN KEY (society_id) REFERENCES societies(id) ON DELETE CASCADE,
                        FOREIGN KEY (member_id) REFERENCES users(id) ON DELETE CASCADE
                    )
                """))
                await db.execute(text("CREATE INDEX IF NOT EXISTS idx_usage_template ON template_usage_log(template_id)"))
                await db.execute(text("CREATE INDEX IF NOT EXISTS idx_usage_member ON template_usage_log(member_id)"))
                await db.execute(text("CREATE INDEX IF NOT EXISTS idx_usage_date ON template_usage_log(generated_at)"))
                await db.commit()
                logger.info("  ✓ Created template_usage_log table")
            
            # Seed sample templates for all societies that don't have templates
            # Get all society IDs
            result = await db.execute(text("SELECT DISTINCT id FROM societies"))
            societies = result.fetchall()
            
            for (society_id,) in societies:
                result = await db.execute(text("SELECT COUNT(*) as count FROM document_templates WHERE society_id = :society_id"), {'society_id': society_id})
                count = result.fetchone()[0]
                if count == 0:
                    await seed_sample_templates(db, society_id=society_id)
                    logger.info(f"  ✓ Seeded sample templates for society_id={society_id}")
            
            # Also seed for society_id=1 if it doesn't exist in societies table
            result = await db.execute(text("SELECT COUNT(*) as count FROM document_templates WHERE society_id = 1"))
            count = result.fetchone()[0]
            if count == 0:
                await seed_sample_templates(db, society_id=1)
                logger.info("  ✓ Seeded sample templates for default society_id=1")
    except Exception as e:
        logger.warning(f"Template system migration check failed: {e}")


async def seed_sample_templates(db: AsyncSession, society_id: int = 1):
    """Seed sample templates for Resource Centre"""
    from sqlalchemy import text
    
    # Sample HTML templates
    NOC_MOVEOUT_HTML = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 40px; }
        .title { font-size: 20px; font-weight: bold; text-align: center; margin: 30px 0; text-decoration: underline; }
        .content { margin: 20px 0; }
        table { width: 100%; margin: 20px 0; }
        table td { padding: 8px; }
        .signature-section { margin-top: 60px; }
        .signature-block { display: inline-block; width: 45%; text-align: center; }
    </style>
</head>
<body>
    <div class="title">NO OBJECTION CERTIFICATE (NOC)</div>
    
    <div class="content">
        <p>This is to certify that:</p>
        
        <table>
            <tr>
                <td width="30%"><strong>Name:</strong></td>
                <td>{{member_name}}</td>
            </tr>
            <tr>
                <td><strong>Flat Number:</strong></td>
                <td>{{flat_number}}</td>
            </tr>
            <tr>
                <td><strong>Contact:</strong></td>
                <td>{{member_phone}}</td>
            </tr>
            <tr>
                <td><strong>Email:</strong></td>
                <td>{{member_email}}</td>
            </tr>
        </table>
        
        <p>has cleared all outstanding dues and obligations towards the society as of {{current_date}}.</p>
        
        <p><strong>Clearance Details:</strong></p>
        <ul>
            <li>✓ Maintenance dues: Cleared</li>
            <li>✓ Utility bills: Cleared</li>
            <li>✓ Special assessments: Cleared</li>
            <li>✓ Security deposit: Refunded/Adjusted</li>
            <li>✓ Keys returned: Yes</li>
        </ul>
        
        <p><strong>Purpose:</strong> {{reason}}</p>
        
        <p>The society has <strong>NO OBJECTION</strong> to the above-mentioned action.</p>
    </div>
    
    <div class="signature-section">
        <div class="signature-block">
            <div style="height: 60px; border-bottom: 1px solid #000;"></div>
            <div><strong>Secretary</strong></div>
            <div>{{society_name}}</div>
        </div>
        
        <div class="signature-block" style="float: right;">
            <div style="height: 60px; border-bottom: 1px solid #000;"></div>
            <div><strong>Chairman</strong></div>
            <div>{{society_name}}</div>
        </div>
    </div>
    
    <div style="clear: both;"></div>
    
    <div style="margin-top: 40px; text-align: center; font-size: 12px; color: #666;">
        <p>This is a computer-generated certificate.</p>
        <p>Reference No: NOC/{{current_date}}/{{flat_number}}</p>
    </div>
</body>
</html>"""

    MAINTENANCE_BILL_HTML = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 40px; }
        .title { font-size: 20px; font-weight: bold; text-align: center; margin: 30px 0; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        table td { padding: 8px; border-bottom: 1px solid #ddd; }
        .total { font-weight: bold; font-size: 16px; }
    </style>
</head>
<body>
    <div class="title">MAINTENANCE BILL</div>
    
    <div style="margin: 20px 0;">
        <p><strong>Bill To:</strong></p>
        <p>Flat No: {{flat_number}}</p>
        <p>Owner: {{member_name}}</p>
        <p>Email: {{member_email}}</p>
        <p>Phone: {{member_phone}}</p>
    </div>
    
    <table>
        <tr>
            <td><strong>Bill Number:</strong></td>
            <td>MB/{{current_year}}/{{current_month}}/{{flat_number}}</td>
        </tr>
        <tr>
            <td><strong>Bill Date:</strong></td>
            <td>{{current_date}}</td>
        </tr>
        <tr>
            <td><strong>Due Date:</strong></td>
            <td>{{due_date}}</td>
        </tr>
        <tr>
            <td><strong>Billing Period:</strong></td>
            <td>{{current_month}} {{current_year}}</td>
        </tr>
    </table>
    
    <table>
        <tr style="background-color: #f0f0f0;">
            <td><strong>Description</strong></td>
            <td align="right"><strong>Amount (₹)</strong></td>
        </tr>
        <tr>
            <td>Maintenance Charges</td>
            <td align="right">{{maintenance_amount}}</td>
        </tr>
        <tr>
            <td>Water Charges</td>
            <td align="right">{{water_charges}}</td>
        </tr>
        <tr>
            <td>Electricity (Common)</td>
            <td align="right">{{electricity_charges}}</td>
        </tr>
        <tr>
            <td>Sinking Fund</td>
            <td align="right">{{sinking_fund}}</td>
        </tr>
        <tr class="total">
            <td><strong>TOTAL AMOUNT DUE</strong></td>
            <td align="right"><strong>₹{{total_amount}}</strong></td>
        </tr>
    </table>
    
    <div style="margin-top: 30px;">
        <p><strong>Payment Methods:</strong></p>
        <p>1. Online: UPI - {{society_upi_id}}</p>
        <p>2. Bank Transfer: {{society_bank_details}}</p>
        <p>3. Cash/Cheque: At society office</p>
    </div>
</body>
</html>"""

    COMPLAINT_FORM_HTML = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 40px; }
        .title { font-size: 20px; font-weight: bold; text-align: center; margin: 30px 0; }
        table { width: 100%; margin: 20px 0; }
        table td { padding: 8px; }
    </style>
</head>
<body>
    <div class="title">COMPLAINT FORM</div>
    
    <table>
        <tr>
            <td width="30%"><strong>Complaint ID:</strong></td>
            <td>COMP/{{current_date}}/{{flat_number}}</td>
        </tr>
        <tr>
            <td><strong>Date:</strong></td>
            <td>{{current_date}}</td>
        </tr>
        <tr>
            <td><strong>Complainant Name:</strong></td>
            <td>{{member_name}}</td>
        </tr>
        <tr>
            <td><strong>Flat Number:</strong></td>
            <td>{{flat_number}}</td>
        </tr>
        <tr>
            <td><strong>Contact:</strong></td>
            <td>{{member_phone}}</td>
        </tr>
        <tr>
            <td><strong>Email:</strong></td>
            <td>{{member_email}}</td>
        </tr>
    </table>
    
    <div style="margin: 20px 0;">
        <p><strong>Complaint Category:</strong> {{complaint_category}}</p>
        <p><strong>Priority:</strong> {{priority}}</p>
        <p><strong>Subject:</strong> {{subject}}</p>
        <p><strong>Description:</strong></p>
        <p style="border: 1px solid #ddd; padding: 10px; min-height: 100px;">{{description}}</p>
        <p><strong>Location:</strong> {{location}}</p>
    </div>
    
    <div style="margin-top: 40px;">
        <p><strong>FOR OFFICE USE ONLY:</strong></p>
        <p>Assigned to: _________________</p>
        <p>Status: _________________</p>
        <p>Resolution Date: _________________</p>
    </div>
</body>
</html>"""

    # Simple blank template HTML
    BLANK_TEMPLATE_HTML = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 40px; }
        .title { font-size: 20px; font-weight: bold; text-align: center; margin: 30px 0; }
        .content { margin: 20px 0; }
    </style>
</head>
<body>
    <div class="title">{{template_name}}</div>
    <div class="content">
        <p>Fill in the details below:</p>
        <p>_________________________________</p>
        <p>_________________________________</p>
        <p>_________________________________</p>
    </div>
</body>
</html>"""

    templates = [
        # Move-In/Move-Out
        ('NOC for Move-Out', 'NOC_MOVEOUT', 'moveout', 
         'No Objection Certificate for tenant/owner moving out',
         'This form will be auto-filled with your details. You only need to provide the reason for move-out.',
         'auto_fill', True, 
         '["member_name","flat_number","member_email","member_phone","society_name","society_address","current_date"]',
         NOC_MOVEOUT_HTML,
         '["reason"]', 'file-certificate', 'all', 1),
        ('Move-In Form', 'MOVE_IN_FORM', 'moveout',
         'Form for new tenant/owner moving in',
         'Fill in the move-in details.',
         'blank_download', False,
         '[]',
         BLANK_TEMPLATE_HTML.replace('{{template_name}}', 'Move-In Form'),
         '[]', 'home-export-outline', 'all', 2),
        
        # Maintenance & Payments
        ('Monthly Maintenance Bill', 'MAINT_BILL', 'maintenance',
         'Monthly maintenance bill template',
         'Auto-filled with member and billing details. Fill in the amounts.',
         'auto_fill', True,
         '["member_name","flat_number","member_email","member_phone","society_name","current_date","current_month","current_year"]',
         MAINTENANCE_BILL_HTML,
         '["maintenance_amount","water_charges","electricity_charges","sinking_fund","total_amount","due_date","society_upi_id","society_bank_details"]',
         'receipt', 'all', 1),
        ('Payment Receipt', 'PAYMENT_RECEIPT', 'maintenance',
         'Payment receipt template',
         'Generate receipt for maintenance payments.',
         'blank_download', False,
         '[]',
         BLANK_TEMPLATE_HTML.replace('{{template_name}}', 'Payment Receipt'),
         '[]', 'receipt-outline', 'all', 2),
        
        # Complaints & Requests
        ('Complaint Form', 'COMPLAINT_FORM', 'complaints',
         'Form to register complaints and requests',
         'Fill in the complaint details. Your information will be auto-filled.',
         'auto_fill', True,
         '["member_name","flat_number","member_email","member_phone","current_date"]',
         COMPLAINT_FORM_HTML,
         '["complaint_category","priority","subject","description","location"]',
         'alert-circle', 'all', 1),
        ('Service Request', 'SERVICE_REQUEST', 'complaints',
         'Request for maintenance or services',
         'Fill in service request details.',
         'blank_download', False,
         '[]',
         BLANK_TEMPLATE_HTML.replace('{{template_name}}', 'Service Request'),
         '[]', 'construct-outline', 'all', 2),
        
        # Permissions & Approvals
        ('Permission Request', 'PERMISSION_REQUEST', 'permissions',
         'Request permission for various activities',
         'Fill in permission request details.',
         'blank_download', False,
         '[]',
         BLANK_TEMPLATE_HTML.replace('{{template_name}}', 'Permission Request'),
         '[]', 'checkmark-circle-outline', 'all', 1),
        ('Renovation Approval', 'RENOVATION_APPROVAL', 'permissions',
         'Request approval for flat renovation',
         'Fill in renovation details.',
         'blank_download', False,
         '[]',
         BLANK_TEMPLATE_HTML.replace('{{template_name}}', 'Renovation Approval Request'),
         '[]', 'hammer-outline', 'all', 2),
        
        # Society Governance
        ('Meeting Notice', 'MEETING_NOTICE', 'governance',
         'Notice for society meetings',
         'Generate meeting notice.',
         'blank_download', False,
         '[]',
         BLANK_TEMPLATE_HTML.replace('{{template_name}}', 'Meeting Notice'),
         '[]', 'gavel', 'all', 1),
        ('Election Nomination', 'ELECTION_NOMINATION', 'governance',
         'Nomination form for society elections',
         'Fill in nomination details.',
         'blank_download', False,
         '[]',
         BLANK_TEMPLATE_HTML.replace('{{template_name}}', 'Election Nomination Form'),
         '[]', 'person-add-outline', 'all', 2),
        
        # Legal & Compliance
        ('Legal Notice', 'LEGAL_NOTICE', 'legal',
         'Legal notice template',
         'Generate legal notices.',
         'blank_download', False,
         '[]',
         BLANK_TEMPLATE_HTML.replace('{{template_name}}', 'Legal Notice'),
         '[]', 'scale-balance', 'all', 1),
        ('Compliance Certificate', 'COMPLIANCE_CERT', 'legal',
         'Compliance certificate template',
         'Generate compliance certificates.',
         'blank_download', False,
         '[]',
         BLANK_TEMPLATE_HTML.replace('{{template_name}}', 'Compliance Certificate'),
         '[]', 'document-text-outline', 'all', 2),
        
        # Communication
        ('Circular Notice', 'CIRCULAR_NOTICE', 'communication',
         'Circular notice template',
         'Generate circular notices.',
         'blank_download', False,
         '[]',
         BLANK_TEMPLATE_HTML.replace('{{template_name}}', 'Circular Notice'),
         '[]', 'mail-outline', 'all', 1),
        ('Announcement', 'ANNOUNCEMENT', 'communication',
         'Announcement template',
         'Generate announcements.',
         'blank_download', False,
         '[]',
         BLANK_TEMPLATE_HTML.replace('{{template_name}}', 'Announcement'),
         '[]', 'megaphone-outline', 'all', 2),
        
        # Administrative
        ('Member Registration', 'MEMBER_REGISTRATION', 'administrative',
         'New member registration form',
         'Fill in member registration details.',
         'blank_download', False,
         '[]',
         BLANK_TEMPLATE_HTML.replace('{{template_name}}', 'Member Registration Form'),
         '[]', 'folder-outline', 'all', 1),
        ('Member Update Form', 'MEMBER_UPDATE', 'administrative',
         'Update member information',
         'Fill in updated member details.',
         'blank_download', False,
         '[]',
         BLANK_TEMPLATE_HTML.replace('{{template_name}}', 'Member Information Update Form'),
         '[]', 'create-outline', 'all', 2),
        
        # Financial
        ('Financial Request', 'FINANCIAL_REQUEST', 'financial',
         'Request for financial transactions',
         'Fill in financial request details.',
         'blank_download', False,
         '[]',
         BLANK_TEMPLATE_HTML.replace('{{template_name}}', 'Financial Request'),
         '[]', 'currency-inr', 'all', 1),
        ('Budget Approval', 'BUDGET_APPROVAL', 'financial',
         'Budget approval request',
         'Fill in budget details.',
         'blank_download', False,
         '[]',
         BLANK_TEMPLATE_HTML.replace('{{template_name}}', 'Budget Approval Request'),
         '[]', 'calculator-outline', 'all', 2),
        
        # Emergency & Safety
        ('Emergency Contact Form', 'EMERGENCY_CONTACT', 'emergency',
         'Emergency contact information form',
         'Fill in emergency contact details.',
         'blank_download', False,
         '[]',
         BLANK_TEMPLATE_HTML.replace('{{template_name}}', 'Emergency Contact Form'),
         '[]', 'alert-outline', 'all', 1),
        ('Safety Incident Report', 'SAFETY_INCIDENT', 'emergency',
         'Report safety incidents',
         'Fill in incident details.',
         'blank_download', False,
         '[]',
         BLANK_TEMPLATE_HTML.replace('{{template_name}}', 'Safety Incident Report'),
         '[]', 'warning-outline', 'all', 2),
    ]
    
    from datetime import datetime
    now = datetime.utcnow()
    
    for (name, code, cat, desc, inst, ttype, can_autofill, autofill_fields, html, vars, icon, avail, order) in templates:
        await db.execute(text("""
            INSERT INTO document_templates 
            (society_id, template_name, template_code, category, description, 
             instructions, template_type, can_autofill, autofill_fields,
             template_html, template_variables, icon_name, available_to, display_order, is_active, created_at, updated_at)
            VALUES (:society_id, :name, :code, :cat, :desc, :inst, :ttype, :can_autofill, :autofill_fields, :html, :vars, :icon, :avail, :order, TRUE, :created_at, :updated_at)
        """), {
            'society_id': society_id,
            'name': name,
            'code': code,
            'cat': cat,
            'desc': desc,
            'inst': inst,
            'ttype': ttype,
            'can_autofill': can_autofill,
            'autofill_fields': autofill_fields,
            'html': html,
            'vars': vars,
            'icon': icon,
            'avail': avail,
            'order': order,
            'created_at': now,
            'updated_at': now
        })
    
    await db.commit()


async def migrate_flats_bedrooms():
    """Add bedrooms column to flats table if it doesn't exist"""
    from sqlalchemy import text
    try:
        async with AsyncSessionLocal() as db:
            # Check existing columns (PostgreSQL/SQLite compatible)
            columns = await get_table_columns(db, "flats")
            
            # Add bedrooms column if it doesn't exist
            if 'bedrooms' not in columns:
                try:
                    await db.execute(text("ALTER TABLE flats ADD COLUMN bedrooms INTEGER DEFAULT 2"))
                    await db.commit()
                    logger.info("  ✓ Added bedrooms column to flats table (default: 2)")
                    
                    # Update existing flats to have default value of 2
                    await db.execute(text("UPDATE flats SET bedrooms = 2 WHERE bedrooms IS NULL"))
                    await db.commit()
                    logger.info("  ✓ Updated existing flats with default bedrooms value")
                except Exception as e:
                    logger.warning(f"  ⚠ Could not add bedrooms column: {e}")
            else:
                logger.info("  - bedrooms column already exists in flats table")
    except Exception as e:
        logger.warning(f"Flats bedrooms migration failed: {e}")
        # Don't raise - allow app to continue even if migration fails


async def close_db():
    """Close database connection"""
    try:
        await engine.dispose()
        logger.info("Database connection closed")
    except Exception as e:
        logger.error(f"Error closing database connection: {e}")


async def seed_default_data():
    """Seed default society and admin user if they don't exist"""
    # Use ORM to handle Enums and Defaults correctly
    from app.models_db import Society, User, UserRole, AccountingType
    from app.utils.security import get_password_hash
    from sqlalchemy import select
    
    try:
        async with AsyncSessionLocal() as db:
            # 1. Check if Default Society exists
            result = await db.execute(select(Society).where(Society.id == 1))
            society_exists = result.scalar_one_or_none()
            
            if not society_exists:
                logger.info("  🌱 Seeding Default Society...")
                default_society = Society(
                    id=1,
                    name='GharMitra Society',
                    address_line='Default Address',
                    total_flats=0,
                    gst_registration_applicable=False,
                    accounting_type=AccountingType.CASH, # Use Enum
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(default_society)
                await db.commit()
                logger.info("  ✓ Created Default Society (ID: 1)")
            else:
                logger.info("  - Default Society already exists")

            # 2. Check if Admin User exists
            result = await db.execute(select(User).where(User.email == 'admin@example.com'))
            admin_user = result.scalar_one_or_none()
            
            if not admin_user:
                logger.info("  🌱 Seeding Admin User...")
                password_hash = get_password_hash("admin123")
                
                admin_user = User(
                    society_id=1,
                    email='admin@example.com',
                    password_hash=password_hash,
                    name='Admin User',
                    apartment_number='ADMIN',
                    role=UserRole.ADMIN, # Use Enum
                    terms_accepted=True,
                    privacy_accepted=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(admin_user)
                await db.commit()
                logger.info("  ✓ Created Admin User (admin@example.com / admin123)")
            else:
                logger.info("  - Admin User already exists")
                
    except Exception as e:
        logger.warning(f"  ⚠ Default data seeding failed: {e}")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session
    Usage: db: AsyncSession = Depends(get_db)
    Ensures engine is initialized before use (lazy initialization)
    """
    # Ensure engine is initialized (lazy initialization)
    if AsyncSessionLocal is None:
        create_engine_instance()
    
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

