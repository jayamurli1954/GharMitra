"""
Script to fix trial balance mismatch.
Check all accounts and verify their balances are correct.
Also check for any transactions that might be causing the mismatch.
"""

import asyncio
import sys
from pathlib import Path
from datetime import date
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import AsyncSessionLocal
from app.models_db import Transaction, AccountCode, FinancialYear
from sqlalchemy import select, and_, func
from collections import defaultdict


async def main():
    async with AsyncSessionLocal() as db:
        print("=" * 80)
        print("FIXING TRIAL BALANCE MISMATCH")
        print("=" * 80)
        print()
        
        society_id = 1  # Default society_id
        as_on_date = date(2026, 1, 10)
        
        # 1. Get or find financial year
        fy_result = await db.execute(
            select(FinancialYear)
            .where(
                and_(
                    FinancialYear.society_id == society_id,
                    FinancialYear.start_date <= as_on_date,
                    FinancialYear.end_date >= as_on_date
                )
            )
            .order_by(FinancialYear.start_date.desc())
        )
        financial_year = fy_result.scalars().first()
        
        if not financial_year:
            fy_result = await db.execute(
                select(FinancialYear)
                .where(
                    and_(
                        FinancialYear.society_id == society_id,
                        FinancialYear.is_active == True
                    )
                )
                .order_by(FinancialYear.start_date.desc())
            )
            financial_year = fy_result.scalars().first()
        
        if not financial_year:
            print("ERROR: No financial year found")
            return
        
        fy_start_date = financial_year.start_date
        effective_date = min(as_on_date, financial_year.end_date)
        
        print(f"Financial Year: {fy_start_date} to {financial_year.end_date}")
        print(f"Effective Date: {effective_date}")
        print()
        
        # 2. Get all accounts
        accounts_result = await db.execute(
            select(AccountCode)
            .where(AccountCode.society_id == society_id)
            .order_by(AccountCode.code)
        )
        accounts = accounts_result.scalars().all()
        
        print(f"Found {len(accounts)} accounts")
        print()
        
        # 3. Recalculate all account balances from transactions
        print("3. Recalculating account balances from transactions...")
        print("-" * 80)
        
        total_debit = Decimal("0.00")
        total_credit = Decimal("0.00")
        
        account_balances = {}
        
        for account in accounts:
            # Get all transactions for this account from FY start to as_on_date
            txn_result = await db.execute(
                select(Transaction)
                .where(
                    and_(
                        Transaction.society_id == society_id,
                        Transaction.account_code == account.code,
                        Transaction.date >= fy_start_date,
                        Transaction.date <= effective_date
                    )
                )
            )
            transactions = txn_result.scalars().all()
            
            # Calculate balance from transactions
            account_debit = Decimal("0.00")
            account_credit = Decimal("0.00")
            
            for txn in transactions:
                if txn.debit_amount:
                    account_debit += Decimal(str(txn.debit_amount))
                if txn.credit_amount:
                    account_credit += Decimal(str(txn.credit_amount))
            
            # Calculate net balance based on account type
            if account.type.value in ['asset', 'expense']:
                # Asset/Expense: Debit increases, Credit decreases
                net_balance = account_debit - account_credit
            else:
                # Liability/Capital/Income: Credit increases, Debit decreases
                # Store as negative for credit balance
                net_balance = account_credit - account_debit
                # For income accounts, make it negative (credit balance)
                if account.type.value == 'income':
                    net_balance = -net_balance
            
            # Update account balance
            old_balance = Decimal(str(account.current_balance or 0.0))
            account.current_balance = float(net_balance)
            db.add(account)
            
            # For trial balance calculation
            if abs(net_balance) >= Decimal("0.01"):
                account_balances[account.code] = {
                    'account': account,
                    'balance': net_balance,
                    'debit_total': account_debit,
                    'credit_total': account_credit,
                    'transaction_count': len(transactions)
                }
                
                # Calculate trial balance totals
                if account.type.value in ['asset', 'expense']:
                    if net_balance > 0:
                        total_debit += net_balance
                    else:
                        total_credit += abs(net_balance)
                else:  # liability, capital, income
                    if net_balance < 0:
                        # Credit balance (negative), display as positive credit
                        total_credit += abs(net_balance)
                    else:
                        # Debit balance (abnormal), display as debit
                        total_debit += net_balance
        
        # 4. Show key accounts
        print("Key Accounts:")
        print("-" * 80)
        for code in ['1100', '4000', '4010']:
            if code in account_balances:
                info = account_balances[code]
                acct = info['account']
                bal = info['balance']
                
                if acct.type.value == 'income':
                    # For income, display as positive credit in trial balance
                    display_credit = abs(bal) if bal < 0 else 0
                    display_debit = bal if bal > 0 else 0
                elif acct.type.value in ['asset', 'expense']:
                    display_debit = bal if bal > 0 else 0
                    display_credit = abs(bal) if bal < 0 else 0
                else:
                    display_debit = bal if bal > 0 else 0
                    display_credit = abs(bal) if bal < 0 else 0
                
                print(f"  {code} ({acct.name}):")
                print(f"    Balance: Rs.{bal:,.2f}")
                print(f"    TB Debit: Rs.{display_debit:,.2f}")
                print(f"    TB Credit: Rs.{display_credit:,.2f}")
                print(f"    Transactions: {info['transaction_count']}")
                print()
        
        await db.commit()
        
        difference = abs(total_debit - total_credit)
        is_balanced = difference < Decimal("1.00")  # Allow for rounding
        
        print("=" * 80)
        print("TRIAL BALANCE SUMMARY")
        print("=" * 80)
        print(f"Total Debit: Rs.{total_debit:,.2f}")
        print(f"Total Credit: Rs.{total_credit:,.2f}")
        print(f"Difference: Rs.{difference:,.2f}")
        print(f"Status: {'Balanced' if is_balanced else 'Not Balanced'}")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
