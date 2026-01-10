"""Check all data needed for dashboard"""
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


async def check_dashboard_data():
    """Check all data needed for dashboard"""
    async with async_session() as db:
        print("=" * 70)
        print("DASHBOARD DATA CHECK")
        print("=" * 70)
        print()
        
        # 1. Check Society Balance (Cash + Bank accounts)
        print("1. SOCIETY BALANCE (Cash + Bank):")
        print("-" * 70)
        
        # Check for account codes 1200, 1210 (current dashboard logic)
        result = await db.execute(
            text("""
                SELECT code, name, current_balance
                FROM account_codes
                WHERE code IN ('1200', '1210')
            """)
        )
        accounts_1200_1210 = result.fetchall()
        
        if accounts_1200_1210:
            total = 0
            for code, name, balance in accounts_1200_1210:
                print(f"  Code {code}: {name} - Balance: Rs.{balance}")
                total += float(balance or 0)
            print(f"  TOTAL (1200 + 1210): Rs.{total}")
        else:
            print("  No accounts found with codes 1200 or 1210")
        
        # Check for other possible Cash/Bank codes
        result = await db.execute(
            text("""
                SELECT code, name, current_balance
                FROM account_codes
                WHERE (name LIKE '%Cash%' OR name LIKE '%Bank%' OR name LIKE '%bank%')
                AND code NOT IN ('1200', '1210')
                ORDER BY code
            """)
        )
        other_accounts = result.fetchall()
        
        if other_accounts:
            print("\n  Other Cash/Bank accounts found:")
            for code, name, balance in other_accounts:
                print(f"    Code {code}: {name} - Balance: Rs.{balance}")
        
        # 2. Check December 2025 Billing
        print("\n2. THIS MONTH BILLING (December 2025):")
        print("-" * 70)
        result = await db.execute(
            text("""
                SELECT COUNT(*) as count, COALESCE(SUM(total_amount), 0) as total
                FROM maintenance_bills
                WHERE month = 12 AND year = 2025
            """)
        )
        row = result.fetchone()
        bill_count = row[0] if row else 0
        bill_total = float(row[1] if row else 0)
        print(f"  Bills found: {bill_count}")
        print(f"  Total amount: Rs.{bill_total}")
        
        # 3. Check Dues Pending
        print("\n3. DUES PENDING (Unpaid bills):")
        print("-" * 70)
        result = await db.execute(
            text("""
                SELECT COUNT(*) as count, COALESCE(SUM(total_amount), 0) as total
                FROM maintenance_bills
                WHERE status = 'unpaid'
            """)
        )
        row = result.fetchone()
        unpaid_count = row[0] if row else 0
        unpaid_total = float(row[1] if row else 0)
        print(f"  Unpaid bills: {unpaid_count}")
        print(f"  Total dues: Rs.{unpaid_total}")
        
        # Also check flat balances (member dues register)
        result = await db.execute(
            text("""
                SELECT COUNT(*) as count
                FROM flats
            """)
        )
        flat_count = result.fetchone()[0]
        print(f"  Total flats: {flat_count}")
        
        # 4. Check Complaints
        print("\n4. COMPLAINTS OPEN:")
        print("-" * 70)
        result = await db.execute(
            text("""
                SELECT COUNT(*) as count
                FROM complaints
                WHERE status IN ('open', 'in_progress')
            """)
        )
        complaint_count = result.fetchone()[0]
        print(f"  Open/In-progress complaints: {complaint_count}")
        
        # Check if complaints table exists
        result = await db.execute(
            text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='complaints'
            """)
        )
        table_exists = result.fetchone()
        if not table_exists:
            print("  WARNING: 'complaints' table does not exist")
        
        print("\n" + "=" * 70)
        print("SUMMARY:")
        print(f"  Society Balance: {'Rs.' + str(sum(float(a[2] or 0) for a in accounts_1200_1210)) if accounts_1200_1210 else 'Rs.0 (no accounts 1200/1210 found)'}")
        print(f"  December 2025 Billing: Rs.{bill_total}")
        print(f"  Dues Pending: Rs.{unpaid_total}")
        print(f"  Complaints Open: {complaint_count}")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(check_dashboard_data())
