"""Fix duplicate flat A-101 and update A-001 to A-101"""
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


async def fix_duplicate():
    async with async_session() as db:
        print("=" * 70)
        print("FIXING DUPLICATE FLAT A-101")
        print("=" * 70)
        
        # Check A-001
        result = await db.execute(
            text("SELECT id, flat_number, owner_name FROM flats WHERE flat_number = 'A-001'")
        )
        flat_001 = result.fetchone()
        
        # Check A-101
        result = await db.execute(
            text("SELECT id, flat_number, owner_name FROM flats WHERE flat_number = 'A-101'")
        )
        flat_101 = result.fetchone()
        
        if not flat_001:
            print("A-001 not found")
            return
        
        if not flat_101:
            print("A-101 not found - updating A-001 to A-101")
            await db.execute(
                text("UPDATE flats SET flat_number = 'A-101' WHERE id = :id"),
                {"id": flat_001[0]}
            )
            await db.commit()
            print("[SUCCESS] Updated A-001 to A-101")
            return
        
        print(f"A-001: ID {flat_001[0]}, Owner: {flat_001[2]}")
        print(f"A-101: ID {flat_101[0]}, Owner: {flat_101[2]}")
        
        # Check which one has members
        result = await db.execute(
            text("SELECT COUNT(*) FROM members WHERE flat_id = :id"),
            {"id": flat_001[0]}
        )
        members_001 = result.fetchone()[0]
        
        result = await db.execute(
            text("SELECT COUNT(*) FROM members WHERE flat_id = :id"),
            {"id": flat_101[0]}
        )
        members_101 = result.fetchone()[0]
        
        print(f"\nA-001 has {members_001} members")
        print(f"A-101 has {members_101} members")
        
        # Delete the one with no members (or fewer members)
        if members_101 == 0 and members_001 > 0:
            print("\nDeleting A-101 (no members), keeping A-001")
            await db.execute(
                text("DELETE FROM flats WHERE id = :id"),
                {"id": flat_101[0]}
            )
            await db.commit()
            print("[SUCCESS] Deleted duplicate A-101")
            
            # Now update A-001 to A-101
            print("Updating A-001 to A-101...")
            await db.execute(
                text("UPDATE flats SET flat_number = 'A-101' WHERE id = :id"),
                {"id": flat_001[0]}
            )
            await db.commit()
            print("[SUCCESS] Updated A-001 to A-101")
        elif members_001 == 0 and members_101 > 0:
            print("\nDeleting A-001 (no members), keeping A-101")
            await db.execute(
                text("DELETE FROM flats WHERE id = :id"),
                {"id": flat_001[0]}
            )
            await db.commit()
            print("[SUCCESS] Deleted A-001, A-101 already exists")
        elif members_001 == 0 and members_101 == 0:
            # Both have no members, delete A-101 and update A-001
            print("\nBoth have no members, deleting A-101 and updating A-001 to A-101")
            await db.execute(
                text("DELETE FROM flats WHERE id = :id"),
                {"id": flat_101[0]}
            )
            await db.execute(
                text("UPDATE flats SET flat_number = 'A-101' WHERE id = :id"),
                {"id": flat_001[0]}
            )
            await db.commit()
            print("[SUCCESS] Deleted duplicate A-101 and updated A-001 to A-101")
        else:
            print("\n[WARNING] Both flats have members. Manual intervention required.")
            print("  You may need to merge members or reassign them before fixing flat numbers.")


if __name__ == "__main__":
    asyncio.run(fix_duplicate())
