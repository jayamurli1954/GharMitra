"""Fix water calculation details in existing bills"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os
import json
from decimal import Decimal

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./gharmitra.db")
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def fix_bills():
    """Fix water calculation details in existing bills"""
    async with async_session() as db:
        print("=" * 70)
        print("FIXING WATER CALCULATION IN EXISTING BILLS")
        print("=" * 70)
        print()
        
        # Get all bills with water charges
        result = await db.execute(
            text("""
                SELECT id, flat_number, breakdown, water_amount
                FROM maintenance_bills
                WHERE water_amount > 0
                ORDER BY year, month, flat_number
            """)
        )
        bills = result.fetchall()
        
        if not bills:
            print("No bills with water charges found")
            return
        
        print(f"Found {len(bills)} bills with water charges")
        print()
        
        updated_count = 0
        
        for bill_id, flat_number, breakdown_json, water_amount in bills:
            if not breakdown_json:
                continue
                
            try:
                breakdown = json.loads(breakdown_json) if isinstance(breakdown_json, str) else breakdown_json
            except:
                breakdown = {}
            
            try:
                water_amount_decimal = Decimal(str(water_amount))
                
                # Check if we need to fix the water calculation
                per_person_rate = breakdown.get('water_per_person_rate') or breakdown.get('water_per_person') or breakdown.get('per_person_water_charge') or 0
                occupants_used = breakdown.get('inmates_used')
                occupants = breakdown.get('occupants') or breakdown.get('number_of_occupants') or 0
                
                # If we have water amount but missing rate or occupants, calculate from amount
                if water_amount_decimal > 0:
                    # Try to get occupants from flat
                    flat_result = await db.execute(
                        text("SELECT occupants FROM flats WHERE flat_number = :flat_num"),
                        {"flat_num": flat_number}
                    )
                    flat_row = flat_result.fetchone()
                    flat_occupants = flat_row[0] if flat_row else 0
                    
                    # Use the best available occupant count
                    final_occupants = occupants_used if occupants_used is not None and occupants_used > 0 else (occupants if occupants > 0 else flat_occupants)
                    
                    # Calculate per person rate if missing
                    if per_person_rate == 0 and final_occupants > 0:
                        calculated_rate = float(water_amount_decimal / Decimal(str(final_occupants)))
                        per_person_rate = calculated_rate
                        print(f"  Flat {flat_number}: Calculated rate Rs.{calculated_rate:.3f} from amount Rs.{water_amount} / {final_occupants} occupants")
                    
                    # Update breakdown with correct values
                    breakdown['water_per_person_rate'] = per_person_rate
                    breakdown['water_per_person'] = per_person_rate  # For backward compatibility
                    breakdown['inmates_used'] = final_occupants
                    breakdown['occupants'] = final_occupants
                    
                    # Create water calculation string
                    if breakdown.get('is_vacant') or breakdown.get('vacancy_fee_applied'):
                        water_calculation = f"Vacant flat - Minimum charge"
                    elif per_person_rate > 0 and final_occupants > 0:
                        water_calculation = f"Per person: Rs.{per_person_rate:.3f}, Occupants: {final_occupants}"
                    else:
                        water_calculation = f"Water charges: Rs.{water_amount:.2f}"
                    
                    breakdown['water_calculation'] = water_calculation
                    
                    # Update the bill
                    await db.execute(
                        text("""
                            UPDATE maintenance_bills
                            SET breakdown = :breakdown
                            WHERE id = :bill_id
                        """),
                        {"breakdown": json.dumps(breakdown), "bill_id": bill_id}
                    )
                    
                    updated_count += 1
                    print(f"  Fixed Flat {flat_number}: {water_calculation}")
                    
            except Exception as e:
                print(f"  Error fixing Flat {flat_number}: {e}")
        
        await db.commit()
        
        print()
        print("=" * 70)
        print(f"SUMMARY: Updated {updated_count} bill(s)")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(fix_bills())
