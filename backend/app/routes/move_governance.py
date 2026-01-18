"""
Move-In / Move-Out Governance API routes
Handles Dues isolation, NDC generation, and Personal Arrears management
"""
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, insert
from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel
from decimal import Decimal
import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm

from app.database import get_db
from app.models.user import UserResponse
from app.models_db import (
    Member, Flat, Transaction, JournalEntry,
    TransactionType,
    PersonalArrears, PersonalArrearsStatus, Society,
    AccountCode, AccountType, MaintenanceBill,
    SupplementaryBill, SupplementaryBillFlat, BillStatus
)
from app.dependencies import get_current_admin_user
from app.utils.audit import log_action

router = APIRouter()

# ============ PYDANTIC MODELS ============
class ArrearsTransferRequest(BaseModel):
    member_id: int
    flat_id: int
    amount: Decimal
    notes: Optional[str] = None

class ArrearsResponse(BaseModel):
    id: int
    member_id: int
    flat_id: int
    account_code: str
    original_balance: Decimal
    current_balance: Decimal
    status: str
    transfer_date: date

class FinalBillResponse(BaseModel):
    flat_number: str
    outstanding_arrears: Decimal
    current_month_prorata: Decimal
    total_payable: Decimal
    calculation_notes: str

class DamageClaimCreate(BaseModel):
    flat_id: int
    amount: Decimal
    description: str
    instant_post: bool = True

# ============ HELPERS ============
async def generate_next_account_code(society_id: int, db: AsyncSession) -> str:
    """Generates a unique Personal Arrears account code (range 1201-1499)"""
    result = await db.execute(
        select(AccountCode.code)
        .where(AccountCode.society_id == society_id, AccountCode.code.like('12%'))
        .order_by(AccountCode.code.desc())
        .limit(1)
    )
    last_code = result.scalar_one_or_none()
    
    if not last_code:
        return "1201"
    
    next_int = int(last_code) + 1
    return str(next_int)

# ============ API ENDPOINTS ============

