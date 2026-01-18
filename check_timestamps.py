
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

async def debug_timestamps():
    async with AsyncSessionLocal() as db:
        # Get accounts
        res = await db.execute(select(AccountCode).where(AccountCode.code.in_(['1100', '4000'])))
        accounts = res.scalars().all()
        for acc in accounts:
            print(f"\nAccount: {acc.code} - {acc.name}")
            res_txn = await db.execute(
                select(Transaction)
                .where(Transaction.account_code == acc.code)
                .order_by(Transaction.date, Transaction.id)
            )
            txns = res_txn.scalars().all()
            for t in txns:
                print(f"  Date: {t.date} | Created: {t.created_at} | Desc: {t.description[:40]}")

if __name__ == "__main__":
    asyncio.run(debug_timestamps())
