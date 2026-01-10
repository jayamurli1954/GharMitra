"""Check which account codes are used for Cash and Bank"""
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


async def check_accounts():
    """Check Cash and Bank account codes and their balances"""
    async with async_session() as db:
        print("=" * 70)
        print("CASH AND BANK ACCOUNT CODES")
        print("=" * 70)
        print()
        
        # Find all account codes that might be Cash or Bank
        result = await db.execute(
            text("""
                SELECT code, name, current_balance, type
                FROM account_codes
                WHERE (name LIKE '%Cash%' OR name LIKE '%Bank%' OR name LIKE '%bank%' OR code LIKE '1%')
                ORDER BY code
            """)
        )
        accounts = result.fetchall()
        
        if not accounts:
            print("No Cash/Bank accounts found")
            return
        
        print("All Cash and Bank related accounts:")
        total_balance = 0
        for code, name, balance, acct_type in accounts:
            print(f"  Code: {code} | Name: {name} | Balance: Rs.{balance} | Type: {acct_type}")
            if code in ["1200", "1210", "1000", "1010", "1001", "1002"]:
                total_balance += float(balance or 0)
        
        print()
        print("=" * 70)
        print(f"TOTAL BALANCE (from codes 1200, 1210, 1000, 1010, 1001, 1002): Rs.{total_balance}")
        print("=" * 70)
        
        # Check what the dashboard is currently using
        result = await db.execute(
            text("""
                SELECT code, name, current_balance
                FROM account_codes
                WHERE code IN ('1200', '1210')
            """)
        )
        dashboard_accounts = result.fetchall()
        
        print()
        print("Accounts currently used by dashboard (1200, 1210):")
        if dashboard_accounts:
            for code, name, balance in dashboard_accounts:
                print(f"  Code: {code} | Name: {name} | Balance: Rs.{balance}")
        else:
            print("  No accounts found with codes 1200 or 1210")
            print("  Dashboard may be showing Rs.0")


if __name__ == "__main__":
    asyncio.run(check_accounts())
