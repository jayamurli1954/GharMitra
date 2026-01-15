"""Maintenance billing API routes"""
from decimal import Decimal, ROUND_CEILING
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_, or_, func
from sqlalchemy.orm import selectinload
import calendar
import math

from app.database import get_db
from app.models.maintenance import (
    ApartmentSettings,
    ApartmentSettingsResponse,
    FixedExpense,
    FixedExpenseResponse,
    WaterExpense,
    WaterExpenseResponse,
    BillGenerationRequest,
    BillGenerationResponse,
    MaintenanceBill,
    MaintenanceBillDetail,
    BillBreakdown,
    PostBillsRequest,
    CollectibleExpense,
    CollectibleExpensesResponse,
    ReverseBillRequest,
    RegenerateBillRequest
)
from app.models_db import (
    CalculationMethod,
    BillStatus,
    ApartmentSettings as ApartmentSettingsDB,
    FixedExpense as FixedExpenseDB,
    WaterExpense as WaterExpenseDB,
    MaintenanceBill as MaintenanceBillDB,
    Flat,
    Member,
    Society,
    SocietySettings,
    Transaction,
    TransactionType,
    AccountCode as AccountCodeDB,
    AccountType,
    OccupancyStatus,
    User,
    Payment,
    JournalEntry,
    SupplementaryBill as SupplementaryBillDB,
    SupplementaryBillFlat as SupplementaryBillFlatDB
)
from app.models.user import UserResponse
from app.dependencies import get_current_user, get_current_admin_user
from app.utils.number_to_words import number_to_words
from app.utils.audit import log_action

async def get_flat_balance(db: AsyncSession, society_id: int, flat_id: int, as_of_date: Optional[date] = None) -> Decimal:
    """
    Calculate the current balance for a flat based on posted bills and payments.
    Positive = Flat owes money (Arrears)
    Negative = Flat has advance payment
    """
    if as_of_date is None:
        as_of_date = date.today()
    
    # 1. Total Posted Bills (Amount we asked for)
    # We use create_at for bills to determine the 'period' it belongs to for balance calculation
    bill_query = select(func.sum(MaintenanceBillDB.total_amount)).where(
        and_(
            MaintenanceBillDB.society_id == society_id,
            MaintenanceBillDB.flat_id == flat_id,
            MaintenanceBillDB.is_posted == True,
            MaintenanceBillDB.created_at <= datetime.combine(as_of_date, datetime.max.time())
        )
    )
    bill_res = await db.execute(bill_query)
    total_billed = Decimal(str(bill_res.scalar() or "0.00"))
    
    # 2. Total Payments (Amount we received)
    pay_query = select(func.sum(Payment.amount)).where(
        and_(
            Payment.society_id == society_id,
            Payment.flat_id == flat_id,
            Payment.status == "completed",
            Payment.payment_date <= as_of_date
        )
    )
    pay_res = await db.execute(pay_query)
    total_paid = Decimal(str(pay_res.scalar() or "0.00"))
    
    # 3. Arrears = Billed - Paid
    return (total_billed - total_paid).quantize(Decimal("0.01"))

router = APIRouter()


# ============= APARTMENT SETTINGS =============

@router.get("/allowed-bill-month")
async def get_allowed_bill_month(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get the allowed month for bill generation (previous month only)"""
    today = date.today()
    current_month = today.month
    current_year = today.year
    
    # Calculate previous month
    if current_month == 1:
        allowed_month = 12
        allowed_year = current_year - 1
    else:
        allowed_month = current_month - 1
        allowed_year = current_year
    
    # Check if bills already exist for allowed month
    result = await db.execute(
        select(MaintenanceBillDB).where(
            and_(
                MaintenanceBillDB.month == allowed_month,
                MaintenanceBillDB.year == allowed_year,
                MaintenanceBillDB.society_id == current_user.society_id
            )
        )
    )
    existing_bills = result.scalars().all()
    already_generated = len(existing_bills) > 0
    
    return {
        "allowed_month": allowed_month,
        "allowed_year": allowed_year,
        "current_month": current_month,
        "current_year": current_year,
        "already_generated": already_generated,
        "month_name": calendar.month_name[allowed_month],
        "formatted": f"{calendar.month_name[allowed_month]} {allowed_year}"
    }


@router.get("/settings", response_model=ApartmentSettingsResponse)
async def get_apartment_settings(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get apartment settings (filtered by user's society)"""
    # PRD: Multi-tenancy - Filter by society_id
    # Note: ApartmentSettingsDB may need society_id field, for now using SocietySettings
    result = await db.execute(
        select(SocietySettings).where(SocietySettings.society_id == current_user.society_id)
    )
    settings = result.scalar_one_or_none()
    
    # If SocietySettings doesn't exist, try ApartmentSettingsDB (legacy)
    if not settings:
        result = await db.execute(select(ApartmentSettingsDB))
        settings = result.scalar_one_or_none()

    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Apartment settings not configured. Please configure settings first."
        )

    return ApartmentSettingsResponse(
        id=str(settings.id),
        apartment_name=settings.apartment_name,
        total_flats=settings.total_flats,
        calculation_method=str(settings.calculation_method.value) if hasattr(settings.calculation_method, 'value') else str(settings.calculation_method),
        sqft_rate=settings.sqft_rate,
        sinking_fund_total=settings.sinking_fund_total,
        created_at=settings.created_at,
        updated_at=settings.updated_at
    )


