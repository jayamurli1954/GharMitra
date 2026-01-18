"""
Script to delete incorrect transactions in account 4010 that should not exist.
According to , all maintenance bill income should post to 4000 only, not 4010.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import AsyncSessionLocal
from app.models_db import Transaction, AccountCode
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from decimal import Decimal


async def main():
    async with AsyncSessionLocal() as db:
        print("=" * 80)
        print("DELETING INCORRECT TRANSACTIONS IN ACCOUNT 4010")
        print("=" * 80)
        print()
        
        society_id = 1  # Default society_id
        
        # Find all transactions in account 4010 related to maintenance bills
        result = await db.execute(
            select(Transaction)
            .where(
                and_(
                    Transaction.account_code == "4010",
                    Transaction.society_id == society_id
                )
            )
            .options(selectinload(Transaction.journal_entry))
        )
        transactions_4010 = result.scalars().all()
        
        print(f"Found {len(transactions_4010)} transactions in account 4010")
        print()
        
        # Filter transactions that are from maintenance bills
        incorrect_transactions = [
            txn for txn in transactions_4010
            if any(keyword in txn.description.lower() 
                   for keyword in ['maintenance', 'bill', 'month', 'charges for', 'posted'])
        ]
        
        print(f"Found {len(incorrect_transactions)} incorrect transactions (maintenance bill related)")
        print()
        
        if len(incorrect_transactions) == 0:
            print("No incorrect transactions found. All transactions in 4010 appear to be legitimate.")
            return
        
        # Show transactions to be deleted
        total_credit = Decimal("0.00")
        for txn in incorrect_transactions:
            print(f"  - ID: {txn.id}, Date: {txn.date}, "
                  f"Desc: {txn.description[:60]}, "
                  f"Credit: Rs.{txn.credit_amount or 0}")
            if txn.credit_amount:
                total_credit += Decimal(str(txn.credit_amount))
        
        print()
        print(f"Total credit amount to be removed: Rs.{total_credit:,.2f}")
        print()
        
        # Delete transactions
        print("Deleting incorrect transactions...")
        for txn in incorrect_transactions:
            await db.delete(txn)
            print(f"  Deleted transaction {txn.id}")
        
        await db.commit()
        print()
        print(f"Successfully deleted {len(incorrect_transactions)} transactions")
        
        # Recalculate account 4010 balance
        print()
        print("Recalculating account 4010 balance...")
        remaining_result = await db.execute(
            select(Transaction)
            .where(
                and_(
                    Transaction.account_code == "4010",
                    Transaction.society_id == society_id
                )
            )
        )
        remaining_transactions = remaining_result.scalars().all()
        
        total_debit = Decimal("0.00")
        remaining_credit = Decimal("0.00")
        for txn in remaining_transactions:
            if txn.debit_amount:
                total_debit += Decimal(str(txn.debit_amount))
            if txn.credit_amount:
                remaining_credit += Decimal(str(txn.credit_amount))
        
        # Update account balance
        account_result = await db.execute(
            select(AccountCode).where(
                and_(
                    AccountCode.code == "4010",
                    AccountCode.society_id == society_id
                )
            )
        )
        account = account_result.scalar_one_or_none()
        
        if account:
            # For income accounts, balance = credit - debit
            correct_balance = remaining_credit - total_debit
            old_balance = Decimal(str(account.current_balance or 0.0))
            account.current_balance = float(correct_balance)
            db.add(account)
            await db.commit()
            
            print(f"Account 4010 (Water Charges):")
            print(f"  Old Balance: Rs.{old_balance:,.2f}")
            print(f"  New Balance: Rs.{correct_balance:,.2f}")
            print(f"  Difference: Rs.{(correct_balance - old_balance):,.2f}")
        
        print()
        print("=" * 80)
        print("COMPLETE")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
