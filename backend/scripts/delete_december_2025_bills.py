"""
Delete unposted bills for December 2025
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


async def delete_december_bills():
    """Delete unposted bills for December 2025"""
    async with async_session() as db:
        print("=" * 70)
        print("DELETING DECEMBER 2025 BILLS")
        print("=" * 70)
        
        month = 12
        year = 2025
        
        # Check for bills
        result = await db.execute(
            text("""
                SELECT id, flat_id, bill_number, is_posted, total_amount
                FROM maintenance_bills
                WHERE month = :month AND year = :year
            """),
            {"month": month, "year": year}
        )
        bills = result.fetchall()
        
        if not bills:
            print(f"\nNo bills found for {month}/{year}")
            return
        
        print(f"\nFound {len(bills)} bills for {month}/{year}:")
        posted_count = 0
        unposted_count = 0
        
        for bill_id, flat_id, bill_num, is_posted, total in bills:
            status = "POSTED" if is_posted else "UNPOSTED"
            if is_posted:
                posted_count += 1
            else:
                unposted_count += 1
            print(f"  - {bill_num}: Flat {flat_id}, Status: {status}, Amount: Rs.{total or 0}")
        
        if posted_count > 0:
            print(f"\n[WARNING] {posted_count} bills are POSTED and cannot be deleted!")
            print("Only unposted bills will be deleted.")
        
        if unposted_count == 0:
            print("\nNo unposted bills to delete.")
            return
        
        # Delete unposted bills
        print(f"\nDeleting {unposted_count} unposted bills...")
        result = await db.execute(
            text("""
                DELETE FROM maintenance_bills
                WHERE month = :month AND year = :year AND is_posted = 0
            """),
            {"month": month, "year": year}
        )
        await db.commit()
        
        deleted_count = result.rowcount if hasattr(result, 'rowcount') else unposted_count
        print(f"\n[SUCCESS] Deleted {deleted_count} unposted bills for {month}/{year}")
        print("\nYou can now regenerate the bills with the correct fixed expense accounts.")


if __name__ == "__main__":
    asyncio.run(delete_december_bills())
