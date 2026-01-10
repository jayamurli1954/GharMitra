"""
Script to create an admin user or list existing users
Run this if you forgot your login credentials
"""
import asyncio
import sys
from datetime import datetime
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models_db import User, UserRole, Society
from app.utils.security import get_password_hash

async def list_users():
    """List all existing users"""
    db = AsyncSessionLocal()
    try:
        result = await db.execute(select(User).order_by(User.email))
        users = result.scalars().all()
        
        if not users:
            print("\n❌ No users found in database!")
            return False
        
        print("\n" + "=" * 70)
        print("EXISTING USERS IN DATABASE")
        print("=" * 70)
        print(f"{'Email':<30} {'Name':<25} {'Role':<15} {'Society ID':<10}")
        print("-" * 70)
        
        for user in users:
            print(f"{user.email:<30} {user.name:<25} {user.role.value:<15} {user.society_id:<10}")
        
        print("=" * 70)
        return True
    finally:
        await db.close()

async def create_admin_user(email, password, name="Admin User", apartment="ADMIN"):
    """Create a new admin user"""
    db = AsyncSessionLocal()
    try:
        # Check if user already exists
        result = await db.execute(select(User).where(User.email == email))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print(f"\n❌ User with email '{email}' already exists!")
            print(f"   Name: {existing_user.name}")
            print(f"   Role: {existing_user.role.value}")
            return False
        
        # Check if society exists (default to society_id=1)
        result = await db.execute(select(Society).where(Society.id == 1))
        society = result.scalar_one_or_none()
        
        if not society:
            print("\n⚠️  No society found. Creating default society...")
            society = Society(
                name="Default Society",
                total_flats=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(society)
            await db.flush()
            print(f"✅ Created default society (ID: {society.id})")
        
        # Create admin user
        hashed_password = get_password_hash(password)
        new_user = User(
            society_id=society.id,
            email=email,
            password_hash=hashed_password,
            name=name,
            apartment_number=apartment,
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
        
        print("\n" + "=" * 70)
        print("✅ ADMIN USER CREATED SUCCESSFULLY!")
        print("=" * 70)
        print(f"Email:    {new_user.email}")
        print(f"Password: {password}")
        print(f"Name:     {new_user.name}")
        print(f"Role:     {new_user.role.value}")
        print(f"Society:  {society.name} (ID: {society.id})")
        print("=" * 70)
        print("\n💡 You can now login with these credentials!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error creating user: {e}")
        await db.rollback()
        return False
    finally:
        await db.close()

async def main():
    print("\n" + "=" * 70)
    print("GharMitra - USER MANAGEMENT")
    print("=" * 70)
    
    # List existing users
    has_users = await list_users()
    
    if has_users:
        print("\n💡 If you see your email above, you can try logging in.")
        print("   If you forgot the password, you'll need to create a new user.")
    
    # Ask if user wants to create a new admin
    print("\n" + "-" * 70)
    create_new = input("\nDo you want to create a new admin user? (y/n): ").strip().lower()
    
    if create_new == 'y':
        print("\n" + "-" * 70)
        email = input("Enter email address: ").strip()
        password = input("Enter password (min 6 chars): ").strip()
        name = input("Enter name (or press Enter for 'Admin User'): ").strip() or "Admin User"
        
        if not email or not password:
            print("\n❌ Email and password are required!")
            return
        
        if len(password) < 6:
            print("\n❌ Password must be at least 6 characters!")
            return
        
        await create_admin_user(email, password, name)
    else:
        print("\n👋 Exiting. Run this script again if you need to create a user.")

if __name__ == "__main__":
    asyncio.run(main())


