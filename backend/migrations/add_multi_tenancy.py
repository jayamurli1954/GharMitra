"""
Migration Script: Add Multi-Tenancy Support
This script:
1. Creates the societies table
2. Creates a default society
3. Adds society_id column to all existing tables
4. Assigns all existing data to the default society (society_id = 1)
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import engine, AsyncSessionLocal
from app.models_db import Society, User, Flat, Transaction, ChatRoom, ApartmentSettings, FixedExpense, WaterExpense, MaintenanceBill, AccountCode
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate():
    """Run migration to add multi-tenancy support"""
    async with AsyncSessionLocal() as db:
        try:
            logger.info("Starting multi-tenancy migration...")
            
            # Step 1: Create societies table if it doesn't exist
            logger.info("Step 1: Creating societies table...")
            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS societies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(100) NOT NULL,
                    address TEXT,
                    total_flats INTEGER NOT NULL,
                    min_vacancy_fee REAL DEFAULT 500.0,
                    billing_config TEXT,
                    subscription_plan VARCHAR(50) DEFAULT 'free',
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                )
            """))
            await db.commit()
            logger.info("✓ Societies table created")
            
            # Step 2: Check if default society exists, create if not
            logger.info("Step 2: Creating default society...")
            result = await db.execute(text("SELECT COUNT(*) FROM societies WHERE id = 1"))
            count = result.scalar()
            
            if count == 0:
                # Get total flats count
                result = await db.execute(text("SELECT COUNT(*) FROM flats"))
                total_flats = result.scalar() or 0
                
                await db.execute(text("""
                    INSERT INTO societies (id, name, address, total_flats, min_vacancy_fee, subscription_plan, created_at, updated_at)
                    VALUES (1, 'Default Society', 'Address to be updated', :total_flats, 500.0, 'free', datetime('now'), datetime('now'))
                """), {"total_flats": total_flats})
                await db.commit()
                logger.info(f"✓ Default society created with {total_flats} flats")
            else:
                logger.info("✓ Default society already exists")
            
            # Step 3: Add society_id columns to existing tables
            logger.info("Step 3: Adding society_id columns to existing tables...")
            
            tables_to_migrate = [
                ("users", "society_id INTEGER DEFAULT 1"),
                ("flats", "society_id INTEGER DEFAULT 1"),
                ("transactions", "society_id INTEGER DEFAULT 1"),
                ("chat_rooms", "society_id INTEGER DEFAULT 1"),
                ("apartment_settings", "society_id INTEGER DEFAULT 1"),
                ("fixed_expenses", "society_id INTEGER DEFAULT 1"),
                ("water_expenses", "society_id INTEGER DEFAULT 1"),
                ("maintenance_bills", "society_id INTEGER DEFAULT 1"),
                ("account_codes", "society_id INTEGER DEFAULT 1"),
            ]
            
            for table_name, column_def in tables_to_migrate:
                try:
                    # Check if column already exists
                    result = await db.execute(text(f"PRAGMA table_info({table_name})"))
                    columns = [row[1] for row in result.fetchall()]
                    
                    if "society_id" not in columns:
                        await db.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_def}"))
                        await db.commit()
                        logger.info(f"  ✓ Added society_id to {table_name}")
                    else:
                        logger.info(f"  - society_id already exists in {table_name}")
                except Exception as e:
                    logger.warning(f"  ⚠ Could not add society_id to {table_name}: {e}")
            
            # Step 4: Update all existing records to have society_id = 1
            logger.info("Step 4: Assigning existing data to default society...")
            
            update_queries = [
                "UPDATE users SET society_id = 1 WHERE society_id IS NULL",
                "UPDATE flats SET society_id = 1 WHERE society_id IS NULL",
                "UPDATE transactions SET society_id = 1 WHERE society_id IS NULL",
                "UPDATE chat_rooms SET society_id = 1 WHERE society_id IS NULL",
                "UPDATE apartment_settings SET society_id = 1 WHERE society_id IS NULL",
                "UPDATE fixed_expenses SET society_id = 1 WHERE society_id IS NULL",
                "UPDATE water_expenses SET society_id = 1 WHERE society_id IS NULL",
                "UPDATE maintenance_bills SET society_id = 1 WHERE society_id IS NULL",
                "UPDATE account_codes SET society_id = 1 WHERE society_id IS NULL",
            ]
            
            for query in update_queries:
                try:
                    result = await db.execute(text(query))
                    await db.commit()
                    logger.info(f"  ✓ Updated {result.rowcount} rows")
                except Exception as e:
                    logger.warning(f"  ⚠ Could not update: {e}")
            
            # Step 5: Add new columns to flats table (block, floor, occupancy_status, parking_slots)
            logger.info("Step 5: Adding PRD fields to flats table...")
            try:
                result = await db.execute(text("PRAGMA table_info(flats)"))
                columns = [row[1] for row in result.fetchall()]
                
                new_columns = [
                    ("block", "VARCHAR(10)"),
                    ("floor", "INTEGER"),
                    ("occupancy_status", "VARCHAR(20) DEFAULT 'vacant'"),
                    ("parking_slots", "INTEGER DEFAULT 0"),
                ]
                
                for col_name, col_type in new_columns:
                    if col_name not in columns:
                        await db.execute(text(f"ALTER TABLE flats ADD COLUMN {col_name} {col_type}"))
                        await db.commit()
                        logger.info(f"  ✓ Added {col_name} to flats")
                    else:
                        logger.info(f"  - {col_name} already exists in flats")
            except Exception as e:
                logger.warning(f"  ⚠ Could not add new columns to flats: {e}")
            
            logger.info("✅ Migration completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(migrate())

