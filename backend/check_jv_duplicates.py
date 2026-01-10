
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from app.models_db import JournalEntry

# Define correct DB path
db_path = os.path.abspath(os.path.join("backend", "gharmitra.db"))
if not os.path.exists(db_path):
    print(f"DB not found at {db_path}, trying GharMitra.db...")
    db_path = os.path.abspath(os.path.join("backend", "GharMitra.db"))

print(f"Connecting to database: {db_path}")
db_url = f"sqlite+aiosqlite:///{db_path}"

async def check_duplicates():
    engine = create_async_engine(db_url, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        try:
            # Fetch all JVs
            result = await session.execute(select(JournalEntry).order_by(JournalEntry.id))
            jvs = result.scalars().all()
            
            print(f"Total Journal Entries: {len(jvs)}")
            print(f"{'ID':<5} {'Date':<12} {'Amount':<10} {'Description'}")
            print("-" * 60)
            
            seen = {}
            duplicates = []
            
            for jv in jvs:
                # Key for duplication: Date + Amount + Description (approx)
                key = (jv.date, jv.total_debit, jv.description)
                if key in seen:
                    duplicates.append((jv, seen[key]))
                seen[key] = jv
                
                print(f"{jv.id:<5} {jv.date} {jv.total_debit:<10} {jv.description[:30]}")
                
            if duplicates:
                print("\n!!! POTENTIAL DUPLICATES FOUND !!!")
                for dup, orig in duplicates:
                    print(f"Duplicate ID {dup.id} matches Original ID {orig.id}")
                    print(f"  Date: {dup.date}, Amount: {dup.total_debit}, Desc: {dup.description}")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_duplicates())

