"""
Migration Script: Add Society Registration and Logo Fields
This script adds the following columns to the societies table:
- registration_no
- pan_no
- reg_cert_url
- pan_card_url
- logo_url
- financial_year_start
- financial_year_end
- accounting_type
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import engine, AsyncSessionLocal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate():
    """Run migration to add society registration and logo fields"""
    async with AsyncSessionLocal() as db:
        try:
            logger.info("Starting society fields migration...")
            
            # Check existing columns
            result = await db.execute(text("PRAGMA table_info(societies)"))
            columns = {row[1]: row for row in result.fetchall()}
            
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
            ]
            
            for col_name, col_type in new_columns:
                if col_name not in columns:
                    try:
                        await db.execute(text(f"ALTER TABLE societies ADD COLUMN {col_name} {col_type}"))
                        await db.commit()
                        logger.info(f"  ✓ Added {col_name} to societies table")
                    except Exception as e:
                        logger.warning(f"  ⚠ Could not add {col_name}: {e}")
                else:
                    logger.info(f"  - {col_name} already exists in societies table")
            
            logger.info("✅ Migration completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(migrate())

