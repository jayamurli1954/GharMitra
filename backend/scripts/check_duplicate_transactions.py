"""Check for duplicate transactions in account 4000 and 4010"""
import asyncio
import sys
from pathlib import Path
from decimal import Decimal

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./gharmitra.db")
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def check_duplicates():
    """Check for duplicate transactions in maintenance and water charges"""
    async with async_session() as db:
        print("=" * 70)
        print("CHECKING DUPLICATE TRANSACTIONS FOR ACCOUNTS 4000 AND 4010")
        print("=" * 70)
        print()
        
        # Check account 4000 (Maintenance Charges)
        result = await db.execute(
            text("""
                SELECT 
                    account_code,
                    COUNT(*) as transaction_count,
                    SUM(debit_amount) as total_debit,
                    SUM(credit_amount) as total_credit,
                    MIN(date) as first_date,
                    MAX(date) as last_date
                FROM transactions
                WHERE account_code = '4000'
                GROUP BY account_code
            """)
        )
        maint_data = result.fetchone()
        
        if maint_data:
            print(f"Account 4000 (Maintenance Charges):")
            print(f"  Total Transactions: {maint_data[1]}")
            print(f"  Total Debit: Rs.{maint_data[2] or 0:,.2f}")
            print(f"  Total Credit: Rs.{maint_data[3] or 0:,.2f}")
            print(f"  Date Range: {maint_data[4]} to {maint_data[5]}")
            print()
        
        # Check account 4010 (Water Charges)
        result = await db.execute(
            text("""
                SELECT 
                    account_code,
                    COUNT(*) as transaction_count,
                    SUM(debit_amount) as total_debit,
                    SUM(credit_amount) as total_credit,
                    MIN(date) as last_date,
                    MAX(date) as last_date
                FROM transactions
                WHERE account_code = '4010'
                GROUP BY account_code
            """)
        )
        water_data = result.fetchone()
        
        if water_data:
            print(f"Account 4010 (Water Charges):")
            print(f"  Total Transactions: {water_data[1]}")
            print(f"  Total Debit: Rs.{water_data[2] or 0:,.2f}")
            print(f"  Total Credit: Rs.{water_data[3] or 0:,.2f}")
            print(f"  Date Range: {water_data[4]} to {water_data[5]}")
            print()
        
        # Check for December 2025 transactions specifically
        result = await db.execute(
            text("""
                SELECT 
                    account_code,
                    COUNT(*) as count,
                    SUM(debit_amount) as total_debit,
                    SUM(credit_amount) as total_credit
                FROM transactions
                WHERE account_code IN ('4000', '4010')
                AND (expense_month = 'December, 2025' OR (date >= '2025-12-01' AND date <= '2025-12-31'))
                GROUP BY account_code
            """)
        )
        dec_data = result.fetchall()
        
        print("December 2025 Transactions:")
        for row in dec_data:
            print(f"  Account {row[0]}: {row[1]} transactions, Debit: Rs.{row[2] or 0:,.2f}, Credit: Rs.{row[3] or 0:,.2f}")
        print()
        
        # Check for duplicate journal entries
        result = await db.execute(
            text("""
                SELECT 
                    je.entry_number,
                    COUNT(*) as entry_count,
                    SUM(CASE WHEN t.account_code = '4000' THEN t.debit_amount ELSE 0 END) as maint_debit,
                    SUM(CASE WHEN t.account_code = '4010' THEN t.debit_amount ELSE 0 END) as water_debit
                FROM journal_entries je
                JOIN transactions t ON t.journal_entry_id = je.id
                WHERE t.account_code IN ('4000', '4010')
                AND (t.expense_month = 'December, 2025' OR (t.date >= '2025-12-01' AND t.date <= '2025-12-31'))
                GROUP BY je.entry_number
                HAVING COUNT(*) > 2
            """)
        )
        duplicates = result.fetchall()
        
        if duplicates:
            print("Potential Duplicate Journal Entries:")
            for row in duplicates:
                print(f"  Entry {row[0]}: {row[1]} transactions, Maint: Rs.{row[2] or 0:,.2f}, Water: Rs.{row[3] or 0:,.2f}")
        else:
            print("No obvious duplicate journal entries found.")
        print()


if __name__ == "__main__":
    asyncio.run(check_duplicates())
