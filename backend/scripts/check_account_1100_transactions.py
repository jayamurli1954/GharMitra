"""
Script to check account 1100 (Maintenance Dues Receivable) transactions.
This will help identify why the balance is incorrect.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import AsyncSessionLocal
from app.models_db import Transaction, JournalEntry, AccountCode
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from decimal import Decimal


async def main():
    async with AsyncSessionLocal() as db:
        print("=" * 80)
        print("CHECKING ACCOUNT 1100 (Maintenance Dues Receivable) TRANSACTIONS")
        print("=" * 80)
        print()
        
        society_id = 1  # Default society_id
        
        # 1. Get all transactions in account 1100
        result = await db.execute(
            select(Transaction)
            .where(
                and_(
                    Transaction.account_code == "1100",
                    Transaction.society_id == society_id
                )
            )
            .options(selectinload(Transaction.journal_entry))
            .order_by(Transaction.date.desc(), Transaction.created_at.desc())
        )
        transactions = result.scalars().all()
        
        print(f"Found {len(transactions)} transactions in account 1100")
        print()
        
        # 2. Group by date/month
        transactions_by_date = {}
        total_debit = Decimal("0.00")
        total_credit = Decimal("0.00")
        
        for txn in transactions:
            date_key = txn.date.strftime("%Y-%m-%d") if txn.date else "Unknown"
            if date_key not in transactions_by_date:
                transactions_by_date[date_key] = []
            transactions_by_date[date_key].append(txn)
            
            if txn.debit_amount:
                total_debit += Decimal(str(txn.debit_amount))
            if txn.credit_amount:
                total_credit += Decimal(str(txn.credit_amount))
        
        print("Transactions by Date:")
        print("-" * 80)
        for date_key in sorted(transactions_by_date.keys(), reverse=True):
            txns = transactions_by_date[date_key]
            date_total = sum(Decimal(str(txn.debit_amount or 0)) for txn in txns)
            print(f"  {date_key}: {len(txns)} transactions, Total: Rs.{date_total:,.2f}")
            
            # Show first few transactions for each date
            for txn in txns[:3]:
                jv_number = txn.journal_entry.entry_number if txn.journal_entry else "No JV"
                # Extract flat number from description if available
                flat_from_desc = "N/A"
                if txn.description and "Flat:" in txn.description:
                    try:
                        flat_part = txn.description.split("Flat:")[-1].strip().split()[0]
                        flat_from_desc = flat_part
                    except:
                        pass
                
                print(f"    - ID: {txn.id}, Flat: {flat_from_desc}, "
                      f"Debit: Rs.{txn.debit_amount or 0}, JV: {jv_number}")
            if len(txns) > 3:
                print(f"    ... and {len(txns) - 3} more")
            print()
        
        # 3. Check for duplicates (same date, same flat, same amount)
        print("Checking for duplicate transactions...")
        print("-" * 80)
        
        seen = {}
        duplicates = []
        
        for txn in transactions:
            # Extract flat number from description for comparison
            flat_from_desc = None
            if txn.description and "Flat:" in txn.description:
                try:
                    flat_part = txn.description.split("Flat:")[-1].strip().split()[0]
                    flat_from_desc = flat_part
                except:
                    pass
            
            # Use date, flat (from description), and amount as key
            key = (txn.date, flat_from_desc, float(txn.debit_amount or 0))
            if key in seen and key[0] and key[1] and key[2] > 0:  # Only check if all parts are present
                duplicates.append((seen[key], txn))
            else:
                seen[key] = txn
        
        if duplicates:
            print(f"Found {len(duplicates)} duplicate transaction pairs:")
            for txn1, txn2 in duplicates[:10]:  # Show first 10
                jv1 = txn1.journal_entry.entry_number if txn1.journal_entry else "No JV"
                jv2 = txn2.journal_entry.entry_number if txn2.journal_entry else "No JV"
                # Extract flat number from description
                flat_from_desc = "N/A"
                if txn1.description and "Flat:" in txn1.description:
                    try:
                        flat_part = txn1.description.split("Flat:")[-1].strip().split()[0]
                        flat_from_desc = flat_part
                    except:
                        pass
                
                print(f"  - Txn {txn1.id} (JV: {jv1}) and Txn {txn2.id} (JV: {jv2}): "
                      f"Date: {txn1.date}, Flat: {flat_from_desc}, "
                      f"Amount: Rs.{txn1.debit_amount or 0}")
            if len(duplicates) > 10:
                print(f"  ... and {len(duplicates) - 10} more duplicates")
        else:
            print("No duplicate transactions found")
        
        # 4. Check December 2025 transactions specifically
        print()
        print("Checking December 2025 transactions...")
        print("-" * 80)
        
        december_txns = [
            txn for txn in transactions
            if txn.date and txn.date.year == 2025 and txn.date.month == 12
        ]
        
        print(f"Found {len(december_txns)} transactions for December 2025")
        
        december_total = Decimal("0.00")
        december_by_jv = {}
        
        for txn in december_txns:
            if txn.debit_amount:
                december_total += Decimal(str(txn.debit_amount))
            
            jv_number = txn.journal_entry.entry_number if txn.journal_entry else "No JV"
            if jv_number not in december_by_jv:
                december_by_jv[jv_number] = []
            december_by_jv[jv_number].append(txn)
        
        print(f"Total December 2025 debit: Rs.{december_total:,.2f}")
        print()
        print("December 2025 transactions by Journal Entry:")
        for jv_number, txns in sorted(december_by_jv.items()):
            jv_total = sum(Decimal(str(txn.debit_amount or 0)) for txn in txns)
            print(f"  {jv_number}: {len(txns)} transactions, Total: Rs.{jv_total:,.2f}")
            
            # Check if this JV matches the duplicate JVs we deleted
            if jv_number in [f"JE-20251201-{i:03d}" for i in range(1, 21)]:
                print(f"    WARNING: This JV entry should have been deleted!")
        
        # 5. Get account balance
        print()
        print("Account Balance Information:")
        print("-" * 80)
        
        account_result = await db.execute(
            select(AccountCode).where(
                and_(
                    AccountCode.code == "1100",
                    AccountCode.society_id == society_id
                )
            )
        )
        account = account_result.scalar_one_or_none()
        
        if account:
            account_balance = Decimal(str(account.current_balance or 0.0))
            calculated_balance = total_debit - total_credit
            
            print(f"Account 1100 (Maintenance Dues Receivable):")
            print(f"  Current Balance (from account): Rs.{account_balance:,.2f}")
            print(f"  Calculated Balance (from transactions): Rs.{calculated_balance:,.2f}")
            print(f"  Total Debit: Rs.{total_debit:,.2f}")
            print(f"  Total Credit: Rs.{total_credit:,.2f}")
            print(f"  Difference: Rs.{(account_balance - calculated_balance):,.2f}")
            
            if abs(account_balance - calculated_balance) > Decimal("1.00"):
                print(f"  WARNING: Account balance does not match calculated balance!")
        
        print()
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
