"""Check all flats"""
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


async def check_flats():
    async with async_session() as db:
        result = await db.execute(
            text("SELECT id, flat_number, owner_name FROM flats WHERE flat_number LIKE 'A-%' ORDER BY flat_number")
        )
        flats = result.fetchall()
        
        print(f"Total flats with A- prefix: {len(flats)}")
        print("\nFlat numbers:")
        for flat_id, flat_num, owner in flats:
            print(f"  {flat_num} (ID: {flat_id}, Owner: {owner or 'None'})")


if __name__ == "__main__":
    asyncio.run(check_flats())
