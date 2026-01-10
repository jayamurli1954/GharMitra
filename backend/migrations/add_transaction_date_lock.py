"""
Migration Script: Add transaction date lock fields to society_settings table
This script adds date lock configuration fields for transaction date validation.
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
    """Run migration to add transaction date lock fields"""
    async with AsyncSessionLocal() as db:
        try:
            logger.info("Starting transaction date lock fields migration...")
            
            # Check if columns already exist
            result = await db.execute(text("PRAGMA table_info(society_settings)"))
            columns = [row[1] for row in result.fetchall()]
            
            new_columns = [
                ("transaction_date_lock_enabled", "BOOLEAN DEFAULT 1"),
                ("transaction_date_lock_months", "INTEGER DEFAULT 1"),
            ]
            
            for col_name, col_def in new_columns:
                if col_name not in columns:
                    logger.info(f"Adding {col_name} column to society_settings table...")
                    await db.execute(text(f"ALTER TABLE society_settings ADD COLUMN {col_name} {col_def}"))
                    await db.commit()
                    logger.info(f"✓ Added {col_name} to society_settings")
                else:
                    logger.info(f"✓ {col_name} already exists in society_settings")
            
            logger.info("✅ Migration completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(migrate())




