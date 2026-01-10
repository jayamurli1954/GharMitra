"""
Quick script to check if templates exist in database
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text
from app.database import AsyncSessionLocal

async def check_templates():
    async with AsyncSessionLocal() as db:
        # Check all templates
        result = await db.execute(text("SELECT COUNT(*) as count FROM document_templates"))
        total = result.fetchone()[0]
        print(f"Total templates in database: {total}")
        
        # Check by society_id
        result = await db.execute(text("SELECT society_id, COUNT(*) as count FROM document_templates GROUP BY society_id"))
        rows = result.fetchall()
        print(f"\nTemplates by society_id:")
        for row in rows:
            print(f"  Society ID {row[0]}: {row[1]} templates")
        
        # Check by category
        result = await db.execute(text("SELECT category, COUNT(*) as count FROM document_templates GROUP BY category"))
        rows = result.fetchall()
        print(f"\nTemplates by category:")
        for row in rows:
            print(f"  {row[0]}: {row[1]} templates")
        
        # List all templates
        result = await db.execute(text("SELECT id, template_name, category, society_id FROM document_templates"))
        templates = result.fetchall()
        if templates:
            print(f"\nAll templates:")
            for t in templates:
                print(f"  ID {t[0]}: {t[1]} ({t[2]}) - Society {t[3]}")
        else:
            print("\nNo templates found in database!")

if __name__ == '__main__':
    asyncio.run(check_templates())





