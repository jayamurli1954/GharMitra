"""
Migration Script: Add description column to water_expenses table
This script adds the missing description column to the water_expenses table
to match the model definition.
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
    """Run migration to add description column to water_expenses"""
    async with AsyncSessionLocal() as db:
        try:
            logger.info("Starting water_expenses description column migration...")
            
            # Check if column already exists
            result = await db.execute(text("PRAGMA table_info(water_expenses)"))
            columns = [row[1] for row in result.fetchall()]
            
            if "description" not in columns:
                logger.info("Adding description column to water_expenses table...")
                await db.execute(text("ALTER TABLE water_expenses ADD COLUMN description TEXT"))
                await db.commit()
                logger.info("✓ Added description column to water_expenses")
            else:
                logger.info("✓ description column already exists in water_expenses")
            
            logger.info("✅ Migration completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(migrate())




