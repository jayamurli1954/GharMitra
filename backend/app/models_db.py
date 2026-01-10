"""
SQLAlchemy Database Models
All database tables defined here
"""
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Boolean, ForeignKey, Text, Date, Enum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, date
import enum

from app.database import Base


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    ACCOUNTANT = "accountant"
    RESIDENT = "resident"
    # Custom roles (defined per society)
    CHAIRMAN = "chairman"
    SECRETARY = "secretary"
    TREASURER = "treasurer"
    AUDITOR = "auditor"


class TransactionType(str, enum.Enum):
    INCOME = "income"
    EXPENSE = "expense"


class BillStatus(str, enum.Enum):
    UNPAID = "unpaid"
    PAID = "paid"


class CalculationMethod(str, enum.Enum):
    SQFT_RATE = "sqft_rate"
    VARIABLE = "variable"


class FrequencyType(str, enum.Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


class AccountType(str, enum.Enum):
    ASSET = "asset"
    LIABILITY = "liability"
    CAPITAL = "capital"
    INCOME = "income"
    EXPENSE = "expense"


class ChatRoomType(str, enum.Enum):
    GENERAL = "general"
    MAINTENANCE = "maintenance"
    ANNOUNCEMENTS = "announcements"


class OccupancyStatus(str, enum.Enum):
    """Occupancy status for flats per PRD"""
    OWNER_OCCUPIED = "owner_occupied"
    TENANT_OCCUPIED = "tenant_occupied"
    VACANT = "vacant"
    LOCKED = "locked"


class AccountingType(str, enum.Enum):
    """Accounting method type"""
    CASH = "cash"
    ACCRUAL = "accrual"


class MeetingType(str, enum.Enum):
    """Type of meeting"""
    MC = "MC"  # Management Committee meeting
    AGM = "AGM"  # Annual General Meeting
    EGM = "EGM"  # Extraordinary General Meeting
    SGM = "SGM"  # Special General Meeting
    COMMITTEE = "committee"  # Legacy: Board of Committee meeting
    GENERAL_BODY = "general_body"  # Legacy: General Body meeting


# ============ SOCIETY MODEL (PRD: Multi-Tenancy) ============
class Society(Base):
    """Society model for multi-tenant SaaS architecture per PRD"""
    __tablename__ = "societies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    address = Column(Text)  # Legacy field - use address_line, pin_code, city, state instead
    total_flats = Column(Integer, nullable=False, default=0)
    min_vacancy_fee = Column(Numeric(18, 2), default=500.0)  # For water calculation per PRD
    billing_config = Column(Text)  # JSON config per society
    subscription_plan = Column(String(50), default="free")  # For future subscription management
    # Self-service registration fields
    # NOTE: These fields are for SOCIETY documents only, NOT member documents
    registration_no = Column(String(100))  # Optional: Society Registration Number (SOCIETY only, not members)
    pan_no = Column(String(20))  # Optional: Society PAN Number (SOCIETY only, not members)
    reg_cert_url = Column(String(500))  # Optional: Registration Certificate URL (Cloudinary) - SOCIETY document only
    pan_card_url = Column(String(500))  # Optional: PAN Card URL (Cloudinary) - SOCIETY document only
    logo_url = Column(String(500))  # Optional: Society Logo URL (Cloudinary)
    # Address details
    address_line = Column(Text)  # Street address / Building name
    pin_code = Column(String(10))  # PIN/ZIP code
    city = Column(String(100))  # City name (auto-populated from PIN)
    state = Column(String(100))  # State name (selected from dropdown)
    # Contact information
    email = Column(String(255))  # Society email address
    landline = Column(String(20))  # Landline phone number
    mobile = Column(String(20))  # Mobile phone number
    # GST registration
    gst_registration_applicable = Column(Boolean, default=False, nullable=False)  # Whether GST registration is applicable
    # Financial year and accounting settings
    financial_year_start = Column(Date, nullable=True)  # Financial year start date (e.g., April 1)
    financial_year_end = Column(Date, nullable=True)  # Financial year end date (e.g., March 31)
    accounting_type = Column(Enum(AccountingType), default=AccountingType.CASH, nullable=False)  # Cash or Accrual accounting
    # Bank details for payment
    bank_name = Column(String(200))  # Bank name
    bank_branch = Column(String(200))  # Branch name
    bank_account_number = Column(String(50))  # Account number
    bank_ifsc_code = Column(String(20))  # IFSC code
    upi_qr_code_url = Column(String(500))  # Optional: UPI QR code URL
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    flats = relationship("Flat", back_populates="society")
    users = relationship("User", back_populates="society")
    transactions = relationship("Transaction", back_populates="society")
    chat_rooms = relationship("ChatRoom", back_populates="society")
    society_settings = relationship("SocietySettings", back_populates="society", uselist=False)
    meetings = relationship("Meeting", back_populates="society")
    financial_years = relationship("FinancialYear", back_populates="society")


# ============ SOCIETY SETTINGS MODEL ============
class SocietySettings(Base):
    """Comprehensive settings for society accounting and operations"""
    __tablename__ = "society_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    society_id = Column(Integer, ForeignKey("societies.id"), nullable=False, unique=True, index=True)
    
    # Penalty/Interest Rules
    late_payment_penalty_type = Column(String(20), nullable=True)  # 'percentage' or 'fixed'
    late_payment_penalty_value = Column(Numeric(18, 2), nullable=True)  # Percentage or fixed amount
    late_payment_grace_days = Column(Integer, nullable=True, default=0)  # Days before penalty applies
    interest_on_overdue = Column(Boolean, default=False, nullable=False)  # Enable interest on overdue
    interest_rate = Column(Numeric(18, 2), nullable=True)  # Annual interest rate percentage
    
    # Tax Configuration
    gst_enabled = Column(Boolean, default=False, nullable=False)
    gst_number = Column(String(15), nullable=True)  # GSTIN
    gst_rate = Column(Numeric(18, 2), nullable=True)  # Default GST rate percentage
    tds_enabled = Column(Boolean, default=False, nullable=False)
    tds_rate = Column(Numeric(18, 2), nullable=True)  # TDS rate percentage
    tds_threshold = Column(Numeric(18, 2), nullable=True)  # Amount threshold for TDS
    
    # Payment Gateway Settings
    payment_gateway_enabled = Column(Boolean, default=False, nullable=False)
    payment_gateway_provider = Column(String(50), nullable=True)  # 'razorpay', 'payu', 'stripe', etc.
    payment_gateway_key_id = Column(String(255), nullable=True)  # Encrypted
    payment_gateway_key_secret = Column(String(255), nullable=True)  # Encrypted
    upi_enabled = Column(Boolean, default=False, nullable=False)
    upi_id = Column(String(100), nullable=True)  # UPI ID for payments
    
    # Bank Account Settings (JSON for multiple accounts)
    bank_accounts = Column(JSON, nullable=True)  # Array of bank account details
    
    # Vendor Management Settings
    vendor_approval_required = Column(Boolean, default=False, nullable=False)
    vendor_approval_workflow = Column(String(50), nullable=True)  # 'single', 'multi_level'
    
    # Audit Trail Settings
    audit_trail_enabled = Column(Boolean, default=True, nullable=False)  # Enable by default
    audit_retention_days = Column(Integer, nullable=True, default=2555)  # 7 years default
    
    # Billing Settings
    billing_cycle = Column(String(20), nullable=True)  # 'monthly', 'quarterly', 'annual'
    auto_generate_bills = Column(Boolean, default=False, nullable=False)
    bill_due_days = Column(Integer, nullable=True, default=7)  # Days after bill generation
    
    # Detailed Billing Rules (Funds & Formulas)
    maintenance_calculation_logic = Column(String(20), default="sqft") # 'sqft', 'fixed', 'water_based'
    maintenance_rate_sqft = Column(Numeric(18, 2), default=0.0)
    maintenance_rate_flat = Column(Numeric(18, 2), default=0.0)
    sinking_fund_rate = Column(Numeric(18, 2), default=0.0)  # % of maintenance or fixed amount
    repair_fund_rate = Column(Numeric(18, 2), default=0.0)
    association_fund_rate = Column(Numeric(18, 2), default=0.0)
    corpus_fund_rate = Column(Numeric(18, 2), default=0.0)
    
    # Water Billing Rules
    water_calculation_type = Column(String(20), default="flat")  # 'flat', 'person', 'meter'
    water_rate_per_person = Column(Numeric(18, 2), default=0.0)
    water_min_charge = Column(Numeric(18, 2), default=0.0)
    
    # Expense Distribution
    expense_distribution_logic = Column(String(20), default="equal")  # 'equal', 'sqft', 'custom'
    fixed_expense_heads = Column(JSON, nullable=True) # List of fixed expense heads, e.g., ["Security", "Gardening"]

    
    # Member Settings
    bill_to_bill_tracking = Column(Boolean, default=True, nullable=False)  # Enable bill-to-bill tracking
    member_approval_required = Column(Boolean, default=False, nullable=False) # Auto-approve or Admin approval
    tenant_expiry_reminder_days = Column(Integer, default=30) # Reminder before tenant validity expires
    max_members_per_flat = Column(Integer, default=10) # Max allowed members per flat
    
    # Structure Settings
    blocks_config = Column(JSON, nullable=True) # JSON Config: [{"block": "A", "floors": 10, ...}]
    
    # Date Lock Settings for Transactions
    transaction_date_lock_enabled = Column(Boolean, default=True, nullable=False)  # Enable date lock by default
    transaction_date_lock_months = Column(Integer, default=1, nullable=False)  # Allow current month ± 1 month (default)
    
    # Billing Month Restriction
    onboarding_date = Column(Date, nullable=True)  # Date when society was onboarded (used to restrict bill generation to previous month only)
    
    # Notification Settings
    notification_config = Column(JSON, nullable=True) # { "sms": ..., "email": ..., "whatsapp": ... }

    # Complaint & Asset Settings
    complaint_config = Column(JSON, nullable=True) # { "categories": [], "slas": {} }
    asset_config = Column(JSON, nullable=True) # General asset settings
    
    # Legal & Compliance
    legal_config = Column(JSON, nullable=True) # { "agm_date": ..., "audit_due_date": ... }
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    society = relationship("Society", back_populates="society_settings")


# ============ CUSTOM ROLE MODEL ============
class CustomRole(Base):
    """Custom roles defined per society"""
    __tablename__ = "custom_roles"
    
    id = Column(Integer, primary_key=True, index=True)
    society_id = Column(Integer, ForeignKey("societies.id"), nullable=False, index=True)
    role_name = Column(String(50), nullable=False)  # e.g., "Chairman/President", "Secretary", "Treasurer" - flexible naming
    role_code = Column(String(50), nullable=False, index=True)  # e.g., "chairman", "secretary" - internal code
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_system_role = Column(Boolean, default=False, nullable=False)  # System roles can't be deleted
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    society = relationship("Society")
    permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")
    user_assignments = relationship("UserRoleAssignment", back_populates="role", cascade="all, delete-orphan")


# ============ PERMISSION MODEL ============
class Permission(Base):
    """System permissions"""
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    permission_code = Column(String(100), unique=True, nullable=False, index=True)  # e.g., "transactions.view", "transactions.create"
    permission_name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)  # e.g., "transactions", "billing", "settings"
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


