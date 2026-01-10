"""
Online Payment Model for Payment Gateway Integration
Supports Razorpay and can be extended for other gateways
"""
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Text, Numeric, Boolean, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from ..database import Base


class PaymentGateway(str, enum.Enum):
    """Payment gateway enum"""
    RAZORPAY = "razorpay"
    PAYU = "payu"
    CASHFREE = "cashfree"
    PAYTM = "paytm"
    MANUAL = "manual"


class OnlinePaymentStatus(str, enum.Enum):
    """Online payment status enum"""
    CREATED = "created"  # Order created, awaiting payment
    PENDING = "pending"  # Payment initiated
    PROCESSING = "processing"  # Payment being processed
    SUCCESS = "success"  # Payment successful
    FAILED = "failed"  # Payment failed
    CANCELLED = "cancelled"  # User cancelled
    REFUNDED = "refunded"  # Payment refunded
    TIMEOUT = "timeout"  # Payment timed out


class OnlinePaymentMethod(str, enum.Enum):
    """Payment method enum"""
    UPI = "upi"
    CARD = "card"
    NETBANKING = "netbanking"
    WALLET = "wallet"
    EMI = "emi"
    PAYLATER = "paylater"


class OnlinePayment(Base):
    """
    Online Payment Record
    
    Tracks all online payment attempts and completions.
    Integrates with Razorpay (or other payment gateways).
    """
    __tablename__ = "online_payments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    society_id = Column(Integer, ForeignKey("societies.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Bill reference
    bill_id = Column(Integer, ForeignKey("maintenance_bills.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Member/Flat reference
    flat_id = Column(Integer, ForeignKey("flats.id"), nullable=False, index=True)
    member_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Gateway details
    gateway = Column(SQLEnum(PaymentGateway), default=PaymentGateway.RAZORPAY, nullable=False)
    
    # Razorpay specific fields
    razorpay_order_id = Column(String(100), nullable=True, index=True)  # order_xxx
    razorpay_payment_id = Column(String(100), nullable=True, index=True)  # pay_xxx
    razorpay_signature = Column(String(500), nullable=True)
    
    # Alternative gateway fields (for future)
    gateway_order_id = Column(String(200), nullable=True)
    gateway_payment_id = Column(String(200), nullable=True)
    gateway_transaction_id = Column(String(200), nullable=True)
    
    # Payment details
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default='INR', nullable=False)
    convenience_fee = Column(Numeric(10, 2), default=0, nullable=False)
    total_amount = Column(Numeric(15, 2), nullable=False)  # amount + convenience_fee
    
    # Status
    status = Column(SQLEnum(OnlinePaymentStatus), default=OnlinePaymentStatus.CREATED, nullable=False, index=True)
    
    # Payment method (filled after payment)
    payment_method = Column(SQLEnum(OnlinePaymentMethod), nullable=True)
    payment_method_details = Column(JSON, nullable=True)  # Card type, UPI app, etc.
    
    # Customer details
    customer_name = Column(String(200), nullable=True)
    customer_email = Column(String(200), nullable=True)
    customer_phone = Column(String(20), nullable=True)
    
    # Gateway response
    gateway_response = Column(JSON, nullable=True)
    error_code = Column(String(50), nullable=True)
    error_description = Column(Text, nullable=True)
    
    # Refund details (if applicable)
    is_refunded = Column(Boolean, default=False, nullable=False)
    refund_id = Column(String(100), nullable=True)
    refund_amount = Column(Numeric(15, 2), nullable=True)
    refund_date = Column(DateTime, nullable=True)
    refund_reason = Column(Text, nullable=True)
    
    # Link to payment record (once payment is successful)
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    payment_initiated_at = Column(DateTime, nullable=True)
    payment_completed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)  # Order expiry
    
    # Webhook tracking
    webhook_received = Column(Boolean, default=False, nullable=False)
    webhook_received_at = Column(DateTime, nullable=True)
    webhook_data = Column(JSON, nullable=True)
    
    # Metadata
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(Text, nullable=True)
    notes = Column(JSON, nullable=True)
    
    # Relationships
    society = relationship("Society")
    bill = relationship("MaintenanceBill")
    flat = relationship("Flat")
    member = relationship("User", foreign_keys=[member_id])
    payment = relationship("Payment")  # Link to actual payment record
    
    def __repr__(self):
        return f"<OnlinePayment {self.razorpay_order_id}: ₹{self.total_amount} ({self.status.value})>"
    
    @property
    def is_successful(self) -> bool:
        """Check if payment is successful"""
        return self.status == OnlinePaymentStatus.SUCCESS
    
    @property
    def is_pending(self) -> bool:
        """Check if payment is pending"""
        return self.status in [OnlinePaymentStatus.CREATED, OnlinePaymentStatus.PENDING, OnlinePaymentStatus.PROCESSING]
    
    @property
    def is_failed(self) -> bool:
        """Check if payment failed"""
        return self.status in [OnlinePaymentStatus.FAILED, OnlinePaymentStatus.CANCELLED, OnlinePaymentStatus.TIMEOUT]


class PaymentLink(Base):
    """
    Payment Link for sending to members
    
    Generates shareable payment links that can be sent via SMS/Email/WhatsApp
    """
    __tablename__ = "payment_links"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    society_id = Column(Integer, ForeignKey("societies.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Bill reference
    bill_id = Column(Integer, ForeignKey("maintenance_bills.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Link details
    link_id = Column(String(100), nullable=False, unique=True, index=True)  # Short unique ID
    short_url = Column(String(500), nullable=True)  # Razorpay short URL or custom
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_paid = Column(Boolean, default=False, nullable=False)
    
    # Payment reference (once paid)
    online_payment_id = Column(Integer, ForeignKey("online_payments.id"), nullable=True)
    
    # Tracking
    sent_via = Column(String(50), nullable=True)  # 'sms', 'email', 'whatsapp'
    sent_at = Column(DateTime, nullable=True)
    opened_count = Column(Integer, default=0, nullable=False)
    last_opened_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    expires_at = Column(DateTime, nullable=True)
    paid_at = Column(DateTime, nullable=True)
    
    # Relationships
    society = relationship("Society")
    bill = relationship("MaintenanceBill")
    online_payment = relationship("OnlinePayment")
    creator = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<PaymentLink {self.link_id}: {'Paid' if self.is_paid else 'Active' if self.is_active else 'Inactive'}>"

