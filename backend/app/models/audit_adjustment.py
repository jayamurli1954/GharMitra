"""
Audit Adjustment Model for Year-End Adjustments
"""
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Text, Numeric, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from ..database import Base


class AdjustmentType(str, enum.Enum):
    """Adjustment type enum"""
    INCOME_CORRECTION = "income_correction"
    EXPENSE_CORRECTION = "expense_correction"
    DEPRECIATION = "depreciation"
    PROVISION = "provision"
    BAD_DEBT = "bad_debt"
    ACCRUAL = "accrual"
    PREPAYMENT = "prepayment"
    RECLASSIFICATION = "reclassification"
    OTHER = "other"


class AuditAdjustment(Base):
    """
    Audit Adjustment Entry
    
    Tracks adjustments made to a provisionally closed financial year
    during the audit process. These entries are posted with an effective
    date in the closed year but are actually created later.
    """
    __tablename__ = "audit_adjustments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    society_id = Column(Integer, ForeignKey("societies.id", ondelete="CASCADE"), nullable=False, index=True)
    financial_year_id = Column(Integer, ForeignKey("financial_years.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Adjustment Details
    adjustment_number = Column(String(50), nullable=False, unique=True, index=True)  # e.g., "ADJ-2024-001"
    adjustment_date = Column(Date, nullable=False)  # Date posted (e.g., July 10, 2024)
    effective_date = Column(Date, nullable=False)  # Date effective (e.g., March 31, 2024)
    
    # Classification
    adjustment_type = Column(SQLEnum(AdjustmentType), nullable=False)
    
    # Description
    description = Column(Text, nullable=False)
    reason = Column(Text, nullable=False)
    auditor_reference = Column(String(200), nullable=True)  # e.g., "Audit Finding #3"
    
    # Amount
    amount = Column(Numeric(15, 2), nullable=False)
    
    # Approval Workflow
    requested_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    requested_at = Column(DateTime, nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    approved_at = Column(DateTime, nullable=False)
    
    # Journal Entry Reference
    journal_entry_number = Column(String(50), nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    society = relationship("Society")
    financial_year = relationship("FinancialYear")
    requester = relationship("User", foreign_keys=[requested_by])
    approver = relationship("User", foreign_keys=[approved_by])
    
    def __repr__(self):
        return f"<AuditAdjustment {self.adjustment_number}: {self.adjustment_type.value}>"

