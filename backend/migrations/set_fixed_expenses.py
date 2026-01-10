#!/usr/bin/env python3
"""
Migration: Set Fixed Expenses for Billing Calculation
- Marks expense account codes that should be included in fixed expenses for billing
- Fixed expenses are distributed equally across all flats
- Water charges (5110, 5120) are NOT fixed expenses - they are calculated per occupant
"""
import sys
import os
import asyncio
import logging

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import AsyncSessionLocal
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Fixed expense account codes that should be distributed equally across all flats
FIXED_EXPENSE_CODES = [
    '5000',  # Watchman Salary
    '5010',  # Housekeeping Salary
    '5020',  # Manager Salary
    '5030',  # Other Staff Salary
    '5100',  # Electricity Charges - Common Area
    # Add more as needed
]


async def migrate():
    """Set is_fixed_expense=True for relevant expense accounts"""
    async with AsyncSessionLocal() as db:
        try:
            logger.info("Starting fixed expenses configuration migration...")
            
            for code in FIXED_EXPENSE_CODES:
                result = await db.execute(
                    text("UPDATE account_codes SET is_fixed_expense = TRUE WHERE code = :code"),
                    {"code": code}
                )
                if result.rowcount > 0:
                    logger.info(f"✓ Set is_fixed_expense=True for account {code}")
                else:
                    logger.warning(f"⚠️ Account {code} not found")
            
            await db.commit()
            logger.info("✅ Migration completed successfully!")
            logger.info(f"   Fixed expense accounts: {', '.join(FIXED_EXPENSE_CODES)}")
            logger.info("   Water charges (5110, 5120) remain variable and calculated per occupant")
                
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    logger.info("=== Set Fixed Expenses Migration ===")
    asyncio.run(migrate())
    logger.info("=== Migration Complete ===")




