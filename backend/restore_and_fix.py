
import asyncio
from datetime import date, datetime
from sqlalchemy import select, func
from app.database import AsyncSessionLocal
from app.models_db import Transaction, AccountCode
from app.utils.document_numbering import generate_transaction_document_number

async def restore_transactions():
    async with AsyncSessionLocal() as session:
        print("Starting restoration and balance correction...")
        society_id = 1
        txn_date = date(2026, 1, 4)
        
        # --- 1. Restore Corpus Fund Transaction (100,000) ---
        # Leg 1: Credit Corpus Fund (3010)
        # Leg 2: Debit Bank (1001)
        
        # Doc numbers
        doc_num_1 = await generate_transaction_document_number(session, society_id, txn_date, 'bank', offset=10)
        doc_num_2 = await generate_transaction_document_number(session, society_id, txn_date, 'bank', offset=11)
        
        txn_corpus = Transaction(
            society_id=society_id,
            document_number=doc_num_1,
            type='income',
            category='Corpus Fund',
            description='Online Bank Transfer (Restored)',
            amount=100000.0,
            date=txn_date,
            account_code='3010',
            debit_amount=0.0,
            credit_amount=100000.0,
            payment_method='bank',
            added_by=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        txn_bank = Transaction(
            society_id=society_id,
            document_number=doc_num_2,
            type='income',
            category='Corpus Fund',
            description='Online Bank Transfer (Restored) (Bank Receipt)',
            amount=100000.0,
            date=txn_date,
            account_code='1001',
            debit_amount=100000.0,
            credit_amount=0.0,
            payment_method='bank',
            added_by=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        session.add(txn_corpus)
        session.add(txn_bank)
        
        # Update Balances
        # 3010 Corpus: Credit increases (more negative)
        acc_3010 = (await session.execute(select(AccountCode).where(AccountCode.code == '3010'))).scalar_one()
        acc_3010.current_balance -= 100000.0
        
        # 1001 Bank: Debit increases (more positive)
        acc_1001 = (await session.execute(select(AccountCode).where(AccountCode.code == '1001'))).scalar_one()
        acc_1001.current_balance += 100000.0
        
        print(f"Restoring Corpus Fund: 3010 Balance -> {acc_3010.current_balance}, 1001 Balance -> {acc_1001.current_balance}")


        # --- 2. Restore Emergency Fund Transaction (5,000) ---
        # Leg 1: Credit Emergency Fund (3020)
        # Leg 2: Debit Cash (1010)
        
        doc_num_3 = await generate_transaction_document_number(session, society_id, txn_date, 'cash', offset=12)
        doc_num_4 = await generate_transaction_document_number(session, society_id, txn_date, 'cash', offset=13)
        
        txn_emergency = Transaction(
            society_id=society_id,
            document_number=doc_num_3,
            type='income',
            category='Emergency Fund',
            description='Cash (Restored)',
            amount=5000.0,
            date=txn_date,
            account_code='3020',
            debit_amount=0.0,
            credit_amount=5000.0,
            payment_method='cash',
            added_by=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        txn_cash = Transaction(
            society_id=society_id,
            document_number=doc_num_4,
            type='income',
            category='Emergency Fund',
            description='Cash (Restored) (Cash Receipt)',
            amount=5000.0,
            date=txn_date,
            account_code='1010',
            debit_amount=5000.0,
            credit_amount=0.0,
            payment_method='cash',
            added_by=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        session.add(txn_emergency)
        session.add(txn_cash)
        
        # Update Balances
        # 3020 Emergency: Credit increases (more negative)
        acc_3020 = (await session.execute(select(AccountCode).where(AccountCode.code == '3020'))).scalar_one()
        acc_3020.current_balance -= 5000.0
        
        # 1010 Cash: Debit increases (more positive)
        acc_1010 = (await session.execute(select(AccountCode).where(AccountCode.code == '1010'))).scalar_one()
        acc_1010.current_balance += 5000.0
        
        print(f"Restoring Emergency Fund: 3020 Balance -> {acc_3020.current_balance}, 1010 Balance -> {acc_1010.current_balance}")
        
        await session.commit()
        print("Restoration and Balance Correction Complete.")

if __name__ == "__main__":
    asyncio.run(restore_transactions())
