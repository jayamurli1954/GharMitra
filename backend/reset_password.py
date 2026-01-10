import asyncio
import sys
import os

sys.path.append(os.getcwd())

from app.database import init_db, AsyncSessionLocal
from app.models_db import User
from app.utils.security import get_password_hash
from sqlalchemy import select

async def reset_password():
    await init_db()
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == 'admin@test.com'))
        user = result.scalar_one_or_none()
        if user:
            print(f"Resetting password for {user.email}")
            user.password_hash = get_password_hash("admin123")
            await db.commit()
            print("Password reset to 'admin123'")
        else:
            print("User not found!")

if __name__ == "__main__":
    asyncio.run(reset_password())
