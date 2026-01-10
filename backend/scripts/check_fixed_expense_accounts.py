"""
Check which accounts are marked as fixed expenses
"""
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


async def check_fixed_expenses():
    """Check which expense accounts are marked as fixed expenses"""
    async with async_session() as db:
        print("=" * 70)
        print("FIXED EXPENSE ACCOUNTS CHECK")
        print("=" * 70)
        
        # Get all expense accounts
        result = await db.execute(
            text("""
                SELECT code, name, is_fixed_expense, current_balance
                FROM account_codes
                WHERE type = 'expense'
                ORDER BY code
            """)
        )
        accounts = result.fetchall()
        
        print("\nExpense Accounts:")
        print("-" * 70)
        print(f"{'Code':<10} {'Name':<40} {'Fixed?':<10} {'Balance':<15}")
        print("-" * 70)
        
        for code, name, is_fixed, balance in accounts:
            fixed_status = "YES" if is_fixed else "NO"
            print(f"{code:<10} {name[:40]:<40} {fixed_status:<10} Rs.{balance or 0}")
        
        # Check specific accounts mentioned by user
        print("\n" + "=" * 70)
        print("SPECIFIC ACCOUNTS CHECK")
        print("=" * 70)
        
        target_accounts = ['5000', '5010', '5100', '5110', '5120', '5130', '5240']
        for code in target_accounts:
            result = await db.execute(
                text("SELECT code, name, is_fixed_expense FROM account_codes WHERE code = :code"),
                {"code": code}
            )
            row = result.fetchone()
            if row:
                code_val, name, is_fixed = row
                status = "MARKED" if is_fixed else "NOT MARKED"
                print(f"{code}: {name} - {status} as fixed expense")
            else:
                print(f"{code}: NOT FOUND")


if __name__ == "__main__":
    asyncio.run(check_fixed_expenses())
