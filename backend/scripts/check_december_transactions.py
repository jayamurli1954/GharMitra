"""
Check transactions for December 2025
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
    """Check transactions for December 2025"""
    async with async_session() as db:
        print("=" * 70)
        print("CHECKING DECEMBER 2025 TRANSACTIONS")
        print("=" * 70)
        
        # Check fixed expense accounts
        fixed_codes = ['5000', '5010', '5100', '5130', '5240']
        
        expense_month_str = "December, 2025"
        start_date = date(2025, 12, 1)
        end_date = date(2025, 12, 31)
        
        print(f"\nLooking for transactions with:")
        print(f"  expense_month = '{expense_month_str}'")
        print(f"  OR (expense_month IS NULL AND date BETWEEN {start_date} AND {end_date})")
        print()
        
        for code in fixed_codes:
            print(f"\nAccount {code}:")
            
            # Check by expense_month
            result = await db.execute(
                text("""
                    SELECT COUNT(*), SUM(amount), SUM(debit_amount), SUM(credit_amount)
                    FROM transactions
                    WHERE account_code = :code
                    AND expense_month = :expense_month
                """),
                {"code": code, "expense_month": expense_month_str}
            )
            row1 = result.fetchone()
            count1, total1, debit1, credit1 = row1
            
            # Check by date range (if expense_month is NULL)
            result = await db.execute(
                text("""
                    SELECT COUNT(*), SUM(amount), SUM(debit_amount), SUM(credit_amount)
                    FROM transactions
                    WHERE account_code = :code
                    AND expense_month IS NULL
                    AND date >= :start_date
                    AND date <= :end_date
                """),
                {"code": code, "start_date": start_date, "end_date": end_date}
            )
            row2 = result.fetchone()
            count2, total2, debit2, credit2 = row2
            
            # Get all transactions for this account
            result = await db.execute(
                text("""
                    SELECT expense_month, date, amount, debit_amount, credit_amount, description
                    FROM transactions
                    WHERE account_code = :code
                    ORDER BY date
                """),
                {"code": code}
            )
            all_txns = result.fetchall()
            
            print(f"  By expense_month='{expense_month_str}': {count1} txns, Total=Rs.{total1 or 0}")
            print(f"  By date range (NULL expense_month): {count2} txns, Total=Rs.{total2 or 0}")
            print(f"  All transactions for this account:")
            for txn in all_txns:
                exp_month, txn_date, amt, dr, cr, desc = txn
                print(f"    - expense_month={exp_month}, date={txn_date}, amount=Rs.{amt}, debit=Rs.{dr}, credit=Rs.{cr}")
                print(f"      Description: {desc[:60]}")


if __name__ == "__main__":
    asyncio.run(check_transactions())
