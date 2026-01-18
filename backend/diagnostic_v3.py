import asyncio
import os
import sys
import logging

# Disable all logging
logging.getLogger("sqlalchemy").setLevel(logging.ERROR)
logging.getLogger("sqlalchemy.engine").setLevel(logging.ERROR)

# Add current directory to path
sys.path.append(os.getcwd())

from app.database import AsyncSessionLocal
from app.models_db import Transaction, AccountCode, Society, FinancialYear
from sqlalchemy import select, func

async def diagnostic():
    output = []
    async with AsyncSessionLocal() as db:
        # Check financial years
        res = await db.execute(select(FinancialYear))
        fys = res.scalars().all()
        output.append("FINANCIAL YEARS:")
        for fy in fys:
            output.append(f"ID={fy.id}, Start={fy.start_date}, End={fy.end_date}, Active={fy.is_active}")
            
        # Check societies
        res = await db.execute(select(Society))
        societies = res.scalars().all()
        output.append("\nSOCIETIES:")
        for s in societies:
            output.append(f"ID: {s.id}, Name: {s.name}")
        
        # Check date range
        res = await db.execute(select(func.min(Transaction.date), func.max(Transaction.date)))
        min_date, max_date = res.one()
        output.append(f"\nTRANSACTION DATE RANGE: {min_date} to {max_date}")
        
        # Check current counts
        res = await db.execute(select(func.count(Transaction.id)))
        output.append(f"TRANSACTION COUNT: {res.scalar()}")
        
        res = await db.execute(select(func.count(AccountCode.id)))
        output.append(f"ACCOUNT CODE COUNT: {res.scalar()}")
        
        # Check TRANSACTION data details
        res = await db.execute(select(Transaction).limit(5))
        txns = res.scalars().all()
        output.append("\nFIRST 5 TRANSACTIONS:")
        for t in txns:
            output.append(f"ID={t.id}, Soc={t.society_id}, Date={t.date}, Code='{t.account_code}', D={t.debit_amount}, C={t.credit_amount}")
            
        # Check specific Account Code 1100 (Receivable) and 4000 (Income)
        res = await db.execute(select(AccountCode).where(AccountCode.code.in_(['1100', '4000', '1000', '1001'])))
        accounts = res.scalars().all()
        output.append("\nSPECIFIC ACCOUNTS:")
        for a in accounts:
            output.append(f"Soc={a.society_id}, Code='{a.code}', Name='{a.name}', Type={a.type}, Bal={a.current_balance}")

    with open("results.txt", "w") as f:
        f.write("\n".join(output))

if __name__ == "__main__":
    asyncio.run(diagnostic())
