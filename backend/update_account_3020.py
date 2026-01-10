
import asyncio
from sqlalchemy import select, update
from app.database import AsyncSessionLocal
from app.models_db import AccountCode, AccountType

async def update_account():
    async with AsyncSessionLocal() as session:
        # Check current state
        result = await session.execute(select(AccountCode).where(AccountCode.code == "3020"))
        account = result.scalar_one_or_none()
        
        if account:
            print(f"Before: {account.name} ({account.code}) Type: {account.type}")
            
            # Update type to CAPITAL
            # Note: The enum string in DB might be 'capital' (lowercase) or 'CAPITAL' 
            # SQLAlchemy Enum type usually handles conversion, but let's be careful.
            # Using the Enum object AccountType.CAPITAL
            
            account.type = AccountType.CAPITAL
            await session.commit()
            print(f"Updated Account 3020 to CAPITAL.")
            
            # Re-fetch to verify
            result = await session.execute(select(AccountCode).where(AccountCode.code == "3020"))
            updated_account = result.scalar_one_or_none()
            print(f"After: {updated_account.name} Type: {updated_account.type}")
            
        else:
            print("Account 3020 not found.")

if __name__ == "__main__":
    asyncio.run(update_account())
