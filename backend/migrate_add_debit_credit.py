"""
Migration script to add debit_amount, credit_amount, journal_entry_id, and payment_method columns to transactions table
"""
import sqlite3
import os
from pathlib import Path

# Get the database path
db_path = Path(__file__).parent / "GharMitra.db"

if not db_path.exists():
    print(f"ERROR: Database file not found at {db_path}")
    print("   The database will be created automatically when you run the app.")
    exit(1)

print(f"Connecting to database: {db_path}")

try:
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Check if columns already exist
    cursor.execute("PRAGMA table_info(transactions)")
    columns = [row[1] for row in cursor.fetchall()]
    
    print(f"Current columns in transactions table: {columns}")
    
    # Add columns if they don't exist
    changes_made = False
    
    if 'debit_amount' not in columns:
        print("Adding debit_amount column...")
        cursor.execute("ALTER TABLE transactions ADD COLUMN debit_amount REAL DEFAULT 0.0")
        changes_made = True
    
    if 'credit_amount' not in columns:
        print("Adding credit_amount column...")
        cursor.execute("ALTER TABLE transactions ADD COLUMN credit_amount REAL DEFAULT 0.0")
        changes_made = True
    
    if 'journal_entry_id' not in columns:
        print("Adding journal_entry_id column...")
        cursor.execute("ALTER TABLE transactions ADD COLUMN journal_entry_id INTEGER")
        changes_made = True
    
    if 'payment_method' not in columns:
        print("Adding payment_method column...")
        cursor.execute("ALTER TABLE transactions ADD COLUMN payment_method TEXT")
        changes_made = True
    
    if changes_made:
        conn.commit()
        print("SUCCESS: Migration completed successfully!")
        print("   Added columns: debit_amount, credit_amount, journal_entry_id, payment_method")
    else:
        print("SUCCESS: All columns already exist. No migration needed.")
    
    # Verify the columns were added
    cursor.execute("PRAGMA table_info(transactions)")
    columns_after = [row[1] for row in cursor.fetchall()]
    print(f"Columns after migration: {columns_after}")
    
    conn.close()
    
except sqlite3.Error as e:
    print(f"ERROR: Database error: {e}")
    exit(1)
except Exception as e:
    print(f"ERROR: {e}")
    exit(1)


