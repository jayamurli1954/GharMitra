"""
Fix expense_month for transactions that should be December 2025 based on descriptions
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


async def fix_december_expense_month():
    """Fix expense_month for December 2025 transactions"""
    async with async_session() as db:
        print("=" * 70)
        print("FIXING DECEMBER 2025 EXPENSE_MONTH VALUES")
        print("=" * 70)
        
        # Accounts that should be December 2025 based on descriptions
        target_accounts = ['5010', '5100', '5130']
        december_2025 = "December, 2025"
        
        print(f"\nLooking for transactions that should be {december_2025}:")
        
        for account_code in target_accounts:
            # Get transactions for this account
            result = await db.execute(
                text("""
                    SELECT id, expense_month, date, description
                    FROM transactions
                    WHERE account_code = :code
                    ORDER BY date
                """),
                {"code": account_code}
            )
            transactions = result.fetchall()
            
            for txn_id, expense_month, txn_date, description in transactions:
                # Check if description mentions December or Dec
                desc_lower = (description or "").lower()
                if ('dec' in desc_lower or 'december' in desc_lower) and expense_month != december_2025:
                    print(f"\n  Account {account_code}, Transaction ID {txn_id}:")
                    print(f"    Current expense_month: {expense_month}")
                    print(f"    Date: {txn_date}")
                    print(f"    Description: {description[:60]}")
                    print(f"    -> Should be: {december_2025}")
                    
                    # Update to December 2025
                    await db.execute(
                        text("UPDATE transactions SET expense_month = :new_value WHERE id = :id"),
                        {"new_value": december_2025, "id": txn_id}
                    )
                    print(f"    [FIXED] Updated expense_month to '{december_2025}'")
        
        await db.commit()
        
        print("\n" + "=" * 70)
        print("FIX COMPLETE")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(fix_december_expense_month())
