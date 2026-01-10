#!/usr/bin/env python3
"""
Migration: Add onboarding_date to society_settings table
- Tracks when society was onboarded
- Used to restrict bill generation to previous month only
"""
import sys
import os
import asyncio
import logging

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import AsyncSessionLocal
from sqlalchemy import text
from datetime import date

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate():
    """Add onboarding_date column to society_settings table"""
    async with AsyncSessionLocal() as db:
        try:
            logger.info("Starting onboarding_date column migration...")
            
            # Check if column exists
            result = await db.execute(text("PRAGMA table_info(society_settings)"))
            columns = [row[1] for row in result.fetchall()]
            
            if "onboarding_date" not in columns:
                # Add onboarding_date column
                await db.execute(
                    text("ALTER TABLE society_settings ADD COLUMN onboarding_date DATE")
                )
                await db.commit()
                logger.info("✓ Added onboarding_date column to society_settings")
                
                # Set default onboarding_date to today for existing records
                today = date.today()
                await db.execute(
                    text("UPDATE society_settings SET onboarding_date = :today WHERE onboarding_date IS NULL"),
                    {"today": today}
                )
                await db.commit()
                logger.info(f"✓ Set default onboarding_date to {today} for existing records")
            else:
                logger.info("- onboarding_date column already exists in society_settings")
            
            logger.info("✅ Migration completed successfully!")
                
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    logger.info("=== Add onboarding_date Column Migration ===")
    asyncio.run(migrate())
    logger.info("=== Migration Complete ===")




