
import asyncio
from sqlalchemy import select, and_
from app.database import AsyncSessionLocal
from app.models_db import Transaction

async def find_wrong_diesel_entry():
    async with AsyncSessionLocal() as db:
        print("Searching for incorrect Diesel entry in Salary Account (5000)...")
        
        # 1. Search for any 'Diesel' transaction to see what we have
        result = await db.execute(
            select(Transaction).where(
                Transaction.description.like('%Diesel%')
            )
        )
        txns = result.scalars().all()
        
        print(f"Found {len(txns)} transactions matching 'Diesel':")
        for txn in txns:
             print(f"ID: {txn.id:<3} | Code: {txn.account_code:<5} | Date: {txn.date} | Desc: {txn.description[:30]} | Debit: {txn.debit_amount}")
            
            # 2. Try to find the linked Cash leg (Credit Cash 1010)
            # Assuming they share the same Document Number or Link ID? 
            # Or just close timestamp/description?
            # Let's search by exact Description and Amount in 1010.
            
            linked_result = await db.execute(
                select(Transaction).where(
                    Transaction.account_code == '1010',
                    Transaction.description == txn.description,
                    Transaction.credit_amount == txn.debit_amount, # Cash Credit matches Expense Debit
                    Transaction.date == txn.date
                )
            )
            linked_txns = linked_result.scalars().all()
            for l_txn in linked_txns:
                 print(f"  -> Linked Cash Entry: ID {l_txn.id} | Desc: {l_txn.description} | Credit: {l_txn.credit_amount}")

if __name__ == "__main__":
    asyncio.run(find_wrong_diesel_entry())
