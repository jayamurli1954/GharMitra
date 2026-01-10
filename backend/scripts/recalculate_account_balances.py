"""
Script to recalculate account balances for accounts 4000 and 4010.
This ensures balances are correct after deleting incorrect transactions.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import AsyncSessionLocal
from app.models_db import Transaction, AccountCode
from sqlalchemy import select, and_, func
from decimal import Decimal


async def recalculate_account_balance(db, account_code, society_id=1):
    """Recalculate and fix account balance based on transactions"""
    # Get all transactions for the account
    result = await db.execute(
        select(Transaction)
        .where(
            and_(
                Transaction.account_code == account_code,
                Transaction.society_id == society_id
            )
        )
    )
    transactions = result.scalars().all()
    
    # Calculate correct balance
    total_debit = Decimal("0.00")
    total_credit = Decimal("0.00")
    
    for txn in transactions:
        if txn.debit_amount:
            total_debit += Decimal(str(txn.debit_amount))
        if txn.credit_amount:
            total_credit += Decimal(str(txn.credit_amount))
    
    # Get account
    account_result = await db.execute(
        select(AccountCode).where(
            and_(
                AccountCode.code == account_code,
                AccountCode.society_id == society_id
            )
        )
    )
    account = account_result.scalar_one_or_none()
    
    if account:
        # For income accounts (4000, 4010), balance = credit - debit
        # Credit increases income (negative balance), Debit decreases (positive balance)
        correct_balance = total_credit - total_debit
        
        old_balance = Decimal(str(account.current_balance or 0.0))
        account.current_balance = float(correct_balance)
        db.add(account)
        
        return {
            'account_code': account_code,
            'account_name': account.name,
            'old_balance': float(old_balance),
            'correct_balance': float(correct_balance),
            'difference': float(correct_balance - old_balance),
            'total_debit': float(total_debit),
            'total_credit': float(total_credit),
            'transaction_count': len(transactions)
        }
    
    return None


async def main():
    async with AsyncSessionLocal() as db:
        print("=" * 80)
        print("RECALCULATING ACCOUNT BALANCES")
        print("=" * 80)
        print()
        
        society_id = 1  # Default society_id
        
        # Recalculate account 4000 (Maintenance Charges)
        print("1. Recalculating Account 4000 (Maintenance Charges)...")
        print("-" * 80)
        account_4000_info = await recalculate_account_balance(db, "4000", society_id)
        if account_4000_info:
            print(f"   Account: {account_4000_info['account_code']} - {account_4000_info['account_name']}")
            print(f"   Transactions: {account_4000_info['transaction_count']}")
            print(f"   Total Debit: Rs.{account_4000_info['total_debit']:,.2f}")
            print(f"   Total Credit: Rs.{account_4000_info['total_credit']:,.2f}")
            print(f"   Old Balance: Rs.{account_4000_info['old_balance']:,.2f}")
            print(f"   Correct Balance: Rs.{account_4000_info['correct_balance']:,.2f}")
            print(f"   Difference: Rs.{account_4000_info['difference']:,.2f}")
        
        # Recalculate account 4010 (Water Charges)
        print()
        print("2. Recalculating Account 4010 (Water Charges)...")
        print("-" * 80)
        account_4010_info = await recalculate_account_balance(db, "4010", society_id)
        if account_4010_info:
            print(f"   Account: {account_4010_info['account_code']} - {account_4010_info['account_name']}")
            print(f"   Transactions: {account_4010_info['transaction_count']}")
            print(f"   Total Debit: Rs.{account_4010_info['total_debit']:,.2f}")
            print(f"   Total Credit: Rs.{account_4010_info['total_credit']:,.2f}")
            print(f"   Old Balance: Rs.{account_4010_info['old_balance']:,.2f}")
            print(f"   Correct Balance: Rs.{account_4010_info['correct_balance']:,.2f}")
            print(f"   Difference: Rs.{account_4010_info['difference']:,.2f}")
        else:
            print("   Account 4010 not found or has no transactions")
        
        await db.commit()
        
        print()
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        if account_4000_info:
            print(f"Account 4000 (Maintenance Charges): Rs.{account_4000_info['correct_balance']:,.2f}")
        if account_4010_info:
            print(f"Account 4010 (Water Charges): Rs.{account_4010_info['correct_balance']:,.2f}")
        else:
            print(f"Account 4010 (Water Charges): Rs.0.00 (no transactions)")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
