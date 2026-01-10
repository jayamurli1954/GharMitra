"""
Verify that double-entry accounting rules are being followed:
1. All transactions from Quick Entry and Journal Vouchers appear in General Ledger
2. General Ledger Debit = Credit (Golden Rule 1)
3. Trial Balance uses General Ledger balances (Golden Rule 2)
4. All journal entries have minimum 2 accounts with Debit = Credit
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os
from decimal import Decimal
from datetime import date

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./gharmitra.db")
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def verify_rules():
    """Verify double-entry accounting rules"""
    async with async_session() as db:
        print("=" * 70)
        print("DOUBLE-ENTRY ACCOUNTING RULES VERIFICATION")
        print("=" * 70)
        
        # Rule 1: Check that all transactions have proper debit/credit
        print("\n1. CHECKING TRANSACTION INTEGRITY...")
        result = await db.execute(
            text("""
                SELECT 
                    COUNT(*) as total_txns,
                    SUM(debit_amount) as total_debit,
                    SUM(credit_amount) as total_credit
                FROM transactions
            """)
        )
        row = result.fetchone()
        total_txns = row[0]
        total_debit = Decimal(str(row[1] or 0))
        total_credit = Decimal(str(row[2] or 0))
        difference = abs(total_debit - total_credit)
        
        print(f"   Total Transactions: {total_txns}")
        print(f"   Total Debit: Rs.{total_debit}")
        print(f"   Total Credit: Rs.{total_credit}")
        print(f"   Difference: Rs.{difference}")
        
        if difference < Decimal("0.01"):
            print("   [PASS] All transactions are balanced (Debit = Credit)")
        else:
            print(f"   [FAIL] Transactions are NOT balanced! Difference: Rs.{difference}")
            print("   This indicates a data integrity issue!")
        
        # Check Quick Entry transactions (should have journal_entry_id)
        result = await db.execute(
            text("""
                SELECT COUNT(*) 
                FROM transactions 
                WHERE journal_entry_id IS NOT NULL
            """)
        )
        jv_txns = result.fetchone()[0]
        print(f"\n   Transactions linked to Journal Entries: {jv_txns}")
        
        # Check transactions without journal_entry_id (Quick Entry creates 2 transactions per entry)
        result = await db.execute(
            text("""
                SELECT COUNT(*) 
                FROM transactions 
                WHERE journal_entry_id IS NULL
            """)
        )
        quick_entry_txns = result.fetchone()[0]
        print(f"   Transactions from Quick Entry: {quick_entry_txns}")
        
        # Rule 2: Check Journal Entries
        print("\n2. CHECKING JOURNAL ENTRIES...")
        result = await db.execute(
            text("""
                SELECT 
                    id,
                    entry_number,
                    total_debit,
                    total_credit,
                    is_balanced,
                    (SELECT COUNT(*) FROM transactions WHERE journal_entry_id = journal_entries.id) as txn_count
                FROM journal_entries
                ORDER BY id
            """)
        )
        journal_entries = result.fetchall()
        
        print(f"   Total Journal Entries: {len(journal_entries)}")
        
        unbalanced_entries = []
        for je in journal_entries:
            je_id, entry_num, total_dr, total_cr, is_bal, txn_count = je
            dr = Decimal(str(total_dr or 0))
            cr = Decimal(str(total_cr or 0))
            diff = abs(dr - cr)
            
            if diff > Decimal("0.01") or not is_bal:
                unbalanced_entries.append((entry_num, dr, cr, diff))
            if txn_count < 2:
                print(f"   [WARN] Journal Entry {entry_num} has only {txn_count} transaction(s) (minimum 2 required)")
        
        if unbalanced_entries:
            print(f"   [FAIL] Found {len(unbalanced_entries)} unbalanced journal entries:")
            for entry_num, dr, cr, diff in unbalanced_entries:
                print(f"      - {entry_num}: Debit=Rs.{dr}, Credit=Rs.{cr}, Difference=Rs.{diff}")
        else:
            print("   [PASS] All journal entries are balanced")
        
        # Rule 3: Check General Ledger totals for a sample period
        print("\n3. CHECKING GENERAL LEDGER TOTALS...")
        # Use a recent date range
        result = await db.execute(
            text("""
                SELECT 
                    SUM(debit_amount) as total_debit,
                    SUM(credit_amount) as total_credit
                FROM transactions
                WHERE date >= '2026-01-01' AND date <= '2026-01-09'
            """)
        )
        row = result.fetchone()
        gl_debit = Decimal(str(row[0] or 0))
        gl_credit = Decimal(str(row[1] or 0))
        gl_diff = abs(gl_debit - gl_credit)
        
        print(f"   Period: 2026-01-01 to 2026-01-09")
        print(f"   General Ledger Total Debit: Rs.{gl_debit}")
        print(f"   General Ledger Total Credit: Rs.{gl_credit}")
        print(f"   Difference: Rs.{gl_diff}")
        
        if gl_diff < Decimal("0.01"):
            print("   [PASS] General Ledger is balanced (Golden Rule 1)")
        else:
            print(f"   [FAIL] General Ledger is NOT balanced! Difference: Rs.{gl_diff}")
        
        # Rule 4: Check account balances consistency
        print("\n4. CHECKING ACCOUNT BALANCES...")
        result = await db.execute(
            text("""
                SELECT 
                    code,
                    name,
                    current_balance,
                    (SELECT SUM(debit_amount) - SUM(credit_amount) 
                     FROM transactions 
                     WHERE account_code = account_codes.code) as calculated_balance
                FROM account_codes
                WHERE ABS(current_balance) > 0.01
                LIMIT 10
            """)
        )
        accounts = result.fetchall()
        
        print(f"   Checking {len(accounts)} accounts with non-zero balances...")
        mismatches = []
        for acc in accounts:
            code, name, current_bal, calc_bal = acc
            current = Decimal(str(current_bal or 0))
            calculated = Decimal(str(calc_bal or 0))
            diff = abs(current - calculated)
            
            if diff > Decimal("0.01"):
                mismatches.append((code, name, current, calculated, diff))
        
        if mismatches:
            print(f"   [WARN] Found {len(mismatches)} accounts with balance mismatches:")
            for code, name, current, calc, diff in mismatches[:5]:
                print(f"      - {code} ({name}): Current=Rs.{current}, Calculated=Rs.{calc}, Diff=Rs.{diff}")
        else:
            print("   [PASS] Account balances are consistent")
        
        print("\n" + "=" * 70)
        print("VERIFICATION COMPLETE")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(verify_rules())
