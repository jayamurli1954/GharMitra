"""
Script to verify account 4000 balance matches actual posted bills.
This will help identify if there are duplicate postings or incorrect amounts.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import AsyncSessionLocal
from app.models_db import Transaction, MaintenanceBill
from sqlalchemy import select, and_, func
from decimal import Decimal


async def main():
    async with AsyncSessionLocal() as db:
        print("=" * 80)
        print("VERIFYING ACCOUNT 4000 BALANCE")
        print("=" * 80)
        print()
        
        society_id = 1  # Default society_id
        
        # 1. Get all posted bills
        print("1. Checking Posted Bills...")
        print("-" * 80)
        bills_result = await db.execute(
            select(MaintenanceBill)
            .where(
                and_(
                    MaintenanceBill.society_id == society_id,
                    MaintenanceBill.is_posted == True
                )
            )
        )
        posted_bills = bills_result.scalars().all()
        
        total_billed_amount = Decimal("0.00")
        bills_by_month = {}
        
        for bill in posted_bills:
            month_key = f"{bill.month}/{bill.year}"
            if month_key not in bills_by_month:
                bills_by_month[month_key] = Decimal("0.00")
            bills_by_month[month_key] += Decimal(str(bill.amount))  # Current charges only (excluding arrears)
            total_billed_amount += Decimal(str(bill.amount))
        
        print(f"   Total Posted Bills: {len(posted_bills)}")
        print(f"   Total Billed Amount (current charges): Rs.{total_billed_amount:,.2f}")
        print()
        print("   Bills by Month/Year:")
        for month, amount in sorted(bills_by_month.items()):
            print(f"      {month}: Rs.{amount:,.2f}")
        
        # 2. Get all transactions in account 4000
        print()
        print("2. Checking Account 4000 Transactions...")
        print("-" * 80)
        transactions_result = await db.execute(
            select(Transaction)
            .where(
                and_(
                    Transaction.account_code == "4000",
                    Transaction.society_id == society_id
                )
            )
            .order_by(Transaction.date)
        )
        transactions = transactions_result.scalars().all()
        
        total_credit = Decimal("0.00")
        total_debit = Decimal("0.00")
        
        transactions_by_month = {}
        
        for txn in transactions:
            if txn.credit_amount:
                total_credit += Decimal(str(txn.credit_amount))
                # Try to extract month from description or date
                month_key = f"{txn.date.month}/{txn.date.year}" if txn.date else "Unknown"
                if month_key not in transactions_by_month:
                    transactions_by_month[month_key] = Decimal("0.00")
                transactions_by_month[month_key] += Decimal(str(txn.credit_amount))
            if txn.debit_amount:
                total_debit += Decimal(str(txn.debit_amount))
        
        print(f"   Total Transactions: {len(transactions)}")
        print(f"   Total Credit: Rs.{total_credit:,.2f}")
        print(f"   Total Debit: Rs.{total_debit:,.2f}")
        print(f"   Net Balance (Credit - Debit): Rs.{(total_credit - total_debit):,.2f}")
        print()
        print("   Credits by Month/Year:")
        for month, amount in sorted(transactions_by_month.items()):
            print(f"      {month}: Rs.{amount:,.2f}")
        
        # 3. Compare
        print()
        print("3. Comparison...")
        print("-" * 80)
        difference = total_credit - total_billed_amount
        print(f"   Total Billed (from bills): Rs.{total_billed_amount:,.2f}")
        print(f"   Total Credited (from transactions): Rs.{total_credit:,.2f}")
        print(f"   Difference: Rs.{difference:,.2f}")
        
        if abs(difference) > Decimal("1.00"):  # Allow for rounding
            print()
            print("   WARNING: There is a significant difference!")
            print(f"   This suggests there may be:")
            print(f"      - Duplicate bill postings")
            print(f"      - Other income transactions in account 4000")
            print(f"      - Bill reversals that were not properly handled")
        else:
            print()
            print("   ✓ Account 4000 balance matches posted bills")
        
        print()
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
