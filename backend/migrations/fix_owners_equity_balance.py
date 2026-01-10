#!/usr/bin/env python3
"""
Migration: Fix Owners Equity Balance
- Owner's Equity (3001) is a liability/capital account and should have a CREDIT balance
- Credit balances are stored as negative values in the system
- This migration converts the opening balance from positive to negative
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


async def migrate():
    """Fix Owners Equity balance to be negative (credit balance)"""
    async with AsyncSessionLocal() as db:
        try:
            logger.info("Starting Owners Equity balance fix migration...")
            
            # Get current Owners Equity balance
            result = await db.execute(
                text("SELECT opening_balance, current_balance FROM account_codes WHERE code = '3001'")
            )
            row = result.fetchone()
            
            if row:
                opening_balance, current_balance = row
                logger.info(f"Current Owners Equity - Opening: {opening_balance}, Current: {current_balance}")
                
                # If balances are positive, convert to negative (credit balance)
                if opening_balance > 0:
                    await db.execute(
                        text("UPDATE account_codes SET opening_balance = :balance WHERE code = '3001'"),
                        {"balance": -opening_balance}
                    )
                    logger.info(f"✓ Updated opening_balance from {opening_balance} to {-opening_balance}")
                
                if current_balance > 0:
                    await db.execute(
                        text("UPDATE account_codes SET current_balance = :balance WHERE code = '3001'"),
                        {"balance": -current_balance}
                    )
                    logger.info(f"✓ Updated current_balance from {current_balance} to {-current_balance}")
                
                await db.commit()
                logger.info("✅ Migration completed successfully!")
            else:
                logger.warning("⚠️ Owners Equity account (3001) not found")
                
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    logger.info("=== Fix Owners Equity Balance Migration ===")
    asyncio.run(migrate())
    logger.info("=== Migration Complete ===")




