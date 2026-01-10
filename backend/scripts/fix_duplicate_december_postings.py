"""
Script to fix duplicate December 2025 bill postings.
The old logic posted each flat's bill separately, creating 20 separate JV entries.
We need to delete these duplicates and keep only the correct total.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import AsyncSessionLocal
from app.models_db import Transaction, JournalEntry, MaintenanceBill, AccountCode
from sqlalchemy import select, and_, delete
from sqlalchemy.orm import selectinload
from decimal import Decimal
from datetime import date


async def main():
    async with AsyncSessionLocal() as db:
        print("=" * 80)
        print("FIXING DUPLICATE DECEMBER 2025 BILL POSTINGS")
        print("=" * 80)
        print()
        
        society_id = 1  # Default society_id
        
        # 1. Get actual bill total for December 2025
        bills_result = await db.execute(
            select(MaintenanceBill)
            .where(
                and_(
                    MaintenanceBill.society_id == society_id,
                    MaintenanceBill.month == 12,
                    MaintenanceBill.year == 2025,
                    MaintenanceBill.is_posted == True
                )
            )
        )
        posted_bills = bills_result.scalars().all()
        
        actual_bill_total = sum(Decimal(str(bill.amount)) for bill in posted_bills)
        
        print(f"1. Actual Posted Bills for December 2025:")
        print(f"   Number of bills: {len(posted_bills)}")
        print(f"   Total amount: Rs.{actual_bill_total:,.2f}")
        print()
        
        # 2. Find duplicate JV entries (JE-20251201-001 through JE-20251201-020)
        print("2. Finding duplicate journal entries...")
        print("-" * 80)
        
        duplicate_jv_numbers = [f"JE-20251201-{i:03d}" for i in range(1, 21)]
        
        jv_result = await db.execute(
            select(JournalEntry)
            .where(
                and_(
                    JournalEntry.society_id == society_id,
                    JournalEntry.entry_number.in_(duplicate_jv_numbers)
                )
            )
            .options(selectinload(JournalEntry.entries))
        )
        duplicate_jvs = jv_result.scalars().all()
        
        print(f"   Found {len(duplicate_jvs)} duplicate journal entries")
        
        total_to_delete = Decimal("0.00")
        transaction_ids_to_delete = []
        
        for jv in duplicate_jvs:
            print(f"   - {jv.entry_number}: {len(jv.entries)} transactions")
            for txn in jv.entries:
                if txn.credit_amount:
                    total_to_delete += Decimal(str(txn.credit_amount))
                    transaction_ids_to_delete.append(txn.id)
        
        print(f"   Total credit to be deleted: Rs.{total_to_delete:,.2f}")
        print()
        
        # 3. Confirm deletion
        print("3. Deleting duplicate transactions and journal entries...")
        print("-" * 80)
        
        # Delete transactions first (foreign key constraint)
        for txn_id in transaction_ids_to_delete:
            txn_result = await db.execute(
                select(Transaction).where(Transaction.id == txn_id)
            )
            txn = txn_result.scalar_one_or_none()
            if txn:
                await db.delete(txn)
                print(f"   Deleted transaction {txn_id}")
        
        # Delete journal entries
        for jv in duplicate_jvs:
            await db.delete(jv)
            print(f"   Deleted journal entry {jv.entry_number}")
        
        await db.commit()
        print()
        print(f"   Successfully deleted {len(transaction_ids_to_delete)} transactions and {len(duplicate_jvs)} journal entries")
        
        # 4. Recalculate account 4000 balance
        print()
        print("4. Recalculating account 4000 balance...")
        print("-" * 80)
        
        # Get all remaining transactions in account 4000
        remaining_result = await db.execute(
            select(Transaction)
            .where(
                and_(
                    Transaction.account_code == "4000",
                    Transaction.society_id == society_id
                )
            )
        )
        remaining_transactions = remaining_result.scalars().all()
        
        total_debit = Decimal("0.00")
        total_credit = Decimal("0.00")
        
        for txn in remaining_transactions:
            if txn.debit_amount:
                total_debit += Decimal(str(txn.debit_amount))
            if txn.credit_amount:
                total_credit += Decimal(str(txn.credit_amount))
        
        # Update account balance
        account_result = await db.execute(
            select(AccountCode).where(
                and_(
                    AccountCode.code == "4000",
                    AccountCode.society_id == society_id
                )
            )
        )
        account = account_result.scalar_one_or_none()
        
        if account:
            # For income accounts, balance = credit - debit
            correct_balance = total_credit - total_debit
            old_balance = Decimal(str(account.current_balance or 0.0))
            account.current_balance = float(correct_balance)
            db.add(account)
            await db.commit()
            
            print(f"   Account 4000 (Maintenance Charges):")
            print(f"      Transactions: {len(remaining_transactions)}")
            print(f"      Total Debit: Rs.{total_debit:,.2f}")
            print(f"      Total Credit: Rs.{total_credit:,.2f}")
            print(f"      Old Balance: Rs.{old_balance:,.2f}")
            print(f"      New Balance: Rs.{correct_balance:,.2f}")
            print(f"      Difference: Rs.{(correct_balance - old_balance):,.2f}")
        
        print()
        print("=" * 80)
        print("COMPLETE")
        print("=" * 80)
        print(f"Expected bill total: Rs.{actual_bill_total:,.2f}")
        print(f"Account 4000 balance after fix: Rs.{correct_balance:,.2f}")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
