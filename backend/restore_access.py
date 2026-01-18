import asyncio
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import AsyncSessionLocal
from app.models_db import User, UserRole, Society
from app.utils.security import get_password_hash

async def restore_admin():
    db = AsyncSessionLocal()
    try:
        # 1. Ensure Society 1 exists
        from sqlalchemy import text
        result = await db.execute(text("SELECT id FROM societies WHERE id = 1"))
        society = result.fetchone()
        
        if not society:
            print("Creating default society...")
            from app.models_db import Society
            society = Society(
                id=1,
                name="GharMitra Society",
                total_flats=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(society)
            await db.flush()
        
        # 2. Create Admin User
        email = "admin@example.com"
        password = "admin123"
        hashed_password = get_password_hash(password)
        
        # Check if exists
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none():
            print(f"User {email} already exists.")
            return

        admin = User(
            society_id=1,
            email=email,
            password_hash=hashed_password,
            name="Admin User",
            apartment_number="ADMIN",
            role=UserRole.ADMIN,
            terms_accepted=True,
            privacy_accepted=True,
            consent_timestamp=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(admin)
        await db.commit()
        print(f"✅ Created admin user: {email} / {password}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        await db.rollback()
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(restore_admin())
