
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import delete, select
from app.models_db import JournalEntry, Transaction

# Define correct DB path
db_path = os.path.abspath(os.path.join("backend", "gharmitra.db"))
print(f"Connecting to database: {db_path}")
db_url = f"sqlite+aiosqlite:///{db_path}"

async def fix_duplicates():
    engine = create_async_engine(db_url, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        try:
            # IDs to delete based on previous check: 3 and 4 (the later ones)
            ids_to_delete = [3, 4]
            
            # Verify they exist before deleting
            result = await session.execute(select(JournalEntry).where(JournalEntry.id.in_(ids_to_delete)))
            jvs_to_delete = result.scalars().all()
            
            if not jvs_to_delete:
                print("No JVs found with IDs 3, 4")
                return

            print(f"Deleting {len(jvs_to_delete)} duplicate Journal Entries...")
            
            # Delete associated transactions first (cascade should handle it, but being safe)
            # Actually models define relationships, but we'll let cascade or manual del work
            # Deleting JV
            await session.execute(delete(JournalEntry).where(JournalEntry.id.in_(ids_to_delete)))
            
            # Also delete transactions linked to these JVs
            await session.execute(delete(Transaction).where(Transaction.journal_entry_id.in_(ids_to_delete)))
            
            await session.commit()
            print("Successfully deleted duplicate JVs and their transactions.")
            
        except Exception as e:
            await session.rollback()
            print(f"Error: {e}")
        finally:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(fix_duplicates())
