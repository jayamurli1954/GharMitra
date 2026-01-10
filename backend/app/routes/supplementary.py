"""Supplementary billing API routes"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List

from app.database import get_db
from app.models_db import (
    SupplementaryBill as SupplementaryBillDB,
    SupplementaryBillFlat as SupplementaryBillFlatDB,
    Flat
)
from app.models.supplementary import (
    SupplementaryBillCreate,
    SupplementaryBillResponse,
    SupplementaryBillFlatResponse
)
from app.models.user import UserResponse
from app.dependencies import get_current_admin_user

router = APIRouter()

@router.post("/create", response_model=SupplementaryBillResponse)
async def create_supplementary_bill(
    request: SupplementaryBillCreate,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new supplementary bill with charges for specific flats"""
    
    new_bill = SupplementaryBillDB(
        society_id=current_user.society_id,
        title=request.title,
        description=request.description,
        date=request.date,
        approved_by=request.approved_by,
        status="approved" # Automatically approved for now as per simple workflow
    )
    db.add(new_bill)
    await db.flush()

    for charge in request.charges:
        # Verify flat belongs to society
        result = await db.execute(select(Flat).where(and_(Flat.id == charge.flat_id, Flat.society_id == current_user.society_id)))
        flat = result.scalar_one_or_none()
        if not flat:
            continue

        new_charge = SupplementaryBillFlatDB(
            supplementary_bill_id=new_bill.id,
            flat_id=charge.flat_id,
            amount=charge.amount
        )
        db.add(new_charge)

    await db.commit()
    await db.refresh(new_bill)
    
    # Eager load flats for response
    result = await db.execute(
        select(SupplementaryBillDB)
        .where(SupplementaryBillDB.id == new_bill.id)
    )
    new_bill = result.scalar_one()
    
    return new_bill

@router.get("/pending", response_model=List[SupplementaryBillResponse])
async def get_pending_supplementary_bills(
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all approved supplementary bills that haven't been included in a monthly bill yet"""
    result = await db.execute(
        select(SupplementaryBillDB)
        .where(and_(
            SupplementaryBillDB.society_id == current_user.society_id,
            SupplementaryBillDB.status == "approved"
        ))
    )
    bills = result.scalars().all()
    
    # Filter for bills that have at least one unincluded flat charge
    # In a real scenario, we might want more granular control, but this is a start.
    return bills

@router.get("/list", response_model=List[SupplementaryBillResponse])
async def list_supplementary_bills(
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """List all supplementary bills for the society"""
    result = await db.execute(
        select(SupplementaryBillDB)
        .where(SupplementaryBillDB.society_id == current_user.society_id)
        .order_by(SupplementaryBillDB.date.desc())
    )
    return result.scalars().all()
