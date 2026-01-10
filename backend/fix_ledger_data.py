
import asyncio
from sqlalchemy import select, update
from app.database import AsyncSessionLocal
from app.models_db import Transaction

async def fix_ledger_transaction_legs():
    async with AsyncSessionLocal() as db:
        print("Fixing Ledger Transaction Legs...")
        
        # 1. Fetch transactions that are Bank/Cash legs of Income (Corpus/Emergency)
        # We search by description AND account code (1001/1010)
        # And check if they have Credit > 0 (which is WRONG for Income receipt in Bank)
        
        result = await db.execute(
            select(Transaction).where(
                Transaction.type == 'income',
                Transaction.credit_amount > 0, # Wrongly credited
                Transaction.account_code.in_(['1001', '1010']) # Bank or Cash
            )
        )
        txns = result.scalars().all()
        
        print(f"Found {len(txns)} incorrect transactions.")
        
        for txn in txns:
            print(f"Fixing Txn {txn.id}: {txn.account_code} - {txn.description[:30]}...")
            print(f"  Current: Debit={txn.debit_amount}, Credit={txn.credit_amount}")
            
            # Swap
            new_debit = txn.credit_amount
            new_credit = 0.0 # Should be 0 for receipt
            
            txn.debit_amount = new_debit
            txn.credit_amount = new_credit
            
            print(f"  New:     Debit={txn.debit_amount}, Credit={txn.credit_amount}")
            
        if txns:
            await db.commit()
            print("Successfully committed fixes.")
        else:
            print("No transactions matched the fix criteria.")

if __name__ == "__main__":
    asyncio.run(fix_ledger_transaction_legs())