@router.post("/settings", response_model=ApartmentSettingsResponse, status_code=status.HTTP_201_CREATED)
async def create_or_update_settings(
    settings_data: ApartmentSettings,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Create or update apartment settings (admin only)"""
    # Validate apartment_name
    if not settings_data.apartment_name or not settings_data.apartment_name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="apartment_name is required and cannot be empty"
        )
    
    # Validate based on calculation method
    if settings_data.calculation_method == "sqft_rate":
        if settings_data.sqft_rate is None or settings_data.sqft_rate <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="sqft_rate is required and must be greater than 0 for sqft_rate calculation method"
            )
    
    # For variable method, sinking_fund_total can be 0 (optional)
    # No validation needed - it defaults to 0 if not provided

    # Check if settings exist
    result = await db.execute(select(ApartmentSettingsDB))
    existing_apartment = result.scalar_one_or_none()
    
    # Also check/update SocietySettings for onboarding_date
    result = await db.execute(
        select(SocietySettings).where(SocietySettings.society_id == current_user.society_id)
    )
    existing_society = result.scalar_one_or_none()
    
    # Set onboarding_date if creating new settings and it doesn't exist
    if not existing_apartment and (not existing_society or not existing_society.onboarding_date):
        if not existing_society:
            # Create SocietySettings if it doesn't exist
            existing_society = SocietySettings(
                society_id=current_user.society_id,
                onboarding_date=date.today()
            )
            db.add(existing_society)
        else:
            # Update existing SocietySettings
            existing_society.onboarding_date = date.today()
        await db.commit()

    if existing_apartment:
        # Update existing settings
        existing_apartment.apartment_name = settings_data.apartment_name
        existing_apartment.total_flats = settings_data.total_flats
        # Convert string to enum if needed
        if isinstance(settings_data.calculation_method, str):
            existing_apartment.calculation_method = CalculationMethod(settings_data.calculation_method)
        else:
            existing_apartment.calculation_method = settings_data.calculation_method
        existing_apartment.sqft_rate = settings_data.sqft_rate
        existing_apartment.sinking_fund_total = settings_data.sinking_fund_total
        existing_apartment.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(existing_apartment)

        return ApartmentSettingsResponse(
            id=str(existing_apartment.id),
            apartment_name=existing_apartment.apartment_name,
            total_flats=existing_apartment.total_flats,
            calculation_method=str(existing_apartment.calculation_method.value) if hasattr(existing_apartment.calculation_method, 'value') else str(existing_apartment.calculation_method),
            sqft_rate=existing_apartment.sqft_rate,
            sinking_fund_total=existing_apartment.sinking_fund_total,
            created_at=existing_apartment.created_at,
            updated_at=existing_apartment.updated_at
        )
    else:
        # Create new settings
        # Convert string to enum if needed
        calc_method = settings_data.calculation_method
        if isinstance(calc_method, str):
            calc_method = CalculationMethod(calc_method)
        
        new_settings = ApartmentSettingsDB(
            society_id=current_user.society_id,
            apartment_name=settings_data.apartment_name,
            total_flats=settings_data.total_flats,
            calculation_method=calc_method,
            sqft_rate=settings_data.sqft_rate,
            sinking_fund_total=settings_data.sinking_fund_total,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(new_settings)
        await db.commit()
        await db.refresh(new_settings)

        return ApartmentSettingsResponse(
            id=str(new_settings.id),
            apartment_name=new_settings.apartment_name,
            total_flats=new_settings.total_flats,
            calculation_method=str(new_settings.calculation_method.value) if hasattr(new_settings.calculation_method, 'value') else str(new_settings.calculation_method),
            sqft_rate=new_settings.sqft_rate,
            sinking_fund_total=new_settings.sinking_fund_total,
            created_at=new_settings.created_at,
            updated_at=new_settings.updated_at
        )


# ============= FIXED EXPENSES =============

@router.get("/fixed-expenses", response_model=List[FixedExpenseResponse])
async def list_fixed_expenses(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all fixed expenses (filtered by user's society)"""
    # PRD: Multi-tenancy - Filter by society_id
    result = await db.execute(
        select(FixedExpenseDB)
        .where(FixedExpenseDB.society_id == current_user.society_id)
        .order_by(FixedExpenseDB.name)
    )
    expenses = result.scalars().all()

    return [
        FixedExpenseResponse(
            id=str(expense.id),
            name=expense.name,
            amount=expense.amount,
            frequency=expense.frequency,
            created_at=expense.created_at,
            updated_at=expense.updated_at
        )
        for expense in expenses
    ]


@router.post("/fixed-expenses", response_model=FixedExpenseResponse, status_code=status.HTTP_201_CREATED)
async def create_fixed_expense(
    expense_data: FixedExpense,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new fixed expense (admin only)"""
    new_expense = FixedExpenseDB(
        society_id=current_user.society_id,  # PRD: Multi-tenancy
        name=expense_data.name,
        amount=expense_data.amount,
        frequency=expense_data.frequency,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db.add(new_expense)
    await db.commit()
    await db.refresh(new_expense)

    return FixedExpenseResponse(
        id=str(new_expense.id),
        name=new_expense.name,
        amount=new_expense.amount,
        frequency=new_expense.frequency,
        created_at=new_expense.created_at,
        updated_at=new_expense.updated_at
    )


@router.delete("/fixed-expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fixed_expense(
    expense_id: str,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a fixed expense (admin only)"""
    try:
        expense_id_int = int(expense_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid expense ID"
        )

    # PRD: Multi-tenancy - Delete only if belongs to user's society
    result = await db.execute(
        delete(FixedExpenseDB).where(
            FixedExpenseDB.id == expense_id_int,
            FixedExpenseDB.society_id == current_user.society_id
        )
    )
    await db.commit()

    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fixed expense not found"
        )

    return None


# ============= WATER EXPENSES =============

@router.get("/water-expenses", response_model=List[WaterExpenseResponse])
async def list_water_expenses(
    month: Optional[int] = None,
    year: Optional[int] = None,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get water expenses (optionally filter by month/year) - filtered by user's society"""
    # PRD: Multi-tenancy - Filter by society_id
    query = select(WaterExpenseDB).where(
        WaterExpenseDB.society_id == current_user.society_id
    ).order_by(
        WaterExpenseDB.year.desc(),
        WaterExpenseDB.month.desc()
    )

    if month:
        query = query.where(WaterExpenseDB.month == month)
    if year:
        query = query.where(WaterExpenseDB.year == year)

    result = await db.execute(query)
    expenses = result.scalars().all()

    return [
        WaterExpenseResponse(
            id=str(expense.id),
            month=expense.month,
            year=expense.year,
            tanker_charges=expense.tanker_charges,
            government_charges=expense.government_charges,
            other_charges=expense.other_charges,
            total_water_expense=expense.total_amount,
            created_at=expense.created_at
        )
        for expense in expenses
    ]


@router.post("/water-expenses", response_model=WaterExpenseResponse, status_code=status.HTTP_201_CREATED)
async def create_water_expense(
    expense_data: WaterExpense,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new water expense for a month (admin only)"""
    # PRD: Multi-tenancy - Check if water expense already exists for this month/year in this society
    result = await db.execute(
        select(WaterExpenseDB).where(
            and_(
                WaterExpenseDB.month == expense_data.month,
                WaterExpenseDB.year == expense_data.year,
                WaterExpenseDB.society_id == current_user.society_id
            )
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Water expense already exists for {expense_data.month}/{expense_data.year}"
        )

    # Calculate total
    total_water_expense = (
        expense_data.tanker_charges +
        expense_data.government_charges +
        expense_data.other_charges
    )

    new_expense = WaterExpenseDB(
        society_id=current_user.society_id,  # PRD: Multi-tenancy
        month=expense_data.month,
        year=expense_data.year,
        tanker_charges=expense_data.tanker_charges,
        government_charges=expense_data.government_charges,
        other_charges=expense_data.other_charges,
        total_amount=total_water_expense,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db.add(new_expense)
    await db.commit()
    await db.refresh(new_expense)

    return WaterExpenseResponse(
        id=str(new_expense.id),
        month=new_expense.month,
        year=new_expense.year,
        tanker_charges=new_expense.tanker_charges,
        government_charges=new_expense.government_charges,
        other_charges=new_expense.other_charges,
        total_water_expense=new_expense.total_amount,
        created_at=new_expense.created_at
    )


# ============= BILL GENERATION =============

@router.get("/expense-accounts-for-period", response_model=List[CollectibleExpense])
async def get_expense_accounts_for_period(
    month: int,
    year: int,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all expense accounts that have transactions for the given month/year.
    Checks expense_month field first (e.g., "December, 2025"), falls back to date if expense_month is NULL.
    Only returns accounts with total_amount > 0 (filters out zero-balance accounts).
    Used for fixed expense selection in bill generation.
    """
    # Format expense_month string (e.g., "December, 2025")
    month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                   'July', 'August', 'September', 'October', 'November', 'December']
    expense_month_str = f"{month_names[month - 1]}, {year}"
    
    # Also prepare date range as fallback for transactions without expense_month
    start_date = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    end_date = date(year, month, last_day)
    
    # Get all expense type accounts for this society
    # CR-021_revised: Exclude Water Charges (Dynamic Lookup)
    # as they are part of water charges, not fixed expenses
    result = await db.execute(
        select(AccountCodeDB).where(
            and_(
                AccountCodeDB.society_id == current_user.society_id,
                AccountCodeDB.society_id == current_user.society_id,
                AccountCodeDB.type == AccountType.EXPENSE,
                # Dynamic exclusion: Exclude Water Charges based on utility_type
                or_(
                    AccountCodeDB.utility_type.is_(None),
                    AccountCodeDB.utility_type.notin_(['water_tanker', 'water_municipal'])
                )
            )
        ).order_by(AccountCodeDB.code)
    )
    expense_accounts = result.scalars().all()
    
    expense_list = []
    for acct in expense_accounts:
        # Sum transactions for this account matching expense_month OR date range
        # Priority: expense_month field (for expenses incurred in the month, even if paid later)
        res = await db.execute(
            select(func.sum(Transaction.amount), func.count(Transaction.id)).where(
                and_(
                    Transaction.society_id == current_user.society_id,
                    Transaction.account_code == acct.code,
                    # Check expense_month with flexible matching (December, 2025 OR Dec, 2025 OR Dec. 2025)
                    # Also handle cases where expense_month might be in wrong format
                    or_(
                        # Exact match
                        Transaction.expense_month == expense_month_str,
                        # Match with abbreviated month (Dec, 2025 or Dec., 2025)
                        Transaction.expense_month.like(f"{month_names[month - 1][:3]}%, {year}"),
                        Transaction.expense_month.like(f"{month_names[month - 1][:3]}.%, {year}"),
                        # Fallback to transaction date if expense_month is NULL
                        and_(
                            Transaction.expense_month.is_(None),
                            Transaction.date >= start_date,
                            Transaction.date <= end_date
                        )
                    )
                )
            )
        )
        row = res.fetchone()
        total = row[0] if row else 0
        count = row[1] if row else 0
        total_decimal = Decimal(str(total or "0.00"))
        
        # Only include accounts with expenses > 0
        if total_decimal > 0:
            expense_list.append(CollectibleExpense(
                account_code=acct.code,
                account_name=acct.name,
                total_amount=float(total_decimal),
                transaction_count=count or 0
            ))
    
    return expense_list


@router.get("/collectible-expenses", response_model=CollectibleExpensesResponse)
async def get_collectible_expenses(
    month: int,
    year: int,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Fetch potential expenses for the month to be included in maintenance bills.
    Checks expense_month field first (e.g., "December, 2025"), falls back to date if expense_month is NULL.
    Checks expense_month field first (e.g., "December, 2025"), falls back to date if expense_month is NULL.
    Includes Water (Dynamic) and any other marked fixed expenses.
    """
    # Format expense_month string (e.g., "December, 2025")
    month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                   'July', 'August', 'September', 'October', 'November', 'December']
    expense_month_str = f"{month_names[month - 1]}, {year}"
    
    # Also prepare date range as fallback for transactions without expense_month
    start_date = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    end_date = date(year, month, last_day)
    
    # 1. Fetch Water Tanker Codes
    tanker_codes_result = await db.execute(
        select(AccountCodeDB.code).where(
            and_(
                AccountCodeDB.society_id == current_user.society_id,
                AccountCodeDB.utility_type == 'water_tanker'
            )
        )
    )
    tanker_codes = tanker_codes_result.scalars().all() or []

    if tanker_codes:
        result = await db.execute(
            select(func.sum(Transaction.amount)).where(
                and_(
                    Transaction.society_id == current_user.society_id,
                    Transaction.account_code.in_(tanker_codes),
                    or_(
                        Transaction.expense_month == expense_month_str,
                        and_(
                            Transaction.expense_month.is_(None),
                            Transaction.date.between(start_date, end_date)
                        )
                    )
                )
            )
        )
        water_tanker = Decimal(str(result.scalar() or "0.00"))
    else:
        water_tanker = Decimal("0.00")
    
    # 2. Fetch Water Govt Codes
    govt_codes_result = await db.execute(
        select(AccountCodeDB.code).where(
            and_(
                AccountCodeDB.society_id == current_user.society_id,
                AccountCodeDB.utility_type == 'water_municipal'
            )
        )
    )
    govt_codes = govt_codes_result.scalars().all() or []

    if govt_codes:
        result = await db.execute(
            select(func.sum(Transaction.amount)).where(
                and_(
                    Transaction.society_id == current_user.society_id,
                    Transaction.account_code.in_(govt_codes),
                    or_(
                        Transaction.expense_month == expense_month_str,
                        and_(
                            Transaction.expense_month.is_(None),
                            Transaction.date.between(start_date, end_date)
                        )
                    )
                )
            )
        )
        water_govt = Decimal(str(result.scalar() or "0.00"))
    else:
        water_govt = Decimal("0.00")
    
    # 3. Fetch all account codes marked as fixed expenses
    result = await db.execute(
        select(AccountCodeDB).where(
            and_(
                AccountCodeDB.society_id == current_user.society_id,
                AccountCodeDB.is_fixed_expense == True
            )
        )
    )
    fixed_accounts = result.scalars().all()
    
    fixed_expenses_list = []
    for acct in fixed_accounts:
        # Sum transactions for this account
        # Check expense_month first (in format "December, 2025"), then fallback to date range
        # Also handle cases where expense_month might be in wrong format (date string)
        res = await db.execute(
            select(func.sum(Transaction.amount), func.count(Transaction.id)).where(
                and_(
                    Transaction.society_id == current_user.society_id,
                    Transaction.account_code == acct.code,
                    or_(
                        # Match expense_month in correct format
                        Transaction.expense_month == expense_month_str,
                        # Match if expense_month is NULL and date is in range
                        and_(
                            Transaction.expense_month.is_(None),
                            Transaction.date >= start_date,
                            Transaction.date <= end_date
                        ),
                        # Match if expense_month doesn't match but date is in range (handles wrong format)
                        and_(
                            Transaction.expense_month != expense_month_str,
                            Transaction.date >= start_date,
                            Transaction.date <= end_date
                        )
                    )
                )
            )
        )
        row = res.fetchone()
        total = row[0] if row else 0
        count = row[1] if row else 0
        
        # Only include accounts with transactions (total_amount > 0)
        # This matches the frontend expectation that only accounts with expenses are shown
        if total and float(Decimal(str(total))) > 0:
            fixed_expenses_list.append(CollectibleExpense(
                account_code=acct.code,
                account_name=acct.name,
                total_amount=float(Decimal(str(total or "0.00"))),
                transaction_count=count or 0
            ))
    
    return CollectibleExpensesResponse(
        month=month,
        year=year,
        water_tanker_amount=float(water_tanker),
        water_govt_amount=float(water_govt),
        fixed_expenses=fixed_expenses_list
    )


async def calculate_monthly_fixed_expenses(
    db: AsyncSession, 
    society_id: int, 
    month: int, 
    year: int
) -> Decimal:
    """
    Calculate total monthly fixed expenses from account codes marked with is_fixed_expense=True
    Checks expense_month field first (e.g., "December, 2025"), falls back to date if expense_month is NULL.
    Sums all transactions for expense account codes that have is_fixed_expense flag set
    """
    # Format expense_month string (e.g., "December, 2025")
    month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                   'July', 'August', 'September', 'October', 'November', 'December']
    expense_month_str = f"{month_names[month - 1]}, {year}"
    
    # Get account codes marked for fixed expenses
    result = await db.execute(
        select(AccountCodeDB.code).where(
            and_(
                AccountCodeDB.society_id == society_id,
                AccountCodeDB.type == "expense",
                AccountCodeDB.is_fixed_expense == True
            )
        )
    )
    expense_head_codes = [row[0] for row in result.all()]
    
    if not expense_head_codes:
        # No expense heads selected, return 0
        return Decimal("0.00")
    
    # Get transactions for the month matching the selected expense heads
    # Check expense_month first, fallback to date if expense_month is NULL
    start_date = date(year, month, 1)
    # Get last day of month
    last_day = calendar.monthrange(year, month)[1]
    end_date = date(year, month, last_day)
    
    result = await db.execute(
        select(func.sum(Transaction.amount)).where(
            and_(
                Transaction.society_id == society_id,
                Transaction.type == "expense",
                Transaction.account_code.in_(expense_head_codes),
                or_(
                    Transaction.expense_month == expense_month_str,
                    and_(
                        Transaction.expense_month.is_(None),
                        Transaction.date >= start_date,
                        Transaction.date <= end_date
                    )
                )
            )
        )
    )
    total = result.scalar()
    return Decimal(str(total or 0.0))


def generate_bill_number(society_id: int, month: int, year: int, sequence: int) -> str:
    """Generate unique bill number: BILL-YYYY-MM-SEQ"""
    return f"BILL-{year}-{month:02d}-{sequence:03d}"


@router.post("/generate-bills", response_model=BillGenerationResponse)
async def generate_bills(
    request: BillGenerationRequest,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate maintenance bills for all flats for a given month (admin only)"""
    # Get apartment settings (PRD: Multi-tenancy - Filter by society_id)
    result = await db.execute(
        select(SocietySettings).where(SocietySettings.society_id == current_user.society_id)
    )
    settings = result.scalar_one_or_none()
    
    # If SocietySettings doesn't exist, try ApartmentSettingsDB (legacy)
    if not settings:
        result = await db.execute(select(ApartmentSettingsDB))
        settings = result.scalar_one_or_none()

    if not settings:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Apartment settings not configured. Please configure settings first."
        )

    # CR-021_revised: Sequential month validation
    # Bills must be generated sequentially - cannot generate February 2026 without generating January 2026 first
    # Calculate previous month
    today = date.today()
    current_month = today.month
    current_year = today.year
    
    # Calculate previous month
    if current_month == 1:
        allowed_month = 12
        allowed_year = current_year - 1
    else:
        allowed_month = current_month - 1
        allowed_year = current_year
    
    # CR-021_revised: Check if previous month's bill exists (sequential validation)
    # If generating for a month other than the first month, check if previous month's bill exists
    requested_date = date(request.year, request.month, 1)
    if request.month == 1:
        prev_month = 12
        prev_year = request.year - 1
    else:
        prev_month = request.month - 1
        prev_year = request.year
    
    # Check if previous month's bill exists (unless this is the first month ever)
    prev_month_result = await db.execute(
        select(MaintenanceBillDB).where(
            and_(
                MaintenanceBillDB.month == prev_month,
                MaintenanceBillDB.year == prev_year,
                MaintenanceBillDB.society_id == current_user.society_id
            )
        )
    )
    prev_month_bills = prev_month_result.scalars().all()
    
    # If previous month doesn't have bills, check if there are any bills at all
    # If there are bills for later months, this is an error
    if not prev_month_bills:
        # Check if there are any bills for this society
        any_bills_result = await db.execute(
            select(MaintenanceBillDB).where(
                MaintenanceBillDB.society_id == current_user.society_id
            ).order_by(MaintenanceBillDB.year, MaintenanceBillDB.month)
        )
        any_bills = any_bills_result.scalars().all()
        
        if any_bills:
            # There are bills, but not for previous month - sequential violation
            first_bill = any_bills[0]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"CR-021_revised: Bills must be generated sequentially. Cannot generate bills for {calendar.month_name[request.month]} {request.year} without first generating bills for {calendar.month_name[prev_month]} {prev_year}. The earliest bill in the system is for {calendar.month_name[first_bill.month]} {first_bill.year}."
            )
    
    # Check if requested month is the allowed month (previous month) or if sequential validation passes
    # Allow generation if it's the previous month OR if previous month's bill exists
    if request.month != allowed_month or request.year != allowed_year:
        if not prev_month_bills:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Bills can only be generated for the previous month ({calendar.month_name[allowed_month]} {allowed_year}) or sequentially after previous months. Current month: {current_month}/{current_year}"
            )
    
    # Check if onboarding_date exists and validate against it
    # Get SocietySettings for onboarding_date
    result = await db.execute(
        select(SocietySettings).where(SocietySettings.society_id == current_user.society_id)
    )
    society_settings = result.scalar_one_or_none()
    
    if society_settings and society_settings.onboarding_date:
        onboarding = society_settings.onboarding_date
        requested_date = date(request.year, request.month, 1)
        
        # Check if requested month is before onboarding date
        if requested_date < date(onboarding.year, onboarding.month, 1):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot generate bills for months before onboarding date ({onboarding.strftime('%B %Y')})"
            )

    # PRD: Multi-tenancy - Check if bills already exist for this month in this society
    result = await db.execute(
        select(MaintenanceBillDB).where(
            and_(
                MaintenanceBillDB.month == request.month,
                MaintenanceBillDB.year == request.year,
                MaintenanceBillDB.society_id == current_user.society_id
            )
        )
    )
    existing_bills = result.scalars().all()

    if existing_bills:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bills already generated for {request.month}/{request.year}. Delete existing bills first."
        )

    # PRD: Multi-tenancy - Get all flats for this society
    # Only use flats that have details entered (not auto-create missing flats)
    # Fixed expenses will be divided by actual flats count, not total_flats from settings
    result = await db.execute(
        select(Flat).where(Flat.society_id == current_user.society_id)
    )
    flats = result.scalars().all()

    if not flats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No flats found. Add flats before generating bills."
        )

    bills = []
    # Use Decimal for financial calculations as per user requirement
    total_amount = Decimal("0.0")

    # PRD: Fetch society for min_vacancy_fee
    result = await db.execute(select(Society).where(Society.id == current_user.society_id))
    society_obj = result.scalar_one_or_none()
    min_vacancy_fee = Decimal(str(society_obj.min_vacancy_fee if society_obj else 500.0))

    # Calculate total water expense if not overridden
    if request.override_water_charges is not None:
        total_water = Decimal(str(request.override_water_charges))
    else:
        # Fetch sum of codes 5110 and 5120 for the month
        # Format expense_month string (e.g., "December, 2025")
        month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                       'July', 'August', 'September', 'October', 'November', 'December']
        expense_month_str = f"{month_names[request.month - 1]}, {request.year}"
        
        # Also prepare date range as fallback for transactions without expense_month
        start_date = date(request.year, request.month, 1)
        last_day = calendar.monthrange(request.year, request.month)[1]
        end_date = date(request.year, request.month, last_day)
        
        # CR-021: Dynamic water charges lookup - get all water-related account codes
        # Find all account codes with utility_type in ['water_tanker', 'water_municipal']
        water_accounts_res = await db.execute(
            select(AccountCodeDB.code).where(
                and_(
                    AccountCodeDB.society_id == current_user.society_id,
                    AccountCodeDB.utility_type.in_(['water_tanker', 'water_municipal'])
                )
            )
        )
        water_account_codes = [row[0] for row in water_accounts_res.fetchall()]

        # If no water accounts found, calculate water as 0
        if not water_account_codes:
            total_water = Decimal("0.00")
        else:
            # Sum transactions for these water account codes
            # Check expense_month first, fallback to date if expense_month is NULL
            water_res = await db.execute(
                select(func.sum(Transaction.amount)).where(
                    and_(
                        Transaction.society_id == current_user.society_id,
                        Transaction.account_code.in_(water_account_codes),
                        or_(
                            Transaction.expense_month == expense_month_str,
                            and_(
                                Transaction.expense_month.is_(None),
                                Transaction.date.between(start_date, end_date)
                            )
                        )
                    )
                )
            )
            total_water = Decimal(str(water_res.scalar() or "0.00"))

    # Calculate total fixed expenses if using selection
    total_fixed_from_selection = Decimal("0.00")
    if request.selected_fixed_expense_codes:
        # Format expense_month string (e.g., "December, 2025")
        month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                       'July', 'August', 'September', 'October', 'November', 'December']
        expense_month_str = f"{month_names[request.month - 1]}, {request.year}"
        
        # Also prepare date range as fallback for transactions without expense_month
        start_date = date(request.year, request.month, 1)
        last_day = calendar.monthrange(request.year, request.month)[1]
        end_date = date(request.year, request.month, last_day)
        
        # Check expense_month first, fallback to date if expense_month is NULL
        fixed_res = await db.execute(
            select(func.sum(Transaction.amount)).where(
                and_(
                    Transaction.society_id == current_user.society_id,
                    Transaction.account_code.in_(request.selected_fixed_expense_codes),
                    or_(
                        Transaction.expense_month == expense_month_str,
                        and_(
                            Transaction.expense_month.is_(None),
                            Transaction.date.between(start_date, end_date)
                        )
                    )
                )
            )
        )
        total_fixed_from_selection = Decimal(str(fixed_res.scalar() or "0.00"))
    
    # Use override_fixed_expenses as total if provided, otherwise use selection
    monthly_fixed_total = Decimal(str(request.override_fixed_expenses)) if request.override_fixed_expenses is not None else total_fixed_from_selection

    # Fetch approved supplementary bills to include
    result = await db.execute(
        select(SupplementaryBillFlatDB)
        .join(SupplementaryBillDB)
        .where(and_(
            SupplementaryBillDB.society_id == current_user.society_id,
            SupplementaryBillDB.status == "approved",
            SupplementaryBillFlatDB.is_included_in_monthly == False
        ))
        .options(selectinload(SupplementaryBillFlatDB.bill))
    )
    all_supp_charges = result.scalars().all()
    
    flat_to_supp = {}
    for sc in all_supp_charges:
        if sc.flat_id not in flat_to_supp:
            flat_to_supp[sc.flat_id] = []
        flat_to_supp[sc.flat_id].append(sc)

    if settings.maintenance_calculation_logic == "sqft":
        sqft_rate = request.override_sqft_rate if request.override_sqft_rate is not None else (settings.maintenance_rate_sqft or 0)

        for flat in flats:
            area = Decimal(str(flat.area_sqft))
            sqft_rate_dec = Decimal(str(sqft_rate))
            amount = (area * sqft_rate_dec).quantize(Decimal("0.01"))
            # Round up amount to next rupee (ceiling)
            amount = Decimal(math.ceil(float(amount)))

            # Include supplementary charges
            supp_charges = flat_to_supp.get(flat.id, [])
            supp_total = sum(Decimal(str(sc.amount)) for sc in supp_charges)
            final_total = (amount + supp_total).quantize(Decimal("0.01"))
            # Round up to next rupee (ceiling)
            final_total = Decimal(math.ceil(float(final_total)))

            breakdown = {"sqft_calculation": f"{area} sq ft × ₹{sqft_rate_dec} = ₹{amount}"}
            if supp_charges:
                breakdown["supplementary_charges"] = [
                    {"title": sc.bill.title, "amount": float(Decimal(str(sc.amount)).quantize(Decimal("0.01")))} for sc in supp_charges
                ]

            new_bill = MaintenanceBillDB(
                society_id=current_user.society_id,
                flat_id=flat.id,
                flat_number=flat.flat_number,
                month=request.month,
                year=request.year,
                amount=amount,
                maintenance_amount=amount,
                water_amount=Decimal("0.00"),
                total_amount=final_total,
                breakdown=breakdown,
                status=BillStatus.UNPAID,
                is_posted=False,
                created_at=datetime.utcnow(),
                paid_date=None
            )

            db.add(new_bill)
            await db.flush()
            await db.refresh(new_bill)

            # Mark supplementary charges as included
            for sc in supp_charges:
                sc.is_included_in_monthly = True
                sc.maintenance_bill_id = new_bill.id
                db.add(sc)

            bills.append(MaintenanceBill(
                id=str(new_bill.id),
                flat_id=str(new_bill.flat_id),
                flat_number=flat.flat_number,
                month=new_bill.month,
                year=new_bill.year,
                amount=new_bill.total_amount,
                breakdown=new_bill.breakdown if new_bill.breakdown else {},
                status=new_bill.status.value if hasattr(new_bill.status, 'value') else str(new_bill.status),
                created_at=new_bill.created_at,
                paid_at=new_bill.paid_date
            ))
            total_amount += amount

    elif settings.maintenance_calculation_logic == "fixed":
        # Method 2: Fixed per Flat (Flat Rate + Shared Fixed Expenses + Sinking Fund)
        # Usually 'Fixed' means a simple flat rate provided in settings, OR calculated from fixed expenses.
        # Based on UI "Fixed per Flat", we'll check if a global fixed rate is set, otherwise default to expenses.
        
        if request.override_fixed_expenses is not None:
            monthly_fixed_shared = Decimal(str(request.override_fixed_expenses))
        else:
            monthly_fixed_shared = await calculate_monthly_fixed_expenses(
                db=db,
                society_id=current_user.society_id,
                month=request.month,
                year=request.year
            )
        
        actual_flats_count = len(flats)
        shared_expense_per_flat = Decimal(str(monthly_fixed_shared)) / Decimal(str(actual_flats_count)) if actual_flats_count > 0 else Decimal("0.0")
        
        # Sinking Fund
        sinking_fund_total = Decimal(str(request.override_sinking_fund)) if request.override_sinking_fund is not None else Decimal(str(settings.sinking_fund_rate or 0))
        sinking_fund_per_flat = sinking_fund_total / Decimal(str(actual_flats_count)) if actual_flats_count > 0 else Decimal("0.0")

        # Global Flat Rate (if set in settings table as maintenance_rate_flat)
        base_flat_rate = Decimal(str(settings.maintenance_rate_flat or 0))
        
        for flat in flats:
            amount = (base_flat_rate + shared_expense_per_flat + sinking_fund_per_flat).quantize(Decimal("0.01"))
            # Round up amount to next rupee (ceiling)
            amount = Decimal(math.ceil(float(amount)))
            
            # Include supplementary charges
            supp_charges = flat_to_supp.get(flat.id, [])
            supp_total = sum(Decimal(str(sc.amount)) for sc in supp_charges)
            final_total = (amount + supp_total).quantize(Decimal("0.01"))
            # Round up to next rupee (ceiling)
            final_total = Decimal(math.ceil(float(final_total)))

            breakdown = {
                "base_flat_rate": float(base_flat_rate.quantize(Decimal("0.01"))),
                "shared_fixed_expenses": float(shared_expense_per_flat.quantize(Decimal("0.01"))),
                "sinking_fund": float(sinking_fund_per_flat.quantize(Decimal("0.01")))
            }
            if supp_charges:
                breakdown["supplementary_charges"] = [
                    {"title": sc.bill.title, "amount": float(Decimal(str(sc.amount)).quantize(Decimal("0.01")))} for sc in supp_charges
                ]

            new_bill = MaintenanceBillDB(
                society_id=current_user.society_id,
                flat_id=flat.id,
                flat_number=flat.flat_number,
                month=request.month,
                year=request.year,
                amount=amount,
                maintenance_amount=amount,
                water_amount=Decimal("0.00"),
                total_amount=final_total,
                breakdown=breakdown,
                status=BillStatus.UNPAID,
                is_posted=False,
                created_at=datetime.utcnow(),
                paid_date=None
            )
            
            db.add(new_bill)
            await db.flush()
            await db.refresh(new_bill)

            # Mark supplementary charges as included
            for sc in supp_charges:
                sc.is_included_in_monthly = True
                sc.maintenance_bill_id = new_bill.id
                db.add(sc)
            
            bills.append(MaintenanceBill(
                id=str(new_bill.id),
                flat_id=str(new_bill.flat_id),
                flat_number=flat.flat_number,
                month=new_bill.month,
                year=new_bill.year,
                amount=new_bill.total_amount,
                breakdown=new_bill.breakdown or {},
                status=new_bill.status.value if hasattr(new_bill.status, 'value') else str(new_bill.status),
                is_posted=new_bill.is_posted,
                created_at=new_bill.created_at,
                paid_at=new_bill.paid_date
            ))
            total_amount += final_total

    elif settings.maintenance_calculation_logic == "mixed":
        # Method 4: Professional Mixed Method (The "Gold Standard") - ENHANCED
        # - Maintenance: Sqft based (Always)
        # - Water: Per person (Headcount)
        # - Fixed Expenses: Selection-based (Equal or Sqft)
        # - Sinking Fund: Total-based (Equal or Sqft)
        # - Arrears: Carried forward
        # - Late Fee: Applied on Arrears
        
        actual_flats_count = len(flats)
        total_sqft = sum(Decimal(str(f.area_sqft)) for f in flats)
        
        # Step A: Identify vacant/active for water
        vacant_flats = [f for f in flats if f.occupancy_status == OccupancyStatus.VACANT or f.occupants == 0]
        active_flats = [f for f in flats if f.occupancy_status != OccupancyStatus.VACANT and f.occupants > 0]
        
        # Step B: Water Calculation (Headcount based) - CR-021 Enhanced
        # CR-021: Admin can adjust inmates for guests/vacations >7 days
        vacancy_fees_total = Decimal(str(len(vacant_flats))) * min_vacancy_fee
        recoverable_water = max(Decimal("0.0"), total_water - vacancy_fees_total)
        
        # Calculate total active inmates with admin adjustments (CR-021)
        total_active_inmates = Decimal("0.0")
        flat_inmate_map = {}  # Store adjusted inmate counts per flat
        
        for flat in active_flats:
            # Check if admin provided adjusted inmate count for this flat
            adjusted_count = None
            if request.adjusted_inmates:
                flat_id_str = str(flat.id)
                adjusted_count = request.adjusted_inmates.get(flat_id_str)
            
            # Use adjusted count if provided, otherwise use flat.occupants
            final_inmate_count = adjusted_count if adjusted_count is not None else flat.occupants
            flat_inmate_map[flat.id] = int(final_inmate_count)
            total_active_inmates += Decimal(str(final_inmate_count))
        
        per_person_rate = (recoverable_water / total_active_inmates) if total_active_inmates > 0 else Decimal("0.0")

        # Step C: Fixed Expenses components
        fixed_comp_equal = (monthly_fixed_total / Decimal(str(actual_flats_count))) if actual_flats_count > 0 else Decimal("0.0")
        fixed_comp_sqft_rate = (monthly_fixed_total / total_sqft) if total_sqft > 0 else Decimal("0.0")

        # Step D: Sinking Fund components (CR-021: Per sq.ft or per flat)
        # If override is provided, it's per-flat amount. If from settings, check if it's total or per-flat.
        if request.override_sinking_fund is not None:
            # Override value is per-flat amount (user enters what each flat should pay)
            sinking_comp_equal = Decimal(str(request.override_sinking_fund))
            sinking_total = sinking_comp_equal * Decimal(str(actual_flats_count))
        else:
            # From settings - assume it's total amount to be divided
            sinking_total = Decimal(str(settings.sinking_fund_rate or 0))
            sinking_comp_equal = (sinking_total / Decimal(str(actual_flats_count))) if actual_flats_count > 0 else Decimal("0.0")
        sinking_comp_sqft_rate = (sinking_total / total_sqft) if total_sqft > 0 else Decimal("0.0")

        # Step E: Repair Fund components (CR-021: Per sq.ft or per flat)
        if request.override_repair_fund is not None:
            # Override value is per-flat amount (user enters what each flat should pay)
            repair_comp_equal = Decimal(str(request.override_repair_fund))
            repair_total = repair_comp_equal * Decimal(str(actual_flats_count))
        else:
            # From settings - assume it's total amount to be divided
            repair_total = Decimal(str(settings.repair_fund_rate or 0))
            repair_comp_equal = (repair_total / Decimal(str(actual_flats_count))) if actual_flats_count > 0 else Decimal("0.0")
        repair_comp_sqft_rate = (repair_total / total_sqft) if total_sqft > 0 else Decimal("0.0")

        # Step F: Corpus Fund components (CR-021: Per sq.ft or per flat)
        if request.override_corpus_fund is not None:
            # Override value is per-flat amount (user enters what each flat should pay)
            corpus_comp_equal = Decimal(str(request.override_corpus_fund))
            corpus_total = corpus_comp_equal * Decimal(str(actual_flats_count))
        else:
            # From settings - assume it's total amount to be divided
            corpus_total = Decimal(str(settings.corpus_fund_rate or 0))
            corpus_comp_equal = (corpus_total / Decimal(str(actual_flats_count))) if actual_flats_count > 0 else Decimal("0.0")
        corpus_comp_sqft_rate = (corpus_total / total_sqft) if total_sqft > 0 else Decimal("0.0")

        # Step G: Maintenance Base (Sqft) - CR-021: Only calculate if rate > 0
        sqft_maint_rate = Decimal(str(request.override_sqft_rate)) if request.override_sqft_rate is not None else Decimal(str(settings.maintenance_rate_sqft or 0))
        # CR-021: If rate is 0, maintenance not calculated by area

        # Late Fee rate
        interest_rate = Decimal(str(settings.interest_rate or 0)) / Decimal("100") 
        monthly_interest_rate = interest_rate / Decimal("12")

        for flat in flats:
            area = Decimal(str(flat.area_sqft))
            is_vacant = flat in vacant_flats
            
            # 1. Maintenance Component - CR-021: Only calculate if rate > 0
            if sqft_maint_rate > 0:
                maint_comp = (area * sqft_maint_rate).quantize(Decimal("0.01"))
            else:
                maint_comp = Decimal("0.00")  # CR-021: If rate is 0, maintenance not calculated by area
            
            # 2. Water Component - CR-021: Use adjusted inmates if provided
            if is_vacant:
                water_comp = min_vacancy_fee.quantize(Decimal("0.01"))
                actual_inmates_used = 0
            else:
                # Use adjusted inmate count if available, otherwise use flat.occupants
                inmates_for_water = flat_inmate_map.get(flat.id, flat.occupants)
                water_comp = (per_person_rate * Decimal(str(inmates_for_water))).quantize(Decimal("0.01"))
                actual_inmates_used = inmates_for_water
            
            # 3. Fixed Component - CR-021: Equal or sqft distribution
            if request.fixed_calculation_method == "sqft":
                fixed_comp = (area * fixed_comp_sqft_rate).quantize(Decimal("0.01"))
            else:
                fixed_comp = fixed_comp_equal.quantize(Decimal("0.01"))
                
            # 4. Sinking Fund Component - CR-021: Per sq.ft or per flat
            if request.sinking_calculation_method == "sqft":
                sinking_comp = (area * sinking_comp_sqft_rate).quantize(Decimal("0.01"))
            else:
                sinking_comp = sinking_comp_equal.quantize(Decimal("0.01"))
            
            # 5. Repair Fund Component - CR-021: Per sq.ft or per flat
            if request.repair_fund_calculation_method == "sqft":
                repair_comp = (area * repair_comp_sqft_rate).quantize(Decimal("0.01"))
            else:
                repair_comp = repair_comp_equal.quantize(Decimal("0.01"))
            
            # 6. Corpus Fund Component - CR-021: Per sq.ft or per flat
            if request.corpus_fund_calculation_method == "sqft":
                corpus_comp = (area * corpus_comp_sqft_rate).quantize(Decimal("0.01"))
            else:
                corpus_comp = corpus_comp_equal.quantize(Decimal("0.01"))
                
            # 7. Arrears & Late Fee
            calculation_date = date(request.year, request.month, 1)
            arrears = await get_flat_balance(db, current_user.society_id, flat.id, calculation_date)
            
            late_fee = Decimal("0.00")
            if arrears > 0 and settings.interest_on_overdue:
                late_fee = (arrears * monthly_interest_rate).quantize(Decimal("0.01"))

            # 8. Supplementary
            supp_charges = flat_to_supp.get(flat.id, [])
            supp_total = sum(Decimal(str(sc.amount)) for sc in supp_charges)
            
            # Monthly total (current charges ONLY) - CR-021: All components
            monthly_charges = (maint_comp + water_comp + fixed_comp + sinking_comp + repair_comp + corpus_comp + late_fee + supp_total).quantize(Decimal("0.01"))
            # Round up monthly charges to next rupee (ceiling)
            monthly_charges = Decimal(math.ceil(float(monthly_charges)))
            # Grand total including arrears
            final_total = (monthly_charges + arrears).quantize(Decimal("0.01"))
            # Round up to next rupee (ceiling)
            final_total = Decimal(math.ceil(float(final_total)))

            # Create water calculation string for display
            if is_vacant:
                water_calculation = f"Vacant flat - Minimum charge: ₹{min_vacancy_fee}"
            else:
                water_calculation = f"Per person: ₹{per_person_rate:.3f}, Occupants: {actual_inmates_used}"
            
            breakdown = {
                "maintenance_sqft": float(maint_comp),
                "maintenance_rate": float(sqft_maint_rate),
                "water_charges": float(water_comp),
                "water_per_person_rate": float(per_person_rate),
                "water_per_person": float(per_person_rate),  # Also store as water_per_person for backward compatibility
                "inmates_used": actual_inmates_used,
                "occupants": actual_inmates_used,  # Store inmates_used as occupants for display
                "inmates_adjusted": request.adjusted_inmates.get(str(flat.id)) if request.adjusted_inmates and str(flat.id) in request.adjusted_inmates else None,
                "water_calculation": water_calculation,  # Pre-formatted calculation string
                "fixed_expenses": float(fixed_comp),
                "fixed_method": request.fixed_calculation_method,
                "sinking_fund": float(sinking_comp),
                "sinking_method": request.sinking_calculation_method,
                "repair_fund": float(repair_comp),
                "repair_method": request.repair_fund_calculation_method,
                "corpus_fund": float(corpus_comp),
                "corpus_method": request.corpus_fund_calculation_method,
                "arrears": float(arrears),
                "late_fee": float(late_fee),
                "is_vacant": is_vacant,
                "area_sqft": float(area),
                "flat_occupants": flat.occupants  # Store original flat.occupants separately
            }
            if supp_charges:
                breakdown["supplementary_charges"] = [
                    {"title": sc.bill.title, "amount": float(Decimal(str(sc.amount)).quantize(Decimal("0.01")))} for sc in supp_charges
                ]

            new_bill = MaintenanceBillDB(
                society_id=current_user.society_id,
                flat_id=flat.id,
                flat_number=flat.flat_number,
                bill_number=f"BILL-{request.year}{request.month:02d}-{flat.flat_number}",
                month=request.month,
                year=request.year,
                amount=monthly_charges, # Current charges (maint + water + fixed + sinking + repair + corpus + late + supp)
                maintenance_amount=maint_comp,
                water_amount=water_comp,
                fixed_amount=fixed_comp,
                sinking_fund_amount=sinking_comp,
                arrears_amount=arrears,
                late_fee_amount=late_fee,
                total_amount=final_total, # Incl. Arrears
                breakdown=breakdown,  # Includes repair_fund and corpus_fund
                status=BillStatus.UNPAID,
                is_posted=False,
                created_at=datetime.utcnow(),
                paid_date=None
            )
            
            db.add(new_bill)
            await db.flush()
            await db.refresh(new_bill)

            # Mark supplementary charges as included
            for sc in supp_charges:
                sc.is_included_in_monthly = True
                sc.maintenance_bill_id = new_bill.id
                db.add(sc)

            bills.append(MaintenanceBill(
                id=str(new_bill.id),
                flat_id=str(new_bill.flat_id),
                flat_number=flat.flat_number,
                month=new_bill.month,
                year=new_bill.year,
                amount=new_bill.total_amount,
                breakdown=new_bill.breakdown or {},
                status=new_bill.status.value if hasattr(new_bill.status, 'value') else str(new_bill.status),
                is_posted=new_bill.is_posted,
                created_at=new_bill.created_at,
                paid_at=new_bill.paid_date
            ))
            total_amount += monthly_charges

    else:  # 'water_based' or fallback
        # Method 3: Hybrid (Water + Fixed + Sinking Fund)
        # Implement PRD logic with vacancy fees

        # Step A: Identify vacant and active flats
        vacant_flats = [f for f in flats if f.occupancy_status == OccupancyStatus.VACANT or f.occupants == 0]
        active_flats = [f for f in flats if f.occupancy_status != OccupancyStatus.VACANT and f.occupants > 0]
        
        # Step B: Calculate vacancy fees
        vacancy_fees_total = Decimal(str(len(vacant_flats))) * min_vacancy_fee
        
        # Step C: Calculate recoverable amount from active flats
        # If total_water is less than vacancy fees, recoverable is 0 (unlikely but safe)
        recoverable_amount = max(Decimal("0.0"), total_water - vacancy_fees_total)
        
        # Step D: Calculate per-person rate for active flats
        total_active_inmates = sum(f.occupants for f in active_flats)
        
        if total_active_inmates == 0:
            per_person_rate = Decimal("0.0")
        else:
            per_person_rate = recoverable_amount / Decimal(str(total_active_inmates))

        if request.override_fixed_expenses is not None:
            monthly_fixed = Decimal(str(request.override_fixed_expenses))
        else:
            monthly_fixed = await calculate_monthly_fixed_expenses(
                db=db,
                society_id=current_user.society_id,
                month=request.month,
                year=request.year
            )
        
        actual_flats_count = len(flats)
        if actual_flats_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No flats found. Add flats before generating bills."
            )
        
        fixed_per_flat = Decimal(str(monthly_fixed)) / Decimal(str(actual_flats_count))
        # Use sinking_fund_rate if sinking_fund_total is not available (SocietySettings vs legacy ApartmentSettings)
        if request.override_sinking_fund is not None:
            sinking_fund_val = Decimal(str(request.override_sinking_fund))
        else:
            sinking_fund_val = getattr(settings, 'sinking_fund_total', getattr(settings, 'sinking_fund_rate', Decimal("0.00")))
        
        sinking_fund_per_flat = Decimal(str(sinking_fund_val or 0)) / Decimal(str(actual_flats_count))

        # Generate bills
        for flat in flats:
            is_vacant = flat in vacant_flats
            occupants = flat.occupants
            
            if is_vacant:
                water_charges = min_vacancy_fee
            else:
                water_charges = per_person_rate * Decimal(str(occupants))
                
            amount = (water_charges + fixed_per_flat + sinking_fund_per_flat).quantize(Decimal("0.01"))

            # Include supplementary charges
            supp_charges = flat_to_supp.get(flat.id, [])
            supp_total = sum(Decimal(str(sc.amount)) for sc in supp_charges)
            # Round up amount to next rupee (ceiling)
            amount = Decimal(math.ceil(float(amount.quantize(Decimal("0.01")))))
            final_total = (amount + supp_total).quantize(Decimal("0.01"))
            # Round up to next rupee (ceiling)
            final_total = Decimal(math.ceil(float(final_total)))

            # Create water calculation string for display
            if is_vacant:
                water_calculation = f"Vacant flat - Minimum charge: ₹{min_vacancy_fee}"
            else:
                water_calculation = f"Per person: ₹{per_person_rate:.3f}, Occupants: {occupants}"
            
            breakdown = {
                "water_charges": float(water_charges.quantize(Decimal("0.01"))),
                "per_person_water_charge": float(per_person_rate.quantize(Decimal("0.01"))) if not is_vacant else 0,
                "water_per_person_rate": float(per_person_rate.quantize(Decimal("0.01"))) if not is_vacant else 0,
                "water_per_person": float(per_person_rate.quantize(Decimal("0.01"))) if not is_vacant else 0,
                "number_of_occupants": occupants,
                "occupants": occupants,  # For backward compatibility
                "inmates_used": occupants,  # For consistency with mixed method
                "water_calculation": water_calculation,  # Pre-formatted calculation string
                "fixed_expenses": float(fixed_per_flat.quantize(Decimal("0.01"))),
                "sinking_fund": float(sinking_fund_per_flat.quantize(Decimal("0.01"))),
                "is_vacant": is_vacant,
                "vacancy_fee_applied": is_vacant
            }
            if supp_charges:
                breakdown["supplementary_charges"] = [
                    {"title": sc.bill.title, "amount": float(Decimal(str(sc.amount)).quantize(Decimal("0.01")))} for sc in supp_charges
                ]

            new_bill = MaintenanceBillDB(
                society_id=current_user.society_id,
                flat_id=flat.id,
                flat_number=flat.flat_number,
                month=request.month,
                year=request.year,
                amount=amount,
                maintenance_amount=amount - water_charges,
                water_amount=water_charges,
                total_amount=final_total,
                breakdown=breakdown,
                status=BillStatus.UNPAID,
                is_posted=False,
                created_at=datetime.utcnow(),
                paid_date=None
            )

            db.add(new_bill)
            await db.flush()
            await db.refresh(new_bill)

            # Mark supplementary charges as included
            for sc in supp_charges:
                sc.is_included_in_monthly = True
                sc.maintenance_bill_id = new_bill.id
                db.add(sc)

            bills.append(MaintenanceBill(
                id=str(new_bill.id),
                flat_id=str(new_bill.flat_id),
                flat_number=flat.flat_number,
                month=new_bill.month,
                year=new_bill.year,
                amount=new_bill.total_amount,
                breakdown=new_bill.breakdown if new_bill.breakdown else {},
                status=new_bill.status.value if hasattr(new_bill.status, 'value') else str(new_bill.status),
                created_at=new_bill.created_at,
                paid_at=new_bill.paid_date
            ))
            total_amount += amount

    # Log the collection action
    await log_action(
        db=db,
        society_id=current_user.society_id,
        user_id=int(current_user.id),
        action_type="create",
        entity_type="maintenance_bills",
        entity_id=None,
        new_values={
            "month": request.month,
            "year": request.year,
            "total_amount": float(total_amount),
            "status": "draft"
        }
    )
    
    await db.commit()
    
    return BillGenerationResponse(
        total_bills_generated=len(bills),
        total_amount=float(total_amount),
        month=request.month,
        year=request.year,
        bills=bills
    )


