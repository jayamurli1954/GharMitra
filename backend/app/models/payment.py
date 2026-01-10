"""
Payment Model for Bill Payment Collection
"""
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Text, Numeric, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from ..database import Base


class PaymentMode(str, enum.Enum):
    """Payment mode enum"""
    CASH = "cash"
    CHEQUE = "cheque"
    UPI = "upi"
    NEFT = "neft"
    RTGS = "rtgs"
    IMPS = "imps"
    BANK_TRANSFER = "bank_transfer"
    ONLINE = "online"
    DEBIT_CARD = "debit_card"
    CREDIT_CARD = "credit_card"
    OTHER = "other"


class PaymentStatus(str, enum.Enum):
    """Payment status enum"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class Payment(Base):
    """
    Payment Record for Maintenance Bills
    
    Tracks all payments made against maintenance bills.
    Supports partial payments, multiple payment modes, and complete audit trail.
    """
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    society_id = Column(Integer, ForeignKey("societies.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Bill reference
    bill_id = Column(Integer, ForeignKey("maintenance_bills.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Member/Flat reference (for quick access)
    flat_id = Column(Integer, ForeignKey("flats.id"), nullable=False, index=True)
    member_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Payment details
    receipt_number = Column(String(50), nullable=False, unique=True, index=True)  # e.g., "RCT/2024-25/001"
    payment_date = Column(Date, nullable=False, index=True)
    payment_mode = Column(SQLEnum(PaymentMode), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    
    # Transaction details (for cheque, bank transfer, UPI, etc.)
    transaction_reference = Column(String(200), nullable=True)  # Cheque number, UPI ref, transaction ID
    bank_name = Column(String(200), nullable=True)
    remarks = Column(Text, nullable=True)
    
    # Status
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.COMPLETED, nullable=False)
    
    # Accounting integration
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    journal_entry_number = Column(String(50), nullable=True)
    
    # Receipt
    receipt_generated = Column(Boolean, default=False, nullable=False)
    receipt_file_url = Column(String(500), nullable=True)  # Cloudinary URL if uploaded
    receipt_sent_at = Column(DateTime, nullable=True)
    
    # Late fee (if applicable)
    late_fee_charged = Column(Numeric(10, 2), default=0, nullable=False)
    
    # Partial payment support
    is_partial_payment = Column(Boolean, default=False, nullable=False)
    partial_payment_note = Column(Text, nullable=True)
    
    # Audit trail
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    recorded_by = Column(Integer, ForeignKey("users.id"), nullable=False)  # Admin who recorded
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    society = relationship("Society")
    bill = relationship("MaintenanceBill", back_populates="payments")
    flat = relationship("Flat")
    member = relationship("User", foreign_keys=[member_id])
    creator = relationship("User", foreign_keys=[created_by])
    recorder = relationship("User", foreign_keys=[recorded_by])
    transaction = relationship("Transaction")
    
    def __repr__(self):
        return f"<Payment {self.receipt_number}: ₹{self.amount}>"


class PaymentReminder(Base):
    """
    Payment Reminder for Overdue Bills
    
    Tracks reminders sent to members for overdue payments.
    """
    __tablename__ = "payment_reminders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    society_id = Column(Integer, ForeignKey("societies.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Bill reference
    bill_id = Column(Integer, ForeignKey("maintenance_bills.id", ondelete="CASCADE"), nullable=False, index=True)
    flat_id = Column(Integer, ForeignKey("flats.id"), nullable=False)
    member_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Reminder details
    reminder_date = Column(Date, nullable=False)
    reminder_type = Column(String(50), nullable=False)  # 'email', 'sms', 'whatsapp', 'push'
    days_overdue = Column(Integer, nullable=False)
    amount_due = Column(Numeric(15, 2), nullable=False)
    
    # Status
    sent = Column(Boolean, default=False, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    delivery_status = Column(String(50), nullable=True)  # 'delivered', 'failed', 'pending'
    
    # Content
    subject = Column(String(200), nullable=True)
    message = Column(Text, nullable=True)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    society = relationship("Society")
    bill = relationship("MaintenanceBill")
    flat = relationship("Flat")
    member = relationship("User", foreign_keys=[member_id])
    
    def __repr__(self):
        return f"<PaymentReminder Bill:{self.bill_id} Days:{self.days_overdue}>"

