"""
Script to check for duplicate bill postings in account 4000 for December 2025.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import AsyncSessionLocal
from app.models_db import Transaction, JournalEntry
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from decimal import Decimal
from datetime import date


async def main():
    async with AsyncSessionLocal() as db:
        print("=" * 80)
        print("CHECKING FOR DUPLICATE DECEMBER 2025 POSTINGS IN ACCOUNT 4000")
        print("=" * 80)
        print()
        
        society_id = 1  # Default society_id
        
        # Get all transactions in account 4000 for December 2025
        result = await db.execute(
            select(Transaction)
            .where(
                and_(
                    Transaction.account_code == "4000",
                    Transaction.society_id == society_id,
                    Transaction.date >= date(2025, 12, 1),
                    Transaction.date <= date(2025, 12, 31)
                )
            )
            .options(selectinload(Transaction.journal_entry))
            .order_by(Transaction.date, Transaction.created_at)
        )
        transactions = result.scalars().all()
        
        print(f"Found {len(transactions)} transactions in account 4000 for December 2025")
        print()
        
        total_credit = Decimal("0.00")
        journal_entries = {}
        
        for txn in transactions:
            if txn.credit_amount:
                total_credit += Decimal(str(txn.credit_amount))
                jv_number = txn.journal_entry.entry_number if txn.journal_entry else "No JV"
                
                print(f"  Transaction ID: {txn.id}")
                print(f"    Date: {txn.date}")
                print(f"    Description: {txn.description[:80]}")
                print(f"    Credit: Rs.{txn.credit_amount:,.2f}")
                print(f"    Journal Entry: {jv_number}")
                print(f"    Created At: {txn.created_at}")
                print()
                
                # Group by journal entry
                if jv_number not in journal_entries:
                    journal_entries[jv_number] = []
                journal_entries[jv_number].append(txn)
        
        print("-" * 80)
        print(f"Total Credit Amount: Rs.{total_credit:,.2f}")
        print(f"Number of Journal Entries: {len(journal_entries)}")
        print()
        
        # Check for duplicates (multiple transactions with same JV number)
        print("Journal Entries Summary:")
        print("-" * 80)
        for jv_number, txns in journal_entries.items():
            total_for_jv = sum(Decimal(str(txn.credit_amount or 0)) for txn in txns)
            print(f"  {jv_number}: {len(txns)} transaction(s), Total: Rs.{total_for_jv:,.2f}")
            if len(txns) > 1:
                print(f"    WARNING: Multiple transactions in same JV entry!")
                for txn in txns:
                    print(f"      - Txn ID {txn.id}: Rs.{txn.credit_amount:,.2f} - {txn.description[:50]}")
        
        print()
        print("=" * 80)
        print("Expected Bill Amount for December 2025: Rs.71,348.00")
        print(f"Actual Total Credit: Rs.{total_credit:,.2f}")
        print(f"Difference: Rs.{(total_credit - Decimal('71348.00')):,.2f}")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
