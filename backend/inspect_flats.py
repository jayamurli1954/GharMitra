import sqlite3
import os

DB_PATH = "gharmitra.db"

def inspect_flats():
    db_path = DB_PATH
    # Check for DB file
    if not os.path.exists(db_path):
        if os.path.exists("GharMitra.db"):
             db_path = "GharMitra.db"
        else:
             print("Neither gharmitra.db nor GharMitra.db found.")
             return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"Inspecting 'flats' table in {db_path}...")
        
        # Get columns
        cursor.execute("PRAGMA table_info(flats)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"Column: {col[1]} (Type: {col[2]})")
            
        # Select sample data
        cursor.execute("SELECT * FROM flats")
        rows = cursor.fetchall()
        if not rows:
             print("Table 'flats' is empty.")
        else:
             print(f"Found {len(rows)} flats. First 5:")
             for row in rows[:5]:
                 print(row)
                 
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    inspect_flats()

