
import asyncio
from datetime import date
from sqlalchemy import select, and_
from app.database import AsyncSessionLocal
from app.models_db import Transaction, AccountCode, User, TransactionType
from collections import defaultdict

async def test_general_ledger_logic():
    async with AsyncSessionLocal() as db:
        print("Testing General Ledger Logic...")
        society_id = 1
        from_date = date(2025, 12, 31)
        to_date = date(2026, 1, 30)
        
        # 1. Fetch Account Codes
        result = await db.execute(
            select(AccountCode).where(
                AccountCode.society_id == society_id,
                AccountCode.type.in_(["income", "expense"]) # Note: Logic uses strings here?
            ).order_by(AccountCode.code)
        )
        account_codes = result.scalars().all()
        print(f"Found {len(account_codes)} account codes.")
        
        # 2. Fetch Transactions
        # Need to handle Enum types correctly in filter?
        # The original code uses ["income", "expense"] strings.
        # SQLAlchemy usually handles this if Enum column is set up
        
        result = await db.execute(
            select(Transaction).where(
                and_(
                    Transaction.society_id == society_id,
                    Transaction.date >= from_date,
                    Transaction.date <= to_date,
                    # Transaction.type.in_(['income', 'expense']) 
                    # If this fails, it might be because type is Enum
                )
            ).order_by(Transaction.date, Transaction.account_code)
        )
        transactions = result.scalars().all()
        print(f"Found {len(transactions)} transactions.")
        
        # 3. Simulate Logic
        ledger_by_account = defaultdict(lambda: {
            "account_code": "",
            # ...
        })
        
        # Init
        for account in account_codes:
            ledger_by_account[account.code] = {
                "account_code": account.code,
                "account_name": account.name,
                "account_type": account.type, # Type is Enum? or String? AccountType enum.
            }
            
        # Process
        for txn in transactions:
            account_code = txn.account_code
            print(f"Processing Txn ID {txn.id}: Code={account_code}, Type={txn.type} ({type(txn.type)})")
            
            if account_code not in ledger_by_account:
                ledger_by_account[account_code] = {
                    "account_code": account_code,
                    "account_name": str(txn.category) if txn.category else str(account_code),
                    # ...
                }
            
            # Check Enum comparison
            if txn.type == "income":
                print("Matches 'income' string")
            elif txn.type == TransactionType.INCOME:
                print("Matches TransactionType.INCOME enum")
            else:
                print(f"Does not match 'income' string. Values is {txn.type}")
        
        # 4. Sort (The Suspected Crash)
        print("Sorting ledger entries...")
        try:
            ledger_entries = sorted(ledger_by_account.values(), key=lambda x: x["account_code"])
            print("Sorting successful.")
        except TypeError as e:
            print(f"CRITICAL ERROR during sorting: {e}")
            
if __name__ == "__main__":
    asyncio.run(test_general_ledger_logic())
