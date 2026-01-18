
import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.config import settings
settings.DATABASE_URL = "sqlite+aiosqlite:///d:/SanMitra_Tech/GharMitra/backend/gharmitra.db"

from app.database import AsyncSessionLocal, init_db
from app.models_db import User as UserDB
from app.routes.reports import general_ledger_report
from datetime import date
from decimal import Decimal

async def check_gl():
    async with AsyncSessionLocal() as db:
        # Get a user (e.g., admin)
        from sqlalchemy import select
        result = await db.execute(select(UserDB).where(UserDB.role == 'admin'))
        user = result.scalars().first()
        if not user:
             result = await db.execute(select(UserDB).where(UserDB.role == 'super_admin'))
             user = result.scalars().first()
             
        if not user:
            print("No suitable user found")
            return

        # Mock current_user
        from app.models.user import UserResponse
        user_resp = UserResponse(
            id=str(user.id),
            email=user.email,
            name=user.name,
            apartment_number=user.apartment_number,
            role=user.role.value if hasattr(user.role, 'value') else user.role,
            society_id=user.society_id,
            created_at=user.created_at,
            updated_at=user.updated_at
        )

        try:
            print(f"Checking General Ledger for user {user.email}...")
            # Use a typical date range
            today = date.today()
            from_date = date(today.year, 4, 1) # Start of Indian FY
            if today.month < 4:
                from_date = date(today.year - 1, 4, 1)
            to_date = today
            print(f"Period: {from_date} to {to_date}")
            
            resp = await general_ledger_report(from_date=from_date, to_date=to_date, current_user=user_resp, db=db)
            print("Result type:", type(resp))
            print("Result keys:", resp.keys())
            if 'ledger_entries' in resp:
                 print(f"Num ledger entries: {len(resp['ledger_entries'])}")
                 if len(resp['ledger_entries']) > 0:
                     print("First entry summary:", {k: v for k, v in resp['ledger_entries'][0].items() if k != 'transactions'})
            else:
                 print("ledger_entries MISSING IN RESPONSE")
        except Exception as e:
            import traceback
            print(f"Error: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_gl())
