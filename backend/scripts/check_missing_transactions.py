"""
Diagnostic script to check why transactions are missing from ledger
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os
from datetime import date

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./gharmitra.db")
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def check_transactions():
    """Check transactions for missing accounts"""
    async with async_session() as db:
        print("=" * 60)
        print("TRANSACTION DIAGNOSTIC REPORT")
        print("=" * 60)
        
        # Check for transactions with account codes 5000, 5110, 5240
        account_codes_to_check = ['5000', '5110', '5240']
        
        for account_code in account_codes_to_check:
            print(f"\n{'='*60}")
            print(f"Account Code: {account_code}")
            print(f"{'='*60}")
            
            # Get account name
            result = await db.execute(
                text("SELECT name, type FROM account_codes WHERE code = :code"),
                {"code": account_code}
            )
            account_row = result.fetchone()
            if account_row:
                print(f"Account Name: {account_row[0]}")
                print(f"Account Type: {account_row[1]}")
            else:
                print(f"⚠️  Account code {account_code} NOT FOUND in account_codes table!")
                continue
            
            # Get all transactions for this account
            result = await db.execute(
                text("""
                    SELECT id, date, expense_month, description, amount, 
                           debit_amount, credit_amount, payment_method, document_number
                    FROM transactions 
                    WHERE account_code = :code
                    ORDER BY date
                """),
                {"code": account_code}
            )
            transactions = result.fetchall()
            
            print(f"\nTotal transactions found: {len(transactions)}")
            
            if transactions:
                print("\nTransaction Details:")
                for txn in transactions:
                    print(f"  - ID {txn[0]}: Date={txn[1]}, Expense Month={txn[2]}, Amount=Rs.{txn[4]}")
                    print(f"    Debit=Rs.{txn[5]}, Credit=Rs.{txn[6]}, Payment={txn[7]}, Doc={txn[8]}")
                    print(f"    Description: {txn[3]}")
            else:
                print(f"  ⚠️  NO TRANSACTIONS FOUND for account {account_code}!")
            
            # Check current balance
            result = await db.execute(
                text("SELECT current_balance FROM account_codes WHERE code = :code"),
                {"code": account_code}
            )
            balance_row = result.fetchone()
            if balance_row:
                print(f"\nCurrent Balance in account_codes table: Rs.{balance_row[0]}")
            
            # Calculate balance from transactions
            result = await db.execute(
                text("""
                    SELECT 
                        SUM(debit_amount) as total_debit,
                        SUM(credit_amount) as total_credit
                    FROM transactions 
                    WHERE account_code = :code
                """),
                {"code": account_code}
            )
            calc_row = result.fetchone()
            if calc_row and (calc_row[0] or calc_row[1]):
                print(f"Calculated from transactions: Debit=Rs.{calc_row[0] or 0}, Credit=Rs.{calc_row[1] or 0}")
                calculated_balance = (calc_row[0] or 0) - (calc_row[1] or 0)
                print(f"Net Balance (Debit - Credit): Rs.{calculated_balance}")
        
        # Check date range for period 2026-01-01 to 2026-01-09
        print(f"\n{'='*60}")
        print("TRANSACTIONS IN DATE RANGE: 2026-01-01 to 2026-01-09")
        print(f"{'='*60}")
        
        for account_code in account_codes_to_check:
            result = await db.execute(
                text("""
                    SELECT COUNT(*) as count
                    FROM transactions 
                    WHERE account_code = :code
                    AND date >= '2026-01-01'
                    AND date <= '2026-01-09'
                """),
                {"code": account_code}
            )
            count_row = result.fetchone()
            count = count_row[0] if count_row else 0
            print(f"Account {account_code}: {count} transactions in date range")


if __name__ == "__main__":
    asyncio.run(check_transactions())
