"""
Fix expense_month values that are in wrong format (date string instead of month name)
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./gharmitra.db")
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

month_names = ['January', 'February', 'March', 'April', 'May', 'June',
               'July', 'August', 'September', 'October', 'November', 'December']


async def fix_expense_month():
    """Fix expense_month values"""
    async with async_session() as db:
        print("=" * 70)
        print("FIXING EXPENSE_MONTH VALUES")
        print("=" * 70)
        
        # Get all transactions with expense_month that looks like a date string
        result = await db.execute(
            text("""
                SELECT id, account_code, expense_month, date, description
                FROM transactions
                WHERE expense_month IS NOT NULL
                AND expense_month NOT LIKE '%, %'
                ORDER BY date
            """)
        )
        transactions = result.fetchall()
        
        if not transactions:
            print("\nNo transactions with incorrect expense_month format found.")
            return
        
        print(f"\nFound {len(transactions)} transactions with incorrect expense_month format:")
        
        fixed_count = 0
        for txn_id, account_code, expense_month, txn_date, description in transactions:
            # Try to parse expense_month as date
            try:
                # If it's a date string like "2026-01-01", parse it
                if '-' in expense_month and len(expense_month) == 10:
                    parsed_date = datetime.strptime(expense_month, "%Y-%m-%d")
                    # Convert to month name format
                    correct_expense_month = f"{month_names[parsed_date.month - 1]}, {parsed_date.year}"
                    
                    # Update the transaction
                    await db.execute(
                        text("UPDATE transactions SET expense_month = :new_value WHERE id = :id"),
                        {"new_value": correct_expense_month, "id": txn_id}
                    )
                    print(f"  Fixed ID {txn_id} ({account_code}): '{expense_month}' -> '{correct_expense_month}'")
                    fixed_count += 1
                else:
                    print(f"  Skipped ID {txn_id} ({account_code}): '{expense_month}' (unexpected format)")
            except Exception as e:
                print(f"  Error fixing ID {txn_id}: {e}")
        
        await db.commit()
        
        print(f"\n[SUCCESS] Fixed {fixed_count} transactions")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(fix_expense_month())
