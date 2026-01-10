"""
Diagnostic script to check and fix society_id mismatches
Run this to see what's in the database and fix any issues
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./gharmitra.db")

# Create engine
engine = create_async_engine(DATABASE_URL, echo=False)

# Create session factory
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def check_database():
    """Check what's in the database"""
    async with async_session() as db:
        print("=" * 60)
        print("DATABASE DIAGNOSTIC REPORT")
        print("=" * 60)
        
        # Check users
        print("\n1. USERS:")
        result = await db.execute(text("SELECT id, email, society_id FROM users"))
        users = result.fetchall()
        print(f"   Total users: {len(users)}")
        for user in users:
            print(f"   - User ID {user[0]}: {user[1]}, society_id={user[2]}")
        
        # Check societies
        print("\n2. SOCIETIES:")
        result = await db.execute(text("SELECT id, name FROM societies"))
        societies = result.fetchall()
        print(f"   Total societies: {len(societies)}")
        for society in societies:
            print(f"   - Society ID {society[0]}: {society[1]}")
        
        # Check flats by society_id
        print("\n3. FLATS BY SOCIETY_ID:")
        result = await db.execute(
            text("SELECT society_id, COUNT(*) as count FROM flats GROUP BY society_id")
        )
        flats_by_society = result.fetchall()
        if flats_by_society:
            for row in flats_by_society:
                print(f"   - society_id={row[0]}: {row[1]} flats")
        else:
            print("   - NO FLATS FOUND IN DATABASE")
        
        # Check members by society_id
        print("\n4. MEMBERS BY SOCIETY_ID:")
        result = await db.execute(
            text("SELECT society_id, COUNT(*) as count FROM members GROUP BY society_id")
        )
        members_by_society = result.fetchall()
        if members_by_society:
            for row in members_by_society:
                print(f"   - society_id={row[0]}: {row[1]} members")
        else:
            print("   - NO MEMBERS FOUND IN DATABASE")
        
        # Check sample flats
        print("\n5. SAMPLE FLATS (first 10):")
        result = await db.execute(
            text("SELECT id, flat_number, society_id FROM flats LIMIT 10")
        )
        sample_flats = result.fetchall()
        if sample_flats:
            for flat in sample_flats:
                print(f"   - Flat {flat[1]} (ID={flat[0]}): society_id={flat[2]}")
        else:
            print("   - NO FLATS FOUND")
        
        # Check sample members
        print("\n6. SAMPLE MEMBERS (first 10):")
        result = await db.execute(
            text("SELECT id, name, society_id FROM members LIMIT 10")
        )
        sample_members = result.fetchall()
        if sample_members:
            for member in sample_members:
                print(f"   - {member[1]} (ID={member[0]}): society_id={member[2]}")
        else:
            print("   - NO MEMBERS FOUND")
        
        print("\n" + "=" * 60)
        
        # Check if there's a mismatch
        if users:
            user_society_id = users[0][2] if users else None
            print(f"\n7. DIAGNOSIS:")
            print(f"   User's society_id: {user_society_id}")
            
            if flats_by_society:
                flat_society_ids = [row[0] for row in flats_by_society]
                print(f"   Flats exist with society_ids: {flat_society_ids}")
                if user_society_id not in flat_society_ids:
                    print(f"   ⚠️  MISMATCH: User's society_id ({user_society_id}) doesn't match flats!")
                    print(f"   💡 SOLUTION: Update flats to use society_id={user_society_id}")
            else:
                print(f"   WARNING: NO FLATS FOUND in database")
            
            if members_by_society:
                member_society_ids = [row[0] for row in members_by_society]
                print(f"   Members exist with society_ids: {member_society_ids}")
                if user_society_id not in member_society_ids:
                    print(f"   ⚠️  MISMATCH: User's society_id ({user_society_id}) doesn't match members!")
                    print(f"   💡 SOLUTION: Update members to use society_id={user_society_id}")
            else:
                print(f"   ⚠️  NO MEMBERS FOUND in database")


async def fix_society_id_mismatch():
    """Fix society_id mismatches by updating all data to match user's society_id"""
    async with async_session() as db:
        print("\n" + "=" * 60)
        print("FIXING SOCIETY_ID MISMATCH")
        print("=" * 60)
        
        # Get user's society_id
        result = await db.execute(text("SELECT id, email, society_id FROM users LIMIT 1"))
        user_row = result.fetchone()
        
        if not user_row:
            print("❌ No users found in database!")
            return
        
        user_society_id = user_row[2] or 1  # Default to 1 if NULL
        print(f"\nUser's society_id: {user_society_id}")
        
        # Check what society_ids exist in flats
        result = await db.execute(
            text("SELECT DISTINCT society_id FROM flats WHERE society_id IS NOT NULL")
        )
        flat_society_ids = [row[0] for row in result.fetchall()]
        
        # Check what society_ids exist in members
        result = await db.execute(
            text("SELECT DISTINCT society_id FROM members WHERE society_id IS NOT NULL")
        )
        member_society_ids = [row[0] for row in result.fetchall()]
        
        print(f"Flats have society_ids: {flat_society_ids}")
        print(f"Members have society_ids: {member_society_ids}")
        
        # Update flats if needed
        if flat_society_ids and user_society_id not in flat_society_ids:
            print(f"\n📝 Updating flats from society_id={flat_society_ids[0]} to {user_society_id}...")
            await db.execute(
                text("UPDATE flats SET society_id = :new_id WHERE society_id = :old_id"),
                {"new_id": user_society_id, "old_id": flat_society_ids[0]}
            )
            await db.commit()
            print(f"✅ Updated flats to society_id={user_society_id}")
        
        # Update members if needed
        if member_society_ids and user_society_id not in member_society_ids:
            print(f"\n📝 Updating members from society_id={member_society_ids[0]} to {user_society_id}...")
            await db.execute(
                text("UPDATE members SET society_id = :new_id WHERE society_id = :old_id"),
                {"new_id": user_society_id, "old_id": member_society_ids[0]}
            )
            await db.commit()
            print(f"✅ Updated members to society_id={user_society_id}")
        
        # Also update flats/members with NULL society_id
        print(f"\n📝 Updating flats with NULL society_id to {user_society_id}...")
        result = await db.execute(
            text("UPDATE flats SET society_id = :new_id WHERE society_id IS NULL"),
            {"new_id": user_society_id}
        )
        await db.commit()
        print(f"✅ Updated {result.rowcount} flats with NULL society_id")
        
        print(f"\n📝 Updating members with NULL society_id to {user_society_id}...")
        result = await db.execute(
            text("UPDATE members SET society_id = :new_id WHERE society_id IS NULL"),
            {"new_id": user_society_id}
        )
        await db.commit()
        print(f"✅ Updated {result.rowcount} members with NULL society_id")
        
        print("\n✅ Fix complete! Please refresh your browser.")


async def main():
    """Main function"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--fix":
        await check_database()
        print("\n" + "=" * 60)
        response = input("\nDo you want to fix society_id mismatches? (yes/no): ")
        if response.lower() in ['yes', 'y']:
            await fix_society_id_mismatch()
            await check_database()
        else:
            print("Cancelled.")
    else:
        await check_database()
        print("\n💡 To fix mismatches, run: python check_and_fix_society_id.py --fix")


if __name__ == "__main__":
    asyncio.run(main())
