"""
Opening Balance Model for Financial Year
"""
from sqlalchemy import Column, Integer, String, Date, Boolean, DateTime, ForeignKey, Text, Numeric, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from ..database import Base


class BalanceType(str, enum.Enum):
    """Balance type enum"""
    DEBIT = "debit"
    CREDIT = "credit"


class BalanceStatus(str, enum.Enum):
    """Balance status enum"""
    PROVISIONAL = "provisional"
    FINALIZED = "finalized"


class OpeningBalance(Base):
    """
    Opening Balance for Financial Year
    
    Stores the opening balance of each account at the start of a financial year.
    Balances are calculated from the previous year's closing balances.
    """
    __tablename__ = "opening_balances"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    society_id = Column(Integer, ForeignKey("societies.id", ondelete="CASCADE"), nullable=False, index=True)
    financial_year_id = Column(Integer, ForeignKey("financial_years.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Account Details
    account_head_id = Column(Integer, ForeignKey("account_codes.id"), nullable=False)
    account_name = Column(String(200), nullable=False)
    
    # Balance Details
    opening_balance = Column(Numeric(15, 2), nullable=False)
    balance_type = Column(SQLEnum(BalanceType), nullable=False)
    
    # Status
    status = Column(SQLEnum(BalanceStatus), default=BalanceStatus.PROVISIONAL, nullable=False)
    
    # Source
    calculated_from_previous_year = Column(Boolean, default=True, nullable=False)
    manual_entry = Column(Boolean, default=False, nullable=False)
    manual_entry_reason = Column(Text, nullable=True)
    
    # Audit Trail
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    finalized_at = Column(DateTime, nullable=True)
    finalized_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    society = relationship("Society")
    financial_year = relationship("FinancialYear")
    account_head = relationship("AccountCode", back_populates="opening_balances")
    creator = relationship("User", foreign_keys=[created_by])
    finalizer = relationship("User", foreign_keys=[finalized_by])
    
    def __repr__(self):
        return f"<OpeningBalance {self.account_name}: {self.opening_balance} ({self.status.value})>"

