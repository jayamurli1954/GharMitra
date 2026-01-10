"""Verify bill amounts in database"""
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


async def verify():
    """Verify bill amounts"""
    async with async_session() as db:
        print("=" * 70)
        print("VERIFYING BILL AMOUNTS IN DATABASE")
        print("=" * 70)
        print()
        
        result = await db.execute(
            text("""
                SELECT flat_number, amount, total_amount
                FROM maintenance_bills
                WHERE year = 2025 AND month = 12
                ORDER BY flat_number
            """)
        )
        bills = result.fetchall()
        
        print(f"Found {len(bills)} bills for December 2025")
        print()
        print(f"{'Flat':<10} {'Amount':<15} {'Total Amount':<15} {'Has Decimals'}")
        print("-" * 70)
        
        for flat_number, amount, total_amount in bills:
            amount_str = str(amount)
            total_str = str(total_amount)
            has_decimals = '.' in amount_str and amount_str.split('.')[1] != '0'
            has_total_decimals = '.' in total_str and total_str.split('.')[1] != '0'
            
            decimals_note = "YES" if (has_decimals or has_total_decimals) else "NO"
            print(f"{flat_number:<10} {amount_str:<15} {total_str:<15} {decimals_note}")


if __name__ == "__main__":
    asyncio.run(verify())
