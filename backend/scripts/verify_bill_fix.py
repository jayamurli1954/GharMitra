"""Verify bill water calculation fix"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os
import json

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./gharmitra.db")
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def verify():
    """Verify bill water calculation"""
    async with async_session() as db:
        print("=" * 70)
        print("VERIFYING BILL WATER CALCULATION FIX")
        print("=" * 70)
        print()
        
        # Check A-101 bill
        result = await db.execute(
            text("""
                SELECT flat_number, water_amount, breakdown
                FROM maintenance_bills
                WHERE flat_number = 'A-101'
                ORDER BY year DESC, month DESC
                LIMIT 1
            """)
        )
        bill = result.fetchone()
        
        if bill:
            flat_num, water_amt, breakdown_json = bill
            breakdown = json.loads(breakdown_json) if isinstance(breakdown_json, str) else breakdown_json
            
            print(f"Flat: {flat_num}")
            print(f"Water Amount: Rs.{water_amt}")
            print()
            print("Breakdown fields:")
            print(f"  water_per_person_rate: {breakdown.get('water_per_person_rate')}")
            print(f"  water_per_person: {breakdown.get('water_per_person')}")
            print(f"  inmates_used: {breakdown.get('inmates_used')}")
            print(f"  occupants: {breakdown.get('occupants')}")
            print(f"  water_calculation: {breakdown.get('water_calculation')}")
            print()
            
            # Verify calculation
            rate = breakdown.get('water_per_person_rate') or breakdown.get('water_per_person') or 0
            occupants = breakdown.get('inmates_used') or breakdown.get('occupants') or 0
            calculated = rate * occupants
            
            print(f"Verification:")
            print(f"  Rate: Rs.{rate:.3f}")
            print(f"  Occupants: {occupants}")
            print(f"  Calculated: Rs.{rate:.3f} × {occupants} = Rs.{calculated:.2f}")
            print(f"  Actual Amount: Rs.{water_amt}")
            print(f"  Match: {'✓' if abs(calculated - float(water_amt)) < 0.10 else '✗'}")


if __name__ == "__main__":
    asyncio.run(verify())
