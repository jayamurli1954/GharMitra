"""
Script to fix incorrect maintenance charges transactions.
This script will:
1. Check for duplicate or incorrect transactions in accounts 4000 and 4010
2. Identify transactions that should not exist (e.g., separate postings to 4010)
3. Create reversal entries or delete incorrect transactions
4. Recalculate account balances
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import AsyncSessionLocal
from app.models_db import Transaction, JournalEntry, AccountCode
from sqlalchemy import select, and_, func, desc
from sqlalchemy.orm import selectinload
from decimal import Decimal
from datetime import datetime


async def check_account_transactions(db, account_code, society_id=1):
    """Check all transactions for a given account"""
    result = await db.execute(
        select(Transaction)
        .where(
            and_(
                Transaction.account_code == account_code,
                Transaction.society_id == society_id
            )
        )
        .order_by(Transaction.date.desc(), Transaction.created_at.desc())
        .options(selectinload(Transaction.journal_entry))
    )
    transactions = result.scalars().all()
    return transactions


async def fix_account_balance(db, account_code, society_id=1):
    """Recalculate and fix account balance based on transactions"""
    # Get all transactions for the account
    transactions = await check_account_transactions(db, account_code, society_id)
    
    # Calculate correct balance
    total_debit = Decimal("0.00")
    total_credit = Decimal("0.00")
    
    for txn in transactions:
        if txn.debit_amount:
            total_debit += Decimal(str(txn.debit_amount))
        if txn.credit_amount:
            total_credit += Decimal(str(txn.credit_amount))
    
    # For income accounts (4000, 4010), balance = credit - debit
    # For asset accounts, balance = debit - credit
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
        if account.type.value in ['income', 'liability']:
            # Income/Liability: Credit increases, Debit decreases
            correct_balance = total_credit - total_debit
        else:
            # Asset: Debit increases, Credit decreases
            correct_balance = total_debit - total_credit
        
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
            'total_credit': float(total_credit)
        }
    
    return None


async def main():
    async with AsyncSessionLocal() as db:
        print("=" * 80)
        print("FIXING INCORRECT MAINTENANCE CHARGES TRANSACTIONS")
        print("=" * 80)
        print()
        
        society_id = 1  # Default society_id
        
        # 1. Check account 4000 (Maintenance Charges)
        print("1. Checking Account 4000 (Maintenance Charges)...")
        print("-" * 80)
        transactions_4000 = await check_account_transactions(db, "4000", society_id)
        print(f"   Found {len(transactions_4000)} transactions")
        
        for txn in transactions_4000[:10]:  # Show first 10
            print(f"   - ID: {txn.id}, Date: {txn.date}, "
                  f"Desc: {txn.description[:50]}, "
                  f"Debit: Rs.{txn.debit_amount or 0}, "
                  f"Credit: Rs.{txn.credit_amount or 0}, "
                  f"JV: {txn.journal_entry.entry_number if txn.journal_entry else 'N/A'}")
        
        if len(transactions_4000) > 10:
            print(f"   ... and {len(transactions_4000) - 10} more transactions")
        
        # 2. Check account 4010 (Water Charges)
        print()
        print("2. Checking Account 4010 (Water Charges)...")
        print("-" * 80)
        transactions_4010 = await check_account_transactions(db, "4010", society_id)
        print(f"   Found {len(transactions_4010)} transactions")
        
        for txn in transactions_4010[:10]:  # Show first 10
            print(f"   - ID: {txn.id}, Date: {txn.date}, "
                  f"Desc: {txn.description[:50]}, "
                  f"Debit: Rs.{txn.debit_amount or 0}, "
                  f"Credit: Rs.{txn.credit_amount or 0}, "
                  f"JV: {txn.journal_entry.entry_number if txn.journal_entry else 'N/A'}")
        
        if len(transactions_4010) > 10:
            print(f"   ... and {len(transactions_4010) - 10} more transactions")
        
        # 3. Check for maintenance bill postings in 4010 (these should not exist)
        print()
        print("3. Checking for incorrect postings to 4010 from maintenance bills...")
        print("-" * 80)
        incorrect_4010 = [
            txn for txn in transactions_4010 
            if 'maintenance' in txn.description.lower() or 
               'bill' in txn.description.lower() or
               'month' in txn.description.lower()
        ]
        
        print(f"   Found {len(incorrect_4010)} potentially incorrect transactions in 4010")
        for txn in incorrect_4010:
            print(f"   - ID: {txn.id}, Date: {txn.date}, "
                  f"Desc: {txn.description}, "
                  f"Credit: Rs.{txn.credit_amount or 0}")
        
        # 4. Fix account balances
        print()
        print("4. Fixing account balances...")
        print("-" * 80)
        
        account_4000_info = await fix_account_balance(db, "4000", society_id)
        if account_4000_info:
            print(f"   Account 4000 ({account_4000_info['account_name']}):")
            print(f"      Old Balance: Rs.{account_4000_info['old_balance']:,.2f}")
            print(f"      Correct Balance: Rs.{account_4000_info['correct_balance']:,.2f}")
            print(f"      Difference: Rs.{account_4000_info['difference']:,.2f}")
            print(f"      Total Debit: Rs.{account_4000_info['total_debit']:,.2f}")
            print(f"      Total Credit: Rs.{account_4000_info['total_credit']:,.2f}")
        
        account_4010_info = await fix_account_balance(db, "4010", society_id)
        if account_4010_info:
            print(f"   Account 4010 ({account_4010_info['account_name']}):")
            print(f"      Old Balance: Rs.{account_4010_info['old_balance']:,.2f}")
            print(f"      Correct Balance: Rs.{account_4010_info['correct_balance']:,.2f}")
            print(f"      Difference: Rs.{account_4010_info['difference']:,.2f}")
            print(f"      Total Debit: Rs.{account_4010_info['total_debit']:,.2f}")
            print(f"      Total Credit: Rs.{account_4010_info['total_credit']:,.2f}")
        
        # 5. Recommendation
        print()
        print("=" * 80)
        print("RECOMMENDATION:")
        print("=" * 80)
        
        if len(incorrect_4010) > 0:
            print(f"Found {len(incorrect_4010)} incorrect transactions in account 4010.")
            print("These transactions should be reversed or deleted because:")
            print("  - Maintenance bills should ONLY post to account 4000")
            print("  - Water charges are part of maintenance charges, not a separate income")
            print()
            print("OPTION 1: Delete incorrect transactions (if unposted)")
            print("OPTION 2: Create reversal journal entries (if posted)")
            print()
            response = input("Do you want to delete incorrect 4010 transactions? (yes/no): ")
            if response.lower() == 'yes':
                deleted_count = 0
                for txn in incorrect_4010:
                    # Check if transaction has a journal entry (means it's posted)
                    if txn.journal_entry_id:
                        print(f"   Transaction {txn.id} has journal entry - cannot delete, need reversal")
                    else:
                        await db.delete(txn)
                        deleted_count += 1
                        print(f"   Deleted transaction {txn.id}")
                
                if deleted_count > 0:
                    await db.commit()
                    print(f"   Deleted {deleted_count} transactions")
                    # Recalculate balances
                    print()
                    print("Recalculating balances after deletion...")
                    await fix_account_balance(db, "4010", society_id)
                    await db.commit()
            else:
                print("Skipping deletion. You can manually reverse these transactions.")
        else:
            print("No incorrect transactions found in account 4010.")
            print("Account balances have been recalculated based on existing transactions.")
        
        await db.commit()
        print()
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        if account_4000_info:
            print(f"Account 4000 (Maintenance Charges): Rs.{account_4000_info['correct_balance']:,.2f}")
        if account_4010_info:
            print(f"Account 4010 (Water Charges): Rs.{account_4010_info['correct_balance']:,.2f}")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
