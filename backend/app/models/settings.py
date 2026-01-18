"""Society Settings models"""
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Dict, Any
from datetime import date
import re


class PenaltyInterestSettings(BaseModel):
    """Penalty and Interest configuration"""
    late_payment_penalty_type: Optional[str] = Field(None, description="'percentage' or 'fixed'")
    late_payment_penalty_value: Optional[float] = Field(None, description="Percentage or fixed amount")
    late_payment_grace_days: Optional[int] = Field(0, description="Days before penalty applies")
    interest_on_overdue: bool = Field(False, description="Enable interest on overdue amounts")
    interest_rate: Optional[float] = Field(None, description="Annual interest rate percentage")


class TaxSettings(BaseModel):
    """Tax configuration (GST, TDS)"""
    gst_enabled: bool = Field(False, description="Enable GST")
    gst_number: Optional[str] = Field(None, max_length=15, description="GSTIN")
    gst_rate: Optional[float] = Field(None, description="Default GST rate percentage")
    tds_enabled: bool = Field(False, description="Enable TDS")
    tds_rate: Optional[float] = Field(None, description="TDS rate percentage")
    tds_threshold: Optional[float] = Field(None, description="Amount threshold for TDS")


class PaymentGatewaySettings(BaseModel):
    """Payment gateway configuration"""
    payment_gateway_enabled: bool = Field(False, description="Enable payment gateway")
    payment_gateway_provider: Optional[str] = Field(None, description="'razorpay', 'payu', 'stripe', etc.")
    payment_gateway_key_id: Optional[str] = Field(None, description="Payment gateway key ID")
    payment_gateway_key_secret: Optional[str] = Field(None, description="Payment gateway key secret")
    upi_enabled: bool = Field(False, description="Enable UPI payments")
    upi_id: Optional[str] = Field(None, description="UPI ID for payments")


class BankAccount(BaseModel):
    """Bank account details"""
    account_name: str
    account_number: str
    bank_name: str
    ifsc_code: str
    branch: Optional[str] = None
    account_type: Optional[str] = Field(None, description="'savings', 'current', 'fd', etc.")
    is_primary: bool = Field(False, description="Primary account for transactions")
    account_code: Optional[str] = Field(None, description="Linked account code from Chart of Accounts (e.g., '1000', '1001')")


class VendorSettings(BaseModel):
    """Vendor management settings"""
    vendor_approval_required: bool = Field(False, description="Require approval for vendor bills")
    vendor_approval_workflow: Optional[str] = Field(None, description="'single' or 'multi_level'")


class AuditTrailSettings(BaseModel):
    """Audit trail configuration"""
    audit_trail_enabled: bool = Field(True, description="Enable audit trail")
    audit_retention_days: Optional[int] = Field(2555, description="Retention period in days (7 years default)")


class BillingSettings(BaseModel):
    """Billing configuration"""
    billing_cycle: Optional[str] = Field(None, description="'monthly', 'quarterly', 'annual'")
    auto_generate_bills: bool = Field(False, description="Auto-generate bills on cycle")
    bill_due_days: Optional[int] = Field(7, description="Days after bill generation until due")


class MemberSettings(BaseModel):
    """Member management settings"""
    bill_to_bill_tracking: bool = Field(True, description="Enable bill-to-bill tracking for members")


