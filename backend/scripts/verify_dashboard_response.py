"""Verify dashboard response data"""
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


async def verify_data():
    """Verify data for dashboard"""
    async with async_session() as db:
        print("=" * 70)
        print("VERIFYING DASHBOARD DATA")
        print("=" * 70)
        print()
        
        # Check society_id for bills
        result = await db.execute(
            text("""
                SELECT DISTINCT society_id, COUNT(*) as count
                FROM maintenance_bills
                WHERE month = 12 AND year = 2025
                GROUP BY society_id
            """)
        )
        rows = result.fetchall()
        print("December 2025 Bills by society_id:")
        for s_id, count in rows:
            print(f"  society_id {s_id}: {count} bills")
        
        # Check account codes with society_id
        result = await db.execute(
            text("""
                SELECT DISTINCT society_id, COUNT(*) as count
                FROM account_codes
                WHERE code IN ('1000', '1001', '1010', '1200', '1210')
                GROUP BY society_id
            """)
        )
        rows = result.fetchall()
        print("\nCash/Bank Accounts by society_id:")
        for s_id, count in rows:
            print(f"  society_id {s_id}: {count} accounts")
        
        # Check what society_id the user likely has
        result = await db.execute(
            text("""
                SELECT id, email, society_id
                FROM users
                LIMIT 5
            """)
        )
        rows = result.fetchall()
        print("\nSample users:")
        for u_id, email, s_id in rows:
            print(f"  User {u_id} ({email}): society_id = {s_id}")


if __name__ == "__main__":
    asyncio.run(verify_data())