# ============ ROLE PERMISSION MODEL ============
class RolePermission(Base):
    """Permissions assigned to roles"""
    __tablename__ = "role_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("custom_roles.id"), nullable=False, index=True)
    permission_id = Column(Integer, ForeignKey("permissions.id"), nullable=False, index=True)
    access_level = Column(String(20), nullable=False, default="view")  # "view", "create", "edit", "delete", "approve"
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    role = relationship("CustomRole", back_populates="permissions")
    permission = relationship("Permission")


# ============ USER ROLE ASSIGNMENT MODEL ============
class UserRoleAssignment(Base):
    """Assign custom roles to users"""
    __tablename__ = "user_role_assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    role_id = Column(Integer, ForeignKey("custom_roles.id"), nullable=False, index=True)
    assigned_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    role = relationship("CustomRole", back_populates="user_assignments")
    assigner = relationship("User", foreign_keys=[assigned_by])


# ============ APPROVAL WORKFLOW MODEL ============
class ApprovalWorkflow(Base):
    """Approval workflows for transactions and actions"""
    __tablename__ = "approval_workflows"
    
    id = Column(Integer, primary_key=True, index=True)
    society_id = Column(Integer, ForeignKey("societies.id"), nullable=False, index=True)
    workflow_name = Column(String(100), nullable=False)  # e.g., "Payment Approval", "Vendor Bill Approval"
    workflow_type = Column(String(50), nullable=False)  # e.g., "payment", "vendor_bill", "policy_change"
    approval_levels = Column(JSON, nullable=False)  # Array of approval levels with role requirements
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    society = relationship("Society")


# ============ APPROVAL REQUEST MODEL ============
class ApprovalRequest(Base):
    """Approval requests for transactions"""
    __tablename__ = "approval_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    society_id = Column(Integer, ForeignKey("societies.id"), nullable=False, index=True)
    workflow_id = Column(Integer, ForeignKey("approval_workflows.id"), nullable=True, index=True)
    request_type = Column(String(50), nullable=False)  # e.g., "payment", "vendor_bill"
    entity_id = Column(Integer, nullable=False)  # ID of the entity (transaction, bill, etc.)
    requested_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    current_level = Column(Integer, default=1, nullable=False)
    status = Column(String(20), default="pending", nullable=False)  # "pending", "approved", "rejected", "cancelled"
    approval_history = Column(JSON, nullable=True)  # Array of approval actions
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    society = relationship("Society")
    workflow = relationship("ApprovalWorkflow")
    requester = relationship("User", foreign_keys=[requested_by])


