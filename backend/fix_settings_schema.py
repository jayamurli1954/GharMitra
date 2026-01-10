import sqlite3
import os

DB_PATH = "gharmitra.db"

def fix_db():
    if not os.path.exists(DB_PATH):
        print(f"Database file {DB_PATH} not found.")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        print("dropping outdated society_settings table...")
        cursor.execute("DROP TABLE IF EXISTS society_settings")
        
        conn.commit()
        print("Success! Table dropped. It will be recreated on next app startup.")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_db()
