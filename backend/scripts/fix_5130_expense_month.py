"""Fix account 5130 expense_month to December 2025"""
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


async def fix_5130():
    async with async_session() as db:
        await db.execute(
            text("UPDATE transactions SET expense_month = 'December, 2025' WHERE account_code = '5130' AND expense_month = 'January, 2026'")
        )
        await db.commit()
        print("Fixed account 5130 expense_month to December, 2025")


if __name__ == "__main__":
    asyncio.run(fix_5130())
