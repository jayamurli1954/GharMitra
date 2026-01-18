"""
Transactions service
Handles transaction CRUD operations and business logic
"""
from typing import List, Optional, Dict, Any
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from fastapi import HTTPException, status

from app.models_db import Transaction, TransactionType, Society


class TransactionsService:
    """Service for handling transaction operations."""

    @staticmethod
    async def create_transaction(db: AsyncSession, transaction_data: dict) -> Transaction:
        """
        Create a new transaction.

        Args:
            db: Database session
            transaction_data: Transaction creation data

        Returns:
            Created transaction instance
        """
        # Validate required fields
        required_fields = ['type', 'category', 'amount', 'date', 'description']
        for field in required_fields:
            if field not in transaction_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )

        # Validate transaction type
        if transaction_data['type'] not in ['income', 'expense']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transaction type must be 'income' or 'expense'"
            )

        # Create transaction
        transaction = Transaction(
            type=TransactionType(transaction_data['type']),
            category=transaction_data['category'],
            account_code=transaction_data.get('account_code'),
            amount=transaction_data['amount'],
            description=transaction_data['description'],
            date=transaction_data['date'],
            quantity=transaction_data.get('quantity'),
            unit_price=transaction_data.get('unit_price'),
            payment_method=transaction_data.get('payment_method', 'cash'),
            expense_month=transaction_data.get('expense_month'),
            debit_amount=transaction_data.get('debit_amount', 0.0),
            credit_amount=transaction_data.get('credit_amount', 0.0),
            added_by=transaction_data.get('added_by'),
            society_id=transaction_data.get('society_id', 1),  # Default for testing
            created_at=transaction_data.get('created_at'),
            updated_at=transaction_data.get('updated_at')
        )

        db.add(transaction)
        await db.commit()
        await db.refresh(transaction)

        return transaction

    @staticmethod
    async def get_transactions(
        db: AsyncSession,
        transaction_type: Optional[str] = None,
        limit: int = 100,
        society_id: int = 1
    ) -> List[Transaction]:
        """
        Get transactions with optional filtering.

        Args:
            db: Database session
            transaction_type: Filter by 'income' or 'expense'
            limit: Maximum number of results
            society_id: Society ID for filtering

        Returns:
            List of transactions
        """
        query = select(Transaction).where(Transaction.society_id == society_id)

        if transaction_type:
            if transaction_type not in ['income', 'expense']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Transaction type must be 'income' or 'expense'"
                )
            query = query.where(Transaction.type == transaction_type)

        query = query.order_by(Transaction.date.desc()).limit(limit)

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_transaction_by_id(db: AsyncSession, transaction_id: int, society_id: int = 1) -> Optional[Transaction]:
        """
        Get transaction by ID.

        Args:
            db: Database session
            transaction_id: Transaction ID
            society_id: Society ID for filtering

        Returns:
            Transaction instance if found, None otherwise
        """
        result = await db.execute(
            select(Transaction).where(
                Transaction.id == transaction_id,
                Transaction.society_id == society_id
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_transaction(
        db: AsyncSession,
        transaction_id: int,
        update_data: dict,
        society_id: int = 1
    ) -> Transaction:
        """
        Update a transaction.

        Args:
            db: Database session
            transaction_id: Transaction ID
            update_data: Fields to update
            society_id: Society ID for filtering

        Returns:
            Updated transaction instance

        Raises:
            HTTPException: If transaction not found
        """
        transaction = await TransactionsService.get_transaction_by_id(db, transaction_id, society_id)

        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )

        # Update fields
        for field, value in update_data.items():
            if hasattr(transaction, field):
                setattr(transaction, field, value)

        transaction.updated_at = update_data.get('updated_at')

        await db.commit()
        await db.refresh(transaction)

        return transaction

    @staticmethod
    async def delete_transaction(db: AsyncSession, transaction_id: int, society_id: int = 1) -> bool:
        """
        Delete a transaction.

        Args:
            db: Database session
            transaction_id: Transaction ID
            society_id: Society ID for filtering

        Returns:
            True if deleted, False if not found
        """
        transaction = await TransactionsService.get_transaction_by_id(db, transaction_id, society_id)

        if not transaction:
            return False

        await db.delete(transaction)
        await db.commit()

        return True

    @staticmethod
    async def get_transactions_summary(db: AsyncSession, society_id: int = 1) -> Dict[str, Any]:
        """
        Get transactions summary statistics.

        Args:
            db: Database session
            society_id: Society ID for filtering

        Returns:
            Summary statistics
        """
        # Get income totals
        income_result = await db.execute(
            select(
                func.coalesce(func.sum(Transaction.amount), 0).label("total")
            ).where(
                Transaction.type == TransactionType.INCOME,
                Transaction.society_id == society_id
            )
        )
        total_income = float(income_result.scalar() or 0)

        # Get expense totals
        expense_result = await db.execute(
            select(
                func.coalesce(func.sum(Transaction.amount), 0).label("total")
            ).where(
                Transaction.type == TransactionType.EXPENSE,
                Transaction.society_id == society_id
            )
        )
        total_expenses = float(expense_result.scalar() or 0)

        return {
            "total_income": total_income,
            "total_expenses": total_expenses,
            "net_amount": total_income - total_expenses
        }


# Create singleton instance
transactions_service = TransactionsService()

# Export methods for backward compatibility
create_transaction = transactions_service.create_transaction
get_transactions = transactions_service.get_transactions
get_transaction_by_id = transactions_service.get_transaction_by_id
update_transaction = transactions_service.update_transaction
delete_transaction = transactions_service.delete_transaction
get_transactions_summary = transactions_service.get_transactions_summary