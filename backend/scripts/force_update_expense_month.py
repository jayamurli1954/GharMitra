"""Force update expense_month to 'December, 2025' for all transactions in specified account codes"""
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

# Account codes to update
ACCOUNT_CODES = ["5000", "5010", "5100", "5110", "5130", "5240"]
EXPENSE_MONTH = "December, 2025"


async def force_update_expense_month():
    """Force set expense_month to 'December, 2025' for ALL transactions in specified account codes"""
    async with async_session() as db:
        print("=" * 70)
        print("FORCE UPDATING EXPENSE_MONTH TO 'December, 2025'")
        print("=" * 70)
        print(f"\nTarget expense_month: {EXPENSE_MONTH}")
        print(f"Account codes: {', '.join(ACCOUNT_CODES)}")
        print()
        
        total_updated = 0
        
        for account_code in ACCOUNT_CODES:
            # Get all transactions for this account code
            result = await db.execute(
                text("""
                    SELECT id, account_code, description, amount, date, expense_month
                    FROM transactions
                    WHERE account_code = :account_code
                """),
                {"account_code": account_code}
            )
            transactions = result.fetchall()
            
            if not transactions:
                print(f"Account {account_code}: No transactions found")
                continue
            
            print(f"\nAccount {account_code}: Found {len(transactions)} transaction(s)")
            
            for txn_id, acct_code, desc, amt, txn_date, exp_month in transactions:
                current_value = exp_month or "NULL"
                print(f"  - ID {txn_id}: {desc[:50]}")
                print(f"    Current expense_month: {current_value}")
                
                # Force update to December, 2025
                await db.execute(
                    text("""
                        UPDATE transactions
                        SET expense_month = :expense_month
                        WHERE id = :txn_id
                    """),
                    {"expense_month": EXPENSE_MONTH, "txn_id": txn_id}
                )
                total_updated += 1
                print(f"    Updated to: {EXPENSE_MONTH}")
            
            await db.commit()
        
        print("\n" + "=" * 70)
        print(f"SUMMARY: Updated {total_updated} transaction(s) to '{EXPENSE_MONTH}'")
        print("=" * 70)
        
        # Verify the updates
        print("\nVerification:")
        for account_code in ACCOUNT_CODES:
            result = await db.execute(
                text("""
                    SELECT COUNT(*) as count
                    FROM transactions
                    WHERE account_code = :account_code
                    AND expense_month = :expense_month
                """),
                {"account_code": account_code, "expense_month": EXPENSE_MONTH}
            )
            count = result.fetchone()[0]
            print(f"  Account {account_code}: {count} transaction(s) with expense_month = '{EXPENSE_MONTH}'")


if __name__ == "__main__":
    asyncio.run(force_update_expense_month())
