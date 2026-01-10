"""Fix bill status for bills that are paid but status is still UNPAID"""
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


async def fix_bill_status():
    """Update bill status to PAID for bills that are marked as is_paid=True"""
    async with async_session() as db:
        print("=" * 70)
        print("FIXING BILL STATUS FOR PAID BILLS")
        print("=" * 70)
        print()
        
        # Find bills that have paid_date set but status is still UNPAID
        result = await db.execute(
            text("""
                SELECT id, flat_number, bill_number, total_amount, paid_date, status
                FROM maintenance_bills
                WHERE paid_date IS NOT NULL AND status = 'UNPAID'
            """)
        )
        bills = result.fetchall()
        
        if not bills:
            print("No bills found that need status update.")
            return
        
        print(f"Found {len(bills)} bills that have paid_date but status is still UNPAID:")
        print()
        
        for bill_id, flat_number, bill_number, total_amount, paid_date, status in bills:
            print(f"  Flat {flat_number} ({bill_number}): Total: Rs.{total_amount}, Paid Date: {paid_date}")
            
            # Update status to PAID
            await db.execute(
                text("""
                    UPDATE maintenance_bills
                    SET status = 'PAID'
                    WHERE id = :bill_id
                """),
                {"bill_id": bill_id}
            )
        
        await db.commit()
        
        print()
        print("=" * 70)
        print(f"SUMMARY: Updated {len(bills)} bill(s) to PAID status")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(fix_bill_status())
