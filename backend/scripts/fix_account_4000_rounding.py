"""
Script to fix account 4000 (Maintenance Charges) rounding issue.
The balance should be rounded to whole rupees for display.
Also verify that trial balance matches.
"""

import asyncio
import sys
from pathlib import Path
import math

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import AsyncSessionLocal
from app.models_db import Transaction, AccountCode
from sqlalchemy import select, and_, func
from decimal import Decimal


async def main():
    async with AsyncSessionLocal() as db:
        print("=" * 80)
        print("FIXING ACCOUNT 4000 ROUNDING AND VERIFYING TRIAL BALANCE")
        print("=" * 80)
        print()
        
        society_id = 1  # Default society_id
        
        # 1. Recalculate account 4000 balance
        print("1. Recalculating Account 4000 (Maintenance Charges)...")
        print("-" * 80)
        
        result = await db.execute(
            select(Transaction)
            .where(
                and_(
                    Transaction.account_code == "4000",
                    Transaction.society_id == society_id
                )
            )
        )
        transactions = result.scalars().all()
        
        total_debit = Decimal("0.00")
        total_credit = Decimal("0.00")
        
        for txn in transactions:
            if txn.debit_amount:
                total_debit += Decimal(str(txn.debit_amount))
            if txn.credit_amount:
                total_credit += Decimal(str(txn.credit_amount))
        
        # For income accounts, balance = credit - debit
        calculated_balance = total_credit - total_debit
        
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
            old_balance = Decimal(str(account.current_balance or 0.0))
            # Round to nearest whole rupee using ceil (round up to next rupee)
            # For income accounts, balance should be negative (credit balance)
            # We round the absolute value first, then apply the sign
            abs_balance = abs(calculated_balance)
            rounded_abs = Decimal(str(math.ceil(float(abs_balance))))
            # Income accounts have credit balance (negative), so make it negative
            rounded_balance = -rounded_abs
            
            account.current_balance = float(rounded_balance)
            db.add(account)
            
            print(f"   Account 4000 (Maintenance Charges):")
            print(f"      Calculated Balance: Rs.{calculated_balance:,.2f}")
            print(f"      Rounded Balance (rounded up): Rs.{rounded_balance:,.2f}")
            print(f"      Old Balance: Rs.{old_balance:,.2f}")
            print(f"      New Balance: Rs.{rounded_balance:,.2f}")
            
            print(f"   Account 4000 (Maintenance Charges):")
            print(f"      Transactions: {len(transactions)}")
            print(f"      Total Debit: Rs.{total_debit:,.2f}")
            print(f"      Total Credit: Rs.{total_credit:,.2f}")
            print(f"      Calculated Balance: Rs.{calculated_balance:,.2f}")
            print(f"      Rounded Balance: Rs.{rounded_balance:,.2f}")
            print(f"      Old Balance: Rs.{old_balance:,.2f}")
            print(f"      New Balance: Rs.{rounded_balance:,.2f}")
        
        # 2. Recalculate account 1100 balance (should already be correct, but verify)
        print()
        print("2. Verifying Account 1100 (Maintenance Dues Receivable)...")
        print("-" * 80)
        
        result_1100 = await db.execute(
            select(Transaction)
            .where(
                and_(
                    Transaction.account_code == "1100",
                    Transaction.society_id == society_id
                )
            )
        )
        transactions_1100 = result_1100.scalars().all()
        
        total_debit_1100 = Decimal("0.00")
        total_credit_1100 = Decimal("0.00")
        
        for txn in transactions_1100:
            if txn.debit_amount:
                total_debit_1100 += Decimal(str(txn.debit_amount))
            if txn.credit_amount:
                total_credit_1100 += Decimal(str(txn.credit_amount))
        
        calculated_balance_1100 = total_debit_1100 - total_credit_1100
        
        account_result_1100 = await db.execute(
            select(AccountCode).where(
                and_(
                    AccountCode.code == "1100",
                    AccountCode.society_id == society_id
                )
            )
        )
        account_1100 = account_result_1100.scalar_one_or_none()
        
        if account_1100:
            old_balance_1100 = Decimal(str(account_1100.current_balance or 0.0))
            account_1100.current_balance = float(calculated_balance_1100)
            db.add(account_1100)
            
            print(f"   Account 1100 (Maintenance Dues Receivable):")
            print(f"      Transactions: {len(transactions_1100)}")
            print(f"      Total Debit: Rs.{total_debit_1100:,.2f}")
            print(f"      Total Credit: Rs.{total_credit_1100:,.2f}")
            print(f"      Calculated Balance: Rs.{calculated_balance_1100:,.2f}")
            print(f"      Old Balance: Rs.{old_balance_1100:,.2f}")
            print(f"      New Balance: Rs.{calculated_balance_1100:,.2f}")
        
        # 3. Verify trial balance
        print()
        print("3. Verifying Trial Balance...")
        print("-" * 80)
        
        # Get all accounts
        all_accounts_result = await db.execute(
            select(AccountCode).where(AccountCode.society_id == society_id)
        )
        all_accounts = all_accounts_result.scalars().all()
        
        total_debit_tb = Decimal("0.00")
        total_credit_tb = Decimal("0.00")
        
        for acct in all_accounts:
            balance = Decimal(str(acct.current_balance or 0.0))
            
            if acct.type.value in ['asset', 'expense']:
                # Assets and Expenses: Debit balance (positive)
                if balance > 0:
                    total_debit_tb += balance
                else:
                    total_credit_tb += abs(balance)  # Negative balance means credit
            else:
                # Liabilities, Capital, Income: Credit balance (negative means debit)
                if balance < 0:
                    total_debit_tb += abs(balance)
                else:
                    total_credit_tb += balance
        
        difference = total_debit_tb - total_credit_tb
        
        print(f"   Total Debit: Rs.{total_debit_tb:,.2f}")
        print(f"   Total Credit: Rs.{total_credit_tb:,.2f}")
        print(f"   Difference: Rs.{difference:,.2f}")
        
        if abs(difference) <= Decimal("1.00"):  # Allow for rounding
            print(f"   Status: Balanced")
        else:
            print(f"   Status: Not Balanced (Difference: Rs.{difference:,.2f})")
        
        await db.commit()
        
        print()
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Account 4000 (Maintenance Charges): Rs.{rounded_balance:,.2f} (rounded)")
        print(f"Account 1100 (Maintenance Dues Receivable): Rs.{calculated_balance_1100:,.2f}")
        print(f"Trial Balance: Debit Rs.{total_debit_tb:,.2f}, Credit Rs.{total_credit_tb:,.2f}")
        if abs(difference) <= Decimal("1.00"):
            print(f"Status: Balanced")
        else:
            print(f"Status: Not Balanced (Difference: Rs.{difference:,.2f})")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
