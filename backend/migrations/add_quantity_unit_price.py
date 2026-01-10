"""
Migration script to add quantity and unit_price columns to transactions table
Run this script to update existing database schema
"""
import asyncio
import sqlite3
from pathlib import Path


async def run_migration():
    """Add quantity and unit_price columns to transactions table"""
    # Get database path
    db_path = Path(__file__).parent.parent / "GharMitra.db"
    
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        print("Creating new database with updated schema...")
        return
    
    print(f"Connecting to database: {db_path}")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(transactions)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'quantity' in columns and 'unit_price' in columns:
            print("[OK] Columns 'quantity' and 'unit_price' already exist in transactions table")
            return
        
        # Add quantity column if it doesn't exist
        if 'quantity' not in columns:
            print("Adding 'quantity' column to transactions table...")
            cursor.execute("ALTER TABLE transactions ADD COLUMN quantity REAL")
            print("[OK] Added 'quantity' column")
        else:
            print("[OK] 'quantity' column already exists")
        
        # Add unit_price column if it doesn't exist
        if 'unit_price' not in columns:
            print("Adding 'unit_price' column to transactions table...")
            cursor.execute("ALTER TABLE transactions ADD COLUMN unit_price REAL")
            print("[OK] Added 'unit_price' column")
        else:
            print("[OK] 'unit_price' column already exists")
        
        # Commit changes
        conn.commit()
        print("\n[SUCCESS] Migration completed successfully!")
        print("   - quantity: REAL (nullable)")
        print("   - unit_price: REAL (nullable)")
        
    except Exception as e:
        conn.rollback()
        print(f"\n[FAILED] Migration failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    asyncio.run(run_migration())


