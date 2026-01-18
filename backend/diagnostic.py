import asyncio
import os
import sys

# Add current directory to path
sys.path.append(os.getcwd())

from app.database import AsyncSessionLocal
from app.models_db import Transaction, AccountCode, Society
from sqlalchemy import select, func

async def diagnostic():
    async with AsyncSessionLocal() as db:
        # Check societies
        res = await db.execute(select(Society))
        societies = res.scalars().all()
        print("SOCIETIES:")
        for s in societies:
            print(f"ID: {s.id}, Name: {s.name}")
        
        # Check current counts
        res = await db.execute(select(func.count(Transaction.id)))
        print(f"TRANSACTION COUNT: {res.scalar()}")
        
        res = await db.execute(select(func.count(AccountCode.id)))
        print(f"ACCOUNT CODE COUNT: {res.scalar()}")
        
        # Check first 5 transactions
        res = await db.execute(select(Transaction).limit(5))
        txns = res.scalars().all()
        print("\nFIRST 5 TRANSACTIONS:")
        for t in txns:
            print(f"ID: {t.id}, Society: {t.society_id}, Date: {t.date}, Code: {t.account_code}, D: {t.debit_amount}, C: {t.credit_amount}, Type: {t.type}")
            
        # Check first 5 accounts
        res = await db.execute(select(AccountCode).limit(5))
        accounts = res.scalars().all()
        print("\nFIRST 5 ACCOUNTS:")
        for a in accounts:
            print(f"ID: {a.id}, Society: {a.society_id}, Code: {a.code}, Name: {a.name}, Type: {a.type}")

if __name__ == "__main__":
    asyncio.run(diagnostic())
