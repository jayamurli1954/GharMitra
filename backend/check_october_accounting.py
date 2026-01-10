"""
Check October 2025 accounting entries
"""
import asyncio
import sys
from pathlib import Path

backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Set the DATABASE_URL to the correct path before importing app modules
import os
db_path = backend_dir / "GharMitra.db"
os.environ['DATABASE_URL'] = f"sqlite+aiosqlite:///{str(db_path).replace(chr(92), '/')}"

from sqlalchemy import text
from app.database import AsyncSessionLocal

async def check_accounting():
    """Check October 2025 accounting entries"""
    async with AsyncSessionLocal() as db:
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            
            print("\n" + "="*70)
            print("CHECKING OCTOBER 2025 ACCOUNTING ENTRIES")
            print("="*70 + "\n")
            
            # Get all October 2025 transactions
            result = await db.execute(text("""
                SELECT id, document_number, type, category, account_code, amount,
                       debit_amount, credit_amount, description, date
                FROM transactions
                WHERE strftime('%Y-%m', date) = '2025-10'
                AND (account_code = '4000' OR account_code = '4100')
                ORDER BY date, id
            """))
            
            transactions = result.fetchall()
            
            if not transactions:
                print("No transactions found for October 2025!")
                return
            
            print(f"Found {len(transactions)} transaction(s):\n")
            
            total_maintenance = 0
            total_sinking_fund = 0
            
            for txn in transactions:
                (id, doc_num, type, category, account_code, amount,
                 debit_amount, credit_amount, description, date) = txn
                
                print(f"Transaction ID: {id}")
                print(f"  Document: {doc_num}")
                print(f"  Type: {type}")
                print(f"  Category: {category}")
                print(f"  Account Code: {account_code}")
                print(f"  Amount: ₹{amount:,.2f}")
                print(f"  Debit: ₹{debit_amount:,.2f}")
                print(f"  Credit: ₹{credit_amount:,.2f}")
                print(f"  Description: {description}")
                print(f"  Date: {date}")
                print()
                
                if account_code == '4000':
                    total_maintenance += credit_amount
                elif account_code == '4100':
                    total_sinking_fund += credit_amount
            
            print("-" * 70)
            print(f"Total Maintenance Charges (4000): ₹{total_maintenance:,.2f}")
            print(f"Total Sinking Fund (4100): ₹{total_sinking_fund:,.2f}")
            print(f"Grand Total: ₹{(total_maintenance + total_sinking_fund):,.2f}")
            print("-" * 70)
            
            # Check maintenance bills total
            result = await db.execute(text("""
                SELECT SUM(total_amount) as total, COUNT(*) as count
                FROM maintenance_bills
                WHERE month = 10 AND year = 2025
            """))
            
            bill_data = result.fetchone()
            if bill_data:
                total, count = bill_data
                print(f"\nMaintenance Bills Total: ₹{total:,.2f} ({count} bills)")
            
            print("\n" + "="*70)
            print("DONE")
            print("="*70 + "\n")
            
        except Exception as e:
            print(f"\nERROR: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(check_accounting())



