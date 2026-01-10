"""
Automatic Document Numbering Utility
Generates unique document numbers for transactions, journal entries, receipts, etc.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import date
from typing import Optional
from app.models_db import Transaction, JournalEntry, Payment


async def generate_quick_entry_voucher_number(
    db: AsyncSession,
    society_id: int,
    offset: int = 0
) -> str:
    """
    Generate sequential voucher number for Quick Entry transactions.
    Format: QV-0001, QV-0002, etc. (sequential across all time)
    
    Args:
        offset: Additional offset to add (useful for creating multiple transactions in same entry)
    """
    # Find the maximum QV number for this society
    result = await db.execute(
        select(Transaction.document_number).where(
            Transaction.society_id == society_id,
            Transaction.document_number.like("QV-%")
        ).order_by(Transaction.document_number.desc())
    )
    existing_numbers = result.scalars().all()
    
    max_num = 0
    for doc_num in existing_numbers:
        if doc_num and doc_num.startswith("QV-"):
            try:
                num = int(doc_num[3:])  # Extract number after "QV-"
                if num > max_num:
                    max_num = num
            except ValueError:
                continue
    
    # Next number is max_num + 1 + offset
    next_num = max_num + 1 + offset
    voucher_number = f"QV-{next_num:04d}"
    
    return voucher_number


async def generate_journal_voucher_number(
    db: AsyncSession,
    society_id: int
) -> str:
    """
    Generate sequential voucher number for Journal Voucher entries.
    Format: JV-0001, JV-0002, etc. (sequential across all time)
    """
    # Find the maximum JV number for this society
    result = await db.execute(
        select(JournalEntry.entry_number).where(
            JournalEntry.society_id == society_id,
            JournalEntry.entry_number.like("JV-%")
        ).order_by(JournalEntry.entry_number.desc())
    )
    existing_numbers = result.scalars().all()
    
    max_num = 0
    for entry_num in existing_numbers:
        if entry_num and entry_num.startswith("JV-"):
            try:
                num = int(entry_num[3:])  # Extract number after "JV-"
                if num > max_num:
                    max_num = num
            except ValueError:
                continue
    
    # Next number is max_num + 1
    next_num = max_num + 1
    voucher_number = f"JV-{next_num:04d}"
    
    return voucher_number


async def generate_receipt_voucher_number(
    db: AsyncSession,
    society_id: int
) -> str:
    """
    Generate sequential voucher number for Receipt Vouchers (maintenance bill payments).
    Format: RV-0001, RV-0002, etc. (sequential across all time)
    """
    # Find the maximum RV number for this society from Payment receipts
    # Note: Payment.society_id is Integer, not UUID
    result = await db.execute(
        select(Payment.receipt_number).where(
            Payment.society_id == society_id,
            Payment.receipt_number.like("RV-%")
        ).order_by(Payment.receipt_number.desc())
    )
    existing_numbers = result.scalars().all()
    
    max_num = 0
    for receipt_num in existing_numbers:
        if receipt_num and receipt_num.startswith("RV-"):
            try:
                num = int(receipt_num[3:])  # Extract number after "RV-"
                if num > max_num:
                    max_num = num
            except ValueError:
                continue
    
    # Next number is max_num + 1
    next_num = max_num + 1
    voucher_number = f"RV-{next_num:04d}"
    
    return voucher_number


# Legacy functions for backward compatibility
async def generate_transaction_document_number(
    db: AsyncSession,
    society_id: int,
    transaction_date: date,
    payment_method: Optional[str] = None,
    offset: int = 0
) -> str:
    """
    Generate unique document number for a transaction (Quick Entry).
    Now uses QV-0001 format (sequential, not date-based).
    
    Args:
        offset: Additional offset to add (useful for creating multiple transactions in same entry)
    """
    return await generate_quick_entry_voucher_number(db, society_id, offset)


async def generate_journal_entry_number(
    db: AsyncSession,
    society_id: int,
    entry_date: date
) -> str:
    """
    Generate unique entry number for a journal entry.
    Now uses JV-0001 format (sequential, not date-based).
    """
    return await generate_journal_voucher_number(db, society_id)

