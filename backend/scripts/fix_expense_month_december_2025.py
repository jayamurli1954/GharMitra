"""Fix expense_month for specific transactions to 'December, 2025' if not already set"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text, select, and_, or_
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os
from datetime import date

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./gharmitra.db")
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Account codes to update
ACCOUNT_CODES = ["5000", "5010", "5100", "5110", "5130", "5240"]
EXPENSE_MONTH = "December, 2025"


async def fix_expense_month():
    """Set expense_month to 'December, 2025' for specified account codes if not already set"""
    async with async_session() as db:
        print("=" * 70)
        print("FIXING EXPENSE_MONTH FOR DECEMBER 2025 TRANSACTIONS")
        print("=" * 70)
        print(f"\nTarget expense_month: {EXPENSE_MONTH}")
        print(f"Account codes: {', '.join(ACCOUNT_CODES)}")
        print()
        
        total_updated = 0
        
        for account_code in ACCOUNT_CODES:
            # Find transactions for this account code where expense_month is NULL or empty
            result = await db.execute(
                text("""
                    SELECT id, account_code, description, amount, date, expense_month
                    FROM transactions
                    WHERE account_code = :account_code
                    AND (expense_month IS NULL OR expense_month = '' OR expense_month != :expense_month)
                """),
                {"account_code": account_code, "expense_month": EXPENSE_MONTH}
            )
            transactions = result.fetchall()
            
            if not transactions:
                print(f"Account {account_code}: No transactions found or all already have expense_month = '{EXPENSE_MONTH}'")
                continue
            
            print(f"\nAccount {account_code}: Found {len(transactions)} transaction(s) to update")
            
            for txn_id, acct_code, desc, amt, txn_date, exp_month in transactions:
                print(f"  - ID {txn_id}: {desc} | Amount: ₹{amt} | Date: {txn_date} | Current expense_month: {exp_month or 'NULL'}")
                
                # Update the transaction
                await db.execute(
                    text("""
                        UPDATE transactions
                        SET expense_month = :expense_month
                        WHERE id = :txn_id
                    """),
                    {"expense_month": EXPENSE_MONTH, "txn_id": txn_id}
                )
                total_updated += 1
            
            await db.commit()
        
        print("\n" + "=" * 70)
        print(f"SUMMARY: Updated {total_updated} transaction(s)")
        print("=" * 70)
        
        # Verify the updates
        print("\nVerification - Checking updated transactions:")
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
    asyncio.run(fix_expense_month())