# ============ AUDIT LOG MODEL ============
class AuditLog(Base):
    """Audit trail for all system actions"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    society_id = Column(Integer, ForeignKey("societies.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    action_type = Column(String(50), nullable=False)  # e.g., "create", "update", "delete", "approve", "view"
    entity_type = Column(String(50), nullable=False)  # e.g., "transaction", "bill", "user", "settings"
    entity_id = Column(Integer, nullable=True)
    old_values = Column(JSON, nullable=True)  # Previous values (for updates)
    new_values = Column(JSON, nullable=True)
    ip_address = Column(String(50), nullable=True)  # IP address of the user
    user_agent = Column(String(500), nullable=True)  # User agent/browser info
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    society = relationship("Society")


# ============ ADMIN GUIDELINES ACKNOWLEDGMENT MODEL ============
class AdminGuidelinesAcknowledgment(Base):
    """Track which admins have read and acknowledged the guidelines"""
    __tablename__ = "admin_guidelines_acknowledgments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)  # One acknowledgment per user
    society_id = Column(Integer, ForeignKey("societies.id"), nullable=False, index=True)
    acknowledged_version = Column(String(20), nullable=False)  # Version of guidelines acknowledged
    acknowledged_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User")
    society = relationship("Society")


# ============ USER MODEL ============
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    society_id = Column(Integer, ForeignKey("societies.id"), nullable=False, default=1, index=True)  # PRD: Multi-tenancy
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    apartment_number = Column(String(50), nullable=False, index=True)
    phone_number = Column(String(20))
    role = Column(Enum(UserRole), default=UserRole.RESIDENT, nullable=False, index=True)
    # Legal consent fields (DPDP Act 2023 compliance)
    terms_accepted = Column(Boolean, default=False, nullable=False)
    privacy_accepted = Column(Boolean, default=False, nullable=False)
    consent_timestamp = Column(DateTime, nullable=True)
    consent_ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    consent_version = Column(String(20), nullable=True)  # Version of terms/privacy accepted
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    society = relationship("Society", back_populates="users")
    transactions = relationship("Transaction", back_populates="added_by_user")
    role_assignments = relationship("UserRoleAssignment", back_populates="user", foreign_keys="UserRoleAssignment.user_id")
    audit_logs = relationship("AuditLog", back_populates="user")


# ============ FLAT MODEL ============
class Flat(Base):
    __tablename__ = "flats"

    id = Column(Integer, primary_key=True, index=True)
    society_id = Column(Integer, ForeignKey("societies.id"), nullable=False, default=1, index=True)  # PRD: Multi-tenancy
    flat_number = Column(String(50), nullable=False, index=True)
    area_sqft = Column(Numeric(18, 2), nullable=False)
    bedrooms = Column(Integer, default=2, nullable=False)  # Number of bedrooms (2 or 3)
    owner_name = Column(String(100))
    owner_phone = Column(String(20))
    owner_email = Column(String(255))
    occupants = Column(Integer, default=1, nullable=False)
    occupancy_status = Column(Enum(OccupancyStatus), default=OccupancyStatus.OWNER_OCCUPIED, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    society = relationship("Society", back_populates="flats")
    maintenance_bills = relationship("MaintenanceBill", back_populates="flat")
    supplementary_bills = relationship("SupplementaryBillFlat", back_populates="flat")
    
    # Unique constraint: flat_number should be unique per society
    __table_args__ = (
        # Note: SQLite doesn't support named constraints well, will handle in application logic
    )


# ============ APARTMENT SETTINGS MODEL ============
class ApartmentSettings(Base):
    __tablename__ = "apartment_settings"

    id = Column(Integer, primary_key=True, index=True)
    society_id = Column(Integer, ForeignKey("societies.id"), nullable=False, default=1, index=True)  # PRD: Multi-tenancy
    apartment_name = Column(String(100), nullable=False)
    total_flats = Column(Integer, nullable=False)
    calculation_method = Column(Enum(CalculationMethod), default=CalculationMethod.VARIABLE, nullable=False)
    sqft_rate = Column(Numeric(18, 2))
    sinking_fund_total = Column(Numeric(18, 2))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    society = relationship("Society")


# ============ FIXED EXPENSE MODEL ============
class FixedExpense(Base):
    __tablename__ = "fixed_expenses"

    id = Column(Integer, primary_key=True, index=True)
    society_id = Column(Integer, ForeignKey("societies.id"), nullable=False, default=1, index=True)  # PRD: Multi-tenancy
    name = Column(String(100), nullable=False)
    amount = Column(Numeric(18, 2), nullable=False)
    frequency = Column(Enum(FrequencyType), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    society = relationship("Society")


# ============ WATER EXPENSE MODEL ============
class WaterExpense(Base):
    __tablename__ = "water_expenses"

    id = Column(Integer, primary_key=True, index=True)
    society_id = Column(Integer, ForeignKey("societies.id"), nullable=False, default=1, index=True)  # PRD: Multi-tenancy
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    tanker_charges = Column(Numeric(18, 2), default=0.0, nullable=False)
    government_charges = Column(Numeric(18, 2), default=0.0, nullable=False)
    other_charges = Column(Numeric(18, 2), default=0.0, nullable=False)
    total_amount = Column(Numeric(18, 2), nullable=False)  # Calculated: tanker + government + other
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    society = relationship("Society")
    
    @property
    def total_water_expense(self) -> float:
        """Calculate total water expense"""
        return self.tanker_charges + self.government_charges + self.other_charges

    # Unique constraint on society_id + month + year (handled in application logic for SQLite)


# ============ MAINTENANCE BILL MODEL ============
class MaintenanceBill(Base):
    __tablename__ = "maintenance_bills"

    id = Column(Integer, primary_key=True, index=True)
    society_id = Column(Integer, ForeignKey("societies.id"), nullable=False, default=1, index=True)  # PRD: Multi-tenancy
    flat_id = Column(Integer, ForeignKey("flats.id"), nullable=False, index=True)
    flat_number = Column(String(50), nullable=False, index=True)  # Flat number for quick reference
    bill_number = Column(String(50), unique=True, nullable=True, index=True)  # Unique bill number (e.g., BILL-2025-11-001)
    month = Column(Integer, nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)
    
    # Financial Components
    amount = Column(Numeric(18, 2), nullable=False)  # Total current monthly charges (maint + water + fixed + sinking + repair + corpus + late + supp)
    maintenance_amount = Column(Numeric(18, 2), nullable=False, default=0.0)
    water_amount = Column(Numeric(18, 2), default=0.0, nullable=False)
    fixed_amount = Column(Numeric(18, 2), default=0.0, nullable=False)
    sinking_fund_amount = Column(Numeric(18, 2), default=0.0, nullable=False)
    repair_fund_amount = Column(Numeric(18, 2), default=0.0, nullable=False)  # CR-021
    corpus_fund_amount = Column(Numeric(18, 2), default=0.0, nullable=False)  # CR-021
    arrears_amount = Column(Numeric(18, 2), default=0.0, nullable=False)
    late_fee_amount = Column(Numeric(18, 2), default=0.0, nullable=False)
    
    total_amount = Column(Numeric(18, 2), nullable=False)  # amount + arrears
    
    breakdown = Column(JSON, nullable=True)  # Store detailed bill breakdown as JSON
    status = Column(Enum(BillStatus), default=BillStatus.UNPAID, nullable=False, index=True)
    due_date = Column(Date, nullable=True)
    paid_date = Column(Date, nullable=True)
    is_posted = Column(Boolean, default=False, nullable=False, index=True)
    posted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    flat = relationship("Flat", back_populates="maintenance_bills")
    payments = relationship("Payment", back_populates="bill")
    supplementary_charges = relationship("SupplementaryBillFlat", back_populates="maintenance_bill")


# ============ SUPPLEMENTARY BILL MODELS ============
class SupplementaryBill(Base):
    __tablename__ = "supplementary_bills"

    id = Column(Integer, primary_key=True, index=True)
    society_id = Column(Integer, ForeignKey("societies.id"), nullable=False, default=1, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    date = Column(Date, default=date.today, nullable=False)
    approved_by = Column(String(100), nullable=True)
    status = Column(String(20), default="draft", nullable=False) # draft, approved, posted
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    flats = relationship("SupplementaryBillFlat", back_populates="bill", cascade="all, delete-orphan")


class SupplementaryBillFlat(Base):
    __tablename__ = "supplementary_bill_flats"

    id = Column(Integer, primary_key=True, index=True)
    supplementary_bill_id = Column(Integer, ForeignKey("supplementary_bills.id"), nullable=False, index=True)
    flat_id = Column(Integer, ForeignKey("flats.id"), nullable=False, index=True)
    amount = Column(Numeric(18, 2), nullable=False)
    is_included_in_monthly = Column(Boolean, default=False, nullable=False) # Linked to a MaintenanceBill
    maintenance_bill_id = Column(Integer, ForeignKey("maintenance_bills.id"), nullable=True, index=True)
    status = Column(String(20), default="unpaid", nullable=False) # unpaid, paid

    # Relationships
    bill = relationship("SupplementaryBill", back_populates="flats")
    flat = relationship("Flat", back_populates="supplementary_bills")
    maintenance_bill = relationship("MaintenanceBill", back_populates="supplementary_charges")


# ============ TRANSACTION MODEL ============
class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    society_id = Column(Integer, ForeignKey("societies.id"), nullable=False, default=1, index=True)  # PRD: Multi-tenancy
    document_number = Column(String(50), unique=True, nullable=True, index=True)  # Auto-generated document number (TXN-YYYYMMDD-001)
    type = Column(Enum(TransactionType), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)
    account_code = Column(String(10), index=True)
    amount = Column(Numeric(18, 2), nullable=False)
    description = Column(Text, nullable=False)
    date = Column(Date, nullable=False, index=True)
    expense_month = Column(String(50), nullable=True)  # Month this expense belongs to (e.g. "January, 2026")
    added_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    # Quantity and unit price for itemized transactions (e.g., water tanker: 20 tankers × 400 = 8000)
    quantity = Column(Numeric(18, 2), nullable=True)  # Quantity/units (e.g., 20 tankers)
    unit_price = Column(Numeric(18, 2), nullable=True)  # Price per unit (e.g., 400 per tanker)
    # Double-entry bookkeeping fields
    debit_amount = Column(Numeric(18, 2), default=0.0)  # Debit amount for this account
    credit_amount = Column(Numeric(18, 2), default=0.0)  # Credit amount for this account
    journal_entry_id = Column(Integer, ForeignKey("journal_entries.id"), nullable=True, index=True)  # Link to journal entry if part of one
    payment_method = Column(String(20))  # 'cash' or 'bank'
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=True, index=True) # Linked Vendor for AP
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    society = relationship("Society", back_populates="transactions")
    added_by_user = relationship("User", back_populates="transactions")
    journal_entry = relationship("JournalEntry", back_populates="entries")
    vendor = relationship("Vendor", back_populates="transactions")


# ============ JOURNAL ENTRY MODEL ============
class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id = Column(Integer, primary_key=True, index=True)
    society_id = Column(Integer, ForeignKey("societies.id"), nullable=False, default=1, index=True)  # PRD: Multi-tenancy
    entry_number = Column(String(50), unique=True, nullable=False, index=True)  # Auto-generated entry number
    date = Column(Date, nullable=False, index=True)
    expense_month = Column(String(50), nullable=True)  # Month this journal entry belongs to
    description = Column(Text, nullable=False)
    total_debit = Column(Numeric(18, 2), nullable=False, default=0.0)
    total_credit = Column(Numeric(18, 2), nullable=False, default=0.0)
    is_balanced = Column(Boolean, default=False)  # True if debit = credit
    added_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    society = relationship("Society")
    creator = relationship("User")
    entries = relationship("Transaction", back_populates="journal_entry")


# ============ ACCOUNT CODE MODEL ============
class AccountCode(Base):
    __tablename__ = "account_codes"

    id = Column(Integer, primary_key=True, index=True)
    society_id = Column(Integer, ForeignKey("societies.id"), nullable=False, default=1, index=True)  # PRD: Multi-tenancy
    code = Column(String(10), nullable=False, index=True)  # Removed unique, now unique per society
    name = Column(String(100), nullable=False)
    type = Column(Enum(AccountType), nullable=False, index=True)
    description = Column(Text)
    opening_balance = Column(Numeric(18, 2), default=0, nullable=False)
    current_balance = Column(Numeric(18, 2), default=0, nullable=False)
    is_fixed_expense = Column(Boolean, default=False, nullable=False, index=True)  # If True, include in fixed expenses calculation for maintenance bills
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    society = relationship("Society")
    opening_balances = relationship("OpeningBalance", back_populates="account_head")


# ============ CHAT ROOM MODEL ============
class ChatRoom(Base):
    __tablename__ = "chat_rooms"

    id = Column(Integer, primary_key=True, index=True)
    society_id = Column(Integer, ForeignKey("societies.id"), nullable=False, default=1, index=True)  # PRD: Multi-tenancy
    name = Column(String(100), nullable=False)
    type = Column(Enum(ChatRoomType), default=ChatRoomType.GENERAL, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_message_at = Column(DateTime)

    # Relationships
    society = relationship("Society", back_populates="chat_rooms")  # PRD: Multi-tenancy
    messages = relationship("Message", back_populates="room")


# ============ MESSAGE MODEL ============
class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("chat_rooms.id"), nullable=False, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    sender_name = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    room = relationship("ChatRoom", back_populates="messages")


# ============ VENDOR MODEL ============
class Vendor(Base):
    """Vendor/Supplier model for Accounts Payable"""
    __tablename__ = "vendors"
    
    id = Column(Integer, primary_key=True, index=True)
    society_id = Column(Integer, ForeignKey("societies.id"), nullable=False, default=1, index=True)
    name = Column(String(100), nullable=False)
    category = Column(String(50)) # e.g., Plumber, Water Supplier, Electrician
    contact_person = Column(String(100))
    phone_number = Column(String(20))
    email = Column(String(100))
    address = Column(Text)
    tax_id = Column(String(50)) # GST/PAN
    
    # Financials
    opening_balance = Column(Numeric(18, 2), default=0.0) # Positive = Payable (Credit), Negative = Advance (Debit)
    current_balance = Column(Numeric(18, 2), default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    society = relationship("Society")
    transactions = relationship("Transaction", back_populates="vendor")


# ============ MEMBER MODEL ============
# IMPORTANT: Legal Compliance - We DO NOT store Aadhaar or PAN card documents or numbers
# We only collect for PRIMARY MEMBER: name, mobile number, email, and status (Owner/Tenant)
class MemberType(str, enum.Enum):
    OWNER = "owner"
    TENANT = "tenant"


class Member(Base):
    """
    Member Model - Primary member information only
    LEGAL COMPLIANCE: We DO NOT store:
    - Aadhaar documents or Aadhaar numbers
    - PAN card documents or PAN numbers
    - Sale Deed documents
    - Rental Agreement documents
    
    We ONLY collect for PRIMARY MEMBER:
    - name: Member's full name
    - phone_number: Mobile number (unique identifier for login matching)
    - email: Email address
    - member_type: Owner or Tenant status
    """
    __tablename__ = "members"
    
    id = Column(Integer, primary_key=True, index=True)
    society_id = Column(Integer, ForeignKey("societies.id"), nullable=False, default=1, index=True)
    flat_id = Column(Integer, ForeignKey("flats.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    name = Column(String(100), nullable=False)  # Primary member name only
    phone_number = Column(String(20), nullable=False, index=True)  # Unique identifier for login matching - mobile number only
    email = Column(String(255), nullable=False)  # Primary member email only
    member_type = Column(Enum(MemberType), nullable=False, index=True)  # Owner or Tenant status
    occupation = Column(String(100), nullable=True) # Added for Onboarding
    is_mobile_public = Column(Boolean, default=False, nullable=False) # Privacy Toggle
    is_primary = Column(Boolean, default=True, nullable=False)
    move_in_date = Column(Date, nullable=False, index=True)  # Used for filtering transactions
    move_out_date = Column(Date, nullable=True, index=True)  # For moving out logic - members don't see records after this date
    status = Column(String(20), default="inactive", nullable=False, index=True)  # "active" or "inactive" - inactive until user claims profile
    clerk_user_id = Column(String(255), nullable=True, unique=True, index=True)  # Clerk user ID after profile is claimed
    total_occupants = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    society = relationship("Society")
    flat = relationship("Flat")
    user = relationship("User", foreign_keys=[user_id])
    family_members = relationship("FamilyMember", back_populates="primary_member", cascade="all, delete-orphan")
    document_checklist = relationship("DocumentChecklist", back_populates="member", cascade="all, delete-orphan", uselist=False)


# ============ FAMILY MEMBER MODEL ============
class FamilyMember(Base):
    __tablename__ = "family_members"
    
    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    relationship_type = Column(String(50), nullable=False)  # Renamed from 'relationship'
    age = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    primary_member = relationship("Member", back_populates="family_members")


# ============ DOCUMENT TYPE ENUM ============
class DocumentType(str, enum.Enum):
    AADHAAR = "aadhaar"
    PAN_CARD = "pan_card"
    SALE_DEED = "sale_deed"
    RENTAL_AGREEMENT = "rental_agreement"


# ============ DOCUMENT CHECKLIST MODEL ============
# IMPORTANT: This is a CHECKLIST only - it tracks STATUS and DATE of submission
# We DO NOT store the actual documents or document numbers (Aadhaar/PAN numbers)
# This is for admin tracking purposes only - to know if documents were submitted
class DocumentChecklist(Base):
    """
    Document Checklist - Tracks submission status only (NOT documents or numbers)
    LEGAL COMPLIANCE: This model only tracks:
    - Status: "pending" or "submitted" 
    - Submitted date: When document was submitted
    
    We DO NOT store:
    - Actual document files
    - Aadhaar numbers
    - PAN numbers
    - Any sensitive document details
    """
    __tablename__ = "document_checklists"
    
    id = Column(Integer, primary_key=True, index=True)
    society_id = Column(Integer, ForeignKey("societies.id"), nullable=False, default=1, index=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False, unique=True, index=True)
    flat_id = Column(Integer, ForeignKey("flats.id"), nullable=False, index=True)
    # Status tracking only - NO document storage
    aadhaar_status = Column(String(20), default="pending", nullable=False)  # "pending" or "submitted" only
    aadhaar_submitted_date = Column(Date, nullable=True)  # Date only, NO Aadhaar number stored
    pan_card_status = Column(String(20), default="pending", nullable=False)  # "pending" or "submitted" only
    pan_card_submitted_date = Column(Date, nullable=True)  # Date only, NO PAN number stored
    sale_deed_status = Column(String(20), default="pending", nullable=False)
    sale_deed_submitted_date = Column(Date, nullable=True)
    rental_agreement_status = Column(String(20), default="pending", nullable=False)
    rental_agreement_submitted_date = Column(Date, nullable=True)
    last_updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    society = relationship("Society")
    member = relationship("Member", back_populates="document_checklist")
    flat = relationship("Flat")
    updated_by_user = relationship("User", foreign_keys=[last_updated_by])


# ============ RESOURCE FILE MODEL ============
class ResourceFile(Base):
    """Resource files uploaded by admins (NOC templates, forms, documents)"""
    __tablename__ = "resource_files"
    
    id = Column(Integer, primary_key=True, index=True)
    society_id = Column(Integer, ForeignKey("societies.id"), nullable=False, default=1, index=True)
    file_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False, default="other", index=True)  # 'noc', 'form', 'template', 'other'
    file_url = Column(String(500), nullable=False)  # URL to file (Cloudinary or other storage)
    file_size = Column(Integer, nullable=True)  # Size in bytes
    mime_type = Column(String(100), nullable=True)  # e.g., 'application/pdf'
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    society = relationship("Society")
    creator = relationship("User", foreign_keys=[created_by])


# ============ NOC DOCUMENT MODEL ============
class NOCDocument(Base):
    """No Objection Certificate documents"""
    __tablename__ = "noc_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    society_id = Column(Integer, ForeignKey("societies.id"), nullable=False, default=1, index=True)
    flat_id = Column(Integer, ForeignKey("flats.id"), nullable=False, index=True)
    member_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    noc_type = Column(String(50), nullable=False, index=True)  # 'society_move_out', 'owner_tenant_move_in'
    noc_number = Column(String(50), nullable=False, unique=True, index=True)  # Auto-generated unique ID
    file_url = Column(String(500), nullable=False)  # URL to PDF document
    qr_code_url = Column(String(500), nullable=True)  # URL to QR code image
    move_out_date = Column(Date, nullable=True)  # For move-out NOCs
    move_in_date = Column(Date, nullable=True)  # For tenant move-in NOCs
    new_owner_name = Column(String(100), nullable=True)  # For ownership transfer
    new_tenant_name = Column(String(100), nullable=True)  # For tenant move-in
    lease_start_date = Column(Date, nullable=True)  # For tenant move-in
    lease_duration_months = Column(Integer, nullable=True)  # For tenant move-in
    status = Column(String(20), default="pending", nullable=False, index=True)  # 'pending', 'approved', 'issued'
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    issued_at = Column(DateTime, nullable=True)
    issued_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    society = relationship("Society")
    flat = relationship("Flat")
    member = relationship("User", foreign_keys=[member_id])
    issuer = relationship("User", foreign_keys=[issued_by])


# ============ DOCUMENT TEMPLATE MODEL ============
class DocumentTemplate(Base):
    """Document templates library for Resource Centre (NO storage of filled forms)"""
    __tablename__ = "document_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    society_id = Column(Integer, ForeignKey("societies.id"), nullable=False, default=1, index=True)
    
    # Template identification
    template_name = Column(String(200), nullable=False)
    template_code = Column(String(50), nullable=False, unique=True, index=True)  # e.g., 'NOC_MOVEOUT'
    
    # Category
    category = Column(String(50), nullable=False, index=True)  # 'moveout', 'maintenance', etc.
    
    # Template content
    template_html = Column(Text, nullable=False)  # HTML template with {{variables}}
    template_variables = Column(Text, nullable=True)  # JSON array: ["member_name", "flat_number"]
    
    # Metadata
    description = Column(Text, nullable=True)
    instructions = Column(Text, nullable=True)
    
    # Template type
    template_type = Column(String(20), nullable=False, index=True)  # 'blank_download' or 'auto_fill'
    
    # Auto-fill configuration
    can_autofill = Column(Boolean, default=False, nullable=False)
    autofill_fields = Column(Text, nullable=True)  # JSON: fields to auto-fill from profile
    
    # Access control
    available_to = Column(String(20), default="all", nullable=False)  # 'all', 'admin_only', 'owner_only', 'committee_only'
    
    # Display
    icon_name = Column(String(50), nullable=True)
    display_order = Column(Integer, default=0, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    society = relationship("Society")
    usage_logs = relationship("TemplateUsageLog", back_populates="template", cascade="all, delete-orphan")


# ============ TEMPLATE CATEGORY MODEL ============
class TemplateCategory(Base):
    """Template categories for display"""
    __tablename__ = "template_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Category info
    category_code = Column(String(50), nullable=False, unique=True, index=True)  # Must match enum in document_templates
    category_name = Column(String(100), nullable=False)
    category_description = Column(Text, nullable=True)
    
    # Display
    icon_name = Column(String(50), nullable=True)
    display_order = Column(Integer, default=0, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)


# ============ TEMPLATE USAGE LOG MODEL ============
class TemplateUsageLog(Base):
    """Usage statistics for templates (NO content stored!)"""
    __tablename__ = "template_usage_log"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # What was generated
    template_id = Column(Integer, ForeignKey("document_templates.id"), nullable=False, index=True)
    template_code = Column(String(50), nullable=False, index=True)  # Denormalized for quick queries
    
    # Who generated it
    society_id = Column(Integer, ForeignKey("societies.id"), nullable=False, index=True)
    member_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # When
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Device/platform info (optional)
    platform = Column(String(20), nullable=True)  # 'android', 'ios', 'web'
    
    # IMPORTANT: We do NOT store:
    # - form_data (what user filled)
    # - generated_pdf_url (where PDF is)
    # - filled_variables (actual values)
    # We only log THAT it was generated, not WHAT was generated!
    
    # Relationships
    template = relationship("DocumentTemplate", back_populates="usage_logs")
    society = relationship("Society")
    member = relationship("User", foreign_keys=[member_id])


# ============ MEETING STATUS ENUM ============
class MeetingStatus(str, enum.Enum):
    """Status of meeting"""
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# ============ MEETING MODEL ============
class Meeting(Base):
    """Society meetings - Committee meetings and General Body meetings"""
    __tablename__ = "meetings"
    
    id = Column(Integer, primary_key=True, index=True)
    society_id = Column(Integer, ForeignKey("societies.id"), nullable=False, default=1, index=True)
    meeting_type = Column(Enum(MeetingType), nullable=False, index=True)  # MC, AGM, EGM, SGM, etc.
    
    # Meeting details
    meeting_number = Column(String(50), nullable=True, index=True)  # e.g., "MC/2024/001"
    meeting_date = Column(Date, nullable=False, index=True)
    meeting_time = Column(String(20), nullable=True)  # e.g., "10:00 AM"
    meeting_title = Column(String(200), nullable=False)  # e.g., "Monthly Committee Meeting - November 2025"
    venue = Column(String(200), nullable=True)  # Meeting venue/location
    
    # Notice details
    notice_sent = Column(Boolean, default=False, nullable=False, index=True)  # Whether meeting notice was sent
    notice_sent_at = Column(DateTime, nullable=True)  # When notice was sent
    notice_sent_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # Admin who sent the notice
    notice_sent_to = Column(String(50), nullable=True)  # 'all_members' or 'mc_only'
    
    # Status
    status = Column(Enum(MeetingStatus), default=MeetingStatus.SCHEDULED, nullable=False, index=True)
    
    # Attendance
    total_members_eligible = Column(Integer, nullable=True)
    total_members_present = Column(Integer, default=0, nullable=False)
    quorum_required = Column(Integer, nullable=True)
    quorum_met = Column(Boolean, default=False, nullable=False)
    
    # Minutes
    minutes_text = Column(Text, nullable=True)
    minutes_approved = Column(Boolean, default=False, nullable=False)
    minutes_approved_date = Column(Date, nullable=True)
    
    # Recording
    recorded_by = Column(String(100), nullable=True)  # Name of person who recorded minutes
    recorded_at = Column(DateTime, nullable=True)
    
    # Legacy fields (for backward compatibility)
    agenda = Column(Text, nullable=True)  # Legacy: Meeting agenda (use agenda_items relationship instead)
    attendees_count = Column(Integer, nullable=True)  # Legacy: Number of attendees (use total_members_present)
    chaired_by = Column(String(100), nullable=True)  # Name of person who chaired the meeting
    
    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)  # Admin who created the meeting record
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    society = relationship("Society")
    creator = relationship("User", foreign_keys=[created_by])
    notice_sender = relationship("User", foreign_keys=[notice_sent_by])
    agenda_items = relationship("MeetingAgendaItem", back_populates="meeting", cascade="all, delete-orphan")
    attendance = relationship("MeetingAttendance", back_populates="meeting", cascade="all, delete-orphan")
    resolutions = relationship("MeetingResolution", back_populates="meeting", cascade="all, delete-orphan")


# ============ AGENDA ITEM STATUS ENUM ============
class AgendaItemStatus(str, enum.Enum):
    """Status of agenda item"""
    PENDING = "pending"
    DISCUSSED = "discussed"
    RESOLVED = "resolved"
    DEFERRED = "deferred"
    WITHDRAWN = "withdrawn"


# ============ MEETING AGENDA ITEM MODEL ============
class MeetingAgendaItem(Base):
    """Agenda items for meetings"""
    __tablename__ = "meeting_agenda_items"
    
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False, index=True)
    society_id = Column(Integer, ForeignKey("societies.id"), nullable=False, index=True)
    
    # Agenda item details
    item_number = Column(Integer, nullable=False)
    item_title = Column(String(200), nullable=False)
    item_description = Column(Text, nullable=True)
    
    # Discussion
    discussion_summary = Column(Text, nullable=True)
    
    # Status
    status = Column(Enum(AgendaItemStatus), default=AgendaItemStatus.PENDING, nullable=False)
    
    # Resolution link
    resolution_id = Column(Integer, ForeignKey("meeting_resolutions.id"), nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    meeting = relationship("Meeting", back_populates="agenda_items")
    society = relationship("Society")
    resolution = relationship("MeetingResolution", foreign_keys=[resolution_id])


# ============ ATTENDANCE STATUS ENUM ============
class AttendanceStatus(str, enum.Enum):
    """Attendance status"""
    PRESENT = "present"
    PROXY = "proxy"
    ABSENT = "absent"


# ============ MEETING ATTENDANCE MODEL ============
class MeetingAttendance(Base):
    """Attendance records for meetings"""
    __tablename__ = "meeting_attendance"
    
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False, index=True)
    society_id = Column(Integer, ForeignKey("societies.id"), nullable=False, index=True)
    
    # Attendee
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False, index=True)
    member_name = Column(String(100), nullable=False)
    member_flat = Column(String(50), nullable=True)
    
    # Attendance status
    status = Column(Enum(AttendanceStatus), nullable=False)
    
    # Proxy details
    proxy_holder_id = Column(Integer, ForeignKey("members.id"), nullable=True)
    proxy_holder_name = Column(String(100), nullable=True)
    
    # Time tracking
    arrival_time = Column(String(20), nullable=True)  # e.g., "10:15 AM"
    departure_time = Column(String(20), nullable=True)  # e.g., "12:30 PM"
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    meeting = relationship("Meeting", back_populates="attendance")
    society = relationship("Society")
    member = relationship("Member", foreign_keys=[member_id])
    proxy_holder = relationship("Member", foreign_keys=[proxy_holder_id])


# ============ RESOLUTION TYPE ENUM ============
class ResolutionType(str, enum.Enum):
    """Type of resolution"""
    ORDINARY = "ordinary"
    SPECIAL = "special"
    UNANIMOUS = "unanimous"


# ============ RESOLUTION RESULT ENUM ============
class ResolutionResult(str, enum.Enum):
    """Result of resolution"""
    PASSED = "passed"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


# ============ IMPLEMENTATION STATUS ENUM ============
class ImplementationStatus(str, enum.Enum):
    """Status of resolution implementation"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# ============ MEETING RESOLUTION MODEL ============
