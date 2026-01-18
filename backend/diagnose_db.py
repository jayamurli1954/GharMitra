import sqlite3
import os

db_path = "gharmitra.db"

def check_columns():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(transactions)")
    columns = [column[1] for column in cursor.fetchall()]
    print(f"Columns in transactions: {columns}")
    
    if "is_reversed" in columns:
        print("SUCCESS: 'is_reversed' exists in transactions.")
    else:
        print("FAILURE: 'is_reversed' NOT found in transactions.")

    cursor.execute("PRAGMA table_info(journal_entries)")
    columns = [column[1] for column in cursor.fetchall()]
    print(f"Columns in journal_entries: {columns}")
    conn.close()

if __name__ == "__main__":
    check_columns()
