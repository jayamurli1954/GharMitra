"""
Recreate flats from existing members
This will create flats based on the flat_id references in members table
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./gharmitra.db")
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def recreate_flats():
    """Recreate flats from members"""
    async with async_session() as db:
        print("=" * 60)
        print("RECREATING FLATS FROM MEMBERS")
        print("=" * 60)
        
        # Get all unique flat_ids from members
        result = await db.execute(
            text("""
                SELECT DISTINCT m.flat_id, m.society_id, 
                       GROUP_CONCAT(DISTINCT m.name) as names,
                       GROUP_CONCAT(DISTINCT m.phone_number) as phones,
                       GROUP_CONCAT(DISTINCT m.email) as emails,
                       MAX(m.total_occupants) as max_occupants
                FROM members m
                WHERE m.flat_id IS NOT NULL
                GROUP BY m.flat_id, m.society_id
            """)
        )
        member_flats = result.fetchall()
        
        print(f"\nFound {len(member_flats)} unique flat_ids in members table")
        
        if not member_flats:
            print("No members with flat_id found. Cannot recreate flats.")
            return
        
        # Check if flats table exists
        result = await db.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='flats'")
        )
        if not result.fetchone():
            print("Creating flats table...")
            await db.execute(text("""
                CREATE TABLE flats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    society_id INTEGER NOT NULL DEFAULT 1,
                    flat_number TEXT NOT NULL,
                    area_sqft REAL DEFAULT 0.0,
                    bedrooms INTEGER DEFAULT 2,
                    owner_name TEXT,
                    owner_phone TEXT,
                    owner_email TEXT,
                    occupants INTEGER DEFAULT 1,
                    occupancy_status TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            await db.commit()
        
        # For each flat_id, try to get flat_number from somewhere
        # Since we don't have flat_number, we'll need to generate it
        created_count = 0
        updated_count = 0
        
        for row in member_flats:
            flat_id = row[0]
            society_id = row[1] or 1
            names = row[2] or ""
            phones = row[3] or ""
            emails = row[4] or ""
            max_occupants = row[5] or 1
            
            # Check if flat already exists
            result = await db.execute(
                text("SELECT id, flat_number FROM flats WHERE id = :flat_id"),
                {"flat_id": flat_id}
            )
            existing_flat = result.fetchone()
            
            if existing_flat:
                print(f"Flat ID {flat_id} already exists: {existing_flat[1]}")
                updated_count += 1
            else:
                # Generate flat_number from flat_id (e.g., A-101, A-102, etc.)
                # Try to infer from flat_id
                flat_number = f"A-{flat_id:03d}"  # A-001, A-002, etc.
                
                # Get first name, phone, email
                first_name = names.split(',')[0] if names else None
                first_phone = phones.split(',')[0] if phones else None
                first_email = emails.split(',')[0] if emails else None
                
                # Insert new flat
                await db.execute(
                    text("""
                        INSERT INTO flats 
                        (id, society_id, flat_number, area_sqft, bedrooms, owner_name, owner_phone, owner_email, occupants, occupancy_status, created_at, updated_at)
                        VALUES (:id, :society_id, :flat_number, :area_sqft, :bedrooms, :owner_name, :owner_phone, :owner_email, :occupants, :occupancy_status, datetime('now'), datetime('now'))
                    """),
                    {
                        "id": flat_id,
                        "society_id": society_id,
                        "flat_number": flat_number,
                        "area_sqft": 1000.0,  # Default area
                        "bedrooms": 2,  # Default bedrooms
                        "owner_name": first_name,
                        "owner_phone": first_phone,
                        "owner_email": first_email,
                        "occupants": max_occupants,
                        "occupancy_status": "OWNER_OCCUPIED"
                    }
                )
                print(f"Created flat ID {flat_id}: {flat_number} ({first_name})")
                created_count += 1
        
        await db.commit()
        
        print(f"\n{'='*60}")
        print(f"SUMMARY:")
        print(f"  Created: {created_count} flats")
        print(f"  Updated: {updated_count} flats")
        print(f"{'='*60}")
        print("\nFlats recreated! Please refresh your browser.")


if __name__ == "__main__":
    asyncio.run(recreate_flats())
