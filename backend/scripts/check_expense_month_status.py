"""Check expense_month status for specific account codes"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./gharmitra.db")
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Account codes to check
ACCOUNT_CODES = ["5000", "5010", "5100", "5110", "5130", "5240"]


async def check_expense_month():
    """Check expense_month status for specified account codes"""
    async with async_session() as db:
        print("=" * 70)
        print("CHECKING EXPENSE_MONTH STATUS FOR TRANSACTIONS")
        print("=" * 70)
        print()
        
        for account_code in ACCOUNT_CODES:
            # Get all transactions for this account code
            result = await db.execute(
                text("""
                    SELECT id, account_code, description, amount, date, expense_month
                    FROM transactions
                    WHERE account_code = :account_code
                    ORDER BY date DESC
                """),
                {"account_code": account_code}
            )
            transactions = result.fetchall()
            
            if not transactions:
                print(f"Account {account_code}: No transactions found")
                continue
            
            print(f"\nAccount {account_code}: {len(transactions)} transaction(s) found")
            for txn_id, acct_code, desc, amt, txn_date, exp_month in transactions:
                status = "SET" if exp_month == "December, 2025" else f"NOT SET: {exp_month or 'NULL'}"
                print(f"  - ID {txn_id}: {desc[:50]}")
                print(f"    Amount: Rs.{amt} | Date: {txn_date} | Expense Month: {status}")


if __name__ == "__main__":
    asyncio.run(check_expense_month())
