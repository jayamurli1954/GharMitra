
import asyncio
from sqlalchemy import delete, text
from app.database import AsyncSessionLocal
from app.models_db import Transaction

async def delete_duplicates():
    async with AsyncSessionLocal() as session:
        # Delete transactions by ID
        # IDs to delete: 7, 8, 9, 10
        ids_to_delete = [7, 8, 9, 10]
        
        print(f"Deleting transactions with IDs: {ids_to_delete}")
        
        # Using text for explicit safety and clarity, though delete(Transaction) works too
        query = text(f"DELETE FROM transactions WHERE id IN ({','.join(map(str, ids_to_delete))})")
        
        await session.execute(query)
        await session.commit()
        print("Deletion complete.")

if __name__ == "__main__":
    asyncio.run(delete_duplicates())
