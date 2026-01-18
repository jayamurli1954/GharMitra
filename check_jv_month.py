
import asyncio
import os
import sys
from sqlalchemy import select, text

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.config import settings
settings.DATABASE_URL = "sqlite+aiosqlite:///d:/SanMitra_Tech/GharMitra/backend/gharmitra.db"

from app.database import AsyncSessionLocal

async def check_jv():
    async with AsyncSessionLocal() as db:
        result = await db.execute(text("SELECT id, entry_number, date, description, created_at FROM journal_entries WHERE description LIKE '%December 2025%'"))
        jvs = result.fetchall()
        for jv in jvs:
            print(f"JV ID: {jv[0]} | No: {jv[1]} | Date: {jv[2]} | Desc: {jv[3]} | Created: {jv[4]}")

if __name__ == "__main__":
    asyncio.run(check_jv())
