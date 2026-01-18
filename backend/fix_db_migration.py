import sqlite3
import os

db_path = "gharmitra.db"

def fix_database():
    if not os.path.exists(db_path):
        print(f"Error: Database file {db_path} not found.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if is_reversed exists in transactions
        cursor.execute("PRAGMA table_info(transactions)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if "is_reversed" not in columns:
            print("Adding 'is_reversed' column to 'transactions' table...")
            cursor.execute("ALTER TABLE transactions ADD COLUMN is_reversed BOOLEAN DEFAULT 0")
            cursor.execute("CREATE INDEX ix_transactions_is_reversed ON transactions (is_reversed)")
            print("Successfully added 'is_reversed' to 'transactions'.")
        else:
            print("'is_reversed' already exists in 'transactions'.")

        # Check if is_reversed exists in journal_entries
        cursor.execute("PRAGMA table_info(journal_entries)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if "is_reversed" not in columns:
            print("Adding 'is_reversed' column to 'journal_entries' table...")
            cursor.execute("ALTER TABLE journal_entries ADD COLUMN is_reversed BOOLEAN DEFAULT 0")
            cursor.execute("CREATE INDEX ix_journal_entries_is_reversed ON journal_entries (is_reversed)")
            print("Successfully added 'is_reversed' to 'journal_entries'.")
        else:
            print("'is_reversed' already exists in 'journal_entries'.")
            
        # Check for reversal_entry_id and original_entry_id in journal_entries
        if "reversal_entry_id" not in columns:
            print("Adding 'reversal_entry_id' column to 'journal_entries' table...")
            cursor.execute("ALTER TABLE journal_entries ADD COLUMN reversal_entry_id INTEGER REFERENCES journal_entries(id)")
            print("Successfully added 'reversal_entry_id' to 'journal_entries'.")
            
        if "original_entry_id" not in columns:
            print("Adding 'original_entry_id' column to 'journal_entries' table...")
            cursor.execute("ALTER TABLE journal_entries ADD COLUMN original_entry_id INTEGER REFERENCES journal_entries(id)")
            print("Successfully added 'original_entry_id' to 'journal_entries'.")

        conn.commit()
        print("Database migration complete.")

    except Exception as e:
        print(f"An error occurred: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_database()
