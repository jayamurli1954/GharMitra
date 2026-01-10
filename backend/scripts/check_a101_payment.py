"""Check payment status for A-101"""
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


async def check_a101():
    """Check A-101 payment and bill status"""
    async with async_session() as db:
        print("=" * 70)
        print("CHECKING A-101 PAYMENT STATUS")
        print("=" * 70)
        print()
        
        # Get A-101 bills
        result = await db.execute(
            text("""
                SELECT id, flat_number, bill_number, month, year, total_amount, status, paid_date
                FROM maintenance_bills
                WHERE flat_number = 'A-101'
                ORDER BY year DESC, month DESC
            """)
        )
        bills = result.fetchall()
        
        print(f"Found {len(bills)} bills for A-101:")
        for bill_id, flat_number, bill_number, month, year, total_amount, status, paid_date in bills:
            print(f"  {bill_number} ({month}/{year}): Rs.{total_amount}, Status: {status}, Paid Date: {paid_date}")
        print()
        
        # Get payments for A-101
        result = await db.execute(
            text("""
                SELECT p.id, p.receipt_number, p.payment_date, p.amount, p.payment_mode, p.status,
                       mb.bill_number, mb.month, mb.year
                FROM payments p
                JOIN maintenance_bills mb ON p.bill_id = mb.id
                WHERE mb.flat_number = 'A-101'
                ORDER BY p.payment_date DESC
            """)
        )
        payments = result.fetchall()
        
        print(f"Found {len(payments)} payments for A-101:")
        for p_id, receipt, p_date, amount, mode, p_status, bill_num, month, year in payments:
            print(f"  Receipt {receipt} ({p_date}): Rs.{amount} via {mode}, Status: {p_status}, Bill: {bill_num} ({month}/{year})")
        print()


if __name__ == "__main__":
    asyncio.run(check_a101())
