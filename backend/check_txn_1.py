
import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models_db import Transaction

async def check_txn_1():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Transaction).where(Transaction.id == 1))
        txn = result.scalar_one_or_none()
        if txn:
            print(f"Txn ID: {txn.id} | {txn.date} | {txn.description} | Dr: {txn.debit_amount} | Cr: {txn.credit_amount} | Acc: {txn.account_code}")
        else:
            print("Txn ID 1 not found.")

if __name__ == "__main__":
    asyncio.run(check_txn_1())
