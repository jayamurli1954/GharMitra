"""
Script to repost December 2025 bills correctly with one JV entry.
Since the bills were incorrectly posted 20 times, we need to unpost them and repost correctly.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, date

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import AsyncSessionLocal
from app.models_db import Transaction, JournalEntry, MaintenanceBill, AccountCode
from app.models_db import AccountType
from sqlalchemy import select, and_
from decimal import Decimal
from app.utils.document_numbering import generate_journal_entry_number


async def main():
    async with AsyncSessionLocal() as db:
        print("=" * 80)
        print("REPOSTING DECEMBER 2025 BILLS CORRECTLY")
        print("=" * 80)
        print()
        
        society_id = 1  # Default society_id
        
        # 1. Get all posted bills for December 2025
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
        
        print(f"1. Found {len(posted_bills)} posted bills for December 2025")
        
        # Calculate total amount (current charges only, excluding arrears)
        total_amount = sum(Decimal(str(bill.amount)) for bill in posted_bills)
        
        print(f"   Total billed amount: Rs.{total_amount:,.2f}")
        print()
        
        if len(posted_bills) == 0:
            print("No bills found to repost.")
            return
        
        # 2. Check if there's already a correct JV entry for December 2025
        jv_result = await db.execute(
            select(JournalEntry)
            .where(
                and_(
                    JournalEntry.society_id == society_id,
                    JournalEntry.date == date(2025, 12, 1),
                    JournalEntry.description.like('%Maintenance charges for the month December 2025%')
                )
            )
        )
        existing_jvs = jv_result.scalars().all()
        
        # Filter out the duplicate JVs we just deleted (they should be gone, but check)
        correct_jvs = [jv for jv in existing_jvs if jv.entry_number not in [f"JE-20251201-{i:03d}" for i in range(1, 21)]]
        
        if len(correct_jvs) > 0:
            print(f"2. Found {len(correct_jvs)} existing correct JV entry(ies)")
            print("   Skipping repost - bills are already correctly posted.")
            return
        
        # 3. Create correct JV entry for all bills
        print("2. Creating correct JV entry for all December 2025 bills...")
        print("-" * 80)
        
        # Generate JV number
        transaction_date = date(2025, 12, 1)
        jv_number = await generate_journal_entry_number(db, society_id, transaction_date)
        
        description = f"Maintenance charges for the month December 2025 (Posted)"
        
        # Create journal entry
        journal_entry = JournalEntry(
            society_id=society_id,
            entry_number=jv_number,
            date=transaction_date,
            description=description,
            total_debit=total_amount,
            total_credit=total_amount,
            is_balanced=True,
            added_by=1,  # Default user ID
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(journal_entry)
        await db.flush()  # Get journal_entry.id
        
        print(f"   Created journal entry: {jv_number}")
        
        # 4. Create transactions for account 1100 (per flat) and account 4000 (total)
        print()
        print("3. Creating transactions...")
        print("-" * 80)
        
        # Get or create accounts
        async def get_or_create_account(code, name, acct_type):
            account_result = await db.execute(
                select(AccountCode).where(
                    and_(
                        AccountCode.code == code,
                        AccountCode.society_id == society_id
                    )
                )
            )
            account = account_result.scalar_one_or_none()
            if not account:
                account = AccountCode(
                    society_id=society_id,
                    code=code,
                    name=name,
                    type=acct_type,
                    opening_balance=Decimal("0.00"),
                    current_balance=Decimal("0.00"),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(account)
                await db.flush()
            return account
        
        acct_ar = await get_or_create_account("1100", "Maintenance Dues Receivable", AccountType.ASSET)
        acct_4000 = await get_or_create_account("4000", "Maintenance Charges", AccountType.INCOME)
        
        # Aggregate bills by flat
        flat_totals = {}
        for bill in posted_bills:
            if bill.flat_id not in flat_totals:
                flat_totals[bill.flat_id] = {
                    'total': Decimal("0.00"),
                    'flat_number': bill.flat_number
                }
            flat_totals[bill.flat_id]['total'] += Decimal(str(bill.amount))
        
        # Create per-flat AR transactions (debit 1100)
        for flat_id, flat_data in flat_totals.items():
            flat_ar_amount = flat_data['total'].quantize(Decimal("0.01"))
            
            txn_ar = Transaction(
                society_id=society_id,
                document_number=None,  # No individual document number
                type="expense",  # For asset accounts
                category="Maintenance Bill",
                account_code="1100",
                amount=float(flat_ar_amount),
                description=f"{description} - Flat: {flat_data['flat_number']}",
                date=transaction_date,
                expense_month="December, 2025",
                added_by=1,
                debit_amount=float(flat_ar_amount),
                credit_amount=0.0,
                journal_entry_id=journal_entry.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(txn_ar)
            acct_ar.current_balance += flat_ar_amount
            
            print(f"   Created AR transaction for Flat {flat_data['flat_number']}: Rs.{flat_ar_amount:,.2f}")
        
        # Create income transaction (credit 4000)
        total_income = total_amount.quantize(Decimal("0.01"))
        txn_income = Transaction(
            society_id=society_id,
            document_number=None,  # No individual document number
            type="income",
            category="Maintenance Bill",
            account_code="4000",
            amount=float(total_income),
            description=description,
            date=transaction_date,
            expense_month="December, 2025",
            added_by=1,
            debit_amount=0.0,
            credit_amount=float(total_income),
            journal_entry_id=journal_entry.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(txn_income)
        acct_4000.current_balance -= total_income  # Credit increases income (negative balance)
        
        print(f"   Created income transaction for account 4000: Rs.{total_income:,.2f}")
        
        # 5. Commit all changes
        await db.commit()
        
        print()
        print("=" * 80)
        print("COMPLETE")
        print("=" * 80)
        print(f"Journal Entry: {jv_number}")
        print(f"Total Amount: Rs.{total_amount:,.2f}")
        print(f"Account 1100 Balance: Rs.{acct_ar.current_balance:,.2f}")
        print(f"Account 4000 Balance: Rs.{acct_4000.current_balance:,.2f}")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
