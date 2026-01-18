import asyncio
import os
import sys

# Add current directory to path
sys.path.append(os.getcwd())

from app.database import AsyncSessionLocal
from app.models_db import Society
from sqlalchemy import select

async def check():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Society).where(Society.id == 1))
        s = res.scalar_one_or_none()
        if s:
            print(f"Society ID 1: {s.name}")
            print(f"Logo URL: '{s.logo_url}'")
            print(f"Address: '{s.address}'")

if __name__ == "__main__":
    asyncio.run(check())