@router.post("/transfer-to-arrears", response_model=ArrearsResponse)
async def transfer_to_personal_arrears(
    request: ArrearsTransferRequest,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Isolates disputed dues from a Flat Ledger to a Personal Ledger.
    Resets Flat Balance to 0, enabling NDC for New Owner.
    """
    # 1. Validate Member and Flat
    result = await db.execute(select(Member).where(Member.id == request.member_id))
    member = result.scalar_one_or_none()
    if not member or member.society_id != current_user.society_id:
        raise HTTPException(status_code=404, detail="Member not found")
        
    result = await db.execute(select(Flat).where(Flat.id == request.flat_id))
    flat = result.scalar_one_or_none()
    if not flat:
        raise HTTPException(status_code=404, detail="Flat not found")

    # 2. Create proper Account Head for this individual if not already exists
    personal_code = member.personal_account_code
    if not personal_code:
        personal_code = await generate_next_account_code(current_user.society_id, db)
        new_account = AccountCode(
            society_id=current_user.society_id,
            code=personal_code,
            name=f"Arrears: {member.name} ({flat.flat_number})",
            type=AccountType.ASSET,
            description=f"Personal Arrears ledger for {member.name} transferred from Flat {flat.flat_number}",
            opening_balance=0,
            current_balance=request.amount
        )
        db.add(new_account)
        member.personal_account_code = personal_code
    else:
        # Update existing personal account balance
        result = await db.execute(select(AccountCode).where(AccountCode.code == personal_code, AccountCode.society_id == current_user.society_id))
        account = result.scalar_one()
        account.current_balance += request.amount

    # 3. Create Journal Voucher for Transfer
    # Entry: Debit Personal Account (Asset) / Credit Flat Account (Asset - 1100)
    journal_no = f"JV-AR-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    new_jv = JournalEntry(
        society_id=current_user.society_id,
        entry_number=journal_no,
        date=datetime.utcnow().date(),
        description=f"Transfer of disputed dues from Flat {flat.flat_number} to {member.name}'s personal arrears ledger",
        total_debit=request.amount,
        total_credit=request.amount,
        is_balanced=True,
        added_by=int(current_user.id),
        created_at=datetime.utcnow()
    )
    db.add(new_jv)
    await db.flush()

    # Create Debit leg (Personal Account)
    db_txn = Transaction(
        society_id=current_user.society_id,
        document_number=f"{journal_no}-DB",
        type=TransactionType.EXPENSE,
        category="Dues Isolation",
        account_code=personal_code,
        amount=request.amount,
        debit_amount=request.amount,
        description=f"Dues transferred from Flat {flat.flat_number}",
        date=datetime.utcnow().date(),
        added_by=int(current_user.id),
        journal_entry_id=new_jv.id
    )
    
    # Create Credit leg (Flat Account - 1100)
    cr_txn = Transaction(
        society_id=current_user.society_id,
        document_number=f"{journal_no}-CR",
        type="credit",
        category="Dues Transfer",
        account_code="1100", # Receiving Account
        amount=request.amount,
        credit_amount=request.amount,
        description=f"Dues transferred to {member.name}'s personal ledger",
        date=datetime.utcnow().date(),
        added_by=int(current_user.id),
        flat_id=flat.id,
        journal_entry_id=new_jv.id
    )
    
    db.add(db_txn)
    db.add(cr_txn)

    # 4. Record Arrears Entry for Tracking
    new_arrears = PersonalArrears(
        society_id=current_user.society_id,
        member_id=member.id,
        flat_id=flat.id,
        account_code=personal_code,
        original_flat_balance=request.amount,
        current_arrears_balance=request.amount,
        status=PersonalArrearsStatus.OPEN,
        transfer_date=datetime.utcnow().date(),
        transfer_voucher_id=new_jv.id,
        notes=request.notes,
        created_at=datetime.utcnow()
    )
    db.add(new_arrears)

    await db.commit()
    await db.refresh(new_arrears)

    # Log action
    await log_action(
        db=db,
        society_id=current_user.society_id,
        user_id=int(current_user.id),
        action_type="transfer",
        entity_type="personal_arrears",
        entity_id=new_arrears.id,
        new_values={"amount": float(request.amount), "member": member.name}
    )

    return ArrearsResponse(
        id=new_arrears.id,
        member_id=new_arrears.member_id,
        flat_id=new_arrears.flat_id,
        account_code=new_arrears.account_code,
        original_balance=new_arrears.original_flat_balance,
        current_balance=new_arrears.current_arrears_balance,
        status=new_arrears.status.value,
        transfer_date=new_arrears.transfer_date
    )

@router.get("/personal-arrears", response_model=List[ArrearsResponse])
async def list_personal_arrears(
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """List all open/active personal arrears cases"""
    result = await db.execute(
        select(PersonalArrears).where(
            and_(
                PersonalArrears.society_id == current_user.society_id,
                PersonalArrears.status != PersonalArrearsStatus.CLOSED
            )
        ).order_by(PersonalArrears.transfer_date.desc())
    )
    return result.scalars().all()

@router.get("/generate-ndc/{flat_id}")
async def generate_ndc_pdf(
    flat_id: int,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generates No Dues Certificate (NDC) PDF if flat balance is zero.
    Follows template in NDC.md
    """
    # 1. Check flat balance
    from app.routes.member_onboarding import get_flat_balance
    balance = await get_flat_balance(flat_id, db)
    
    if balance > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot issue NDC. Flat has outstanding dues: ₹{balance}"
        )

    # 2. Get Details
    result = await db.execute(select(Flat).where(Flat.id == flat_id))
    flat = result.scalar_one_or_none()
    
    result = await db.execute(select(Society).where(Society.id == current_user.society_id))
    society = result.scalar_one_or_none()
    
    # Get current active member (Owner)
    result = await db.execute(
        select(Member).where(
            and_(
                Member.flat_id == flat_id,
                Member.member_type == "owner",
                Member.status == "active"
            )
        )
    )
    owner = result.scalar_one_or_none()
    owner_name = owner.name if owner else "Owner"

    # 3. Generate PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], alignment=1, spaceAfter=20)
    body_style = ParagraphStyle('BodyStyle', parent=styles['Normal'], leading=16, spaceAfter=10)
    
    elements = []
    
    # Header
    elements.append(Paragraph(f"<b>{society.name.upper()}</b>", title_style))
    elements.append(Paragraph(f"{society.address}", ParagraphStyle('Addr', parent=styles['Normal'], alignment=1)))
    elements.append(Spacer(1, 1*cm))
    
    elements.append(Paragraph("<u>NO DUES CERTIFICATE (NDC)</u>", title_style))
    elements.append(Spacer(1, 0.5*cm))
    
    # Date
    elements.append(Paragraph(f"Date: {date.today().strftime('%d-%m-%Y')}", styles['Normal']))
    elements.append(Spacer(1, 1*cm))
    
    # Body
    body_text = (
        f"This is to certify that there are no outstanding maintenance dues or any other charges "
        f"payable to <b>{society.name}</b> in respect of Flat No. <b>{flat.flat_number}</b> "
        f"owned/occupied by <b>{owner_name}</b> as of date."
    )
    elements.append(Paragraph(body_text, body_style))
    
    # Details Table
    data = [
        ["Flat Number:", flat.flat_number],
        ["Owner/Tenant Name:", owner_name],
        ["Outstanding Amount:", "₹ 0.00"],
        ["Paid Up To:", date.today().strftime('%B %Y')],
        ["Purpose:", "Membership Transfer / Move-Out"]
    ]
    t = Table(data, colWidths=[5*cm, 10*cm])
    t.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 2*cm))
    
    # Footer
    elements.append(Paragraph("For and on behalf of", styles['Normal']))
    elements.append(Paragraph(f"<b>{society.name}</b>", styles['Normal']))
    elements.append(Spacer(1, 3*cm))
    
    footer_data = [["(Chairman)", "(Secretary)", "(Treasurer)"]]
    ft = Table(footer_data, colWidths=[5*cm, 5*cm, 5*cm])
    ft.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER')]))
    elements.append(ft)

    doc.build(elements)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer, 
        media_type='application/pdf', 
        headers={"Content-Disposition": f"attachment; filename=NDC_{flat.flat_number}.pdf"}
    )

