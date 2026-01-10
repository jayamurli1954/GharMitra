"""
Fix account balances by recalculating from transactions
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os
from decimal import Decimal

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./gharmitra.db")
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def fix_balances():
    """Recalculate and fix account balances"""
    async with async_session() as db:
        print("=" * 60)
        print("FIXING ACCOUNT BALANCES")
        print("=" * 60)
        
        # Get all account codes
        result = await db.execute(
            text("SELECT code, name, type, opening_balance, current_balance FROM account_codes")
        )
        accounts = result.fetchall()
        
        print(f"\nFound {len(accounts)} accounts")
        
        fixed_count = 0
        
        for account in accounts:
            account_code = account[0]
            account_name = account[1]
            account_type = account[2]
            opening_balance = Decimal(str(account[3] or 0))
            current_balance = Decimal(str(account[4] or 0))
            
            # Calculate balance from transactions
            result = await db.execute(
                text("""
                    SELECT 
                        SUM(debit_amount) as total_debit,
                        SUM(credit_amount) as total_credit
                    FROM transactions 
                    WHERE account_code = :code
                """),
                {"code": account_code}
            )
            calc_row = result.fetchone()
            
            if calc_row:
                total_debit = Decimal(str(calc_row[0] or 0))
                total_credit = Decimal(str(calc_row[1] or 0))
                
                # Match the actual balance update logic from transactions.py:
                # For expense: current_bal + transaction_amount (debit increases)
                # For income: current_bal - transaction_amount (credit increases, stored as negative)
                # For asset: current_bal + transaction_amount (debit increases)
                # For liability/capital: current_bal - transaction_amount (credit increases, stored as negative)
                
                # Recalculate from opening balance and all transactions
                calculated_balance = opening_balance
                
                # Get all transactions and apply them in order
                result = await db.execute(
                    text("""
                        SELECT debit_amount, credit_amount, type
                        FROM transactions 
                        WHERE account_code = :code
                        ORDER BY date, id
                    """),
                    {"code": account_code}
                )
                txns = result.fetchall()
                
                for txn in txns:
                    txn_debit = Decimal(str(txn[0] or 0))
                    txn_credit = Decimal(str(txn[1] or 0))
                    txn_type = txn[2]
                    
                    if account_type in ['asset', 'expense']:
                        # Debit increases, credit decreases
                        calculated_balance += txn_debit - txn_credit
                    else:  # liability, capital, income
                        # Credit increases (stored as negative), debit decreases
                        calculated_balance += txn_credit - txn_debit
                
                # Check if balance needs fixing
                if abs(calculated_balance - current_balance) > Decimal("0.01"):
                    print(f"\nFixing {account_code} - {account_name}:")
                    print(f"  Current balance: Rs.{current_balance}")
                    print(f"  Calculated balance: Rs.{calculated_balance}")
                    print(f"  Difference: Rs.{abs(calculated_balance - current_balance)}")
                    
                    # Update balance
                    await db.execute(
                        text("UPDATE account_codes SET current_balance = :balance WHERE code = :code"),
                        {"balance": float(calculated_balance), "code": account_code}
                    )
                    fixed_count += 1
        
        await db.commit()
        
        print(f"\n{'='*60}")
        print(f"Fixed {fixed_count} account balances")
        print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(fix_balances())
