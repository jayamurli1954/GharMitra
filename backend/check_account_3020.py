
import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models_db import AccountCode, AccountType

async def check_account():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(AccountCode).where(AccountCode.code == "3020"))
        account = result.scalar_one_or_none()
        if account:
            print(f"Account: {account.name} ({account.code})")
            print(f"Type: {account.type}")
            print(f"Balance: {account.current_balance}")
            print(f"Society ID: {account.society_id}")
        else:
            print("Account 3020 not found.")

if __name__ == "__main__":
    asyncio.run(check_account())