@router.get("/police-verification-form/{member_id}")
async def generate_police_verification_pdf(
    member_id: int,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generates a pre-filled Police Verification Report PDF.
    Follows template in POLICE_VERIFICATION_REPORT.md
    """
    result = await db.execute(select(Member).where(Member.id == member_id))
    member = result.scalar_one_or_none()
    if not member: raise HTTPException(status_code=404, detail="Member not found")
    
    result = await db.execute(select(Flat).where(Flat.id == member.flat_id))
    flat = result.scalar_one()
    
    result = await db.execute(select(Society).where(Society.id == current_user.society_id))
    society = result.scalar_one()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []
    
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], alignment=1)
    subtitle_style = ParagraphStyle('Sub', parent=styles['Heading2'], alignment=1)
    
    elements.append(Paragraph("TENANT POLICE VERIFICATION REPORT", title_style))
    elements.append(Spacer(1, 1*cm))
    
    # Section 1: Society Details
    elements.append(Paragraph("<b>1. HOUSING SOCIETY DETAILS</b>", styles['Heading3']))
    soc_data = [
        ["Society Name:", society.name],
        ["Address:", society.address]
    ]
    st = Table(soc_data, colWidths=[5*cm, 10*cm])
    st.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey)]))
    elements.append(st)
    elements.append(Spacer(1, 0.5*cm))
    
    # Section 2: Occupant Details
    elements.append(Paragraph("<b>2. OCCUPANT DETAILS</b>", styles['Heading3']))
    occ_data = [
        ["Full Name:", member.name],
        ["Phone Number:", member.phone_number],
        ["Email:", member.email or "N/A"],
        ["Flat Number:", flat.flat_number],
        ["Occupation:", member.occupation or "N/A"]
    ]
    ot = Table(occ_data, colWidths=[5*cm, 10*cm])
    ot.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey)]))
    elements.append(ot)
    elements.append(Spacer(1, 1*cm))
    
    # Section 3: Declaration
    elements.append(Paragraph("<b>DECLARATION</b>", styles['Heading3']))
    decl_text = (
        f"I, {member.name}, hereby declare that the information provided above is true to the best of my knowledge. "
        "I understand that providing false information is a punishable offense."
    )
    elements.append(Paragraph(decl_text, styles['Normal']))
    elements.append(Spacer(1, 2*cm))
    
    # Signature fields
    sig_data = [["(Signature of Tenant)", "(Signature of Owner)", "(Society Seal)"]]
    sig_table = Table(sig_data, colWidths=[5*cm, 5*cm, 5*cm])
    elements.append(sig_table)

    doc.build(elements)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer, 
        media_type='application/pdf', 
        headers={"Content-Disposition": f"attachment; filename=Police_Verification_{member.name}.pdf"}
    )

@router.get("/calculate-final-bill/{flat_id}", response_model=FinalBillResponse)
async def calculate_final_bill(
    flat_id: int,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Calculates final bill on move-out (FR-2).
    Includes outstanding arrears + pro-rata charges for the current month.
    """
    from app.routes.member_onboarding import get_flat_balance
    from app.models_db import MaintenanceBill
    
    # 1. Total Outstanding (Ledger Balance)
    balance = await get_flat_balance(flat_id, db)
    
    # 2. Calculate Pro-rata for current month if not already billed
    # Find last month's bill to guestimate current month rate
    result = await db.execute(
        select(MaintenanceBill).where(MaintenanceBill.flat_id == flat_id)
        .order_by(MaintenanceBill.year.desc(), MaintenanceBill.month.desc())
        .limit(1)
    )
    last_bill = result.scalar_one_or_none()
    
    prorata_amount = Decimal("0.00")
    notes = "Calculation based on ledger balance."
    
    if last_bill:
        monthly_rate = last_bill.amount # Excl arrears
        today = date.today()
        import calendar # Import calendar here as it's only used in this block
        days_in_month = calendar.monthrange(today.year, today.month)[1]
        days_used = today.day
        
        # Determine if current month is already billed
        current_bill_result = await db.execute(
            select(MaintenanceBill).where(
                and_(
                    MaintenanceBill.flat_id == flat_id,
                    MaintenanceBill.month == today.month,
                    MaintenanceBill.year == today.year
                )
            )
        )
        if current_bill_result.scalar_one_or_none():
            notes += " Current month already billed in full."
        else:
            prorata_amount = (monthly_rate * Decimal(days_used) / Decimal(days_in_month)).quantize(Decimal("0.01"))
            notes += f" Added pro-rata charges (₹{prorata_amount}) for {days_used} days of current month."

    return FinalBillResponse(
        flat_number=last_bill.flat_number if last_bill else "Unknown",
        outstanding_arrears=Decimal(str(balance)),
        current_month_prorata=prorata_amount,
        total_payable=Decimal(str(balance)) + prorata_amount,
        calculation_notes=notes
    )

@router.post("/damage-claim")
async def raise_damage_claim(
    request: DamageClaimCreate,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Raises an instant damage/misuse charge for a flat.
    Creates SupplementaryBill, MaintenanceBill and posts JV immediately.
    """
    # 1. Look up flat
    result = await db.execute(select(Flat).where(Flat.id == request.flat_id))
    flat = result.scalar_one_or_none()
    if not flat or flat.society_id != current_user.society_id:
        raise HTTPException(status_code=404, detail="Flat not found")

    # 2. Create Supplementary Bill record (for history)
    new_supp = SupplementaryBill(
        society_id=current_user.society_id,
        title=f"Damage/Misc Claim - {flat.flat_number}",
        description=request.description,
        date=date.today(),
        approved_by=current_user.name,
        status="posted"
    )
    db.add(new_supp)
    await db.flush()

    new_supp_flat = SupplementaryBillFlat(
        supplementary_bill_id=new_supp.id,
        flat_id=flat.id,
        amount=request.amount,
        is_included_in_monthly=request.instant_post, # If instant, mark True so monthly doesn't pick it up
        status="unpaid"
    )
    db.add(new_supp_flat)

    if not request.instant_post:
        # Just queue for monthly, no JV or extra MaintenanceBill needed now
        new_supp.status = "approved"
        await db.commit()
        return {"message": "Charge queued for next monthly bill", "id": new_supp.id}

    # 3. Create Maintenance Bill (to reflect in Flat Balance instantly)
    # We use a unique bill number for this claim
    bill_no = f"CLM-{flat.flat_number}-{datetime.utcnow().strftime('%y%m%s')}"
    new_bill = MaintenanceBill(
        society_id=current_user.society_id,
        flat_id=flat.id,
        flat_number=flat.flat_number,
        bill_number=bill_no,
        month=date.today().month,
        year=date.today().year,
        amount=request.amount,
        maintenance_amount=0,
        water_amount=0,
        total_amount=request.amount,
        arrears_amount=0,
        breakdown={
            "supplementary_charges": [{"title": "Damage/Misc Claim", "amount": float(request.amount)}],
            "description": request.description
        },
        status=BillStatus.UNPAID,
        is_posted=True,
        posted_at=datetime.utcnow()
    )
    db.add(new_bill)
    await db.flush()
    
    new_supp_flat.maintenance_bill_id = new_bill.id

    # 4. Immediate Accounting Posting (Credit 4000, Debit 1100)
    # Get Account Heads
    res = await db.execute(select(AccountCode).where(AccountCode.code == "4000", AccountCode.society_id == current_user.society_id))
    acct_4000 = res.scalar_one_or_none()
    res = await db.execute(select(AccountCode).where(AccountCode.code == "1100", AccountCode.society_id == current_user.society_id))
    acct_1100 = res.scalar_one_or_none()
    
    if not acct_1100 or not acct_4000:
        # Fallback to creating them if missing (shouldn't happen in production)
        raise HTTPException(status_code=500, detail="Standard account codes (1100/4000) not found")

    # Create JV
    jv_no = f"JV-CLM-{flat.flat_number}-{datetime.utcnow().strftime('%Y%m%d%H%M')}"
    new_jv = JournalEntry(
        society_id=current_user.society_id,
        entry_number=jv_no,
        date=date.today(),
        description=f"Damage/Misc Claim for Flat {flat.flat_number}: {request.description}",
        total_debit=request.amount,
        total_credit=request.amount,
        is_balanced=True,
        added_by=int(current_user.id)
    )
    db.add(new_jv)
    await db.flush()

    # Debit 1100 (Receivable)
    db.add(Transaction(
        society_id=current_user.society_id,
        document_number=f"{jv_no}-DB",
        type=TransactionType.EXPENSE,
        category="Damage/Misuse Charges",
        account_code="1100",
        amount=request.amount,
        debit_amount=request.amount,
        description=f"Damage claim on Flat {flat.flat_number}",
        date=date.today(),
        added_by=int(current_user.id),
        flat_id=flat.id,
        journal_entry_id=new_jv.id
    ))
    acct_1100.current_balance += request.amount

    # Credit 4000 (Income)
    db.add(Transaction(
        society_id=current_user.society_id,
        document_number=f"{jv_no}-CR",
        type=TransactionType.INCOME,
        category="Damage Claim",
        account_code="4000",
        amount=request.amount,
        credit_amount=request.amount,
        description=f"Damage claim income from Flat {flat.flat_number}",
        date=date.today(),
        added_by=int(current_user.id),
        journal_entry_id=new_jv.id
    ))
    acct_4000.current_balance += request.amount

    await db.commit()
    
    # Log action
    await log_action(
        db=db,
        society_id=current_user.society_id,
        user_id=int(current_user.id),
        action_type="create",
        entity_type="damage_claim",
        entity_id=new_bill.id,
        new_values={"amount": float(request.amount), "flat": flat.flat_number}
    )

    return {"message": "Damage claim raised successfully", "bill_number": bill_no, "total_amount": float(request.amount)}