class MeetingResolution(Base):
    """Resolutions passed in meetings"""
    __tablename__ = "meeting_resolutions"
    
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False, index=True)
    society_id = Column(Integer, ForeignKey("societies.id"), nullable=False, index=True)
    
    # Resolution details
    resolution_number = Column(String(50), nullable=False, unique=True, index=True)  # e.g., "RES/2024/001"
    resolution_type = Column(Enum(ResolutionType), nullable=True)
    
    # Resolution text
    resolution_title = Column(String(200), nullable=False)
    resolution_text = Column(Text, nullable=False)
    
    # Proposer & Seconder
    proposed_by_id = Column(Integer, ForeignKey("members.id"), nullable=True)
    proposed_by_name = Column(String(100), nullable=False)
    seconded_by_id = Column(Integer, ForeignKey("members.id"), nullable=True)
    seconded_by_name = Column(String(100), nullable=False)
    
    # Voting
    votes_for = Column(Integer, default=0, nullable=False)
    votes_against = Column(Integer, default=0, nullable=False)
    votes_abstain = Column(Integer, default=0, nullable=False)
    
    # Result
    result = Column(Enum(ResolutionResult), nullable=False)
    
    # Implementation
    action_items = Column(Text, nullable=True)
    assigned_to = Column(String(100), nullable=True)
    due_date = Column(Date, nullable=True)
    implementation_status = Column(Enum(ImplementationStatus), default=ImplementationStatus.PENDING, nullable=False, index=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    meeting = relationship("Meeting", back_populates="resolutions")
    society = relationship("Society")
    proposer = relationship("Member", foreign_keys=[proposed_by_id])
    seconder = relationship("Member", foreign_keys=[seconded_by_id])


# ============ VOTE TYPE ENUM ============
class VoteType(str, enum.Enum):
    """Type of vote"""
    FOR = "for"
    AGAINST = "against"
    ABSTAIN = "abstain"


# ============ MEETING VOTE MODEL ============
class MeetingVote(Base):
    """Individual votes on resolutions (optional - for detailed tracking)"""
    __tablename__ = "meeting_votes"
    
    id = Column(Integer, primary_key=True, index=True)
    resolution_id = Column(Integer, ForeignKey("meeting_resolutions.id"), nullable=False, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False, index=True)
    society_id = Column(Integer, ForeignKey("societies.id"), nullable=False, index=True)
    
    # Voter
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False, index=True)
    member_name = Column(String(100), nullable=False)
    
    # Vote
    vote = Column(Enum(VoteType), nullable=False)
    
    # Metadata
    voted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    resolution = relationship("MeetingResolution")
    meeting = relationship("Meeting")
    society = relationship("Society")
    member = relationship("Member")


