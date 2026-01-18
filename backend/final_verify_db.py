import sqlite3
import os
from app.config import settings

def final_verify():
    db_url = settings.DATABASE_URL
    path = db_url.replace("sqlite+aiosqlite:///", "")
    abs_path = os.path.abspath(path)
    print(f"VERIFY: Path from settings: {abs_path}")
    
    if os.path.exists(abs_path):
        conn = sqlite3.connect(abs_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(transactions)")
        cols = [c[1] for c in cursor.fetchall()]
        print(f"VERIFY: Columns in transactions: {cols}")
        
        if "is_reversed" in cols:
            print("VERIFY: SUCCESS - Column exists in target DB.")
        else:
            print("VERIFY: FAILURE - Column STILL MISSING in target DB.")
            # Last ditch effort to add it
            try:
                cursor.execute("ALTER TABLE transactions ADD COLUMN is_reversed BOOLEAN DEFAULT 0")
                conn.commit()
                print("VERIFY: Column added in last-ditch effort.")
            except Exception as e:
                print(f"VERIFY: Error in last-ditch effort: {e}")
        conn.close()
    else:
        print(f"VERIFY: Target DB file does not exist at {abs_path}")

if __name__ == "__main__":
    final_verify()
