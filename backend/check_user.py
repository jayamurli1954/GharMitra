"""
Quick script to check if a user exists and show their info
"""
import asyncio
import sys
import os
from sqlalchemy import select

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import AsyncSessionLocal
from app.models_db import User

async def check_user(email):
    """Check if user exists"""
    db = AsyncSessionLocal()
    try:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        if user:
            print("\n" + "=" * 70)
            print(f"✅ USER FOUND: {email}")
            print("=" * 70)
            print(f"Name:     {user.name}")
            print(f"Email:    {user.email}")
            print(f"Role:     {user.role.value}")
            print(f"Society:  {user.society_id}")
            print(f"Created:  {user.created_at}")
            print("=" * 70)
            print("\n💡 Password is stored as hash, so we can't show it.")
            print("   Common test passwords: admin123, password, test123")
            print("   If you forgot, create a new user with create_admin_user.py")
            return True
        else:
            print(f"\n❌ User '{email}' NOT FOUND in database!")
            print("\n💡 You can create this user with:")
            print("   python create_admin_user.py")
            return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False
    finally:
        await db.close()

async def list_all_users():
    """List all users"""
    db = AsyncSessionLocal()
    try:
        result = await db.execute(select(User).order_by(User.email))
        users = result.scalars().all()
        
        if not users:
            print("\n❌ No users found in database!")
            return
        
        print("\n" + "=" * 70)
        print("ALL USERS IN DATABASE")
        print("=" * 70)
        print(f"{'Email':<35} {'Name':<25} {'Role':<15}")
        print("-" * 70)
        
        for user in users:
            print(f"{user.email:<35} {user.name:<25} {user.role.value:<15}")
        
        print("=" * 70)
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        await db.close()

async def main():
    email = "admin@example.com"
    
    print("\n" + "=" * 70)
    print("CHECKING USER: admin@example.com")
    print("=" * 70)
    
    found = await check_user(email)
    
    if not found:
        print("\n" + "-" * 70)
        print("Showing all users in database:")
        await list_all_users()
        
        print("\n" + "-" * 70)
        create = input("\nDo you want to create admin@example.com? (y/n): ").strip().lower()
        
        if create == 'y':
            from create_admin_user import create_admin_user
            password = input("Enter password (default: admin123): ").strip() or "admin123"
            name = input("Enter name (default: Admin User): ").strip() or "Admin User"
            await create_admin_user(email, password, name)

if __name__ == "__main__":
    asyncio.run(main())

