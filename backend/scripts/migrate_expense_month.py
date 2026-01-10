import sqlite3
import datetime

def migrate():
    conn = sqlite3.connect('gharmitra.db')
    cursor = conn.cursor()

    print("Starting migration...")

    # 1. Add expense_month to transactions
    try:
        cursor.execute("ALTER TABLE transactions ADD COLUMN expense_month DATE")
        print("Added expense_month to transactions table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("expense_month already exists in transactions.")
        else:
            raise e

    # 2. Add expense_month to journal_entries
    try:
        cursor.execute("ALTER TABLE journal_entries ADD COLUMN expense_month DATE")
        print("Added expense_month to journal_entries table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("expense_month already exists in journal_entries.")
        else:
            raise e

    # 3. Populate expense_month for transactions
    cursor.execute("SELECT id, date FROM transactions WHERE expense_month IS NULL")
    rows = cursor.fetchall()
    for row_id, date_str in rows:
        # Assuming date_str is YYYY-MM-DD
        dt = datetime.datetime.strptime(date_str, '%Y-%m-%d')
        expense_month = dt.replace(day=1).strftime('%Y-%m-%d')
        cursor.execute("UPDATE transactions SET expense_month = ? WHERE id = ?", (expense_month, row_id))
    
    print(f"Migrated {len(rows)} transactions.")

    # 4. Populate expense_month for journal_entries
    cursor.execute("SELECT id, date FROM journal_entries WHERE expense_month IS NULL")
    rows = cursor.fetchall()
    for row_id, date_str in rows:
        dt = datetime.datetime.strptime(date_str, '%Y-%m-%d')
        expense_month = dt.replace(day=1).strftime('%Y-%m-%d')
        cursor.execute("UPDATE journal_entries SET expense_month = ? WHERE id = ?", (expense_month, row_id))
    
    print(f"Migrated {len(rows)} journal entries.")

    conn.commit()
    conn.close()
    print("Migration completed successfully.")

if __name__ == "__main__":
    migrate()
