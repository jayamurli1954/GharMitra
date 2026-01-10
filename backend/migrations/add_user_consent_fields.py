"""
Migration: Add legal consent fields to users table
DPDP Act 2023 compliance - Track user consent for Terms of Service and Privacy Policy
"""
import asyncio
from sqlalchemy import text
from app.database import get_async_session


async def migrate_user_consent_fields():
    """
    Add consent tracking fields to users table
    
    Fields added:
    - terms_accepted: BOOLEAN (default: FALSE)
    - privacy_accepted: BOOLEAN (default: FALSE)
    - consent_timestamp: DATETIME (nullable)
    - consent_ip_address: VARCHAR(45) (nullable, for IPv4/IPv6)
    - consent_version: VARCHAR(20) (nullable, track which version of terms/privacy accepted)
    """
    async for db in get_async_session():
        try:
            # Check if columns already exist (for idempotency)
            result = await db.execute(text("PRAGMA table_info(users)"))
            columns = [row[1] for row in result.fetchall()]
            
            # Add terms_accepted column if it doesn't exist
            if "terms_accepted" not in columns:
                await db.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN terms_accepted BOOLEAN NOT NULL DEFAULT 0
                """))
                print("✓ Added terms_accepted column")
            else:
                print("→ terms_accepted column already exists")
            
            # Add privacy_accepted column if it doesn't exist
            if "privacy_accepted" not in columns:
                await db.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN privacy_accepted BOOLEAN NOT NULL DEFAULT 0
                """))
                print("✓ Added privacy_accepted column")
            else:
                print("→ privacy_accepted column already exists")
            
            # Add consent_timestamp column if it doesn't exist
            if "consent_timestamp" not in columns:
                await db.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN consent_timestamp DATETIME
                """))
                print("✓ Added consent_timestamp column")
            else:
                print("→ consent_timestamp column already exists")
            
            # Add consent_ip_address column if it doesn't exist
            if "consent_ip_address" not in columns:
                await db.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN consent_ip_address VARCHAR(45)
                """))
                print("✓ Added consent_ip_address column")
            else:
                print("→ consent_ip_address column already exists")
            
            # Add consent_version column if it doesn't exist
            if "consent_version" not in columns:
                await db.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN consent_version VARCHAR(20)
                """))
                print("✓ Added consent_version column")
            else:
                print("→ consent_version column already exists")
            
            await db.commit()
            print("\n✅ Migration completed: User consent fields added successfully")
            
        except Exception as e:
            await db.rollback()
            print(f"\n❌ Migration failed: {str(e)}")
            raise
        finally:
            await db.close()
            break


if __name__ == "__main__":
    asyncio.run(migrate_user_consent_fields())






