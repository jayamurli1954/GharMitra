"""
Migration Script: Add Physical Documents Checklist Tables
This script creates:
1. physical_documents_checklist table
2. document_access_logs table
3. Required indexes
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import AsyncSessionLocal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate():
    """Run migration to add physical documents checklist tables"""
    async with AsyncSessionLocal() as db:
        try:
            logger.info("Starting physical documents checklist migration...")
            
            # Step 1: Create physical_documents_checklist table
            logger.info("Step 1: Creating physical_documents_checklist table...")
            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS physical_documents_checklist (
                  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                  society_id INTEGER NOT NULL,
                  member_id INTEGER NOT NULL,
                  flat_id INTEGER NOT NULL,
                  
                  -- Document tracking
                  document_type TEXT NOT NULL CHECK (document_type IN (
                    'aadhaar', 
                    'pan', 
                    'passport',
                    'driving_license',
                    'rent_agreement', 
                    'sale_deed',
                    'electricity_bill',
                    'water_bill',
                    'other'
                  )),
                  
                  -- Simple yes/no tracking
                  submitted INTEGER DEFAULT 0, -- SQLite boolean: 0 = No, 1 = Yes
                  submission_date TEXT, -- ISO format: 'YYYY-MM-DD'
                  
                  -- Verification
                  verified INTEGER DEFAULT 0, -- 0 = No, 1 = Yes
                  verified_by INTEGER,
                  verification_date TEXT,
                  
                  -- Physical storage location (optionally encrypted)
                  storage_location TEXT, -- Example: 'Filing Cabinet A, Drawer 2'
                  
                  -- Optional encrypted versions (if encryption is enabled)
                  storage_location_encrypted TEXT,
                  verification_notes TEXT,
                  verification_notes_encrypted TEXT,
                  
                  -- Metadata
                  created_at TEXT DEFAULT (datetime('now')),
                  updated_at TEXT DEFAULT (datetime('now')),
                  
                  -- Constraints
                  UNIQUE(member_id, document_type),
                  FOREIGN KEY (society_id) REFERENCES societies(id) ON DELETE CASCADE,
                  FOREIGN KEY (member_id) REFERENCES users(id) ON DELETE CASCADE,
                  FOREIGN KEY (flat_id) REFERENCES flats(id) ON DELETE CASCADE,
                  FOREIGN KEY (verified_by) REFERENCES users(id)
                )
            """))
            await db.commit()
            logger.info("✓ physical_documents_checklist table created")
            
            # Step 2: Create indexes for performance
            logger.info("Step 2: Creating indexes...")
            indexes = [
                ("idx_physical_docs_member", "physical_documents_checklist(member_id)"),
                ("idx_physical_docs_society", "physical_documents_checklist(society_id)"),
                ("idx_physical_docs_verification", "physical_documents_checklist(verified, verification_date)"),
                ("idx_physical_docs_submission", "physical_documents_checklist(submitted, submission_date)"),
            ]
            
            for index_name, index_def in indexes:
                try:
                    await db.execute(text(f"CREATE INDEX IF NOT EXISTS {index_name} ON {index_def}"))
                    await db.commit()
                    logger.info(f"  ✓ Created index {index_name}")
                except Exception as e:
                    logger.warning(f"  ⚠ Could not create index {index_name}: {e}")
            
            # Step 3: Create document_access_logs table
            logger.info("Step 3: Creating document_access_logs table...")
            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS document_access_logs (
                  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                  document_id TEXT,
                  document_type TEXT NOT NULL CHECK (document_type IN ('physical', 'digital')),
                  accessed_by INTEGER,
                  access_type TEXT NOT NULL, -- 'view', 'verify', 'create', 'update', 'delete'
                  access_timestamp TEXT DEFAULT (datetime('now')),
                  ip_address TEXT,
                  user_agent TEXT,
                  
                  FOREIGN KEY (accessed_by) REFERENCES users(id)
                )
            """))
            await db.commit()
            logger.info("✓ document_access_logs table created")
            
            # Step 4: Create indexes for access logs
            logger.info("Step 4: Creating access log indexes...")
            access_log_indexes = [
                ("idx_access_logs_document", "document_access_logs(document_id)"),
                ("idx_access_logs_user", "document_access_logs(accessed_by)"),
                ("idx_access_logs_timestamp", "document_access_logs(access_timestamp)"),
            ]
            
            for index_name, index_def in access_log_indexes:
                try:
                    await db.execute(text(f"CREATE INDEX IF NOT EXISTS {index_name} ON {index_def}"))
                    await db.commit()
                    logger.info(f"  ✓ Created index {index_name}")
                except Exception as e:
                    logger.warning(f"  ⚠ Could not create index {index_name}: {e}")
            
            logger.info("✅ Physical documents checklist migration completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(migrate())






