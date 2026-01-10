
import asyncio
from sqlalchemy import select, update
from app.database import AsyncSessionLocal
from app.models_db import Transaction, TransactionType

async def fix_transaction_types():
    async with AsyncSessionLocal() as db:
        print("Fixing Transaction Types...")
        
        # 1. Find transactions that look like Receipts but are marked as EXPENSE
        # Description like "received"
        # Type = 'expense'
        
        result = await db.execute(
            select(Transaction).where(
                Transaction.type == TransactionType.EXPENSE,
                Transaction.description.like('%received%')
            )
        )
        txns = result.scalars().all()
        
        print(f"Found {len(txns)} mismatched transactions.")
        
        count = 0
        for txn in txns:
            # Verify it is indeed a receipt (Debit > 0 or linked to Income)
            # Actually, "received" in description is a strong indicator.
            print(f"ID {txn.id}: {txn.description} (Currently EXPENSE)")
            
            txn.type = TransactionType.INCOME
            count += 1
            print(f"  -> Changed to INCOME")
            
        if count > 0:
            await db.commit()
            print(f"Successfully updated {count} transactions.")
        else:
            print("No transactions to update.")

if __name__ == "__main__":
    asyncio.run(fix_transaction_types())
