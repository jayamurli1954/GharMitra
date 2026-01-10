"""Delete the 21st flat (A-021) that shouldn't exist"""
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


async def delete_extra_flat():
    """Delete A-021 flat"""
    async with async_session() as db:
        # Find A-021
        result = await db.execute(
            text("SELECT id, flat_number, owner_name FROM flats WHERE flat_number = 'A-021'")
        )
        flat = result.fetchone()
        
        if not flat:
            print("A-021 flat not found (may have already been deleted)")
            return
        
        flat_id, flat_num, owner = flat
        print(f"Found flat: ID {flat_id}, Number: {flat_num}, Owner: {owner}")
        
        # Check if it has active members
        result = await db.execute(
            text("""
                SELECT COUNT(*) FROM members 
                WHERE flat_id = :flat_id AND status = 'active'
            """),
            {"flat_id": flat_id}
        )
        member_count = result.fetchone()[0]
        
        if member_count > 0:
            print(f"[ERROR] Cannot delete {flat_num} - it has {member_count} active member(s)")
            return
        
        # Delete the flat
        await db.execute(
            text("DELETE FROM flats WHERE id = :flat_id"),
            {"flat_id": flat_id}
        )
        await db.commit()
        
        print(f"[SUCCESS] Deleted flat {flat_num} (ID: {flat_id})")


if __name__ == "__main__":
    asyncio.run(delete_extra_flat())
