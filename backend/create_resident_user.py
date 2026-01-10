"""
Script to create a resident user for testing permissions.
"""
import asyncio
from datetime import datetime
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models_db import User, UserRole, Society
from app.utils.security import get_password_hash

async def create_resident():
    email = "resident@gharmitra.com"
    password = "password123"
    name = "Resident Test User"
    
    db = AsyncSessionLocal()
    try:
        # Check if user already exists
        result = await db.execute(select(User).where(User.email == email))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print(f"User {email} already exists.")
            return

        # Get Society
        result = await db.execute(select(Society).where(Society.id == 1))
        society = result.scalar_one_or_none()
        
        hashed_password = get_password_hash(password)
        new_user = User(
            society_id=society.id,
            email=email,
            password_hash=hashed_password,
            name=name,
            apartment_number="B-101",
            role=UserRole.RESIDENT, # Key difference: RESIDENT role
            terms_accepted=True,
            privacy_accepted=True,
            consent_timestamp=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(new_user)
        await db.commit()
        print(f"Created Resident: {email} / {password}")
        
    except Exception as e:
        print(f"Error: {e}")
        await db.rollback()
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(create_resident())
