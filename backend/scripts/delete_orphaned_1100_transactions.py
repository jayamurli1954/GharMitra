"""
Script to delete orphaned AR transactions (account 1100) from December 2025
that have no journal_entry_id. These are from the duplicate bill postings we deleted.
"""

import asyncio
import sys
from pathlib import Path
from datetime import date

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import AsyncSessionLocal
from app.models_db import Transaction, AccountCode
from sqlalchemy import select, and_
from decimal import Decimal


async def main():
    async with AsyncSessionLocal() as db:
        print("=" * 80)
        print("DELETING ORPHANED ACCOUNT 1100 TRANSACTIONS")
        print("=" * 80)
        print()
        
        society_id = 1  # Default society_id
        
        # Find all AR transactions for December 2025 that have no journal_entry_id
        result = await db.execute(
            select(Transaction)
            .where(
                and_(
                    Transaction.account_code == "1100",
                    Transaction.society_id == society_id,
                    Transaction.date >= date(2025, 12, 1),
                    Transaction.date <= date(2025, 12, 31),
                    Transaction.journal_entry_id == None  # No journal entry (orphaned)
                )
            )
            .order_by(Transaction.date, Transaction.created_at)
        )
        orphaned_txns = result.scalars().all()
        
        print(f"Found {len(orphaned_txns)} orphaned AR transactions (no journal_entry_id)")
        print()
        
        if len(orphaned_txns) == 0:
            print("No orphaned transactions found.")
            return
        
        total_to_delete = Decimal("0.00")
        
        print("Orphaned transactions to delete:")
        print("-" * 80)
        for txn in orphaned_txns:
            if txn.debit_amount:
                total_to_delete += Decimal(str(txn.debit_amount))
            
            # Extract flat from description
            flat_from_desc = "N/A"
            if txn.description and "Flat:" in txn.description:
                try:
                    flat_part = txn.description.split("Flat:")[-1].strip().split()[0]
                    flat_from_desc = flat_part
                except:
                    pass
            
            print(f"  - ID: {txn.id}, Date: {txn.date}, Flat: {flat_from_desc}, "
                  f"Debit: Rs.{txn.debit_amount or 0}, "
                  f"Desc: {txn.description[:60]}")
        
        print()
        print(f"Total debit amount to be deleted: Rs.{total_to_delete:,.2f}")
        print()
        
        # Delete transactions
        print("Deleting orphaned transactions...")
        for txn in orphaned_txns:
            await db.delete(txn)
            print(f"  Deleted transaction {txn.id}")
        
        await db.commit()
        print()
        print(f"Successfully deleted {len(orphaned_txns)} orphaned transactions")
        
        # Recalculate account 1100 balance
        print()
        print("Recalculating account 1100 balance...")
        print("-" * 80)
        
        remaining_result = await db.execute(
            select(Transaction)
            .where(
                and_(
                    Transaction.account_code == "1100",
                    Transaction.society_id == society_id
                )
            )
        )
        remaining_txns = remaining_result.scalars().all()
        
        total_debit = Decimal("0.00")
        total_credit = Decimal("0.00")
        
        for txn in remaining_txns:
            if txn.debit_amount:
                total_debit += Decimal(str(txn.debit_amount))
            if txn.credit_amount:
                total_credit += Decimal(str(txn.credit_amount))
        
        # Update account balance
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
            # For asset accounts, balance = debit - credit
            correct_balance = total_debit - total_credit
            old_balance = Decimal(str(account.current_balance or 0.0))
            account.current_balance = float(correct_balance)
            db.add(account)
            await db.commit()
            
            print(f"Account 1100 (Maintenance Dues Receivable):")
            print(f"  Old Balance: Rs.{old_balance:,.2f}")
            print(f"  New Balance: Rs.{correct_balance:,.2f}")
            print(f"  Difference: Rs.{(correct_balance - old_balance):,.2f}")
            print(f"  Total Debit: Rs.{total_debit:,.2f}")
            print(f"  Total Credit: Rs.{total_credit:,.2f}")
            print(f"  Remaining Transactions: {len(remaining_txns)}")
        
        print()
        print("=" * 80)
        print("COMPLETE")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
