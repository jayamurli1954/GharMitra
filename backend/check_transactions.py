
import asyncio
from typing import List
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models_db import Transaction, AccountCode

async def check_transactions():
    async with AsyncSessionLocal() as session:
        # Check Account 3010 (Corpus Fund)
        print("--- Account 3010 (Corpus Fund) ---")
        
        # Get Account details
        result = await session.execute(select(AccountCode).where(AccountCode.code == "3010"))
        account = result.scalar_one_or_none()
        if account:
            print(f"Account Opening Balance: {account.opening_balance}")
            print(f"Account Current Balance: {account.current_balance}")
        
        # Get Transactions
        result = await session.execute(select(Transaction).where(Transaction.account_code == "3010"))
        transactions = result.scalars().all()
        print(f"Transaction Count: {len(transactions)}")
        for txn in transactions:
            print(f"Txn ID: {txn.id} | {txn.date} | {txn.description} | Dr: {txn.debit_amount} | Cr: {txn.credit_amount}")

        # Check Account 3020 (Emergency Fund)
        print("\n--- Account 3020 (Emergency Fund) ---")
        result = await session.execute(select(AccountCode).where(AccountCode.code == "3020"))
        account = result.scalar_one_or_none()
        if account:
            print(f"Account Opening Balance: {account.opening_balance}")
            print(f"Account Current Balance: {account.current_balance}")

        # Check Account 1001 (HDFC)
        print("\n--- Account 1001 (HDFC Bank) ---")
        result = await session.execute(select(AccountCode).where(AccountCode.code == "1001"))
        account = result.scalar_one_or_none()
        if account:
            print(f"Account Opening Balance: {account.opening_balance}")
            print(f"Account Current Balance: {account.current_balance}")
        
        result = await session.execute(select(Transaction).where(Transaction.account_code == "1001"))
        transactions = result.scalars().all()
        print(f"Transaction Count: {len(transactions)}")
        for txn in transactions:
            print(f"Txn ID: {txn.id} | {txn.date} | {txn.description} | Dr: {txn.debit_amount} | Cr: {txn.credit_amount}")

        # Check Account 1010 (Cash)
        print("\n--- Account 1010 (Cash in Hand) ---")
        result = await session.execute(select(AccountCode).where(AccountCode.code == "1010"))
        account = result.scalar_one_or_none()
        if account:
            print(f"Account Opening Balance: {account.opening_balance}")
            print(f"Account Current Balance: {account.current_balance}")
        
        result = await session.execute(select(Transaction).where(Transaction.account_code == "1010"))
        transactions = result.scalars().all()
        print(f"Transaction Count: {len(transactions)}")
        for txn in transactions:
            print(f"Txn ID: {txn.id} | {txn.date} | {txn.description} | Dr: {txn.debit_amount} | Cr: {txn.credit_amount}")

if __name__ == "__main__":
    asyncio.run(check_transactions())
