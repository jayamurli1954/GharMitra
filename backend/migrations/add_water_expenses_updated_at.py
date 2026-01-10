#!/usr/bin/env python3
"""
Migration: Add updated_at column to water_expenses table
"""
import sys
import os
import asyncio
import logging

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import AsyncSessionLocal
from sqlalchemy import text
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate():
    """Add updated_at column to water_expenses table"""
    async with AsyncSessionLocal() as db:
        try:
            logger.info("Starting water_expenses updated_at column migration...")
            
            # Check if column exists
            result = await db.execute(text("PRAGMA table_info(water_expenses)"))
            columns = [row[1] for row in result.fetchall()]
            
            if "updated_at" not in columns:
                # Add updated_at column with default value
                await db.execute(
                    text("ALTER TABLE water_expenses ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL")
                )
                await db.commit()
                logger.info("✓ Added updated_at column to water_expenses")
            else:
                logger.info("- updated_at column already exists in water_expenses")
            
            logger.info("✅ Migration completed successfully!")
                
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    logger.info("=== Add water_expenses updated_at Column Migration ===")
    asyncio.run(migrate())
    logger.info("=== Migration Complete ===")




