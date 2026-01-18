
import asyncio
import os
import sys
from sqlalchemy import select, and_
from decimal import Decimal

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.config import settings
settings.DATABASE_URL = "sqlite+aiosqlite:///d:/SanMitra_Tech/GharMitra/backend/gharmitra.db"

from app.database import AsyncSessionLocal
from app.models_db import Transaction, AccountCode

async def verify():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Transaction).where(Transaction.account_code == '4000').order_by(Transaction.date))
        txns = res.scalars().all()
        print("Updated Transactions for 4000:")
        for t in txns:
            print(f"  Date: {t.date} | Desc: {t.description[:40]}")

if __name__ == "__main__":
    asyncio.run(verify())
