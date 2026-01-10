
import asyncio
from datetime import date, datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models_db import AccountCode, Transaction, User
from app.routes.transactions import generate_transaction_document_number

# Mock Request Data
class TransactionCreate(BaseModel):
    type: Literal["income", "expense"]
    category: str
    amount: Optional[float] = None
    description: str
    date: str
    account_code: Optional[str] = None
    payment_method: str
    quantity: Optional[float] = None
    unit_price: Optional[float] = None

async def simulate_transaction_creation():
    async with AsyncSessionLocal() as session:
        print("Simulating Cash Transaction Creation...")
        
        # User Context
        result = await session.execute(select(User).where(User.id == 1))
        current_user = result.scalar_one()
        society_id = current_user.society_id
        
        # Payload (simulating user input)
        # Assuming account_code IS provided (e.g. diesel) or MAYBE NOT?
        # Let's try WITHOUT first, as that mimics a potential frontend bug where it's not sent.
        # But wait, frontend requires it.
        # Let's try WITH a valid expense code first.
        # I need to find an expense code.
        result = await session.execute(select(AccountCode).where(AccountCode.type == 'expense'))
        expense_acc = result.scalars().first()
        if not expense_acc:
            print("No expense account found to test with.")
            # Create one?
            expense_code = "5999"
        else:
            expense_code = expense_acc.code
            print(f"Using Expense Account: {expense_code} ({expense_acc.name})")

        transaction_data = TransactionCreate(
            type='expense',
            category='Generator Expenses',
            amount=2000.0,
            description='Diesel purchased for Generator cash paid',
            date='2026-01-04',
            account_code=expense_code,
            payment_method='cash',
            # quantity/unit_price are None
        )
        
        # --- Logic from transactions.py ---
        
        # 1. Parse Date
        # (Assuming Pydantic handled it, passing date object)
        txn_date = date(2026, 1, 4)
        
        # 2. Amounts
        debit_amount = 0.0
        credit_amount = 0.0
        
        # Account Lookup
        result = await session.execute(select(AccountCode).where(AccountCode.code == transaction_data.account_code))
        account = result.scalar_one_or_none()
        
        if account:
            if account.type == 'expense':
                debit_amount = transaction_data.amount
            else:
                 # .. logic ..
                 debit_amount = transaction_data.amount
        
        # 3. Second Leg (Cash)
        second_account_code = None
        second_debit_amount = 0.0
        second_credit_amount = 0.0
        
        if transaction_data.payment_method == 'cash':
            second_account_code = '1010'
            second_credit_amount = transaction_data.amount
            
        print(f"Second Account (Cash): {second_account_code}")
        
        # 4. Verify Second Account Exists
        # THIS IS WHERE I SUSPECT IT MIGHT FAIL IF 1010 IS MISSING
        result = await session.execute(select(AccountCode).where(AccountCode.code == second_account_code))
        second_account = result.scalar_one_or_none()
        
        if not second_account:
            print(f"ERROR: Account code {second_account_code} not found! This would raise 400.")
        else:
            print(f"Second Account Found: {second_account.name}")

        # 5. Generate Doc Numbers
        try:
             doc1 = await generate_transaction_document_number(session, society_id, txn_date, 'cash')
             doc2 = await generate_transaction_document_number(session, society_id, txn_date, 'cash', offset=1)
             print(f"Generated Docs: {doc1}, {doc2}")
        except Exception as e:
            print(f"ERROR generating doc numbers: {e}")
            return

        # 6. Create Objects
        try:
            new_transaction = Transaction(
                society_id=society_id,
                document_number=doc1,
                type=transaction_data.type,
                category=transaction_data.category,
                description=transaction_data.description,
                amount=transaction_data.amount,
                date=txn_date,
                account_code=transaction_data.account_code,
                debit_amount=debit_amount,
                credit_amount=credit_amount,
                payment_method=transaction_data.payment_method,
                added_by=current_user.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            second_transaction = Transaction(
                society_id=society_id,
                document_number=doc2,
                type=transaction_data.type,
                category=transaction_data.category,
                description=f"{transaction_data.description} (Cash Payment)",
                amount=transaction_data.amount,
                date=txn_date,
                account_code=second_account_code, # 1010
                debit_amount=second_debit_amount,
                credit_amount=second_credit_amount,
                payment_method=transaction_data.payment_method,
                added_by=current_user.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            session.add(new_transaction)
            session.add(second_transaction)
            
            # 7. Commit
            # This is the real test
            print("Attempting to commit...")
            await session.commit()
            print("Commit Successful!")
            
        except Exception as e:
            print(f"CRITICAL ERROR during commit: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(simulate_transaction_creation())
