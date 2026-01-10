"""
Script to check and fix admin@example.com user
Creates the user if it doesn't exist, or resets password if it does
"""
import asyncio
import sys
import os
from datetime import datetime
from sqlalchemy import select

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import AsyncSessionLocal
from app.models_db import User, UserRole, Society
from app.utils.security import get_password_hash, verify_password

async def fix_admin_user():
    """Check and fix admin@example.com user"""
    db = AsyncSessionLocal()
    email = "admin@example.com"
    password = "admin123"
    
    try:
        print("\n" + "=" * 70)
        print("FIXING ADMIN USER: admin@example.com")
        print("=" * 70)
        
        # Check if user exists
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        # Check if society exists
        result = await db.execute(select(Society).where(Society.id == 1))
        society = result.scalar_one_or_none()
        
        if not society:
            print("\n[1] Creating default society...")
            society = Society(
                name="Default Society",
                total_flats=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(society)
            await db.flush()
            print(f"    ✅ Created society (ID: {society.id})")
        else:
            print(f"\n[1] Society exists (ID: {society.id})")
        
        if not user:
            # Create new user
            print(f"\n[2] User '{email}' NOT FOUND - Creating new user...")
            hashed_password = get_password_hash(password)
            new_user = User(
                society_id=society.id,
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
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)
            print(f"    [OK] User created successfully!")
            user = new_user
        else:
            # User exists - reset password
            print(f"\n[2] User '{email}' EXISTS - Resetting password...")
            print(f"    Current name: {user.name}")
            print(f"    Current role: {user.role.value}")
            
            # Update password
            user.password_hash = get_password_hash(password)
            user.updated_at = datetime.utcnow()
            
            # Make sure it's an admin
            if user.role != UserRole.ADMIN:
                print(f"    ⚠️  Role is '{user.role.value}', changing to 'admin'...")
                user.role = UserRole.ADMIN
            
            # Make sure society_id is set
            if not user.society_id:
                print(f"    ⚠️  No society_id, setting to {society.id}...")
                user.society_id = society.id
            
            await db.commit()
            await db.refresh(user)
            print(f"    [OK] Password reset successfully!")
        
        # Verify password works
        print(f"\n[3] Verifying password...")
        is_valid = verify_password(password, user.password_hash)
        
        if is_valid:
            print(f"    [OK] Password verification successful!")
        else:
            print(f"    [ERROR] Password verification failed! This shouldn't happen.")
            return False
        
        # Show final info
        print("\n" + "=" * 70)
        print("[SUCCESS] USER READY TO USE!")
        print("=" * 70)
        print(f"Email:    {user.email}")
        print(f"Password: {password}")
        print(f"Name:     {user.name}")
        print(f"Role:     {user.role.value}")
        print(f"Society:  {society.name} (ID: {society.id})")
        print("=" * 70)
        print("\n[INFO] You can now login with these credentials!")
        print("       Login at: http://localhost:3001/login")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        await db.rollback()
        return False
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(fix_admin_user())

