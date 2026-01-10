"""
Script to initialize Chart of Accounts for Society ID 1
"""
import asyncio
from datetime import datetime
from sqlalchemy import select, func
from app.database import AsyncSessionLocal
from app.models_db import AccountCode as AccountCodeDB, AccountType

# Copying the list from accounting.py to ensure consistency
CHART_OF_ACCOUNTS = [
    # ASSETS (1000-1999)
    {"code": "1000", "name": "Bank Account - Main", "type": "asset", "description": "Primary bank account"},
    {"code": "1001", "name": "Bank Account - Savings", "type": "asset", "description": "Savings account"},
    {"code": "1010", "name": "Cash in Hand", "type": "asset", "description": "Physical cash"},
    {"code": "1020", "name": "Fixed Deposits", "type": "asset", "description": "Fixed deposit investments"},
    {"code": "1100", "name": "Maintenance Dues Receivable", "type": "asset", "description": "Outstanding maintenance from members"},
    {"code": "1200", "name": "Other Receivables", "type": "asset", "description": "Other amounts to be received"},
    {"code": "1500", "name": "Common Area Assets", "type": "asset", "description": "Furniture, equipment in common areas"},
    {"code": "1510", "name": "Generator", "type": "asset", "description": "Generator equipment"},
    {"code": "1520", "name": "Water Pumps & Motors", "type": "asset", "description": "Water supply equipment"},
    {"code": "1530", "name": "Security Equipment", "type": "asset", "description": "CCTV, intercom systems"},

    # LIABILITIES (2000-2999)
    {"code": "2000", "name": "Advance Maintenance Received", "type": "liability", "description": "Advance payments from members"},
    {"code": "2100", "name": "Security Deposits", "type": "liability", "description": "Refundable deposits from members"},
    {"code": "2200", "name": "Electricity Bill Payable", "type": "liability", "description": "Outstanding electricity bills"},
    {"code": "2210", "name": "Water Bill Payable", "type": "liability", "description": "Outstanding water bills"},
    {"code": "2220", "name": "Salary Payable", "type": "liability", "description": "Outstanding staff salaries"},
    {"code": "2300", "name": "Other Payables", "type": "liability", "description": "Other amounts to be paid"},

    # CAPITAL/RESERVES (3000-3999)
    {"code": "3001", "name": "Owner's Equity / Capital Fund", "type": "capital", "description": "Owner's equity to balance assets and liabilities"},
    {"code": "3000", "name": "Sinking Fund", "type": "capital", "description": "Reserve fund for major repairs"},
    {"code": "3010", "name": "Corpus Fund", "type": "capital", "description": "Long-term capital fund"},
    {"code": "3100", "name": "Retained Surplus", "type": "capital", "description": "Accumulated surplus from previous years"},

    # INCOME (4000-4999)
    {"code": "4000", "name": "Maintenance Charges", "type": "income", "description": "Monthly maintenance from members"},
    {"code": "4010", "name": "Water Charges", "type": "income", "description": "Water charges collected"},
    {"code": "4020", "name": "Parking Fees", "type": "income", "description": "Parking slot fees"},
    {"code": "4030", "name": "Amenity Charges", "type": "income", "description": "Charges for amenity usage"},
    {"code": "4040", "name": "Late Payment Fees", "type": "income", "description": "Penalty on late payments"},
    {"code": "4050", "name": "Interest Income", "type": "income", "description": "Interest from bank deposits"},
    {"code": "4100", "name": "Rental Income - Common Area", "type": "income", "description": "Rent from common area usage"},
    {"code": "4200", "name": "Other Income", "type": "income", "description": "Miscellaneous income"},

    # EXPENSES (5000-5999)
    # Staff & Security
    {"code": "5000", "name": "Watchman Salary", "type": "expense", "description": "Security guard salaries"},
    {"code": "5010", "name": "Housekeeping Salary", "type": "expense", "description": "Cleaning staff salaries"},
    {"code": "5020", "name": "Manager Salary", "type": "expense", "description": "Society manager salary"},
    {"code": "5030", "name": "Other Staff Salary", "type": "expense", "description": "Other staff payments"},

    # Utilities
    {"code": "5100", "name": "Electricity Charges - Common Area", "type": "expense", "description": "Common area electricity"},
    {"code": "5110", "name": "Water Charges - Tanker", "type": "expense", "description": "Water tanker charges"},
    {"code": "5120", "name": "Water Charges - Government", "type": "expense", "description": "Municipal water charges"},
    {"code": "5130", "name": "Generator Fuel", "type": "expense", "description": "Diesel/fuel for generator"},

    # Repairs & Maintenance
    {"code": "5200", "name": "Building Repairs", "type": "expense", "description": "Building maintenance and repairs"},
    {"code": "5210", "name": "Plumbing Repairs", "type": "expense", "description": "Plumbing work"},
    {"code": "5220", "name": "Electrical Repairs", "type": "expense", "description": "Electrical maintenance"},
    {"code": "5230", "name": "Painting Work", "type": "expense", "description": "Painting and whitewashing"},
    {"code": "5240", "name": "Lift Maintenance", "type": "expense", "description": "Elevator servicing and repairs"},
    {"code": "5250", "name": "Generator Maintenance", "type": "expense", "description": "Generator servicing"},
    {"code": "5260", "name": "Water Pump Repairs", "type": "expense", "description": "Pump maintenance"},

    # AMCs & Contracts
    {"code": "5300", "name": "Lift AMC", "type": "expense", "description": "Annual maintenance contract for lift"},
    {"code": "5310", "name": "Generator AMC", "type": "expense", "description": "Generator annual maintenance"},
    {"code": "5320", "name": "Fire Safety AMC", "type": "expense", "description": "Fire equipment maintenance"},
    {"code": "5330", "name": "Water Pump AMC", "type": "expense", "description": "Water pump maintenance contract"},
    {"code": "5340", "name": "CCTV AMC", "type": "expense", "description": "Security camera maintenance"},

    # Services
    {"code": "5400", "name": "Pest Control", "type": "expense", "description": "Pest control services"},
    {"code": "5410", "name": "Garbage Collection", "type": "expense", "description": "Waste disposal charges"},
    {"code": "5420", "name": "Cleaning Services", "type": "expense", "description": "Professional cleaning"},
    {"code": "5430", "name": "Gardening & Landscaping", "type": "expense", "description": "Garden maintenance"},
    {"code": "5440", "name": "Security Services", "type": "expense", "description": "Professional security services"},

    # Insurance & Legal
    {"code": "5500", "name": "Building Insurance", "type": "expense", "description": "Property insurance premium"},
    {"code": "5510", "name": "Legal Fees", "type": "expense", "description": "Legal consultation charges"},
    {"code": "5520", "name": "Audit Fees", "type": "expense", "description": "Auditor fees"},

    # Administrative
    {"code": "5600", "name": "Office Supplies", "type": "expense", "description": "Stationery and supplies"},
    {"code": "5610", "name": "Printing & Copying", "type": "expense", "description": "Printing expenses"},
    {"code": "5620", "name": "Internet & Phone", "type": "expense", "description": "Communication charges"},
    {"code": "5630", "name": "Bank Charges", "type": "expense", "description": "Bank transaction fees"},
    {"code": "5640", "name": "Software Subscriptions", "type": "expense", "description": "Accounting software, etc."},

    # Miscellaneous
    {"code": "5900", "name": "Festival Celebrations", "type": "expense", "description": "Community event expenses"},
    {"code": "5910", "name": "Welfare Activities", "type": "expense", "description": "Social welfare programs"},
    {"code": "5990", "name": "Other Expenses", "type": "expense", "description": "Miscellaneous expenses"},
]

async def initialize_accounts():
    db = AsyncSessionLocal()
    society_id = 1
    
    try:
        # Check if already initialized
        result = await db.execute(select(func.count(AccountCodeDB.id)).where(AccountCodeDB.society_id == society_id))
        count = result.scalar()
        
        if count > 0:
            print(f"Chart of Accounts already initialized ({count} records).")
            return

        print("Initializing Chart of Accounts...")
        accounts_to_insert = []
        for account in CHART_OF_ACCOUNTS:
            account_type = AccountType(account["type"])
            account_obj = AccountCodeDB(
                society_id=society_id,
                code=account["code"],
                name=account["name"],
                type=account_type,
                description=account["description"],
                opening_balance=0.0,
                current_balance=0.0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            accounts_to_insert.append(account_obj)
        
        db.add_all(accounts_to_insert)
        await db.commit()
        print(f"Successfully created {len(accounts_to_insert)} account codes!")

    except Exception as e:
        print(f"Error: {e}")
        await db.rollback()
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(initialize_accounts())
