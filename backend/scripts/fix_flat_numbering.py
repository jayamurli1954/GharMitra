"""
Fix flat numbering from sequential (A-001 to A-020) to floor-based (A-101 to A-405)
Based on blocks_config: 4 floors, 5 flats per floor
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


async def fix_flat_numbering():
    """Fix flat numbering to use floor-based format"""
    async with async_session() as db:
        print("=" * 70)
        print("FIXING FLAT NUMBERING")
        print("=" * 70)
        
        # Get all flats ordered by current flat_number
        result = await db.execute(
            text("""
                SELECT id, flat_number, owner_name
                FROM flats
                WHERE flat_number LIKE 'A-%'
                ORDER BY flat_number
            """)
        )
        flats = result.fetchall()
        
        if not flats:
            print("\nNo flats found with A- prefix")
            return
        
        print(f"\nFound {len(flats)} flats with A- prefix")
        print("\nCurrent flat numbers:")
        for flat_id, flat_num, owner in flats[:10]:
            print(f"  ID {flat_id}: {flat_num} - {owner or 'No owner'}")
        
        # Configuration: 4 floors, 5 flats per floor
        floors = 4
        flats_per_floor = 5
        block_name = "A"
        
        # Generate mapping: sequential number -> floor-based number
        # A-001 -> A-101, A-002 -> A-102, ..., A-005 -> A-105
        # A-006 -> A-201, A-007 -> A-202, ..., A-010 -> A-205
        # etc.
        
        mapping = {}
        flat_index = 0
        
        for floor in range(1, floors + 1):
            for flat_seq in range(1, flats_per_floor + 1):
                if flat_index < len(flats):
                    old_flat_number = flats[flat_index][1]  # Current flat_number
                    new_flat_number = f"{block_name}-{(floor * 100) + flat_seq}"
                    flat_id = flats[flat_index][0]
                    mapping[flat_id] = (old_flat_number, new_flat_number)
                    flat_index += 1
        
        print(f"\nMapping {len(mapping)} flats:")
        for flat_id, (old_num, new_num) in list(mapping.items())[:10]:
            print(f"  ID {flat_id}: {old_num} -> {new_num}")
        
        if len(mapping) < len(flats):
            print(f"\n[WARNING] Only {len(mapping)} flats can be mapped (expected {floors * flats_per_floor} = {floors * flats_per_floor} flats)")
            print(f"  You have {len(flats)} flats, but configuration allows only {floors * flats_per_floor} flats")
            print(f"  Extra flats ({len(flats) - len(mapping)}) will not be renamed")
        
        # Update flat numbers
        print(f"\nUpdating flat numbers...")
        updated_count = 0
        for flat_id, (old_num, new_num) in mapping.items():
            if old_num != new_num:
                # Check if new flat_number already exists
                check_result = await db.execute(
                    text("SELECT id FROM flats WHERE flat_number = :new_num AND id != :flat_id"),
                    {"new_num": new_num, "flat_id": flat_id}
                )
                existing = check_result.fetchone()
                
                if existing:
                    print(f"  [SKIP] ID {flat_id}: {old_num} -> {new_num} (new number already exists)")
                else:
                    await db.execute(
                        text("UPDATE flats SET flat_number = :new_num WHERE id = :flat_id"),
                        {"new_num": new_num, "flat_id": flat_id}
                    )
                    print(f"  [OK] ID {flat_id}: {old_num} -> {new_num}")
                    updated_count += 1
        
        await db.commit()
        
        print(f"\n[SUCCESS] Updated {updated_count} flat numbers")
        print("=" * 70)
        print("\nNOTE: If you have more than 20 flats, please delete the extra ones")
        print("      or adjust your blocks configuration (4 floors × 5 flats = 20 flats max)")


if __name__ == "__main__":
    asyncio.run(fix_flat_numbering())