# ============ MOVE-OUT REQUEST STATUS ENUM ============
class MoveOutRequestStatus(str, enum.Enum):
    """Status of move-out request"""
    PENDING = "pending"
    DUES_VERIFICATION = "dues_verification"
    INSPECTION = "inspection"
    SETTLEMENT = "settlement"
    NOC_ISSUED = "noc_issued"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# ============ MOVE-OUT REQUEST MODEL ============
class MoveOutRequest(Base):
    """Move-out request from member"""
    __tablename__ = "moveout_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    society_id = Column(Integer, ForeignKey("societies.id"), nullable=False, index=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False, index=True)
    flat_id = Column(Integer, ForeignKey("flats.id"), nullable=False, index=True)
    
    # Request details
    request_date = Column(Date, default=datetime.utcnow().date(), nullable=False)
    expected_moveout_date = Column(Date, nullable=True)
    reason = Column(String(50), nullable=True)  # 'sale', 'transfer', 'lease_end', 'other'
    contact_phone = Column(String(20), nullable=True)
    contact_email = Column(String(255), nullable=True)
    forwarding_address = Column(Text, nullable=True)
    
    # Status tracking
    status = Column(Enum(MoveOutRequestStatus), default=MoveOutRequestStatus.PENDING, nullable=False, index=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    society = relationship("Society")
    member = relationship("Member")
    flat = relationship("Flat")
    checklist = relationship("MoveOutChecklist", back_populates="moveout_request", uselist=False, cascade="all, delete-orphan")
    noc_logs = relationship("NOCGenerationLog", back_populates="moveout_request", cascade="all, delete-orphan")


# ============ SETTLEMENT STATUS ENUM ============
class SettlementStatus(str, enum.Enum):
    """Status of final settlement"""
    PENDING = "pending"
    CALCULATED = "calculated"
    PAID = "paid"
    COMPLETED = "completed"


# ============ MOVE-OUT CHECKLIST MODEL ============
class MoveOutChecklist(Base):
    """Move-out checklist - tracks all verification steps"""
    __tablename__ = "moveout_checklist"
    
    id = Column(Integer, primary_key=True, index=True)
    moveout_request_id = Column(Integer, ForeignKey("moveout_requests.id"), nullable=False, unique=True, index=True)
    society_id = Column(Integer, ForeignKey("societies.id"), nullable=False, index=True)
    
    # Dues Verification (Digital - from existing records)
    maintenance_dues_cleared = Column(Boolean, default=False, nullable=False)
    maintenance_pending_amount = Column(Numeric(18, 2), default=0.0, nullable=False)
    
    utility_bills_cleared = Column(Boolean, default=False, nullable=False)
    utility_pending_amount = Column(Numeric(18, 2), default=0.0, nullable=False)
    
    penalties_cleared = Column(Boolean, default=False, nullable=False)
    penalties_pending_amount = Column(Numeric(18, 2), default=0.0, nullable=False)
    
    other_dues_cleared = Column(Boolean, default=False, nullable=False)
    other_dues_amount = Column(Numeric(18, 2), default=0.0, nullable=False)
    other_dues_description = Column(Text, nullable=True)
    
    # Physical Inspection (Checklist Only - No Files Stored)
    keys_returned = Column(Boolean, default=False, nullable=False)
    keys_returned_date = Column(Date, nullable=True)
    keys_received_by = Column(String(100), nullable=True)  # Admin name
    
    flat_inspection_done = Column(Boolean, default=False, nullable=False)
    flat_inspection_date = Column(Date, nullable=True)
    flat_inspection_by = Column(String(100), nullable=True)  # Admin name
    flat_damages_noted = Column(Text, nullable=True)  # Description only, no photos
    flat_damage_charges = Column(Numeric(18, 2), default=0.0, nullable=False)
    
    utility_meters_verified = Column(Boolean, default=False, nullable=False)
    utility_meters_reading = Column(Text, nullable=True)  # Final readings
    utility_meters_verified_by = Column(String(100), nullable=True)
    
    parking_slot_vacated = Column(Boolean, default=False, nullable=False)
    parking_slot_verified_by = Column(String(100), nullable=True)
    
    # Document Return (Physical - Checklist Only)
    documents_returned = Column(Boolean, default=False, nullable=False)
    documents_returned_date = Column(Date, nullable=True)
    documents_returned_to = Column(String(100), nullable=True)  # Member name
    documents_list = Column(Text, nullable=True)  # "Aadhaar copy, PAN copy, Sale deed"
    return_acknowledgment_signed = Column(Boolean, default=False, nullable=False)
    
    # Final Settlement
    security_deposit_amount = Column(Numeric(18, 2), default=0.0, nullable=False)
    deductions_amount = Column(Numeric(18, 2), default=0.0, nullable=False)
    deductions_reason = Column(Text, nullable=True)
    refund_amount = Column(Numeric(18, 2), default=0.0, nullable=False)
    
    settlement_status = Column(Enum(SettlementStatus), default=SettlementStatus.PENDING, nullable=False, index=True)
    settlement_date = Column(Date, nullable=True)
    settlement_by = Column(String(100), nullable=True)  # Admin who processed
    payment_method = Column(String(50), nullable=True)  # 'cash', 'bank_transfer', 'cheque', 'upi'
    payment_reference = Column(String(100), nullable=True)  # Transaction ID
    
    # NOC Generation (Log Only - File NOT Stored)
    noc_generated = Column(Boolean, default=False, nullable=False)
    noc_generated_date = Column(DateTime, nullable=True)
    noc_generated_by = Column(String(100), nullable=True)
    noc_reference_number = Column(String(100), nullable=True, unique=True, index=True)  # Unique NOC number for tracking
    noc_downloaded_by_member = Column(Boolean, default=False, nullable=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    moveout_request = relationship("MoveOutRequest", back_populates="checklist")
    society = relationship("Society")


# ============ NOC GENERATION LOG MODEL ============
class NOCGenerationLog(Base):
    """NOC generation log - audit trail only (NOT storing PDF files)"""
    __tablename__ = "noc_generation_log"
    
    id = Column(Integer, primary_key=True, index=True)
    moveout_request_id = Column(Integer, ForeignKey("moveout_requests.id"), nullable=False, index=True)
    society_id = Column(Integer, ForeignKey("societies.id"), nullable=False, index=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False, index=True)
    
    # NOC details (metadata only, NOT the file)
    noc_reference_number = Column(String(100), unique=True, nullable=False, index=True)
    noc_type = Column(String(50), nullable=False)  # 'moveout', 'sale', 'transfer'
    
    generated_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    generated_by = Column(String(100), nullable=False)  # Admin who generated
    
    # What was in the NOC (for audit)
    member_name = Column(String(100), nullable=True)
    flat_number = Column(String(50), nullable=True)
    moveout_date = Column(Date, nullable=True)
    dues_status = Column(String(50), nullable=True)  # 'all_cleared'
    
    # Download tracking
    downloaded = Column(Boolean, default=False, nullable=False)
    download_count = Column(Integer, default=0, nullable=False)
    last_downloaded_at = Column(DateTime, nullable=True)
    
    # Security
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(Text, nullable=True)
    
    # IMPORTANT: We do NOT store the actual PDF file
    # Member downloads it, we just log that it was generated
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    moveout_request = relationship("MoveOutRequest", back_populates="noc_logs")
    society = relationship("Society")
    member = relationship("Member")


# ============ MEMBERS ARCHIVE MODEL ============
class MembersArchive(Base):
    """Archived member data - for retention and compliance"""
    __tablename__ = "members_archive"
    
    id = Column(Integer, primary_key=True, index=True)
    society_id = Column(Integer, ForeignKey("societies.id"), nullable=False, index=True)
    
    # Copy of member fields
    original_member_id = Column(Integer, nullable=False, index=True)  # Original member.id
    name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    flat_id = Column(Integer, nullable=True)
    
    # Archive metadata
    archived_date = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    archived_by = Column(String(100), nullable=True)
    archive_reason = Column(String(50), nullable=True)  # 'moveout_completed'
    
    # Original move-out details
    moveout_date = Column(Date, nullable=True)
    moveout_request_id = Column(Integer, nullable=True)
    final_settlement_amount = Column(Numeric(18, 2), nullable=True)
    
    # Retention info
    financial_records_retention_until = Column(Date, nullable=True, index=True)  # date('now', '+6 years')
    eligible_for_deletion_after = Column(Date, nullable=True, index=True)  # date('now', '+6 years')
    
    # All other member fields (JSON dump)
    original_member_data = Column(Text, nullable=True)  # JSON dump of full member record
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    society = relationship("Society")


# ============================================================================
# IMPORT NEW MODELS FROM SEPARATE FILES
# ============================================================================
# These models are defined in separate files but imported here for consistency

from app.models.payment import (
    Payment,
    PaymentReminder,
    PaymentMode,
    PaymentStatus
)

from app.models.online_payment import (
    OnlinePayment,
    OnlinePaymentStatus,
    PaymentGateway,
    OnlinePaymentMethod,
    PaymentLink
)

from app.models.financial_year import (
    FinancialYear,
    YearStatus,
    OpeningBalanceStatus
)

from app.models.opening_balance import (
    OpeningBalance,
    BalanceType,
    BalanceStatus
)

from app.models.audit_adjustment import (
    AuditAdjustment,
    AdjustmentType
)

# ============ COMPLAINT MANAGEMENT MODULE ============
class ComplaintStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

class ComplaintType(str, enum.Enum):
    PLUMBING = "plumbing"
    ELECTRICAL = "electrical"
    SECURITY = "security"
    CLEANING = "cleaning"
    PARKING = "parking"
    OTHER = "other"

class ComplaintPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class Complaint(Base):
    """Complaint model for resident issues"""
    __tablename__ = "complaints"
    
    id = Column(Integer, primary_key=True, index=True)
    society_id = Column(Integer, ForeignKey("societies.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)  # Author
    
    type = Column(Enum(ComplaintType), nullable=False, default=ComplaintType.OTHER)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(Enum(ComplaintStatus), default=ComplaintStatus.OPEN, nullable=False)
    priority = Column(Enum(ComplaintPriority), default=ComplaintPriority.MEDIUM, nullable=False)
    
    assigned_to = Column(String(100), nullable=True)  # E.g., name of staff/vendor
    resolution_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    society = relationship("Society", back_populates="complaints")
    user = relationship("User", back_populates="complaints")

# Add back_populates to Society and User (monkey-patching or manual update recommended if not using alembic)
# Note: In a real migration, we'd update Society/User classes. 
# Here we ensure Society has 'complaints' relationship.
# It is assumed Society model is defined above.
Society.complaints = relationship("Complaint", back_populates="society", cascade="all, delete-orphan")
# User.complaints relationship
from app.models_db import User
User.complaints = relationship("Complaint", back_populates="user")
