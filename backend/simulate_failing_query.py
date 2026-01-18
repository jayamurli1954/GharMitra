import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text
from app.config import settings

async def simulate_query():
    print(f"SIMULATE: DATABASE_URL = {settings.DATABASE_URL}")
    engine = create_async_engine(settings.DATABASE_URL)
    
    async with engine.connect() as conn:
        try:
            # Try a simple select with is_reversed
            query = text("SELECT id, is_reversed FROM transactions LIMIT 1")
            result = await conn.execute(query)
            row = result.fetchone()
            print(f"SIMULATE: SUCCESS! Row: {row}")
        except Exception as e:
            print(f"SIMULATE: FAILURE - {e}")
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(simulate_query())
