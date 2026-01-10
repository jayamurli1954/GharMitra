"""
Financial Year Model for Year-wise Accounting with Three-Stage Closing
"""
from sqlalchemy import Column, Integer, String, Date, Boolean, DateTime, ForeignKey, Text, Numeric, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from ..database import Base


class YearStatus(str, enum.Enum):
    """Financial year status enum"""
    OPEN = "open"  # Current year, all transactions allowed
    PROVISIONAL_CLOSE = "provisional_close"  # Year ended, under review/audit
    FINAL_CLOSE = "final_close"  # Audited and locked permanently


class OpeningBalanceStatus(str, enum.Enum):
    """Opening balance status enum"""
    PROVISIONAL = "provisional"  # Can change if adjustments made to previous year
    FINALIZED = "finalized"  # Locked permanently after audit


class FinancialYear(Base):
    """
    Financial Year for society accounting with three-stage closing process
    
    Stages:
    1. OPEN: Current year, normal operations
    2. PROVISIONAL_CLOSE: Year-end, under audit, adjustments allowed
    3. FINAL_CLOSE: Audit complete, permanently locked
    """
    __tablename__ = "financial_years"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    society_id = Column(Integer, ForeignKey("societies.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Year details
    year_name = Column(String(50), nullable=False)  # e.g., "FY 2023-24", "2024-2025"
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    
    # Year Status (Three-stage system)
    status = Column(SQLEnum(YearStatus), default=YearStatus.OPEN, nullable=False, index=True)
    
    # Provisional Closing Information
    provisional_close_date = Column(Date, nullable=True)
    provisional_closed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Final Closing Information
    final_close_date = Column(Date, nullable=True)
    final_closed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Audit Information
    audit_start_date = Column(Date, nullable=True)
    audit_end_date = Column(Date, nullable=True)
    auditor_name = Column(String(200), nullable=True)
    auditor_firm = Column(String(200), nullable=True)
    audit_report_date = Column(Date, nullable=True)
    audit_report_file_url = Column(String(500), nullable=True)  # Cloudinary URL
    
    # Opening Balances Status
    opening_balances_status = Column(
        SQLEnum(OpeningBalanceStatus), 
        default=OpeningBalanceStatus.PROVISIONAL,
        nullable=False
    )
    
    # Legacy fields for compatibility
    is_active = Column(Boolean, default=True, nullable=False)
    is_closed = Column(Boolean, default=False, nullable=False)
    closed_at = Column(DateTime, nullable=True)
    closed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    closing_notes = Column(Text, nullable=True)
    
    # Financial summary at closing
    closing_bank_balance = Column(Numeric(15, 2), nullable=True)
    closing_cash_balance = Column(Numeric(15, 2), nullable=True)
    total_income = Column(Numeric(15, 2), nullable=True)
    total_expenses = Column(Numeric(15, 2), nullable=True)
    net_surplus_deficit = Column(Numeric(15, 2), nullable=True)
    
    # Audit trail
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    society = relationship("Society", back_populates="financial_years")
    provisional_closer = relationship("User", foreign_keys=[provisional_closed_by])
    final_closer = relationship("User", foreign_keys=[final_closed_by])
    closed_by = relationship("User", foreign_keys=[closed_by_user_id])  # Legacy
    
    def __repr__(self):
        return f"<FinancialYear {self.year_name} ({self.status.value})>"