class SocietySettingsCreate(BaseModel):
    """Model for creating/updating society settings"""
    # Penalty/Interest
    late_payment_penalty_type: Optional[str] = Field(None, description="'percentage' or 'fixed'")
    late_payment_penalty_value: Optional[float] = Field(None, ge=0, description="Penalty value (must be >= 0)")
    late_payment_grace_days: Optional[int] = Field(None, ge=0, le=365, description="Grace days (0-365)")
    interest_on_overdue: Optional[bool] = None
    interest_rate: Optional[float] = Field(None, ge=0, le=100, description="Interest rate percentage (0-100)")
    
    # Society Details (Proxy to Society model)
    society_name: Optional[str] = Field(None, max_length=100)
    society_address: Optional[str] = None
    registration_number: Optional[str] = None
    registration_date: Optional[str] = None
    pan_no: Optional[str] = Field(None, max_length=20)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    pin_code: Optional[str] = Field(None, max_length=10)
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    gst_registration_applicable: Optional[bool] = None
    
    # Tax
    gst_enabled: Optional[bool] = None
    gst_number: Optional[str] = Field(None, max_length=15, description="GSTIN (15 characters)")
    gst_rate: Optional[float] = Field(None, ge=0, le=100, description="GST rate percentage (0-100)")
    tds_enabled: Optional[bool] = None
    tds_rate: Optional[float] = Field(None, ge=0, le=100, description="TDS rate percentage (0-100)")
    tds_threshold: Optional[float] = Field(None, ge=0, description="TDS threshold amount (>= 0)")
    
    # Payment Gateway
    payment_gateway_enabled: Optional[bool] = None
    payment_gateway_provider: Optional[str] = Field(None, description="'razorpay', 'payu', 'stripe', etc.")
    payment_gateway_key_id: Optional[str] = None
    payment_gateway_key_secret: Optional[str] = None
    upi_enabled: Optional[bool] = None
    upi_id: Optional[str] = Field(None, max_length=100, description="UPI ID")
    
    # Bank Accounts (JSON array)
    bank_accounts: Optional[List[Dict[str, Any]]] = None
    
    # Vendor
    vendor_approval_required: Optional[bool] = None
    vendor_approval_workflow: Optional[str] = Field(None, description="'single' or 'multi_level'")
    
    # Audit Trail
    audit_trail_enabled: Optional[bool] = None
    audit_retention_days: Optional[int] = Field(None, ge=1, le=2555, description="Retention days (1-2555, max 7 years)")
    
    # Billing
    billing_cycle: Optional[str] = Field(None, description="'monthly', 'quarterly', or 'annual'")
    auto_generate_bills: Optional[bool] = None
    bill_due_days: Optional[int] = Field(None, ge=1, le=90, description="Bill due days (1-90)")
    fixed_expense_heads: Optional[List[str]] = Field(None, description="List of account codes to include in fixed expenses")
    
    # Detailed Billing Rules
    maintenance_calculation_logic: Optional[str] = Field(None, description="'sqft', 'fixed', 'water_based'")
    maintenance_rate_sqft: Optional[float] = None
    maintenance_rate_flat: Optional[float] = None
    sinking_fund_rate: Optional[float] = None
    repair_fund_rate: Optional[float] = None
    association_fund_rate: Optional[float] = None
    corpus_fund_rate: Optional[float] = None
    
    water_calculation_type: Optional[str] = Field(None, description="'flat', 'person', 'meter'")
    water_rate_per_person: Optional[float] = None
    water_min_charge: Optional[float] = None
    
    expense_distribution_logic: Optional[str] = Field(None, description="'equal', 'sqft'")

    
    # Member
    bill_to_bill_tracking: Optional[bool] = None
    member_approval_required: Optional[bool] = None
    tenant_expiry_reminder_days: Optional[int] = None
    max_members_per_flat: Optional[int] = None

    # Transaction Locking
    transaction_date_lock_enabled: Optional[bool] = None
    transaction_date_lock_months: Optional[int] = None
    financial_year_start: Optional[str] = None # Frontend sends this, valid for validation even if not stored directly column-wise yet

    # Structure
    blocks_config: Optional[List[Dict[str, Any]]] = None

    # Notifications
    notification_config: Optional[Dict[str, Any]] = None

    # Complaint & Asset
    complaint_config: Optional[Dict[str, Any]] = None
    asset_config: Optional[Dict[str, Any]] = None
    
    # Legal
    legal_config: Optional[Dict[str, Any]] = None
    
    @field_validator('late_payment_penalty_type')
    @classmethod
    def validate_penalty_type(cls, v):
        if v is not None and v not in ['percentage', 'fixed']:
            raise ValueError("late_payment_penalty_type must be 'percentage' or 'fixed'")
        return v
    
    @field_validator('gst_number')
    @classmethod
    def validate_gst_number(cls, v):
        if v is not None:
            # GSTIN format: 15 characters, alphanumeric
            gst_pattern = re.compile(r'^[0-9A-Z]{15}$')
            if not gst_pattern.match(v):
                raise ValueError("GST number must be 15 characters alphanumeric (GSTIN format)")
        return v
    
    @field_validator('payment_gateway_provider')
    @classmethod
    def validate_payment_gateway_provider(cls, v):
        if v is not None:
            valid_providers = ['razorpay', 'payu', 'stripe', 'paypal', 'instamojo']
            if v.lower() not in valid_providers:
                raise ValueError(f"payment_gateway_provider must be one of: {', '.join(valid_providers)}")
        return v
    
    @field_validator('vendor_approval_workflow')
    @classmethod
    def validate_vendor_workflow(cls, v):
        if v is not None and v not in ['single', 'multi_level']:
            raise ValueError("vendor_approval_workflow must be 'single' or 'multi_level'")
        return v
    
    @field_validator('billing_cycle')
    @classmethod
    def validate_billing_cycle(cls, v):
        if v is not None and v not in ['monthly', 'quarterly', 'annual']:
            raise ValueError("billing_cycle must be 'monthly', 'quarterly', or 'annual'")
        return v
    
    @field_validator('upi_id')
    @classmethod
    def validate_upi_id(cls, v):
        if v is not None:
            # UPI ID format: username@paytm, username@phonepe, etc.
            upi_pattern = re.compile(r'^[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}$')
            if not upi_pattern.match(v):
                raise ValueError("UPI ID must be in format: username@provider (e.g., user@paytm)")
        return v
    
    @field_validator('bank_accounts')
    @classmethod
    def validate_bank_accounts(cls, v):
        if v is not None:
            if not isinstance(v, list):
                raise ValueError("bank_accounts must be a list")
            for account in v:
                if not isinstance(account, dict):
                    raise ValueError("Each bank account must be a dictionary")
                required_fields = ['account_name', 'account_number', 'bank_name', 'ifsc_code']
                for field in required_fields:
                    if field not in account or not account[field]:
                        raise ValueError(f"Bank account missing required field: {field}")
                # Validate IFSC code format
                ifsc_pattern = re.compile(r'^[A-Z]{4}0[A-Z0-9]{6}$')
                if not ifsc_pattern.match(account.get('ifsc_code', '')):
                    raise ValueError("IFSC code must be in format: AAAA0XXXXXX (4 letters, 0, 6 alphanumeric)")
        return v
    
    @field_validator('fixed_expense_heads')
    @classmethod
    def validate_fixed_expense_heads(cls, v):
        if v is not None:
            if not isinstance(v, list):
                raise ValueError("fixed_expense_heads must be a list")
            for code in v:
                if not isinstance(code, str) or len(code) < 4 or len(code) > 10:
                    raise ValueError("Each account code in fixed_expense_heads must be 4-10 characters")
        return v
    
    @model_validator(mode='after')
    def validate_penalty_settings(self):
        """Validate penalty settings are complete if penalty is enabled"""
        if self.late_payment_penalty_type is not None:
            if self.late_payment_penalty_value is None or self.late_payment_penalty_value <= 0:
                raise ValueError("late_payment_penalty_value is required and must be > 0 when penalty_type is set")
        return self
    
    @model_validator(mode='after')
    def validate_interest_settings(self):
        """Validate interest settings are complete if interest is enabled"""
        if self.interest_on_overdue is True:
            if self.interest_rate is None or self.interest_rate <= 0:
                raise ValueError("interest_rate is required and must be > 0 when interest_on_overdue is enabled")
        return self
    
    @model_validator(mode='after')
    def validate_gst_settings(self):
        """Validate GST settings are complete if GST is enabled"""
        if self.gst_enabled is True:
            if not self.gst_number:
                raise ValueError("gst_number is required when gst_enabled is True")
            if self.gst_rate is None or self.gst_rate < 0:
                raise ValueError("gst_rate is required and must be >= 0 when gst_enabled is True")
        return self
    
    @model_validator(mode='after')
    def validate_tds_settings(self):
        """Validate TDS settings are complete if TDS is enabled"""
        if self.tds_enabled is True:
            if self.tds_rate is None or self.tds_rate <= 0:
                raise ValueError("tds_rate is required and must be > 0 when tds_enabled is True")
            if self.tds_threshold is None or self.tds_threshold <= 0:
                raise ValueError("tds_threshold is required and must be > 0 when tds_enabled is True")
        return self
    
    @model_validator(mode='after')
    def validate_payment_gateway_settings(self):
        """Validate payment gateway settings are complete if gateway is enabled"""
        if self.payment_gateway_enabled is True:
            if not self.payment_gateway_provider:
                raise ValueError("payment_gateway_provider is required when payment_gateway_enabled is True")
            if not self.payment_gateway_key_id:
                raise ValueError("payment_gateway_key_id is required when payment_gateway_enabled is True")
            if not self.payment_gateway_key_secret:
                raise ValueError("payment_gateway_key_secret is required when payment_gateway_enabled is True")
        return self
    
    @model_validator(mode='after')
    def validate_upi_settings(self):
        """Validate UPI settings are complete if UPI is enabled"""
        if self.upi_enabled is True:
            if not self.upi_id:
                raise ValueError("upi_id is required when upi_enabled is True")
        return self
    
    @model_validator(mode='after')
    def validate_vendor_workflow_settings(self):
        """Validate vendor workflow settings are complete if approval is required"""
        if self.vendor_approval_required is True:
            if not self.vendor_approval_workflow:
                raise ValueError("vendor_approval_workflow is required when vendor_approval_required is True")
        return self
    
    @model_validator(mode='after')
    def validate_billing_settings(self):
        """Validate billing settings are complete if auto-generate is enabled"""
        if self.auto_generate_bills is True:
            if not self.billing_cycle:
                raise ValueError("billing_cycle is required when auto_generate_bills is True")
            if self.bill_due_days is None or self.bill_due_days <= 0:
                raise ValueError("bill_due_days is required and must be > 0 when auto_generate_bills is True")
        return self


