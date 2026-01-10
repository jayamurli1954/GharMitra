
import asyncio
from sqlalchemy import select, or_
from app.database import AsyncSessionLocal
from app.models_db import Transaction, AccountCode

async def check_ledger_entries():
    async with AsyncSessionLocal() as db:
        print("Checking Ledger Entries...")
        
        # 1. Fetch Corpus Fund (3010) and Bank (1001) Transactions
        # User complained about "Corpus Fund receipt"
        # We look for transactions where account_code is 3010 OR 1001
        
        result = await db.execute(
            select(Transaction).where(
                or_(
                    Transaction.description.like('%Corpus%'),
                    Transaction.description.like('%Emergency%')
                )
            ).order_by(Transaction.date, Transaction.id)
        )
        txns = result.scalars().all()
        
        print(f"{'ID':<5} | {'Date':<10} | {'Code':<6} | {'Type':<8} | {'Debit':<10} | {'Credit':<10} | {'Description'}")
        print("-" * 100)
        
        for txn in txns:
            print(f"{txn.id:<5} | {str(txn.date):<10} | {txn.account_code:<6} | {str(txn.type):<8} | {txn.debit_amount:<10} | {txn.credit_amount:<10} | {txn.description[:40]}")

if __name__ == "__main__":
    asyncio.run(check_ledger_entries())
