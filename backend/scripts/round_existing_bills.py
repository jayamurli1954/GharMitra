"""Round existing bills to next rupee"""
import asyncio
import sys
from pathlib import Path
import math
from decimal import Decimal

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./gharmitra.db")
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def round_bills():
    """Round all unposted bills to next rupee"""
    async with async_session() as db:
        print("=" * 70)
        print("ROUNDING EXISTING BILLS TO NEXT RUPEE")
        print("=" * 70)
        print()
        
        # Get all bills (both posted and unposted)
        result = await db.execute(
            text("""
                SELECT id, flat_number, amount, total_amount, is_posted
                FROM maintenance_bills
                ORDER BY year, month, flat_number
            """)
        )
        bills = result.fetchall()
        
        if not bills:
            print("No bills found")
            return
        
        print(f"Found {len(bills)} bills")
        print()
        
        updated_count = 0
        
        for bill_id, flat_number, amount, total_amount, is_posted in bills:
            try:
                # Round amount and total_amount to next rupee
                rounded_amount = Decimal(math.ceil(float(amount)))
                rounded_total = Decimal(math.ceil(float(total_amount)))
                
                # Only update if rounding changes the value
                if rounded_amount != Decimal(str(amount)) or rounded_total != Decimal(str(total_amount)):
                    status_note = "(POSTED)" if is_posted else "(unposted)"
                    await db.execute(
                        text("""
                            UPDATE maintenance_bills
                            SET amount = :amount, total_amount = :total_amount
                            WHERE id = :bill_id
                        """),
                        {
                            "amount": float(rounded_amount),
                            "total_amount": float(rounded_total),
                            "bill_id": bill_id
                        }
                    )
                    updated_count += 1
                    print(f"  Flat {flat_number} {status_note}: Rs.{amount} -> Rs.{rounded_amount}, Total: Rs.{total_amount} -> Rs.{rounded_total}")
                else:
                    print(f"  Flat {flat_number}: Already rounded (Rs.{amount})")
                    
            except Exception as e:
                print(f"  Error rounding Flat {flat_number}: {e}")
        
        await db.commit()
        
        print()
        print("=" * 70)
        print(f"SUMMARY: Updated {updated_count} bill(s)")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(round_bills())
