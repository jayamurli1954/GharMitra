"""
Admin Guidelines - Do's and Don'ts for GharMitra
This content is displayed to all admins and must be acknowledged before using the system
"""
from datetime import datetime

GUIDELINES_VERSION = "1.0"
LAST_UPDATED = "2025-11-18"

ADMIN_GUIDELINES = {
    "version": GUIDELINES_VERSION,
    "last_updated": LAST_UPDATED,
    "title": "GharMitra Admin Guidelines - Do's and Don'ts",
    "sections": [
        {
            "id": "legal_compliance",
            "title": "Legal Compliance & Data Privacy",
            "icon": "shield-checkmark",
            "dos": [
                "✅ DO collect only primary member information: Name, Mobile Number, Email, and Status (Owner/Tenant)",
                "✅ DO use the Document Checklist to track document submission status (NOT the actual documents)",
                "✅ DO mark documents as 'submitted on date' or 'pending' in the checklist",
                "✅ DO maintain physical document records separately (not in the system)"
            ],
            "donts": [
                "❌ DO NOT store Aadhaar documents or Aadhaar numbers in the system",
                "❌ DO NOT store PAN card documents or PAN numbers in the system",
                "❌ DO NOT store Sale Deed documents in the system",
                "❌ DO NOT store Rental Agreement documents in the system",
                "❌ DO NOT upload sensitive documents to the system"
            ],
            "important": "GharMitra is designed for legal compliance. We only track document submission status, not the documents themselves."
        },
        {
            "id": "billing_maintenance",
            "title": "Maintenance Bill Generation",
            "icon": "receipt",
            "dos": [
                "✅ DO set occupants to '0' for vacant flats BEFORE month end",
                "✅ DO select expense heads in Chart of Accounts for fixed expenses calculation",
                "✅ DO verify water expense is added before generating bills",
                "✅ DO review bill breakdown before finalizing",
                "✅ DO ensure all flats have correct occupant count before bill generation"
            ],
            "donts": [
                "❌ DO NOT generate bills if occupants are not set correctly (vacant flats must have 0 occupants)",
                "❌ DO NOT forget to update occupant count when members move in/out",
                "❌ DO NOT generate bills without adding water expense for the month",
                "❌ DO NOT change occupant count after bills are generated (it affects water charges calculation)"
            ],
            "important": "Water charges are calculated based on occupants. If a flat is vacant (occupants=0), water charges will be ₹0, but fixed expenses and sinking fund will still be charged."
        },
        {
            "id": "member_management",
            "title": "Member Onboarding & Management",
            "icon": "people",
            "dos": [
                "✅ DO collect only: Name, Mobile Number, Email, and Member Type (Owner/Tenant)",
                "✅ DO link members to correct flat numbers",
                "✅ DO update move-in and move-out dates accurately",
                "✅ DO update total occupants when family size changes",
                "✅ DO use the 'Claim Profile' workflow - Admin creates profile, User claims it"
            ],
            "donts": [
                "❌ DO NOT collect Aadhaar or PAN numbers from members",
                "❌ DO NOT store sensitive member documents",
                "❌ DO NOT allow members to self-register (Admin must create profiles)",
                "❌ DO NOT create duplicate member profiles for the same flat"
            ],
            "important": "Mobile number is the unique identifier for member login. Ensure it's correct and unique."
        },
        {
            "id": "expense_management",
            "title": "Expense Head Selection",
            "icon": "list",
            "dos": [
                "✅ DO select expense heads in Chart of Accounts that should be included in fixed expenses",
                "✅ DO review selected expense heads periodically",
                "✅ DO ensure only relevant expense heads are selected",
                "✅ DO understand that selected expense heads are summed and divided by total flats"
            ],
            "donts": [
                "❌ DO NOT select income account codes for fixed expenses",
                "❌ DO NOT select all expense heads blindly - be selective",
                "❌ DO NOT forget to update selections when expense structure changes"
            ],
            "important": "Only expense-type account codes can be marked for fixed expenses. These are automatically included in maintenance bill calculations."
        },
        {
            "id": "financial_year",
            "title": "Financial Year & Accounting",
            "icon": "calendar",
            "dos": [
                "✅ DO set Financial Year Start and End dates during society setup",
                "✅ DO select Accounting Method (Cash or Accrual) based on your society's needs",
                "✅ DO ensure opening balances are accurate before starting",
                "✅ DO validate balance sheet (Assets = Liabilities + Equity)"
            ],
            "donts": [
                "❌ DO NOT change financial year dates after transactions are recorded",
                "❌ DO NOT mix cash and accrual accounting methods",
                "❌ DO NOT skip balance sheet validation"
            ],
            "important": "Financial year settings affect all reports and calculations. Set them correctly at the beginning."
        },
        {
            "id": "roles_permissions",
            "title": "User Roles & Permissions",
            "icon": "lock-closed",
            "dos": [
                "✅ DO assign Auditor role ONLY to external auditors",
                "✅ DO understand that Auditors can ONLY VIEW - they cannot add, edit, or delete",
                "✅ DO assign appropriate roles based on responsibilities",
                "✅ DO review role assignments periodically"
            ],
            "donts": [
                "❌ DO NOT assign Auditor role to internal staff who need to make changes",
                "❌ DO NOT give Admin role to members who should only view",
                "❌ DO NOT ignore permission warnings"
            ],
            "important": "Auditor role is view-only. If an auditor needs to make changes, assign a different role."
        },
        {
            "id": "data_backup",
            "title": "Data Backup & Security",
            "icon": "cloud-upload",
            "dos": [
                "✅ DO take regular backups of your data",
                "✅ DO keep admin credentials secure",
                "✅ DO use strong passwords",
                "✅ DO log out when not using the system"
            ],
            "donts": [
                "❌ DO NOT share admin credentials",
                "❌ DO NOT ignore security warnings",
                "❌ DO NOT skip regular backups"
            ],
            "important": "Regular backups ensure data safety. Consider exporting reports periodically."
        },
        {
            "id": "reporting",
            "title": "Reports & Documentation",
            "icon": "document-text",
            "dos": [
                "✅ DO generate reports for proper date ranges",
                "✅ DO review reports before sharing",
                "✅ DO export reports in Excel/PDF for records",
                "✅ DO maintain audit trail for transparency"
            ],
            "donts": [
                "❌ DO NOT generate reports with incorrect date ranges",
                "❌ DO NOT share reports without verification",
                "❌ DO NOT delete audit logs"
            ],
            "important": "Reports should be generated for specific periods and verified before distribution."
        }
    ],
    "acknowledgment_required": True,
    "acknowledgment_message": "I have read and understood the Admin Guidelines and agree to follow them."
}


def get_guidelines() -> dict:
    """Get the current admin guidelines"""
    return ADMIN_GUIDELINES


def get_guidelines_version() -> str:
    """Get the current guidelines version"""
    return GUIDELINES_VERSION

