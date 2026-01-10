#!/usr/bin/env python3
"""
Migration: Apply Existing Transaction Balance Updates
- Recalculate and update account balances based on existing transactions
- This fixes any transactions created before the balance update logic was working properly
"""
import sys
import os
import asyncio
import logging

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import AsyncSessionLocal
from app.models_db import Transaction, AccountCode
from sqlalchemy import select

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate():
    """Recalculate account balances from all transactions"""
    async with AsyncSessionLocal() as db:
        try:
            logger.info("Starting transaction balance recalculation migration...")
            
            # Get all accounts
            result = await db.execute(select(AccountCode))
            accounts = result.scalars().all()
            
            # Reset all current balances to opening balances
            for account in accounts:
                account.current_balance = account.opening_balance or 0.0
                db.add(account)
            
            logger.info(f"✓ Reset {len(accounts)} account balances to opening balances")
            
            # Get all transactions ordered by date
            result = await db.execute(
                select(Transaction).order_by(Transaction.date, Transaction.id)
            )
            transactions = result.scalars().all()
            
            logger.info(f"Processing {len(transactions)} transactions...")
            
            # Process each transaction and update account balances
            for txn in transactions:
                # Get transaction type as string
                txn_type = txn.type.value if hasattr(txn.type, 'value') else str(txn.type)
                
                # Update cash/bank account balance
                if txn.payment_method == 'cash':
                    cash_result = await db.execute(
                        select(AccountCode).where(
                            AccountCode.code == '1010',
                            AccountCode.society_id == txn.society_id
                        )
                    )
                    cash_account = cash_result.scalar_one_or_none()
                    if cash_account:
                        if txn_type == 'expense':
                            cash_account.current_balance -= txn.amount
                        else:  # income
                            cash_account.current_balance += txn.amount
                        db.add(cash_account)
                
                elif txn.payment_method == 'bank':
                    bank_result = await db.execute(
                        select(AccountCode).where(
                            AccountCode.code == '1000',
                            AccountCode.society_id == txn.society_id
                        )
                    )
                    bank_account = bank_result.scalar_one_or_none()
                    if bank_account:
                        if txn_type == 'expense':
                            bank_account.current_balance -= txn.amount
                        else:  # income
                            bank_account.current_balance += txn.amount
                        db.add(bank_account)
                
                # Update expense/income account balance
                if txn.account_code:
                    account_result = await db.execute(
                        select(AccountCode).where(
                            AccountCode.code == txn.account_code,
                            AccountCode.society_id == txn.society_id
                        )
                    )
                    account = account_result.scalar_one_or_none()
                    if account:
                        if txn_type == 'expense':
                            # Debit increases expense
                            account.current_balance += txn.amount
                        else:  # income
                            # Credit increases income (negative balance)
                            account.current_balance -= txn.amount
                        db.add(account)
                
                logger.info(f"✓ Processed transaction ID {txn.id}: {txn_type} {txn.amount} ({txn.payment_method})")
            
            await db.commit()
            logger.info(f"✅ Migration completed successfully! Processed {len(transactions)} transactions")
                
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    logger.info("=== Apply Existing Transaction Balances Migration ===")
    asyncio.run(migrate())
    logger.info("=== Migration Complete ===")




