"""
Seed script to add sample templates to the database
Run this to populate the Resource Centre with initial templates
Run with: python -m app.seed_templates (from backend directory)
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Import after path is set
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models_db import DocumentTemplate

# Sample HTML templates
NOC_MOVEOUT_HTML = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 40px; }
        .title { font-size: 20px; font-weight: bold; text-align: center; margin: 30px 0; text-decoration: underline; }
        .content { margin: 20px 0; }
        table { width: 100%; margin: 20px 0; }
        table td { padding: 8px; }
        .signature-section { margin-top: 60px; }
        .signature-block { display: inline-block; width: 45%; text-align: center; }
    </style>
</head>
<body>
    <div class="title">NO OBJECTION CERTIFICATE (NOC)</div>
    
    <div class="content">
        <p>This is to certify that:</p>
        
        <table>
            <tr>
                <td width="30%"><strong>Name:</strong></td>
                <td>{{member_name}}</td>
            </tr>
            <tr>
                <td><strong>Flat Number:</strong></td>
                <td>{{flat_number}}</td>
            </tr>
            <tr>
                <td><strong>Contact:</strong></td>
                <td>{{member_phone}}</td>
            </tr>
            <tr>
                <td><strong>Email:</strong></td>
                <td>{{member_email}}</td>
            </tr>
        </table>
        
        <p>has cleared all outstanding dues and obligations towards the society as of {{current_date}}.</p>
        
        <p><strong>Clearance Details:</strong></p>
        <ul>
            <li>✓ Maintenance dues: Cleared</li>
            <li>✓ Utility bills: Cleared</li>
            <li>✓ Special assessments: Cleared</li>
            <li>✓ Security deposit: Refunded/Adjusted</li>
            <li>✓ Keys returned: Yes</li>
        </ul>
        
        <p><strong>Purpose:</strong> {{reason}}</p>
        
        <p>The society has <strong>NO OBJECTION</strong> to the above-mentioned action.</p>
    </div>
    
    <div class="signature-section">
        <div class="signature-block">
            <div style="height: 60px; border-bottom: 1px solid #000;"></div>
            <div><strong>Secretary</strong></div>
            <div>{{society_name}}</div>
        </div>
        
        <div class="signature-block" style="float: right;">
            <div style="height: 60px; border-bottom: 1px solid #000;"></div>
            <div><strong>Chairman</strong></div>
            <div>{{society_name}}</div>
        </div>
    </div>
    
    <div style="clear: both;"></div>
    
    <div style="margin-top: 40px; text-align: center; font-size: 12px; color: #666;">
        <p>This is a computer-generated certificate.</p>
        <p>Reference No: NOC/{{current_date}}/{{flat_number}}</p>
    </div>
</body>
</html>"""

