import asyncio
import sys
import os
from datetime import date

# Add parent directory to path to import app
sys.path.append(os.getcwd())

from app.database import AsyncSessionLocal
from app.models_db import AccountCode, Transaction
from sqlalchemy import select

async def check_data():
    async with AsyncSessionLocal() as session:
        # Check Account Balances
        res = await session.execute(
            select(AccountCode).where(AccountCode.code.in_(['1010', '5000']))
        )
        accounts = res.scalars().all()
        print("ACCOUNTS:")
        for a in accounts:
            print(f"Code: {a.code}, Name: {a.name}, Balance: {a.current_balance}, Opening: {a.opening_balance}, Society ID: {a.society_id}")
        
        # Check Recent Transactions
        res = await session.execute(
            select(Transaction)
            .where(Transaction.date == date(2026, 1, 4))
            .order_by(Transaction.id.desc())
        )
        txns = res.scalars().all()
        import json
        data = []
        for t in txns:
            t_type = t.type.value if hasattr(t.type, 'value') else str(t.type)
            data.append({
                "id": t.id,
                "date": str(t.date),
                "code": t.account_code,
                "type": t_type,
                "amount": t.amount,
                "dr": t.debit_amount,
                "cr": t.credit_amount,
                "desc": t.description
            })
        
        with open("txns_debug.json", "w") as f:
            json.dump(data, f, indent=4)
        print(f"Wrote {len(data)} transactions to txns_debug.json")

if __name__ == "__main__":
    asyncio.run(check_data())
