
import sqlite3
from datetime import date, datetime
import os

DB_PATH = r"d:\SanMitra_Tech\GharMitra\backend\gharmitra.db"

def verify_month_tagging():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("--- Verification of CR-022: Month-Tagged Expenses ---")
    
    # 1. Check schema
    cursor.execute("PRAGMA table_info(transactions)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'expense_month' in columns:
        print("[OK] 'expense_month' column exists in 'transactions' table.")
    else:
        print("[FAIL] 'expense_month' column MISSING in 'transactions' table.")
        return

    cursor.execute("PRAGMA table_info(journal_entries)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'expense_month' in columns:
        print("[OK] 'expense_month' column exists in 'journal_entries' table.")
    else:
        print("[FAIL] 'expense_month' column MISSING in 'journal_entries' table.")
        return

    # 2. Insert test data
    # Scenario: Security expense for Dec 2025, paid on 05-Jan-2026
    test_desc = "TEST_SECURITY_EXPENSE_CR022"
    txn_date = "2026-01-05"
    exp_month = "2025-12-01"
    amount = 5000.0
    society_id = 1
    
    # Delete previous test data
    cursor.execute("DELETE FROM transactions WHERE description = ?", (test_desc,))
    
    # Insert expense leg
    cursor.execute("""
        INSERT INTO transactions (
            society_id, type, category, amount, description, date, expense_month, account_code, debit_amount, credit_amount, added_by, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (society_id, 'expense', 'Security', amount, test_desc, txn_date, exp_month, '5001', amount, 0.0, 1, datetime.utcnow().isoformat(), datetime.utcnow().isoformat()))
    
    # Insert cash leg
    cursor.execute("""
        INSERT INTO transactions (
            society_id, type, category, amount, description, date, expense_month, account_code, debit_amount, credit_amount, added_by, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (society_id, 'expense', 'Security', amount, f"{test_desc} (Cash Payment)", txn_date, exp_month, '1010', 0.0, amount, 1, datetime.utcnow().isoformat(), datetime.utcnow().isoformat()))
    
    conn.commit()
    print(f"[OK] Inserted test transaction: Date={txn_date}, ExpenseMonth={exp_month}")

    # 3. Simulate Report Logic
    # P&L for Dec should include this
    cursor.execute("""
        SELECT SUM(amount) FROM transactions 
        WHERE expense_month BETWEEN '2025-12-01' AND '2025-12-31' 
        AND description = ? AND account_code = '5001'
    """, (test_desc,))
    pnl_sum = cursor.fetchone()[0]
    if pnl_sum == amount:
        print(f"[OK] P&L for Dec correctly INCLUDES the expense (Amount: {pnl_sum})")
    else:
        print(f"[FAIL] P&L for Dec MISSING the expense. Found: {pnl_sum}")

    # P&L for Jan should NOT include this
    cursor.execute("""
        SELECT SUM(amount) FROM transactions 
        WHERE expense_month BETWEEN '2026-01-01' AND '2026-01-31' 
        AND description = ? AND account_code = '5001'
    """, (test_desc,))
    pnl_sum_jan = cursor.fetchone()[0]
    if not pnl_sum_jan:
        print("[OK] P&L for Jan correctly EXCLUDES the expense.")
    else:
        print(f"[FAIL] P&L for Jan INCORRECTLY includes the expense. Amount: {pnl_sum_jan}")

    # Cash Book for Jan should include this
    cursor.execute("""
        SELECT SUM(credit_amount) FROM transactions 
        WHERE date BETWEEN '2026-01-01' AND '2026-01-31' 
        AND description LIKE ? AND account_code = '1010'
    """, (f"%{test_desc}%",))
    cash_sum = cursor.fetchone()[0]
    if cash_sum == amount:
        print(f"[OK] Cash Book for Jan correctly INCLUDES the payment (Amount: {cash_sum})")
    else:
        print(f"[FAIL] Cash Book for Jan MISSING the payment. Found: {cash_sum}")

    # Cleanup
    cursor.execute("DELETE FROM transactions WHERE description LIKE ?", (f"%{test_desc}%",))
    conn.commit()
    conn.close()
    print("--- Verification Complete ---")

if __name__ == "__main__":
    verify_month_tagging()
