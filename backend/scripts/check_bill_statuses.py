"""Check bill statuses and verify dashboard data"""
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


async def check_bills():
    """Check bill statuses"""
    async with async_session() as db:
        print("=" * 70)
        print("BILL STATUS CHECK")
        print("=" * 70)
        print()
        
        # Check bill statuses
        result = await db.execute(
            text("""
                SELECT status, COUNT(*) as count, COALESCE(SUM(total_amount), 0) as total
                FROM maintenance_bills
                GROUP BY status
            """)
        )
        rows = result.fetchall()
        
        print("Bill Status Summary:")
        for status, count, total in rows:
            print(f"  {status}: {count} bills, Total: Rs.{total}")
        
        # Check December 2025 bills specifically
        print("\nDecember 2025 Bills:")
        result = await db.execute(
            text("""
                SELECT status, COUNT(*) as count, COALESCE(SUM(total_amount), 0) as total
                FROM maintenance_bills
                WHERE month = 12 AND year = 2025
                GROUP BY status
            """)
        )
        rows = result.fetchall()
        for status, count, total in rows:
            print(f"  {status}: {count} bills, Total: Rs.{total}")


if __name__ == "__main__":
    asyncio.run(check_bills())
