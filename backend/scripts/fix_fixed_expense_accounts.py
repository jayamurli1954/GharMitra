"""
Fix fixed expense accounts - mark correct accounts as fixed expenses
Exclude water charges (5110, 5120) as they are handled separately
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


async def fix_fixed_expenses():
    """Mark correct accounts as fixed expenses"""
    async with async_session() as db:
        print("=" * 70)
        print("FIXING FIXED EXPENSE ACCOUNTS")
        print("=" * 70)
        
        # Accounts that SHOULD be marked as fixed expenses
        fixed_expense_codes = ['5000', '5010', '5100', '5130', '5240']
        
        # Accounts that should NOT be marked (water charges)
        exclude_codes = ['5110', '5120']
        
        # First, unmark all expense accounts
        print("\n1. Unmarking all expense accounts...")
        await db.execute(
            text("UPDATE account_codes SET is_fixed_expense = 0 WHERE type = 'expense'")
        )
        await db.commit()
        print("   Done")
        
        # Mark the correct accounts as fixed expenses
        print("\n2. Marking correct accounts as fixed expenses...")
        for code in fixed_expense_codes:
            result = await db.execute(
                text("SELECT code, name FROM account_codes WHERE code = :code"),
                {"code": code}
            )
            row = result.fetchone()
            if row:
                code_val, name = row
                await db.execute(
                    text("UPDATE account_codes SET is_fixed_expense = 1 WHERE code = :code"),
                    {"code": code}
                )
                print(f"   [OK] Marked {code} - {name} as fixed expense")
            else:
                print(f"   [ERROR] Account {code} not found")
        
        await db.commit()
        
        # Verify water charges are NOT marked
        print("\n3. Verifying water charges are NOT marked...")
        for code in exclude_codes:
            result = await db.execute(
                text("SELECT code, name, is_fixed_expense FROM account_codes WHERE code = :code"),
                {"code": code}
            )
            row = result.fetchone()
            if row:
                code_val, name, is_fixed = row
                if is_fixed:
                    await db.execute(
                        text("UPDATE account_codes SET is_fixed_expense = 0 WHERE code = :code"),
                        {"code": code}
                    )
                    print(f"   [OK] Unmarked {code} - {name} (water charge, not fixed expense)")
                else:
                    print(f"   [OK] {code} - {name} is correctly NOT marked")
        
        await db.commit()
        
        # Final verification
        print("\n4. Final verification...")
        result = await db.execute(
            text("""
                SELECT code, name, is_fixed_expense
                FROM account_codes
                WHERE type = 'expense' AND code IN ('5000', '5010', '5100', '5110', '5120', '5130', '5240')
                ORDER BY code
            """)
        )
        accounts = result.fetchall()
        
        print("\n   Fixed Expense Status:")
        for code, name, is_fixed in accounts:
            status = "YES" if is_fixed else "NO"
            expected = "YES" if code in fixed_expense_codes else "NO"
            match = "[OK]" if (is_fixed and code in fixed_expense_codes) or (not is_fixed and code not in fixed_expense_codes) else "[ERROR]"
            print(f"   {match} {code} - {name}: {status} (Expected: {expected})")
        
        print("\n" + "=" * 70)
        print("FIX COMPLETE")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(fix_fixed_expenses())
