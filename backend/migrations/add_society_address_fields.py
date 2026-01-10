"""
Migration: Add address and contact fields to Society model
Adds: address_line, pin_code, city, state, email, landline, mobile, gst_registration_applicable
"""
import sqlite3
import os
from pathlib import Path

def migrate():
    db_path = Path(__file__).parent.parent / "GharMitra.db"
    
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(societies)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Add new columns if they don't exist
        if 'address_line' not in columns:
            cursor.execute("ALTER TABLE societies ADD COLUMN address_line TEXT")
            print("Added address_line column")
        
        if 'pin_code' not in columns:
            cursor.execute("ALTER TABLE societies ADD COLUMN pin_code VARCHAR(10)")
            print("Added pin_code column")
        
        if 'city' not in columns:
            cursor.execute("ALTER TABLE societies ADD COLUMN city VARCHAR(100)")
            print("Added city column")
        
        if 'state' not in columns:
            cursor.execute("ALTER TABLE societies ADD COLUMN state VARCHAR(100)")
            print("Added state column")
        
        if 'email' not in columns:
            cursor.execute("ALTER TABLE societies ADD COLUMN email VARCHAR(255)")
            print("Added email column")
        
        if 'landline' not in columns:
            cursor.execute("ALTER TABLE societies ADD COLUMN landline VARCHAR(20)")
            print("Added landline column")
        
        if 'mobile' not in columns:
            cursor.execute("ALTER TABLE societies ADD COLUMN mobile VARCHAR(20)")
            print("Added mobile column")
        
        if 'gst_registration_applicable' not in columns:
            cursor.execute("ALTER TABLE societies ADD COLUMN gst_registration_applicable BOOLEAN DEFAULT 0 NOT NULL")
            print("Added gst_registration_applicable column")
        
        conn.commit()
        print("Migration completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()




