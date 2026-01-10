"""
Comprehensive template seeding script - adds all 25 templates
Run this to populate Resource Centre with full template library
Run with: python seed_all_templates.py (from backend directory)
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Import after path is set
from sqlalchemy import select, text
from app.database import AsyncSessionLocal
from app.models_db import DocumentTemplate

# Simple HTML templates (can be enhanced later with professional styling)

SIMPLE_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 40px; }}
        .title {{ font-size: 20px; font-weight: bold; text-align: center; margin: 30px 0; }}
        table {{ width: 100%; margin: 20px 0; }}
        table td {{ padding: 8px; }}
    </style>
</head>
<body>
    <div class="title">{title}</div>
    <table>{fields}</table>
</body>
</html>"""

async def seed_all_templates():
    """Insert all 25 templates across 10 categories"""
    async with AsyncSessionLocal() as db:
        try:
            # Check existing templates count
            result = await db.execute(text("SELECT COUNT(*) FROM document_templates WHERE society_id = 1"))
            count = result.scalar()
            
            print(f"\n{'='*70}")
            print(f"COMPREHENSIVE TEMPLATE SEEDING - GharMitra RESOURCE CENTRE")
            print(f"{'='*70}")
            print(f"Current templates in database: {count}")
            print(f"Target: 25 templates across 10 categories")
            print(f"{'='*70}\n")
            
            # All 25 templates data
            templates_data = [
                # ============ CATEGORY 1: MOVE-IN/MOVE-OUT (3 templates) ============
                {
                    'template_name': 'Move-In Application',
                    'template_code': 'MOVEIN_APPLICATION',
                    'category': 'moveout',
                    'description': 'Application form for new tenant/owner moving in',
                    'instructions': 'Complete all fields for new member registration.',
                    'template_type': 'auto_fill',
                    'can_autofill': True,
                    'autofill_fields': '["member_name","flat_number","member_email","member_phone","current_date"]',
                    'template_html': SIMPLE_TEMPLATE.format(
                        title='MOVE-IN APPLICATION',
                        fields='<tr><td>Name:</td><td>{{member_name}}</td></tr><tr><td>Flat:</td><td>{{flat_number}}</td></tr><tr><td>Email:</td><td>{{member_email}}</td></tr><tr><td>Phone:</td><td>{{member_phone}}</td></tr><tr><td>Move-in Date:</td><td>{{current_date}}</td></tr>'
                    ),
                    'template_variables': '[]',
                    'icon_name': 'home-import-outline',
                    'available_to': 'all',
                    'display_order': 2
                },
                {
                    'template_name': 'Tenant Registration Form',
                    'template_code': 'TENANT_REGISTRATION',
                    'category': 'moveout',
                    'description': 'Registration form for new tenant',
                    'instructions': 'Fill in tenant details and landlord information.',
                    'template_type': 'auto_fill',
                    'can_autofill': True,
                    'autofill_fields': '["flat_number","society_name","current_date"]',
                    'template_html': SIMPLE_TEMPLATE.format(
                        title='TENANT REGISTRATION FORM',
                        fields='<tr><td>Tenant Name:</td><td>{{tenant_name}}</td></tr><tr><td>Flat:</td><td>{{flat_number}}</td></tr><tr><td>Landlord Name:</td><td>{{landlord_name}}</td></tr><tr><td>Date:</td><td>{{current_date}}</td></tr>'
                    ),
                    'template_variables': '["tenant_name","landlord_name"]',
                    'icon_name': 'account-plus',
                    'available_to': 'all',
                    'display_order': 3
                },
                
                # ============ CATEGORY 2: MAINTENANCE & PAYMENTS (2 more) ============
                {
                    'template_name': 'Payment Receipt',
                    'template_code': 'PAYMENT_RECEIPT',
                    'category': 'maintenance',
                    'description': 'Receipt for maintenance payment received',
                    'instructions': 'Receipt will be auto-generated after payment.',
                    'template_type': 'auto_fill',
                    'can_autofill': True,
                    'autofill_fields': '["member_name","flat_number","society_name","current_date"]',
                    'template_html': SIMPLE_TEMPLATE.format(
                        title='PAYMENT RECEIPT',
                        fields='<tr><td>Received from:</td><td>{{member_name}}</td></tr><tr><td>Flat:</td><td>{{flat_number}}</td></tr><tr><td>Amount:</td><td>Rs.{{amount_paid}}</td></tr><tr><td>Mode:</td><td>{{payment_mode}}</td></tr><tr><td>Date:</td><td>{{current_date}}</td></tr>'
                    ),
                    'template_variables': '["amount_paid","payment_mode"]',
                    'icon_name': 'receipt',
                    'available_to': 'all',
                    'display_order': 2
                },
                {
                    'template_name': 'Demand Notice',
                    'template_code': 'DEMAND_NOTICE',
                    'category': 'maintenance',
                    'description': 'Notice for overdue maintenance payments',
                    'instructions': 'Sent to members with pending dues.',
                    'template_type': 'auto_fill',
                    'can_autofill': True,
                    'autofill_fields': '["member_name","flat_number","current_date"]',
                    'template_html': SIMPLE_TEMPLATE.format(
                        title='DEMAND NOTICE',
                        fields='<tr><td colspan="2">Dear {{member_name}},</td></tr><tr><td>Flat Number:</td><td>{{flat_number}}</td></tr><tr><td>Overdue Amount:</td><td>Rs.{{overdue_amount}}</td></tr><tr><td>Due Date:</td><td>{{due_date}}</td></tr><tr><td colspan="2">Please clear your dues immediately.</td></tr>'
                    ),
                    'template_variables': '["overdue_amount","due_date"]',
                    'icon_name': 'alert-circle',
                    'available_to': 'admin_only',
                    'display_order': 3
                },
                
                # ============ CATEGORY 3: COMPLAINTS & REQUESTS (2 more) ============
                {
                    'template_name': 'Maintenance Request',
                    'template_code': 'MAINTENANCE_REQUEST',
                    'category': 'complaints',
                    'description': 'Request repair or maintenance work',
                    'instructions': 'Specify the issue and location.',
                    'template_type': 'auto_fill',
                    'can_autofill': True,
                    'autofill_fields': '["member_name","flat_number","member_phone","current_date"]',
                    'template_html': SIMPLE_TEMPLATE.format(
                        title='MAINTENANCE REQUEST',
                        fields='<tr><td>Requested by:</td><td>{{member_name}}</td></tr><tr><td>Flat:</td><td>{{flat_number}}</td></tr><tr><td>Phone:</td><td>{{member_phone}}</td></tr><tr><td>Issue:</td><td>{{issue_description}}</td></tr><tr><td>Location:</td><td>{{issue_location}}</td></tr>'
                    ),
                    'template_variables': '["issue_description","issue_location"]',
                    'icon_name': 'tools',
                    'available_to': 'all',
                    'display_order': 2
                },
                {
                    'template_name': 'Amenity Booking Form',
                    'template_code': 'AMENITY_BOOKING',
                    'category': 'complaints',
                    'description': 'Book community hall or other amenities',
                    'instructions': 'Select date and amenity to book.',
                    'template_type': 'auto_fill',
                    'can_autofill': True,
                    'autofill_fields': '["member_name","flat_number","member_phone","current_date"]',
                    'template_html': SIMPLE_TEMPLATE.format(
                        title='AMENITY BOOKING REQUEST',
                        fields='<tr><td>Booked by:</td><td>{{member_name}}</td></tr><tr><td>Flat:</td><td>{{flat_number}}</td></tr><tr><td>Phone:</td><td>{{member_phone}}</td></tr><tr><td>Amenity:</td><td>{{amenity_type}}</td></tr><tr><td>Booking Date:</td><td>{{booking_date}}</td></tr><tr><td>Duration:</td><td>{{duration}}</td></tr>'
                    ),
                    'template_variables': '["amenity_type","booking_date","duration"]',
                    'icon_name': 'calendar-check',
                    'available_to': 'all',
                    'display_order': 3
                },
                
                # ============ CATEGORY 4: PERMISSIONS & APPROVALS (3 templates) ============
                {
                    'template_name': 'Renovation Permission',
                    'template_code': 'RENOVATION_PERMISSION',
                    'category': 'permissions',
                    'description': 'Request permission for flat renovation',
                    'instructions': 'Provide renovation details and contractor information.',
                    'template_type': 'auto_fill',
                    'can_autofill': True,
                    'autofill_fields': '["member_name","flat_number","member_phone","current_date"]',
                    'template_html': SIMPLE_TEMPLATE.format(
                        title='RENOVATION PERMISSION REQUEST',
                        fields='<tr><td>Owner:</td><td>{{member_name}}</td></tr><tr><td>Flat:</td><td>{{flat_number}}</td></tr><tr><td>Work Type:</td><td>{{work_type}}</td></tr><tr><td>Contractor:</td><td>{{contractor_name}}</td></tr><tr><td>Duration:</td><td>{{work_duration}}</td></tr>'
                    ),
                    'template_variables': '["work_type","contractor_name","work_duration"]',
                    'icon_name': 'hammer-wrench',
                    'available_to': 'all',
                    'display_order': 1
                },
                {
                    'template_name': 'Pet Permission',
                    'template_code': 'PET_PERMISSION',
                    'category': 'permissions',
                    'description': 'Request permission to keep pets',
                    'instructions': 'Provide pet details and vaccination records.',
                    'template_type': 'auto_fill',
                    'can_autofill': True,
                    'autofill_fields': '["member_name","flat_number","current_date"]',
                    'template_html': SIMPLE_TEMPLATE.format(
                        title='PET PERMISSION REQUEST',
                        fields='<tr><td>Owner:</td><td>{{member_name}}</td></tr><tr><td>Flat:</td><td>{{flat_number}}</td></tr><tr><td>Pet Type:</td><td>{{pet_type}}</td></tr><tr><td>Pet Breed:</td><td>{{pet_breed}}</td></tr><tr><td>Vaccinated:</td><td>{{vaccination_status}}</td></tr>'
                    ),
                    'template_variables': '["pet_type","pet_breed","vaccination_status"]',
                    'icon_name': 'paw',
                    'available_to': 'all',
                    'display_order': 2
                },
                {
                    'template_name': 'Vehicle Registration',
                    'template_code': 'VEHICLE_REGISTRATION',
                    'category': 'permissions',
                    'description': 'Register additional vehicle for parking',
                    'instructions': 'Provide vehicle details and RC copy.',
                    'template_type': 'auto_fill',
                    'can_autofill': True,
                    'autofill_fields': '["member_name","flat_number","current_date"]',
                    'template_html': SIMPLE_TEMPLATE.format(
                        title='VEHICLE REGISTRATION',
                        fields='<tr><td>Owner:</td><td>{{member_name}}</td></tr><tr><td>Flat:</td><td>{{flat_number}}</td></tr><tr><td>Vehicle No:</td><td>{{vehicle_number}}</td></tr><tr><td>Vehicle Type:</td><td>{{vehicle_type}}</td></tr><tr><td>Model:</td><td>{{vehicle_model}}</td></tr>'
                    ),
                    'template_variables': '["vehicle_number","vehicle_type","vehicle_model"]',
                    'icon_name': 'car',
                    'available_to': 'all',
                    'display_order': 3
                },
                
                # ============ CATEGORY 5: SOCIETY GOVERNANCE (3 templates) ============
                {
                    'template_name': 'AGM Notice',
                    'template_code': 'AGM_NOTICE',
                    'category': 'governance',
                    'description': 'Notice for Annual General Meeting',
                    'instructions': 'AGM details will be auto-filled by admin.',
                    'template_type': 'auto_fill',
                    'can_autofill': True,
                    'autofill_fields': '["society_name","society_address","current_date"]',
                    'template_html': SIMPLE_TEMPLATE.format(
                        title='ANNUAL GENERAL MEETING NOTICE',
                        fields='<tr><td>Society:</td><td>{{society_name}}</td></tr><tr><td>Meeting Date:</td><td>{{meeting_date}}</td></tr><tr><td>Time:</td><td>{{meeting_time}}</td></tr><tr><td>Venue:</td><td>{{meeting_venue}}</td></tr><tr><td colspan="2">All members are requested to attend.</td></tr>'
                    ),
                    'template_variables': '["meeting_date","meeting_time","meeting_venue"]',
                    'icon_name': 'calendar-star',
                    'available_to': 'admin_only',
                    'display_order': 1
                },
                {
                    'template_name': 'Proxy Form',
                    'template_code': 'PROXY_FORM',
                    'category': 'governance',
                    'description': 'Proxy form for AGM/meeting voting',
                    'instructions': 'Authorize someone to vote on your behalf.',
                    'template_type': 'auto_fill',
                    'can_autofill': True,
                    'autofill_fields': '["member_name","flat_number","society_name","current_date"]',
                    'template_html': SIMPLE_TEMPLATE.format(
                        title='PROXY FORM',
                        fields='<tr><td colspan="2">I, {{member_name}}, residing in Flat {{flat_number}}, authorize {{proxy_holder_name}} to vote on my behalf at the meeting on {{meeting_date}}.</td></tr><tr><td>Date:</td><td>{{current_date}}</td></tr><tr><td>Signature:</td><td>___________________</td></tr>'
                    ),
                    'template_variables': '["proxy_holder_name","meeting_date"]',
                    'icon_name': 'account-arrow-right',
                    'available_to': 'all',
                    'display_order': 2
                },
                {
                    'template_name': 'General Notice',
                    'template_code': 'GENERAL_NOTICE',
                    'category': 'governance',
                    'description': 'General announcement to all members',
                    'instructions': 'Create notice for society announcements.',
                    'template_type': 'blank_download',
                    'can_autofill': False,
                    'autofill_fields': None,
                    'template_html': SIMPLE_TEMPLATE.format(
                        title='NOTICE',
                        fields='<tr><td>Date:</td><td>{{date}}</td></tr><tr><td>Subject:</td><td>{{subject}}</td></tr><tr><td colspan="2">{{notice_content}}</td></tr>'
                    ),
                    'template_variables': '["date","subject","notice_content"]',
                    'icon_name': 'bullhorn',
                    'available_to': 'admin_only',
                    'display_order': 3
                },
                
                # ============ CATEGORY 6: LEGAL & COMPLIANCE (2 templates) ============
                {
                    'template_name': 'Member Consent Form (DPDP)',
                    'template_code': 'DPDP_CONSENT',
                    'category': 'legal',
                    'description': 'Data consent form as per DPDP Act 2023',
                    'instructions': 'Required for member data processing.',
                    'template_type': 'auto_fill',
                    'can_autofill': True,
                    'autofill_fields': '["member_name","flat_number","society_name","current_date"]',
                    'template_html': SIMPLE_TEMPLATE.format(
                        title='DATA CONSENT FORM (DPDP ACT 2023)',
                        fields='<tr><td colspan="2">I, {{member_name}}, residing in Flat {{flat_number}}, consent to {{society_name}} processing my personal data for society management purposes.</td></tr><tr><td>Date:</td><td>{{current_date}}</td></tr><tr><td>Signature:</td><td>___________________</td></tr>'
                    ),
                    'template_variables': '[]',
                    'icon_name': 'shield-check',
                    'available_to': 'all',
                    'display_order': 1
                },
                {
                    'template_name': 'Affidavit Template',
                    'template_code': 'AFFIDAVIT',
                    'category': 'legal',
                    'description': 'General affidavit template',
                    'instructions': 'Fill in affidavit details as needed.',
                    'template_type': 'blank_download',
                    'can_autofill': False,
                    'autofill_fields': None,
                    'template_html': SIMPLE_TEMPLATE.format(
                        title='AFFIDAVIT',
                        fields='<tr><td colspan="2">I, {{name}}, do hereby solemnly affirm that {{affidavit_content}}</td></tr><tr><td>Date:</td><td>{{date}}</td></tr><tr><td>Place:</td><td>{{place}}</td></tr><tr><td>Signature:</td><td>___________________</td></tr>'
                    ),
                    'template_variables': '["name","affidavit_content","date","place"]',
                    'icon_name': 'file-document',
                    'available_to': 'all',
                    'display_order': 2
                },
                
                # ============ CATEGORY 7: COMMUNICATION (2 templates) ============
                {
                    'template_name': 'Festival Greetings',
                    'template_code': 'FESTIVAL_GREETING',
                    'category': 'communication',
                    'description': 'Festival greeting template',
                    'instructions': 'Send festival wishes to members.',
                    'template_type': 'blank_download',
                    'can_autofill': False,
                    'autofill_fields': None,
                    'template_html': SIMPLE_TEMPLATE.format(
                        title='FESTIVAL GREETINGS',
                        fields='<tr><td colspan="2"><center><h2>{{festival_name}}</h2><p>{{greeting_message}}</p><p>- {{society_name}}</p></center></td></tr>'
                    ),
                    'template_variables': '["festival_name","greeting_message","society_name"]',
                    'icon_name': 'party-popper',
                    'available_to': 'admin_only',
                    'display_order': 1
                },
                {
                    'template_name': 'Emergency Notice',
                    'template_code': 'EMERGENCY_NOTICE',
                    'category': 'communication',
                    'description': 'Urgent emergency notification',
                    'instructions': 'Use for urgent announcements.',
                    'template_type': 'auto_fill',
                    'can_autofill': True,
                    'autofill_fields': '["society_name","current_date"]',
                    'template_html': '<html><body style="background:#ff0000; color:#fff; padding:40px;"><h1 style="text-align:center;">EMERGENCY NOTICE</h1><p style="font-size:18px;">{{emergency_details}}</p><p>Date: {{current_date}}</p><p>- {{society_name}}</p></body></html>',
                    'template_variables': '["emergency_details"]',
                    'icon_name': 'alert',
                    'available_to': 'admin_only',
                    'display_order': 2
                },
                
                # ============ CATEGORY 8: ADMINISTRATIVE (2 templates) ============
                {
                    'template_name': 'Member Information Update',
                    'template_code': 'MEMBER_INFO_UPDATE',
                    'category': 'administrative',
                    'description': 'Update member contact details',
                    'instructions': 'Notify society of updated information.',
                    'template_type': 'auto_fill',
                    'can_autofill': True,
                    'autofill_fields': '["member_name","flat_number","current_date"]',
                    'template_html': SIMPLE_TEMPLATE.format(
                        title='INFORMATION UPDATE REQUEST',
                        fields='<tr><td>Member:</td><td>{{member_name}}</td></tr><tr><td>Flat:</td><td>{{flat_number}}</td></tr><tr><td>New Email:</td><td>{{new_email}}</td></tr><tr><td>New Phone:</td><td>{{new_phone}}</td></tr><tr><td>Date:</td><td>{{current_date}}</td></tr>'
                    ),
                    'template_variables': '["new_email","new_phone"]',
                    'icon_name': 'account-edit',
                    'available_to': 'all',
                    'display_order': 1
                },
                {
                    'template_name': 'Parking Sticker Request',
                    'template_code': 'PARKING_STICKER',
                    'category': 'administrative',
                    'description': 'Request new parking sticker',
                    'instructions': 'For lost or new vehicle stickers.',
                    'template_type': 'auto_fill',
                    'can_autofill': True,
                    'autofill_fields': '["member_name","flat_number","current_date"]',
                    'template_html': SIMPLE_TEMPLATE.format(
                        title='PARKING STICKER REQUEST',
                        fields='<tr><td>Member:</td><td>{{member_name}}</td></tr><tr><td>Flat:</td><td>{{flat_number}}</td></tr><tr><td>Vehicle Number:</td><td>{{vehicle_number}}</td></tr><tr><td>Reason:</td><td>{{reason}}</td></tr>'
                    ),
                    'template_variables': '["vehicle_number","reason"]',
                    'icon_name': 'parking',
                    'available_to': 'all',
                    'display_order': 2
                },
                
                # ============ CATEGORY 9: FINANCIAL (2 templates) ============
                {
                    'template_name': 'Loan Application',
                    'template_code': 'LOAN_APPLICATION',
                    'category': 'financial',
                    'description': 'Apply for loan from society fund',
                    'instructions': 'Specify loan amount and purpose.',
                    'template_type': 'auto_fill',
                    'can_autofill': True,
                    'autofill_fields': '["member_name","flat_number","member_phone","current_date"]',
                    'template_html': SIMPLE_TEMPLATE.format(
                        title='LOAN APPLICATION',
                        fields='<tr><td>Applicant:</td><td>{{member_name}}</td></tr><tr><td>Flat:</td><td>{{flat_number}}</td></tr><tr><td>Loan Amount:</td><td>Rs.{{loan_amount}}</td></tr><tr><td>Purpose:</td><td>{{loan_purpose}}</td></tr><tr><td>Repayment Period:</td><td>{{repayment_period}}</td></tr>'
                    ),
                    'template_variables': '["loan_amount","loan_purpose","repayment_period"]',
                    'icon_name': 'cash',
                    'available_to': 'all',
                    'display_order': 1
                },
                {
                    'template_name': 'Expense Approval Form',
                    'template_code': 'EXPENSE_APPROVAL',
                    'category': 'financial',
                    'description': 'Request approval for society expense',
                    'instructions': 'Committee approval required for expenses.',
                    'template_type': 'auto_fill',
                    'can_autofill': True,
                    'autofill_fields': '["society_name","current_date"]',
                    'template_html': SIMPLE_TEMPLATE.format(
                        title='EXPENSE APPROVAL REQUEST',
                        fields='<tr><td>Item:</td><td>{{expense_item}}</td></tr><tr><td>Amount:</td><td>Rs.{{expense_amount}}</td></tr><tr><td>Vendor:</td><td>{{vendor_name}}</td></tr><tr><td>Justification:</td><td>{{justification}}</td></tr><tr><td>Date:</td><td>{{current_date}}</td></tr>'
                    ),
                    'template_variables': '["expense_item","expense_amount","vendor_name","justification"]',
                    'icon_name': 'file-check',
                    'available_to': 'admin_only',
                    'display_order': 2
                },
                
                # ============ CATEGORY 10: EMERGENCY & SAFETY (2 templates) ============
                {
                    'template_name': 'Emergency Contact Form',
                    'template_code': 'EMERGENCY_CONTACT',
                    'category': 'emergency',
                    'description': 'Register emergency contact details',
                    'instructions': 'Provide emergency contact information.',
                    'template_type': 'auto_fill',
                    'can_autofill': True,
                    'autofill_fields': '["member_name","flat_number","member_phone"]',
                    'template_html': SIMPLE_TEMPLATE.format(
                        title='EMERGENCY CONTACT DETAILS',
                        fields='<tr><td>Member:</td><td>{{member_name}}</td></tr><tr><td>Flat:</td><td>{{flat_number}}</td></tr><tr><td>Phone:</td><td>{{member_phone}}</td></tr><tr><td>Emergency Contact Name:</td><td>{{emergency_contact_name}}</td></tr><tr><td>Emergency Phone:</td><td>{{emergency_phone}}</td></tr><tr><td>Relationship:</td><td>{{relationship}}</td></tr>'
                    ),
                    'template_variables': '["emergency_contact_name","emergency_phone","relationship"]',
                    'icon_name': 'phone-alert',
                    'available_to': 'all',
                    'display_order': 1
                },
                {
                    'template_name': 'Fire Safety Checklist',
                    'template_code': 'FIRE_SAFETY',
                    'category': 'emergency',
                    'description': 'Fire safety inspection checklist',
                    'instructions': 'Annual fire safety inspection form.',
                    'template_type': 'blank_download',
                    'can_autofill': False,
                    'autofill_fields': None,
                    'template_html': '<html><body style="font-family:Arial;margin:40px;"><h2 style="text-align:center;">FIRE SAFETY CHECKLIST</h2><ul style="line-height:2;"><li>[ ] Fire extinguishers checked</li><li>[ ] Exit signs working</li><li>[ ] Emergency lights functional</li><li>[ ] Fire alarms tested</li><li>[ ] Evacuation routes clear</li><li>[ ] Fire hoses inspected</li></ul><p>Inspector: ___________________</p><p>Date: ___________________</p></body></html>',
                    'template_variables': '[]',
                    'icon_name': 'fire',
                    'available_to': 'admin_only',
                    'display_order': 2
                },
            ]
            
            inserted_count = 0
            skipped_count = 0
            
            for template_data in templates_data:
                try:
                    # Check if template already exists
                    result = await db.execute(
                        text("SELECT id FROM document_templates WHERE template_code = :code AND society_id = 1"),
                        {'code': template_data['template_code']}
                    )
                    existing = result.fetchone()
                    
                    if existing:
                        print(f"  [SKIP] {template_data['template_name']} (already exists)")
                        skipped_count += 1
                        continue
                    
                    # Insert template
                    template = DocumentTemplate(
                        society_id=1,
                        is_active=True,
                        **template_data
                    )
                    db.add(template)
                    inserted_count += 1
                    print(f"  [OK] Added: {template_data['template_name']} ({template_data['category']})")
                    
                except Exception as e:
                    print(f"  [ERROR] {template_data['template_code']}: {e}")
            
            await db.commit()
            
            # Final count
            result = await db.execute(text("SELECT COUNT(*) FROM document_templates WHERE society_id = 1"))
            final_count = result.scalar()
            
            print(f"\n{'='*70}")
            print(f"SEEDING COMPLETE!")
            print(f"{'='*70}")
            print(f"New templates added: {inserted_count}")
            print(f"Already existing (skipped): {skipped_count}")
            print(f"Total templates in database: {final_count}")
            print(f"{'='*70}\n")
            
            # Count by category
            result = await db.execute(text("""
                SELECT category, COUNT(*) as count 
                FROM document_templates 
                WHERE society_id = 1 AND is_active = 1
                GROUP BY category
                ORDER BY category
            """))
            
            categories = result.fetchall()
            
            print("Templates by category:")
            for cat, cat_count in categories:
                print(f"  - {cat}: {cat_count} templates")
            
            print(f"\nSUCCESS! Resource Centre is now fully populated!")
            print(f"Refresh your mobile app to see all templates!\n")
            
        except Exception as e:
            await db.rollback()
            print(f"\nERROR: {e}")
            import traceback
            traceback.print_exc()
            raise

if __name__ == '__main__':
    print("\nStarting comprehensive template seeding...")
    asyncio.run(seed_all_templates())


