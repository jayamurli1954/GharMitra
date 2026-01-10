import sqlite3
import os

DB_PATH = "gharmitra.db"

def check_schema():
    if not os.path.exists(DB_PATH):
        print(f"Database file {DB_PATH} not found.")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        print(f"Inspecting {DB_PATH}...")
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='society_settings'")
        if not cursor.fetchone():
            print("Table 'society_settings' does NOT exist.")
            conn.close()
            return

        # Get columns
        cursor.execute("PRAGMA table_info(society_settings)")
        columns = cursor.fetchall()
        
        print("Columns in society_settings:")
        found_logic = False
        for col in columns:
            cid, name, field_type, notnull, dflt_value, pk = col
            print(f"- {name} ({field_type})")
            if name == 'maintenance_calculation_logic':
                found_logic = True
        
        if found_logic:
            print("\nSUCCESS: maintenance_calculation_logic column FOUND.")
        else:
            print("\nFAILURE: maintenance_calculation_logic column NOT FOUND.")

        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_schema()