MAINTENANCE_BILL_HTML = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 40px; }
        .title { font-size: 20px; font-weight: bold; text-align: center; margin: 30px 0; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        table td { padding: 8px; border-bottom: 1px solid #ddd; }
        .total { font-weight: bold; font-size: 16px; }
    </style>
</head>
<body>
    <div class="title">MAINTENANCE BILL</div>
    
    <div style="margin: 20px 0;">
        <p><strong>Bill To:</strong></p>
        <p>Flat No: {{flat_number}}</p>
        <p>Owner: {{member_name}}</p>
        <p>Email: {{member_email}}</p>
        <p>Phone: {{member_phone}}</p>
    </div>
    
    <table>
        <tr>
            <td><strong>Bill Number:</strong></td>
            <td>MB/{{current_year}}/{{current_month}}/{{flat_number}}</td>
        </tr>
        <tr>
            <td><strong>Bill Date:</strong></td>
            <td>{{current_date}}</td>
        </tr>
        <tr>
            <td><strong>Due Date:</strong></td>
            <td>{{due_date}}</td>
        </tr>
        <tr>
            <td><strong>Billing Period:</strong></td>
            <td>{{current_month}} {{current_year}}</td>
        </tr>
    </table>
    
    <table>
        <tr style="background-color: #f0f0f0;">
            <td><strong>Description</strong></td>
            <td align="right"><strong>Amount (₹)</strong></td>
        </tr>
        <tr>
            <td>Maintenance Charges</td>
            <td align="right">{{maintenance_amount}}</td>
        </tr>
        <tr>
            <td>Water Charges</td>
            <td align="right">{{water_charges}}</td>
        </tr>
        <tr>
            <td>Electricity (Common)</td>
            <td align="right">{{electricity_charges}}</td>
        </tr>
        <tr>
            <td>Sinking Fund</td>
            <td align="right">{{sinking_fund}}</td>
        </tr>
        <tr class="total">
            <td><strong>TOTAL AMOUNT DUE</strong></td>
            <td align="right"><strong>₹{{total_amount}}</strong></td>
        </tr>
    </table>
    
    <div style="margin-top: 30px;">
        <p><strong>Payment Methods:</strong></p>
        <p>1. Online: UPI - {{society_upi_id}}</p>
        <p>2. Bank Transfer: {{society_bank_details}}</p>
        <p>3. Cash/Cheque: At society office</p>
    </div>
</body>
</html>"""

COMPLAINT_FORM_HTML = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 40px; }
        .title { font-size: 20px; font-weight: bold; text-align: center; margin: 30px 0; }
        table { width: 100%; margin: 20px 0; }
        table td { padding: 8px; }
    </style>
</head>
<body>
    <div class="title">COMPLAINT FORM</div>
    
    <table>
        <tr>
            <td width="30%"><strong>Complaint ID:</strong></td>
            <td>COMP/{{current_date}}/{{flat_number}}</td>
        </tr>
        <tr>
            <td><strong>Date:</strong></td>
            <td>{{current_date}}</td>
        </tr>
        <tr>
            <td><strong>Complainant Name:</strong></td>
            <td>{{member_name}}</td>
        </tr>
        <tr>
            <td><strong>Flat Number:</strong></td>
            <td>{{flat_number}}</td>
        </tr>
        <tr>
            <td><strong>Contact:</strong></td>
            <td>{{member_phone}}</td>
        </tr>
        <tr>
            <td><strong>Email:</strong></td>
            <td>{{member_email}}</td>
        </tr>
    </table>
    
    <div style="margin: 20px 0;">
        <p><strong>Complaint Category:</strong> {{complaint_category}}</p>
        <p><strong>Priority:</strong> {{priority}}</p>
        <p><strong>Subject:</strong> {{subject}}</p>
        <p><strong>Description:</strong></p>
        <p style="border: 1px solid #ddd; padding: 10px; min-height: 100px;">{{description}}</p>
        <p><strong>Location:</strong> {{location}}</p>
    </div>
    
    <div style="margin-top: 40px;">
        <p><strong>FOR OFFICE USE ONLY:</strong></p>
        <p>Assigned to: _________________</p>
        <p>Status: _________________</p>
        <p>Resolution Date: _________________</p>
    </div>
</body>
</html>"""

async def seed_templates():
    """Insert sample templates into database"""
    async with AsyncSessionLocal() as db:
        try:
            # Check if templates already exist
            result = await db.execute(select(DocumentTemplate))
            existing = result.scalars().all()
            
            if len(existing) > 0:
                print(f"⚠️  {len(existing)} templates already exist. Skipping seed.")
                return
            
            # Sample templates to insert
            templates_data = [
                {
                    'template_name': 'NOC for Move-Out',
                    'template_code': 'NOC_MOVEOUT',
                    'category': 'moveout',
                    'description': 'No Objection Certificate for tenant/owner moving out',
                    'instructions': 'This form will be auto-filled with your details. You only need to provide the reason for move-out.',
                    'template_type': 'auto_fill',
                    'can_autofill': True,
                    'autofill_fields': '["member_name","flat_number","member_email","member_phone","society_name","society_address","current_date"]',
                    'template_html': NOC_MOVEOUT_HTML,
                    'template_variables': '["reason"]',
                    'icon_name': 'file-certificate',
                    'available_to': 'all',
                    'display_order': 1,
                    'is_active': True
                },
                {
                    'template_name': 'Monthly Maintenance Bill',
                    'template_code': 'MAINT_BILL',
                    'category': 'maintenance',
                    'description': 'Monthly maintenance bill template',
                    'instructions': 'Auto-filled with member and billing details. Fill in the amounts.',
                    'template_type': 'auto_fill',
                    'can_autofill': True,
                    'autofill_fields': '["member_name","flat_number","member_email","member_phone","society_name","current_date","current_month","current_year"]',
                    'template_html': MAINTENANCE_BILL_HTML,
                    'template_variables': '["maintenance_amount","water_charges","electricity_charges","sinking_fund","total_amount","due_date","society_upi_id","society_bank_details"]',
                    'icon_name': 'receipt',
                    'available_to': 'all',
                    'display_order': 1,
                    'is_active': True
                },
                {
                    'template_name': 'Complaint Form',
                    'template_code': 'COMPLAINT_FORM',
                    'category': 'complaints',
                    'description': 'Form to register complaints and requests',
                    'instructions': 'Fill in the complaint details. Your information will be auto-filled.',
                    'template_type': 'auto_fill',
                    'can_autofill': True,
                    'autofill_fields': '["member_name","flat_number","member_email","member_phone","current_date"]',
                    'template_html': COMPLAINT_FORM_HTML,
                    'template_variables': '["complaint_category","priority","subject","description","location"]',
                    'icon_name': 'alert-circle',
                    'available_to': 'all',
                    'display_order': 1,
                    'is_active': True
                },
            ]
            
            print(f"Inserting {len(templates_data)} sample templates...")
            
            for template_data in templates_data:
                template = DocumentTemplate(
                    society_id=1,  # Default society_id
                    **template_data
                )
                db.add(template)
            
            await db.commit()
            print(f"✅ Successfully inserted {len(templates_data)} templates!")
            print("\nTemplates added:")
            for t in templates_data:
                print(f"  - {t['template_name']} ({t['category']})")
            
        except Exception as e:
            await db.rollback()
            print(f"❌ Error seeding templates: {e}")
            import traceback
            traceback.print_exc()
            raise

if __name__ == '__main__':
    asyncio.run(seed_templates())

