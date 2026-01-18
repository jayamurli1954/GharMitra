
import asyncio
import os
import sys
from sqlalchemy import select, and_, text
from datetime import date

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.config import settings
settings.DATABASE_URL = "sqlite+aiosqlite:///d:/SanMitra_Tech/GharMitra/backend/gharmitra.db"

from app.database import AsyncSessionLocal
from app.models_db import Transaction, JournalEntry

async def fix_december_dates():
    async with AsyncSessionLocal() as db:
        print("Moving December 2025 bill transactions to Jan 1st, 2026...")
        
        # 1. Update Journal Entries
        res_jv = await db.execute(
            select(JournalEntry).where(
                and_(
                    JournalEntry.date == date(2025, 12, 1),
                    JournalEntry.description.like("%Maintenance charges for the month December 2025%")
                )
            )
        )
        jvs = res_jv.scalars().all()
        for jv in jvs:
            print(f"Updating JV {jv.entry_number} (ID: {jv.id}) date to 2026-01-01")
            jv.date = date(2026, 1, 1)
            db.add(jv)
            
        # 2. Update Transactions
        res_txn = await db.execute(
            select(Transaction).where(
                and_(
                    Transaction.date == date(2025, 12, 1),
                    Transaction.account_code.in_(['1100', '4000'])
                )
            )
        )
        txns = res_txn.scalars().all()
        for t in txns:
            print(f"Updating Transaction ID: {t.id} date to 2026-01-01")
            t.date = date(2026, 1, 1)
            db.add(t)
            
        await db.commit()
        print("Fix complete.")

if __name__ == "__main__":
    asyncio.run(fix_december_dates())
