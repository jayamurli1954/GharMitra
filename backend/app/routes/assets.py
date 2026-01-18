from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.asset import AssetCreate, AssetUpdate, AssetResponse
from app.models.user import UserResponse
from app.models_db import Asset, JournalEntry, Transaction, AccountCode, VoucherType, AcquisitionType, AssetCategory, TransactionType, DepreciationMethod
from app.dependencies import get_current_user, get_current_admin_user
from app.utils.document_numbering import generate_journal_entry_number

router = APIRouter()

@router.get("/", response_model=List[AssetResponse])
async def list_assets(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all society assets"""
    result = await db.execute(
        select(Asset).where(Asset.society_id == current_user.society_id).order_by(Asset.created_at.desc())
    )
    return result.scalars().all()

@router.post("/", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
async def create_asset(
    asset_data: AssetCreate,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new asset record.
    If acquisition_type is BUILDER_HANDOVER, it also creates an automated Journal Entry:
    Asset Account (Dr) / Corpus Fund (Cr)
    """
    # 1. Generate Asset Code if not provided
    asset_code = None
    if not asset_data.name: # Should be caught by pydantic but just in case
        raise HTTPException(status_code=400, detail="Asset name is required")
    
    # Simple auto-incrementing code AST-XXXXX
    count_result = await db.execute(select(func.count(Asset.id)).where(Asset.society_id == current_user.society_id))
    count = count_result.scalar()
    asset_code = f"AST-{str(count + 1).zfill(5)}"

    # 2. Create Asset Record
    new_asset = Asset(
        society_id=current_user.society_id,
        asset_code=asset_code,
        **asset_data.model_dump()
    )
    db.add(new_asset)
    
    # 3. Handle Automated Accounting for Builder Handover
    if asset_data.acquisition_type == AcquisitionType.BUILDER_HANDOVER:
        if not asset_data.account_code:
            # Default to 1500 Common Area Assets if not specified
            new_asset.account_code = "1500"
        
        cost = Decimal(str(asset_data.original_cost))
        txn_date = asset_data.handover_date or date.today()
        
        if cost > 0:
            # Create Journal Entry
            entry_num = await generate_journal_entry_number(db, current_user.society_id, txn_date)
            
            journal = JournalEntry(
                society_id=current_user.society_id,
                voucher_type=VoucherType.JOURNAL,
                entry_number=entry_num,
                date=txn_date,
                description=f"Builder Handover: {asset_data.name} (Code: {asset_code})",
                total_amount=float(cost),
                created_by=current_user.id
            )
            db.add(journal)
            await db.flush() # Get journal.id
            
            # Entry 1: Debit Asset Account
            txn_dr = Transaction(
                society_id=current_user.society_id,
                journal_entry_id=journal.id,
                account_code=new_asset.account_code,
                date=txn_date,
                type=TransactionType.EXPENSE,
                debit_amount=float(cost),
                credit_amount=0.0,
                description=f"Asset Handover - {asset_data.name}",
                added_by=current_user.id,
                document_number=journal.entry_number
            )
            
            # Entry 2: Credit Corpus Fund (3010)
            txn_cr = Transaction(
                society_id=current_user.society_id,
                journal_entry_id=journal.id,
                account_code="3010",
                date=txn_date,
                type=TransactionType.INCOME,
                debit_amount=0.0,
                credit_amount=float(cost),
                description=f"Initial Capital Contribution - {asset_data.name}",
                added_by=current_user.id,
                document_number=journal.entry_number
            )
            
            db.add_all([txn_dr, txn_cr])
            
            # Update Account Balances
            # Asset side
            res_dr = await db.execute(select(AccountCode).where(AccountCode.code == new_asset.account_code, AccountCode.society_id == current_user.society_id))
            acct_dr = res_dr.scalar_one_or_none()
            if acct_dr:
                acct_dr.current_balance = float(Decimal(str(acct_dr.current_balance or 0.0)) + cost)
            
            # Liability/Capital side
            res_cr = await db.execute(select(AccountCode).where(AccountCode.code == "3010", AccountCode.society_id == current_user.society_id))
            acct_cr = res_cr.scalar_one_or_none()
            if acct_cr:
                acct_cr.current_balance = float(Decimal(str(acct_cr.current_balance or 0.0)) + cost)

    await db.commit()
    await db.refresh(new_asset)
    return new_asset

@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get details of a specific asset"""
    result = await db.execute(
        select(Asset).where(Asset.id == asset_id, Asset.society_id == current_user.society_id)
    )
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset

@router.put("/{asset_id}", response_model=AssetResponse)
async def update_asset(
    asset_id: int,
    asset_update: AssetUpdate,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Update asset informaton"""
    result = await db.execute(
        select(Asset).where(Asset.id == asset_id, Asset.society_id == current_user.society_id)
    )
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    update_data = asset_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(asset, key, value)
    
    await db.commit()
    await db.refresh(asset)
    return asset

@router.post("/{asset_id}/scrap", response_model=AssetResponse)
async def scrap_asset(
    asset_id: int,
    scrapping_reason: str,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark an asset as scrapped (Audit Requirement)"""
    result = await db.execute(
        select(Asset).where(Asset.id == asset_id, Asset.society_id == current_user.society_id)
    )
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    asset.status = "Scrapped"
    asset.is_scrapped = True
    asset.notes = (asset.notes or "") + f"\nScrapped on {date.today()}: {scrapping_reason}"
    
    await db.commit()
    await db.refresh(asset)
    return asset
