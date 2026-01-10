import asyncio
import sys
import os

# Add the current directory to sys.path so that 'app' module can be found
sys.path.append(os.getcwd())

from app.database import init_db

async def main():
    print("Initializing database...")
    try:
        await init_db()
        print("Database processing complete.")
    except Exception as e:
        print(f"Error initializing database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
