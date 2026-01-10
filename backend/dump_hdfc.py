
import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models_db import Transaction

async def dump_hdfc_txns():
    async with AsyncSessionLocal() as db:
        print("Dumping HDFC Transactions (1001)...")
        result = await db.execute(
            select(Transaction).where(Transaction.account_code == '1001').order_by(Transaction.id)
        )
        txns = result.scalars().all()
        
        print(f"{'ID':<5} | {'Type':<10} | {'Debit':<10} | {'Credit':<10} | {'Description'}")
        print("-" * 80)
        for txn in txns:
            # Print raw type (enum or string)
            print(f"{txn.id:<5} | {str(txn.type):<10} | {txn.debit_amount:<10} | {txn.credit_amount:<10} | {txn.description[:30]}")

if __name__ == "__main__":
    asyncio.run(dump_hdfc_txns())