@router.delete("/bills/drafts", response_model=dict)
async def delete_draft_bills(
    month: int,
    year: int,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete unposted maintenance bills for a specific month and year (admin only).
    """
    # Find all unposted bills for the month/year
    result = await db.execute(
        select(MaintenanceBillDB).where(
            and_(
                MaintenanceBillDB.month == month,
                MaintenanceBillDB.year == year,
                MaintenanceBillDB.society_id == current_user.society_id,
                MaintenanceBillDB.is_posted == False
            )
        )
    )
    bills_to_delete = result.scalars().all()

    if not bills_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No draft bills found for {month}/{year}."
        )

    count = len(bills_to_delete)
    
    # Delete the bills
    for bill in bills_to_delete:
        await db.delete(bill)

    # Log the action
    await log_action(
        db=db,
        society_id=current_user.society_id,
        user_id=int(current_user.id),
        action_type="delete",
        entity_type="maintenance_bills",
        entity_id=None,
        new_values={
            "month": month,
            "year": year,
            "count": count,
            "status": "draft_rejected"
        }
    )

    await db.commit()

    return {
        "status": "success",
        "message": f"Successfully deleted {count} draft bills for {month}/{year}.",
        "count": count
    }


@router.post("/post-bills", response_model=BillGenerationResponse)
async def post_bills(
    request: PostBillsRequest,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Post draft maintenance bills to accounting (admin only).
    This creates the necessary journal entries and updates account balances.
    
    SAFEGUARDS:
    - Prevents duplicate postings for the same month/year
    - Validates that bills exist before posting
    - Creates only ONE Journal Voucher (JV) for all bills
    - All transactions reference the same JV number
    """
    # SAFEGUARD 1: Check if bills for this month/year are already posted
    posted_check = await db.execute(
        select(MaintenanceBillDB).where(
            and_(
                MaintenanceBillDB.month == request.month,
                MaintenanceBillDB.year == request.year,
                MaintenanceBillDB.society_id == current_user.society_id,
                MaintenanceBillDB.is_posted == True
            )
        ).limit(1)
    )
    existing_posted = posted_check.scalar_one_or_none()
    
    if existing_posted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bills for {calendar.month_name[request.month]} {request.year} are already posted. Cannot post again. Use 'Reverse Bill' if you need to regenerate."
        )
    
    # SAFEGUARD 2: Check for existing JV entry for this month/year
    # Use today's date as the accounting date for the JV (Posting Date)
    # This ensures the transaction appears in the current ledger when posted
    # while 'expense_month' handles the P&L period
    transaction_date = date.today()
    month_name = calendar.month_name[request.month]
    expected_description = f"Maintenance charges for the month {month_name} {request.year} (Posted)"
    
    jv_check = await db.execute(
        select(JournalEntry).where(
            and_(
                JournalEntry.society_id == current_user.society_id,
                JournalEntry.date == transaction_date,
                JournalEntry.description == expected_description
            )
        ).limit(1)
    )
    existing_jv = jv_check.scalar_one_or_none()
    
    if existing_jv:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Journal entry {existing_jv.entry_number} already exists for {month_name} {request.year}. Bills are already posted. Cannot create duplicate JV entry."
        )
    
    # 1. Get all unposted bills for the month/year
    result = await db.execute(
        select(MaintenanceBillDB).where(
            and_(
                MaintenanceBillDB.month == request.month,
                MaintenanceBillDB.year == request.year,
                MaintenanceBillDB.society_id == current_user.society_id,
                MaintenanceBillDB.is_posted == False
            )
        )
    )
    bills_to_post = result.scalars().all()
    
    if not bills_to_post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No draft bills found for {request.month}/{request.year}."
        )
    
    # SAFEGUARD 3: Verify bills are rounded (should already be rounded during generation)
    # Bills are rounded during generation (math.ceil), so this is just a validation
    total_amount = Decimal("0.00")
    for bill in bills_to_post:
        # Verify bill.amount is already rounded (no decimals or already ceiled)
        bill_amount = Decimal(str(bill.amount))
        if bill_amount != Decimal(math.ceil(float(bill_amount))):
            # Re-round if not already rounded (safety check)
            bill.amount = Decimal(math.ceil(float(bill_amount)))
            bill.total_amount = Decimal(math.ceil(float(Decimal(str(bill.total_amount)))))
            db.add(bill)
        total_amount += bill.amount  # Use rounded amount
    
    # 2. Update bills to is_posted=True
    post_time = datetime.utcnow()
    for bill in bills_to_post:
        bill.is_posted = True
        bill.posted_at = post_time
        db.add(bill)
    
    # Generate JV number and create transactions
    # IMPORTANT: Create only ONE JV entry for all bills (not per bill)
    from app.utils.document_numbering import generate_journal_entry_number
    description = expected_description  # Use the description defined in SAFEGUARD 2
        
    # Aggregate logic for componentized posting - CR-021 Enhanced
    maint_total = Decimal("0.00")
    water_total = Decimal("0.00")
    sinking_total = Decimal("0.00")
    repair_total = Decimal("0.00")  # CR-021: Repair Fund
    corpus_total = Decimal("0.00")  # CR-021: Corpus Fund
    late_fee_total = Decimal("0.00")
    other_total = Decimal("0.00")
    
    for bill in bills_to_post:
        # IMPORTANT: Use rounded bill.amount (bills are already rounded during generation)
        # We use bill.amount for current charges (excluding arrears)
        # Mixed bills have detailed breakdown
        if bill.breakdown:
            maint_total += Decimal(str(bill.breakdown.get('maintenance_sqft', bill.maintenance_amount)))
            water_total += Decimal(str(bill.breakdown.get('water_charges', bill.water_amount)))
            
            # Check for sinking fund in different keys depending on method
            sinking = bill.breakdown.get('sinking_fund_sqft') or bill.breakdown.get('sinking_fund') or 0
            sinking_total += Decimal(str(sinking))
            
            # CR-021: Repair Fund
            repair = bill.breakdown.get('repair_fund', 0)
            repair_total += Decimal(str(repair))
            
            # CR-021: Corpus Fund
            corpus = bill.breakdown.get('corpus_fund', 0)
            corpus_total += Decimal(str(corpus))
            
            late_fee_total += Decimal(str(bill.breakdown.get('late_fee', 0)))
            
            # Supplementary charges are already included in bill.amount for mixed method
            # but might need to be isolated if they belong to "Other Income"
            supp = sum(Decimal(str(s.get('amount', 0))) for s in bill.breakdown.get('supplementary_charges', []))
            other_total += supp
            
            # Fixed expenses are usually maintenance income or a separate head
            # In mixed model, we have 'fixed_expenses_equal'
            fixed = bill.breakdown.get('fixed_expenses_equal') or bill.breakdown.get('shared_fixed_expenses') or bill.breakdown.get('fixed_expenses') or 0
            maint_total += Decimal(str(fixed))
        else:
            maint_total += Decimal(str(bill.maintenance_amount))
            water_total += Decimal(str(bill.water_amount))
            
    # CR-021_revised: Calculate total current charges (excluding arrears)
    # All charges (maintenance + water + fixed + sinking + repair + corpus + late fee + other) go to 4000 Maintenance Charges
    # IMPORTANT: Use rounded bill amounts (sum of already rounded individual bills)
    # Bills are rounded during generation with math.ceil, so use the actual rounded bill.amount values
    # Round to nearest whole rupee BEFORE posting
    current_charges_total = sum(Decimal(str(bill.amount)) for bill in bills_to_post)  # Already rounded from generation
    current_charges_total = Decimal(math.ceil(float(current_charges_total)))  # Ensure rounding to next rupee
    
    # CR-021_revised: Total credits = total income (all posted to 4000 Maintenance Charges only)
    # IMPORTANT: Round to nearest whole rupee BEFORE posting (already done above)
    total_credits = current_charges_total
    
    # CR-021: Validate double-entry (Debit must equal Credit)
    # Both should be equal (total_credits is rounded version)
    if abs(total_credits - total_credits) > Decimal("0.01"):  # Should always be 0
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Accounting imbalance detected! Debit (₹{total_credits}) ≠ Credit (₹{total_credits}). Difference: ₹{abs(total_credits - total_credits)}. Cannot post bills. Please check calculations."
        )
    
    # Create Journal Entry record first (Accounting Constitution: Journal First)
    # IMPORTANT: Use rounded amounts for JV totals
    # IMPORTANT: Create only ONE JV entry for all bills (not per bill)
    journal_entry = JournalEntry(
        society_id=current_user.society_id,
        entry_number=await generate_journal_entry_number(db, current_user.society_id, transaction_date),
        date=transaction_date,
        description=description,  # "Maintenance charges for the month {month_name} {year} (Posted)"
        total_debit=total_credits,  # Use rounded total (Debit = Credit for double-entry)
        total_credit=total_credits,  # Use rounded total
        is_balanced=True,
        added_by=int(current_user.id),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(journal_entry)
    await db.flush() # Get journal_entry.id
    
    # Helper to get/create account
    async def get_or_create_account(code, name, acct_type):
        res = await db.execute(select(AccountCodeDB).where(and_(AccountCodeDB.code == code, AccountCodeDB.society_id == current_user.society_id)))
        acct = res.scalar_one_or_none()
        if not acct:
            acct = AccountCodeDB(
                society_id=current_user.society_id,
                code=code, name=name, type=acct_type,
                opening_balance=Decimal("0.00"), current_balance=Decimal("0.00"),
                created_at=datetime.utcnow(), updated_at=datetime.utcnow()
            )
            db.add(acct)
            await db.flush()
        return acct

    # Accounts list - CR-021_revised: Only required accounts
    acct_ar = await get_or_create_account("1100", "Maintenance Dues Receivable", AccountType.ASSET)
    acct_maint = await get_or_create_account("4000", "Maintenance Charges", AccountType.INCOME)
    # REMOVED: Separate accounts - all income now posts to 4000 Maintenance Charges only

    # Create Transactions - Enhanced for sub-ledger tracking
    # All transactions reference the same JV number (no individual document numbers)
    def create_txn(acct_code, category, dr, cr, flat_id=None, flat_number=None):
        # Create proper narration: "Maintenance bill generated for {month} {year}"
        txn_desc = f"Maintenance bill generated for {month_name} {request.year}"
        # Add flat info to description for sub-ledger tracking (1100 Maintenance Dues Receivable)
        if flat_id is not None and flat_number:
            txn_desc = f"{txn_desc} - Flat: {flat_number}"
        
        return Transaction(
            society_id=current_user.society_id,
            document_number=None,  # No individual document number - all transactions reference the JV
            type=TransactionType.INCOME if acct_code == "4000" else TransactionType.EXPENSE,
            category=category,
            account_code=acct_code,
            amount=dr if dr > 0 else cr,
            debit_amount=dr,
            credit_amount=cr,
            description=txn_desc,
            date=transaction_date,
            expense_month=f"{month_name}, {request.year}",  # Store month/year for filtering
            added_by=int(current_user.id),
            journal_entry_id=journal_entry.id,  # All transactions reference the same JV
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    # 1. Debit Accounts Receivable - Create per-flat transactions for sub-ledger tracking
    # Aggregate all bills by flat for proper sub-ledger tracking
    # IMPORTANT: Use ROUNDED bill amounts (bills are already rounded during generation)
    flat_totals = {}
    for bill in bills_to_post:
        if bill.flat_id not in flat_totals:
            flat_totals[bill.flat_id] = {
                'total': Decimal("0.00"),
                'flat_number': bill.flat_number
            }
        # Use rounded bill.amount (already rounded during generation)
        flat_totals[bill.flat_id]['total'] += Decimal(str(bill.amount))  # Current charges only (excluding arrears)
    
    # Create per-flat AR transactions for sub-ledger (Member Dues Register)
    # All transactions reference the same JV number (no sub-numbers)
    # IMPORTANT: Round to nearest whole rupee BEFORE posting
    for flat_id, flat_data in flat_totals.items():
        # Round to nearest whole rupee (bills should already be rounded, but ensure here)
        flat_ar_amount = Decimal(math.ceil(float(flat_data['total'])))
        
        txn_ar = create_txn("1100", "Maintenance Dues Receivable", flat_ar_amount, Decimal("0.00"), flat_id=flat_id, flat_number=flat_data['flat_number'])
        db.add(txn_ar)
    
    # Update AR account balance with total (using rounded amount)
    # IMPORTANT: Use rounded total_credits for consistency
    acct_ar.current_balance += total_credits  # Use rounded total
    
    # 2. Credit Income Heads
    # CR-021_revised: Post ALL charges (maintenance + water + fixed + sinking + repair + corpus) to 4000 Maintenance Charges only
    # Water charges are part of maintenance charges, not a separate income head
    # IMPORTANT: Use rounded total_credits (already rounded above) for posting
    total_income = total_credits  # Already rounded to nearest whole rupee
    
    if total_income > 0:
        db.add(create_txn("4000", "Maintenance Charges", Decimal("0.00"), total_income))
        acct_maint.current_balance -= total_income # Credit increases income (balance usually negative in credits unless using absolute)
        
    # REMOVED: All separate postings - now included in Maintenance Charges (4000) only
    # Water Charges (4010), Sinking Fund (3110), Repair Fund (3120), Corpus Fund (3100), 
    # Late Payment Fees (4040), Other Income (4200) - all consolidated into 4000 Maintenance Charges

    # 4. Log the posting action
    await log_action(
        db=db,
        society_id=current_user.society_id,
        user_id=int(current_user.id),
        action_type="update",
        entity_type="maintenance_bills",
        entity_id=None,
        new_values={
            "month": request.month,
            "year": request.year,
            "total_amount": float(total_amount),
            "action": "posted"
        }
    )
    
    # CR-021: Validate that 1100 account matches member dues register
    # Calculate total member dues (sum of all flat balances)
    result = await db.execute(
        select(Flat).where(Flat.society_id == current_user.society_id)
    )
    all_flats = result.scalars().all()
    
    total_member_dues = Decimal("0.00")
    for flat in all_flats:
        flat_balance = await get_flat_balance(db, current_user.society_id, flat.id)
        total_member_dues += flat_balance
    
    # Get 1100 account balance
    acct_1100_result = await db.execute(
        select(AccountCodeDB).where(
            and_(
                AccountCodeDB.code == "1100",
                AccountCodeDB.society_id == current_user.society_id
            )
        )
    )
    acct_1100 = acct_1100_result.scalar_one_or_none()
    
    if acct_1100:
        account_1100_balance = Decimal(str(acct_1100.current_balance or 0.0))
        # CR-021: Account 1100 must match member dues register
        if abs(account_1100_balance - total_member_dues) > Decimal("0.01"):
            # Log warning but don't fail - this is a data integrity check
            await log_action(
                db=db,
                society_id=current_user.society_id,
                user_id=int(current_user.id),
                action_type="warning",
                entity_type="maintenance_bills",
                entity_id=None,
                new_values={
                    "month": request.month,
                    "year": request.year,
                    "account_1100_balance": float(account_1100_balance),
                    "member_dues_total": float(total_member_dues),
                    "difference": float(abs(account_1100_balance - total_member_dues)),
                    "message": "CR-021: Account 1100 balance does not match member dues register"
                }
            )
    
    await db.commit()
    
    # Re-fetch for response
    response_bills = [
        MaintenanceBill(
            id=str(b.id),
            flat_id=str(b.flat_id),
            flat_number=b.flat_number,
            month=b.month,
            year=b.year,
            amount=b.total_amount,
            breakdown=b.breakdown or {},
            status=b.status.value if hasattr(b.status, 'value') else str(b.status),
            is_posted=b.is_posted,
            created_at=b.created_at,
            paid_at=b.paid_date
        ) for b in bills_to_post
    ]
    
    return BillGenerationResponse(
        total_bills_generated=len(response_bills),
        total_amount=float(total_amount),
        month=request.month,
        year=request.year,
        bills=response_bills
    )


@router.get("/bills", response_model=List[MaintenanceBill])
async def list_bills(
    month: Optional[int] = None,
    year: Optional[int] = None,
    flat_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get maintenance bills (with optional filters) - filtered by user's society"""
    # PRD: Multi-tenancy - Filter by society_id
    query = select(MaintenanceBillDB).where(
        MaintenanceBillDB.society_id == current_user.society_id
    ).order_by(
        MaintenanceBillDB.year.desc(),
        MaintenanceBillDB.month.desc()
    )

    if month:
        query = query.where(MaintenanceBillDB.month == month)
    if year:
        query = query.where(MaintenanceBillDB.year == year)
    if flat_id:
        try:
            flat_id_int = int(flat_id)
            query = query.where(MaintenanceBillDB.flat_id == flat_id_int)
        except ValueError:
            pass
    if status:
        from app.models_db import BillStatus
        # Convert string status to enum if needed
        if isinstance(status, str):
            try:
                status_enum = BillStatus(status.lower())
                query = query.where(MaintenanceBillDB.status == status_enum)
            except ValueError:
                # Invalid status, ignore filter
                pass
        else:
            query = query.where(MaintenanceBillDB.status == status)

    result = await db.execute(
        query.options(selectinload(MaintenanceBillDB.flat))
    )
    bills = result.scalars().all()

    # Build response list
    response_list = []
    for bill in bills:
        # Safely get flat_number
        flat_number = ""
        if bill.flat:
            flat_number = bill.flat.flat_number or ""
        
        # Safely get status
        bill_status = bill.status.value if hasattr(bill.status, 'value') else str(bill.status)
        
        # Safely get breakdown
        bill_breakdown = bill.breakdown if bill.breakdown else {}
        
        response_list.append(MaintenanceBill(
            id=str(bill.id),
            flat_id=str(bill.flat_id),
            flat_number=flat_number,
            month=bill.month,
            year=bill.year,
            amount=bill.total_amount,
            breakdown=bill_breakdown,
            status=bill_status,
            is_posted=bill.is_posted,  # Include is_posted field
            created_at=bill.created_at,
            paid_at=bill.paid_date
        ))
    
    return response_list


@router.patch("/bills/{bill_id}/mark-paid")
async def mark_bill_paid(
    bill_id: str,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark a bill as paid (admin only)"""
    try:
        bill_id_int = int(bill_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid bill ID"
        )

    # PRD: Multi-tenancy - Get bill and verify it belongs to user's society
    result = await db.execute(
        select(MaintenanceBillDB).where(
            MaintenanceBillDB.id == bill_id_int,
            MaintenanceBillDB.society_id == current_user.society_id
        )
    )
    bill = result.scalar_one_or_none()

    if not bill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bill not found"
        )

    bill.status = BillStatus.PAID
    bill.paid_date = datetime.utcnow().date()

    await db.commit()
    
    # PRD: Multi-tenancy - Reload with flat relationship to get flat_number
    result = await db.execute(
        select(MaintenanceBillDB)
        .options(selectinload(MaintenanceBillDB.flat))
        .where(
            MaintenanceBillDB.id == bill_id_int,
            MaintenanceBillDB.society_id == current_user.society_id
        )
    )
    bill = result.scalar_one_or_none()

    return MaintenanceBill(
        id=str(bill.id),
        flat_id=str(bill.flat_id),
        flat_number=bill.flat.flat_number if bill.flat else "",
        month=bill.month,
        year=bill.year,
        amount=bill.total_amount,
        breakdown=bill.breakdown if bill.breakdown else {},
        status=bill.status.value if hasattr(bill.status, 'value') else str(bill.status),
        created_at=bill.created_at,
        paid_at=bill.paid_date
    )


@router.delete("/bills/{month}/{year}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bills_for_month(
    month: int,
    year: int,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete all bills for a specific month/year (admin only)"""
    # PRD: Multi-tenancy - Filter by society_id
    # First, get the bills to check if they exist and get the total amount
    result = await db.execute(
        select(MaintenanceBillDB).where(
            and_(
                MaintenanceBillDB.month == month,
                MaintenanceBillDB.year == year,
                MaintenanceBillDB.society_id == current_user.society_id
            )
        )
    )
    bills_to_delete = result.scalars().all()
    
    if not bills_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No bills found for {month}/{year}"
        )
    
    # Calculate total amount to reverse accounting entries
    total_amount = sum(bill.total_amount for bill in bills_to_delete)
    
    # Delete the bills
    await db.execute(
        delete(MaintenanceBillDB).where(
            and_(
                MaintenanceBillDB.month == month,
                MaintenanceBillDB.year == year,
                MaintenanceBillDB.society_id == current_user.society_id
            )
        )
    )
    
    # Reverse accounting entries if they exist
    # Delete transactions for maintenance charges (4000) and accounts receivable (1100)
    # for this month/year
    if total_amount > 0:
        month_name = calendar.month_name[month]
        description = f"Maintenance charges for the month {month_name} {year}"
        
        # Find and delete the accounting transactions
        # Get transactions matching the description and account codes
        transaction_date = date(year, month, 1)
        
        # Delete Maintenance Charges transaction (4000)
        await db.execute(
            delete(Transaction).where(
                and_(
                    Transaction.society_id == current_user.society_id,
                    Transaction.account_code == "4000",
                    Transaction.description == description,
                    Transaction.date == transaction_date
                )
            )
        )
        
        # Delete Accounts Receivable transaction (1100)
        await db.execute(
            delete(Transaction).where(
                and_(
                    Transaction.society_id == current_user.society_id,
                    Transaction.account_code == "1100",
                    Transaction.description == description,
                    Transaction.date == transaction_date
                )
            )
        )
        
        # Reverse account balance updates
        # Get Maintenance Charges account (4000)
        result = await db.execute(
            select(AccountCodeDB).where(
                and_(
                    AccountCodeDB.code == "4000",
                    AccountCodeDB.society_id == current_user.society_id
                )
            )
        )
        maintenance_account = result.scalar_one_or_none()
        if maintenance_account:
            # Reverse: subtract the amount (income was credited, so reverse by adding back)
            maintenance_account.current_balance += Decimal(str(total_amount or 0.0))  # Reverse credit
            maintenance_account.updated_at = datetime.utcnow()
            db.add(maintenance_account)
        
        # Get Accounts Receivable account (1100)
        result = await db.execute(
            select(AccountCodeDB).where(
                and_(
                    AccountCodeDB.code == "1100",
                    AccountCodeDB.society_id == current_user.society_id
                )
            )
        )
        ar_account = result.scalar_one_or_none()
        if ar_account:
            # Reverse: subtract the amount (asset was debited, so reverse by subtracting)
            ar_account.current_balance -= Decimal(str(total_amount or 0.0))  # Reverse debit
            ar_account.updated_at = datetime.utcnow()
            db.add(ar_account)
    
    await db.commit()

    return None


@router.get("/bills/{bill_id}/download-pdf")
async def download_bill_pdf(
    bill_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Download maintenance bill as PDF
    Members can download their own bills, admins can download any bill
    """
    try:
        bill_id_int = int(bill_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid bill ID"
        )
    
    # Get bill with flat information
    result = await db.execute(
        select(MaintenanceBillDB).where(
            MaintenanceBillDB.id == bill_id_int,
            MaintenanceBillDB.society_id == current_user.society_id
        ).options(selectinload(MaintenanceBillDB.flat))
    )
    bill = result.scalar_one_or_none()
    
    if not bill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bill not found"
        )
    
    # Check permission - members can only view their own bills
    if current_user.role == 'member':
        # Get user's flat_id
        result = await db.execute(
            select(User).where(User.id == int(current_user.id))
        )
        user = result.scalar_one_or_none()
        if not user or not user.flat_id or user.flat_id != bill.flat_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only download your own bills"
            )
    
    # Get society information
    result = await db.execute(
        select(Society).where(Society.id == current_user.society_id)
    )
    society = result.scalar_one_or_none()
    
    if not society:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Society not found"
        )
    
    # Get flat member name
    member_name = "N/A"
    if bill.flat and bill.flat.primary_owner_name:
        member_name = bill.flat.primary_owner_name
    
    # Generate bill number if not exists
    bill_number = bill.bill_number or f"BILL-{bill.year}-{bill.month:02d}-{bill.flat_id}"
    
    # Prepare bill data for PDF
    bill_data = {
        'bill_number': bill_number,
        'flat_number': bill.flat.flat_number if bill.flat else "N/A",
        'member_name': member_name,
        'month': bill.month,
        'year': bill.year,
        'amount': bill.total_amount,
        'breakdown': bill.breakdown or {},
        'status': bill.status.value if hasattr(bill.status, 'value') else str(bill.status),
        'is_posted': bill.is_posted,
        'created_at': bill.created_at.isoformat(),
        'paid_at': bill.paid_date.isoformat() if bill.paid_date else None,
        'payment_method': bill.payment_method or None
    }
    
    # Prepare society info
    society_info = {
        'name': society.name,
        'address': society.address or "No address provided",
        'logo_url': None  # Can be added later
    }
    
    # Generate PDF
    from app.utils.export_utils import create_maintenance_bill_pdf
    from fastapi.responses import StreamingResponse
    
    pdf_file = create_maintenance_bill_pdf(bill_data, society_info)
    
    # Generate filename
    month_name = calendar.month_name[bill.month]
    filename = f"Maintenance_Bill_{bill.flat.flat_number}_{month_name}_{bill.year}.pdf"
    
    return StreamingResponse(
        pdf_file,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ============= CR-021_REVISED: INDIVIDUAL FLAT BILL REVERSAL =============

@router.post("/reverse-bill", status_code=status.HTTP_200_OK)
async def reverse_individual_bill(
    request: ReverseBillRequest,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    CR-021_revised: Reverse a single flat's bill for dispute redressal.
    Creates reversal journal entry (Debit 4000, Credit 1100) and updates member dues register.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        from app.utils.document_numbering import generate_journal_entry_number
        
        logger.info(f"Reversing bill: bill_id={request.bill_id}, user_id={current_user.id}, society_id={current_user.society_id}")
        
        try:
            bill_id = int(request.bill_id)
        except ValueError:
            logger.error(f"Invalid bill ID: '{request.bill_id}'")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid bill ID: '{request.bill_id}'. Expected a number."
            )
        
        # Get the bill
        result = await db.execute(
            select(MaintenanceBillDB).where(
                and_(
                    MaintenanceBillDB.id == bill_id,
                    MaintenanceBillDB.society_id == current_user.society_id
                )
            )
        )
        bill = result.scalar_one_or_none()
        
        if not bill:
            logger.error(f"Bill not found: bill_id={bill_id}, society_id={current_user.society_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bill with ID {bill_id} not found"
            )
        
        logger.info(f"Bill found: {bill.flat_number}, amount={bill.total_amount}, is_posted={bill.is_posted}")
        
        # CR-021_revised: Allow reversal of both posted and unposted bills
        # Unposted bills can be reversed and regenerated for corrections
        # Posted bills can be reversed for dispute redressal
        
            # Create reversal journal entry
        # CR-021_revised: Debit 4000 (Maintenance Charges), Credit 1100 (Maintenance Dues Receivable)
        reversal_amount = bill.total_amount
        
        # Get or create accounts
        async def get_or_create_account(code, name, acct_type):
            res = await db.execute(
                select(AccountCodeDB).where(
                    and_(
                        AccountCodeDB.code == code,
                        AccountCodeDB.society_id == current_user.society_id
                    )
                )
            )
            acct = res.scalar_one_or_none()
            if not acct:
                acct = AccountCodeDB(
                    code=code,
                    name=name,
                    type=acct_type,
                    society_id=current_user.society_id,
                    current_balance=Decimal("0.00")
                )
                db.add(acct)
                await db.flush()
            return acct
        
        acct_4000 = await get_or_create_account("4000", "Maintenance Charges", AccountType.INCOME)
        acct_1100 = await get_or_create_account("1100", "Maintenance Dues Receivable", AccountType.ASSET)
        
        # Generate journal entry number
        entry_number = await generate_journal_entry_number(db, current_user.society_id, date.today())
        
        # Create reversal journal entry
        reversal_entry = JournalEntry(
        society_id=current_user.society_id,
        entry_number=entry_number,
        date=date.today(),
        expense_month=f"{calendar.month_name[bill.month]}, {bill.year}",
        description=f"CR-021_revised: Bill reversal for Flat {bill.flat_number} - {request.reversal_reason}. Committee Approval: {request.committee_approval or 'N/A'}",
        total_debit=reversal_amount,
        total_credit=reversal_amount,
        is_balanced=True,
            added_by=int(current_user.id)
        )
        db.add(reversal_entry)
        await db.flush()
        
        # Create reversal transactions - both reference the same JV number (no individual document numbers)
        # Debit 4000 (Maintenance Charges) - reduces income
        reversal_txn_debit = Transaction(
            society_id=current_user.society_id,
            document_number=None,  # No individual document number - references the JV number
            type=TransactionType.EXPENSE,  # This is a reversal, so we debit the income account
            category="Bill Reversal",
            account_code="4000",
            amount=reversal_amount,
            description=f"Reversal: Bill {bill.bill_number} for Flat {bill.flat_number} - {request.reversal_reason}",
            date=date.today(),
            expense_month=f"{calendar.month_name[bill.month]}, {bill.year}",
            added_by=int(current_user.id),
            debit_amount=reversal_amount,
            credit_amount=Decimal("0.00"),
            journal_entry_id=reversal_entry.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(reversal_txn_debit)
        acct_4000.current_balance -= reversal_amount  # Reduce income
        
        # Credit 1100 (Maintenance Dues Receivable) - reduces receivable
        reversal_txn_credit = Transaction(
            society_id=current_user.society_id,
            document_number=None,  # No individual document number - references the JV number
            type=TransactionType.INCOME,  # This is a reversal, so we credit the asset account
            category="Bill Reversal",
            account_code="1100",
            amount=reversal_amount,
            description=f"Reversal: Bill {bill.bill_number} for Flat {bill.flat_number} - {request.reversal_reason}",
            date=date.today(),
            expense_month=f"{calendar.month_name[bill.month]}, {bill.year}",
            added_by=int(current_user.id),
            debit_amount=Decimal("0.00"),
            credit_amount=reversal_amount,
            journal_entry_id=reversal_entry.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(reversal_txn_credit)
        acct_1100.current_balance -= reversal_amount  # Reduce receivable
        
        # Mark bill as reversed (we'll add a reversed flag or delete it)
        # For now, we'll delete the bill and let them regenerate
        bill_month = bill.month
        bill_year = bill.year
        bill_flat_id = bill.flat_id
        bill_flat_number = bill.flat_number
        
        await db.delete(bill)
        
        await db.commit()
        
        logger.info(f"Bill reversed successfully: Flat {bill_flat_number}, Entry {entry_number}")
        
        return {
            "message": f"Bill reversed successfully for Flat {bill_flat_number}",
            "reversal_entry_number": entry_number,
            "reversal_amount": float(reversal_amount),
            "flat_id": str(bill_flat_id),
            "flat_number": bill_flat_number,
            "month": bill_month,
            "year": bill_year,
            "reversal_reason": request.reversal_reason,
            "committee_approval": request.committee_approval
        }
    except Exception as e:
        logger.error(f"Error reversing bill: {str(e)}", exc_info=True)
        try:
            await db.rollback()
        except:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reverse bill: {str(e)}"
        )


@router.post("/regenerate-bill", response_model=MaintenanceBill, status_code=status.HTTP_201_CREATED)
async def regenerate_individual_bill(
    request: RegenerateBillRequest,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    CR-021_revised: Regenerate a single flat's bill after reversal with revised/manual input.
    Creates new bill and posts to accounting (Credit 4000, Debit 1100) to update member dues register.
    """
    from app.utils.document_numbering import generate_journal_entry_number
    
    try:
        flat_id = int(request.flat_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid flat ID: '{request.flat_id}'. Expected a number."
        )
    
    # Get the flat
    result = await db.execute(
        select(Flat).where(
            and_(
                Flat.id == flat_id,
                Flat.society_id == current_user.society_id
            )
        )
    )
    flat = result.scalar_one_or_none()
    
    if not flat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Flat with ID {flat_id} not found"
        )
    
    # Check if a bill already exists for this flat/month/year
    result = await db.execute(
        select(MaintenanceBillDB).where(
            and_(
                MaintenanceBillDB.flat_id == flat_id,
                MaintenanceBillDB.month == request.month,
                MaintenanceBillDB.year == request.year,
                MaintenanceBillDB.society_id == current_user.society_id
            )
        )
    )
    existing_bill = result.scalar_one_or_none()
    
    if existing_bill:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bill already exists for Flat {flat.flat_number} for {calendar.month_name[request.month]} {request.year}. Reverse it first before regenerating."
        )
    
    # Get settings
    result = await db.execute(
        select(SocietySettings).where(SocietySettings.society_id == current_user.society_id)
    )
    settings = result.scalar_one_or_none()
    
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Society settings not configured"
        )
    
    # Calculate bill components from manual overrides
    maintenance_amount = Decimal(str(request.override_maintenance or 0))
    water_amount = Decimal(str(request.override_water or 0))
    fixed_amount = Decimal(str(request.override_fixed or 0))
    sinking_amount = Decimal(str(request.override_sinking or 0))
    repair_amount = Decimal(str(request.override_repair or 0))
    corpus_amount = Decimal(str(request.override_corpus or 0))
    
    # Get arrears (previous balance)
    calculation_date = date(request.year, request.month, 1)
    arrears = await get_flat_balance(db, current_user.society_id, flat_id, calculation_date)
    
    # Calculate late fee if applicable
    late_fee = Decimal("0.00")
    if arrears > 0 and settings.interest_on_overdue:
        interest_rate = Decimal(str(settings.interest_rate or 0)) / Decimal("100")
        monthly_interest_rate = interest_rate / Decimal("12")
        late_fee = (arrears * monthly_interest_rate).quantize(Decimal("0.01"))
    
    # Calculate monthly charges (current month only)
    monthly_charges = (maintenance_amount + water_amount + fixed_amount + sinking_amount + repair_amount + corpus_amount + late_fee).quantize(Decimal("0.01"))
    # Round up monthly charges to next rupee (ceiling)
    monthly_charges = Decimal(math.ceil(float(monthly_charges)))
    
    # Total amount including arrears
    total_amount = (monthly_charges + arrears).quantize(Decimal("0.01"))
    # Round up to next rupee (ceiling)
    total_amount = Decimal(math.ceil(float(total_amount)))
    
    # Create bill breakdown
    breakdown = {
        "maintenance_sqft": float(maintenance_amount),
        "water_charges": float(water_amount),
        "fixed_expenses": float(fixed_amount),
        "sinking_fund": float(sinking_amount),
        "repair_fund": float(repair_amount),
        "corpus_fund": float(corpus_amount),
        "arrears": float(arrears),
        "late_fee": float(late_fee),
        "monthly_charges": float(monthly_charges),
        "total_amount": float(total_amount),
        "regenerated": True,
        "regeneration_notes": request.notes or "Bill regenerated after reversal with manual input"
    }
    
    # Generate bill number
    # Get sequence number for this month/year
    result = await db.execute(
        select(func.count(MaintenanceBillDB.id)).where(
            and_(
                MaintenanceBillDB.month == request.month,
                MaintenanceBillDB.year == request.year,
                MaintenanceBillDB.society_id == current_user.society_id
            )
        )
    )
    sequence = result.scalar() + 1
    bill_number = generate_bill_number(current_user.society_id, request.month, request.year, sequence)
    
    # Create the bill
    new_bill = MaintenanceBillDB(
        society_id=current_user.society_id,
        flat_id=flat_id,
        flat_number=flat.flat_number,
        bill_number=bill_number,
        month=request.month,
        year=request.year,
        amount=monthly_charges,
        maintenance_amount=maintenance_amount,
        water_amount=water_amount,
        fixed_amount=fixed_amount,
        sinking_fund_amount=sinking_amount,
        repair_fund_amount=repair_amount,
        corpus_fund_amount=corpus_amount,
        arrears_amount=arrears,
        late_fee_amount=late_fee,
        total_amount=total_amount,
        breakdown=breakdown,
        status=BillStatus.UNPAID,
        is_posted=False,  # Will be posted immediately
        created_at=datetime.utcnow(),
        paid_date=None
    )
    db.add(new_bill)
    await db.flush()
    await db.refresh(new_bill)
    
    # Immediately post to accounting (Credit 4000, Debit 1100)
    # Get or create accounts
    async def get_or_create_account(code, name, acct_type):
        res = await db.execute(
            select(AccountCodeDB).where(
                and_(
                    AccountCodeDB.code == code,
                    AccountCodeDB.society_id == current_user.society_id
                )
            )
        )
        acct = res.scalar_one_or_none()
        if not acct:
            acct = AccountCodeDB(
                code=code,
                name=name,
                type=acct_type,
                society_id=current_user.society_id,
                current_balance=Decimal("0.00")
            )
            db.add(acct)
            await db.flush()
        return acct
    
    acct_4000 = await get_or_create_account("4000", "Maintenance Charges", AccountType.INCOME)
    acct_1100 = await get_or_create_account("1100", "Maintenance Dues Receivable", AccountType.ASSET)
    
    # Create journal entry for posting
    entry_number = await generate_journal_entry_number(db, current_user.society_id, date.today())
    month_name = calendar.month_name[request.month]
    description = f"CR-021_revised: Regenerated bill for Flat {flat.flat_number} - {month_name} {request.year}. {request.notes or 'Manual input after reversal'}"
    
    journal_entry = JournalEntry(
        society_id=current_user.society_id,
        entry_number=entry_number,
        date=date(request.year, request.month, 1),
        expense_month=f"{month_name}, {request.year}",
        description=description,
        total_debit=total_amount,
        total_credit=total_amount,
        is_balanced=True,
        added_by=int(current_user.id)
    )
    db.add(journal_entry)
    await db.flush()
    
    # Create transactions - both reference the same JV number (no individual document numbers)
    # Credit 4000 (Maintenance Charges) - increases income
    txn_credit = Transaction(
        society_id=current_user.society_id,
        document_number=None,  # No individual document number - references the JV number
        type=TransactionType.INCOME,
        category="Maintenance Bill",
        account_code="4000",
        amount=total_amount,
        description=f"Regenerated Bill {bill_number} for Flat {flat.flat_number} - {description}",
        date=date(request.year, request.month, 1),
        expense_month=f"{month_name}, {request.year}",
        added_by=int(current_user.id),
        debit_amount=Decimal("0.00"),
        credit_amount=total_amount,
        journal_entry_id=journal_entry.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(txn_credit)
    acct_4000.current_balance += total_amount  # Increase income
    
    # Debit 1100 (Maintenance Dues Receivable) - increases receivable
    # Include flat info in description for sub-ledger tracking
    txn_debit = Transaction(
        society_id=current_user.society_id,
        document_number=None,  # No individual document number - references the JV number
        type=TransactionType.EXPENSE,  # For asset accounts, we use EXPENSE type but debit_amount
        category="Maintenance Bill",
        account_code="1100",
        amount=total_amount,
        description=f"Regenerated Bill {bill_number} - Flat: {flat.flat_number} - {description}",
        date=date(request.year, request.month, 1),
        expense_month=f"{month_name}, {request.year}",
        added_by=int(current_user.id),
        debit_amount=total_amount,
        credit_amount=Decimal("0.00"),
        journal_entry_id=journal_entry.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(txn_debit)
    acct_1100.current_balance += total_amount  # Increase receivable
    
    # Mark bill as posted
    new_bill.is_posted = True
    new_bill.posted_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(new_bill)
    
    return MaintenanceBill(
        id=str(new_bill.id),
        flat_id=str(new_bill.flat_id),
        flat_number=new_bill.flat_number,
        month=new_bill.month,
        year=new_bill.year,
        amount=new_bill.total_amount,
        breakdown=new_bill.breakdown or {},
        status=new_bill.status.value if hasattr(new_bill.status, 'value') else str(new_bill.status),
        is_posted=new_bill.is_posted,
        created_at=new_bill.created_at,
        paid_at=new_bill.paid_date
    )