class SocietySettingsResponse(BaseModel):
    """Model for society settings response"""
    id: str
    society_id: int
    
    # Society Details (From Society table)
    society_name: Optional[str] = None
    society_address: Optional[str] = None
    registration_number: Optional[str] = None
    registration_date: Optional[str] = None
    pan_no: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pin_code: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    gst_registration_applicable: bool = False

    # Penalty/Interest
    late_payment_penalty_type: Optional[str] = None
    late_payment_penalty_value: Optional[float] = None
    late_payment_grace_days: Optional[int] = None
    interest_on_overdue: bool = False
    interest_rate: Optional[float] = None
    
    # Tax
    gst_enabled: bool = False
    gst_number: Optional[str] = None
    gst_rate: Optional[float] = None
    tds_enabled: bool = False
    tds_rate: Optional[float] = None
    tds_threshold: Optional[float] = None
    
    # Payment Gateway
    payment_gateway_enabled: bool = False
    payment_gateway_provider: Optional[str] = None
    payment_gateway_key_id: Optional[str] = None
    payment_gateway_key_secret: Optional[str] = None  # Should be masked in response
    upi_enabled: bool = False
    upi_id: Optional[str] = None
    
    # Bank Accounts
    bank_accounts: Optional[List[Dict[str, Any]]] = None
    
    # Vendor
    vendor_approval_required: bool = False
    vendor_approval_workflow: Optional[str] = None
    
    # Audit Trail
    audit_trail_enabled: bool = True
    audit_retention_days: Optional[int] = None
    
    # Billing
    billing_cycle: Optional[str] = None
    auto_generate_bills: bool = False
    bill_due_days: Optional[int] = None
    fixed_expense_heads: Optional[List[str]] = None  # List of account codes to include in fixed expenses
    
    # Detailed Billing Rules
    maintenance_calculation_logic: Optional[str] = None
    maintenance_rate_sqft: Optional[float] = None
    maintenance_rate_flat: Optional[float] = None
    sinking_fund_rate: Optional[float] = None
    repair_fund_rate: Optional[float] = None
    association_fund_rate: Optional[float] = None
    corpus_fund_rate: Optional[float] = None
    
    water_calculation_type: Optional[str] = None
    water_rate_per_person: Optional[float] = None
    water_min_charge: Optional[float] = None
    
    expense_distribution_logic: Optional[str] = None

    
    # Member
    bill_to_bill_tracking: bool = True
    member_approval_required: bool = False
    tenant_expiry_reminder_days: int = 30
    max_members_per_flat: int = 10

    # Structure
    blocks_config: Optional[List[Dict[str, Any]]] = None
    
    # Notifications
    notification_config: Optional[Dict[str, Any]] = None
    
    # Complaint & Asset
    complaint_config: Optional[Dict[str, Any]] = None
    asset_config: Optional[Dict[str, Any]] = None
    
    # Legal
    legal_config: Optional[Dict[str, Any]] = None
    
    created_at: str
    updated_at: str

