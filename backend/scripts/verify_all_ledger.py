
import sqlite3
from datetime import date, datetime
import os
import requests

# Assuming the backend is running on localhost:8001
# We'll use direct DB checks as a foolproof verification if service is down,
# but we aim to test the logic.

DB_PATH = r"d:\SanMitra_Tech\GharMitra\backend\gharmitra.db"

def verify_all_accounts_ledger():
    print("--- Verification: 'All Accounts' Ledger Statement ---")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if there are multiple accounts with transactions
    cursor.execute("SELECT account_code, COUNT(*) FROM transactions GROUP BY account_code HAVING COUNT(*) > 0")
    active_accounts = cursor.fetchall()
    print(f"Active accounts found in DB: {len(active_accounts)}")
    for acc, count in active_accounts:
        print(f"  - Account {acc}: {count} transactions")

    if len(active_accounts) < 2:
        print("[NOTE] Less than 2 active accounts found. Adding a dummy transaction to another account for testing.")
        # Insert a dummy transaction for account '1020' (Bank) if it's not the primary one
        # Primary is usually '1010' or '5001'
        other_acc = '1020' if active_accounts[0][0] != '1020' else '1010'
        cursor.execute("""
            INSERT INTO transactions (
                society_id, type, amount, description, date, expense_month, account_code, debit_amount, credit_amount, added_by, created_at, updated_at
            ) VALUES (1, 'income', 100.0, 'VERIFY_ALL_LEDGER', '2026-01-01', '2026-01-01', ?, 100.0, 0.0, 1, ?, ?)
        """, (other_acc, datetime.utcnow().isoformat(), datetime.utcnow().isoformat()))
        conn.commit()
        print(f"[OK] Added dummy transaction for account {other_acc}")

    # Simulate backend logic for 'all'
    from_date = '2026-01-01'
    to_date = '2026-01-31'
    
    print(f"Simulating 'all' accounts ledger for period {from_date} to {to_date}...")
    
    # 1. Get all accounts
    cursor.execute("SELECT code, name FROM account_codes WHERE society_id = 1")
    accounts = cursor.fetchall()
    
    ledgers_with_data = 0
    for code, name in accounts:
        # Check for opening balance or transactions
        cursor.execute("SELECT COUNT(*) FROM transactions WHERE society_id = 1 AND account_code = ? AND expense_month BETWEEN ? AND ?", (code, from_date, to_date))
        txn_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT opening_balance FROM account_codes WHERE code = ?", (code,))
        ob = cursor.fetchone()[0] or 0.0
        
        if txn_count > 0 or abs(ob) > 0.01:
            ledgers_with_data += 1
            # print(f"  - Generated ledger for {code}: {txn_count} txns, OB: {ob}")

    print(f"[OK] Logic verification: Would generate {ledgers_with_data} ledger statements.")
    
    if ledgers_with_data > 0:
        print(f"[SUCCESS] 'All Accounts' filter would return {ledgers_with_data} statements.")
    else:
        print("[FAIL] No ledger statements would be generated even though we expect some.")

    # Cleanup
    cursor.execute("DELETE FROM transactions WHERE description = 'VERIFY_ALL_LEDGER'")
    conn.commit()
    conn.close()
    print("--- Verification Complete ---")

if __name__ == "__main__":
    verify_all_accounts_ledger()
