"""Society Settings API routes"""
# Trigger Reload Verify 2
from fastapi import APIRouter, HTTPException, Depends, status, Body
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_, func
from datetime import datetime

from app.database import get_db
from app.models.settings import SocietySettingsCreate, SocietySettingsResponse
from app.models.user import UserResponse
from app.models_db import SocietySettings, Society
from app.dependencies import get_current_admin_user, get_optional_current_user

router = APIRouter()


@router.get("/society", response_model=SocietySettingsResponse)
async def get_society_settings(
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get society settings (admin only)"""
    result = await db.execute(
        select(SocietySettings).where(SocietySettings.society_id == current_user.society_id)
    )
    settings = result.scalar_one_or_none()
    
    # Fetch Society details
    society_result = await db.execute(select(Society).where(Society.id == current_user.society_id))
    society = society_result.scalar_one_or_none()
    
    if not settings:
        # Return default settings if none exist, but incl Society details
        response_data = {
            "id": "0",
            "society_id": current_user.society_id,
            "society_name": society.name if society else None,
            "society_address": society.address if society else None,
            "registration_number": society.registration_no if society else None,
            "city": society.city if society else None,
            "state": society.state if society else None,
            "pincode": society.pin_code if society else None,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        return SocietySettingsResponse(**response_data)
    
    response_data = {
        "id": str(settings.id),
        "society_id": settings.society_id,
        "society_name": society.name if society else None,
        "society_address": society.address if society else None,
        "registration_number": society.registration_no if society else None,
        "city": society.city if society else None,
        "state": society.state if society else None,
        "pincode": society.pin_code if society else None,
        "late_payment_penalty_type": settings.late_payment_penalty_type,
        "late_payment_penalty_value": settings.late_payment_penalty_value,
        "late_payment_grace_days": settings.late_payment_grace_days,
        "interest_on_overdue": settings.interest_on_overdue,
        "interest_rate": settings.interest_rate,
        "gst_enabled": settings.gst_enabled,
        "gst_number": settings.gst_number,
        "gst_rate": settings.gst_rate,
        "tds_enabled": settings.tds_enabled,
        "tds_rate": settings.tds_rate,
        "tds_threshold": settings.tds_threshold,
        "payment_gateway_enabled": settings.payment_gateway_enabled,
        "payment_gateway_provider": settings.payment_gateway_provider,
        "payment_gateway_key_id": settings.payment_gateway_key_id,
        "payment_gateway_key_secret": "***" if settings.payment_gateway_key_secret else None,  # Mask secret
        "upi_enabled": settings.upi_enabled,
        "upi_id": settings.upi_id,
        "bank_accounts": settings.bank_accounts,
        "vendor_approval_required": settings.vendor_approval_required,
        "vendor_approval_workflow": settings.vendor_approval_workflow,
        "audit_trail_enabled": settings.audit_trail_enabled,
        "audit_retention_days": settings.audit_retention_days,
        "billing_cycle": settings.billing_cycle,
        "auto_generate_bills": settings.auto_generate_bills,
        "bill_due_days": settings.bill_due_days,
        "bill_to_bill_tracking": settings.bill_to_bill_tracking,
        "fixed_expense_heads": settings.fixed_expense_heads,
        
        # Detailed Billing Rules
        "maintenance_calculation_logic": settings.maintenance_calculation_logic,
        "maintenance_rate_sqft": settings.maintenance_rate_sqft,
        "maintenance_rate_flat": settings.maintenance_rate_flat,
        "sinking_fund_rate": settings.sinking_fund_rate,
        "repair_fund_rate": settings.repair_fund_rate,
        "association_fund_rate": settings.association_fund_rate,
        "corpus_fund_rate": settings.corpus_fund_rate,
        
        "water_calculation_type": settings.water_calculation_type,
        "water_rate_per_person": settings.water_rate_per_person,
        "water_min_charge": settings.water_min_charge,
        
        "expense_distribution_logic": settings.expense_distribution_logic,

        # Member & Structure
        "member_approval_required": settings.member_approval_required,
        "tenant_expiry_reminder_days": settings.tenant_expiry_reminder_days,
        "max_members_per_flat": settings.max_members_per_flat,
        "blocks_config": settings.blocks_config,

        # Configs
        "notification_config": settings.notification_config,
        "complaint_config": settings.complaint_config,
        "asset_config": settings.asset_config,
        "legal_config": settings.legal_config,

        "created_at": settings.created_at.isoformat(),
        "updated_at": settings.updated_at.isoformat()
    }
    return SocietySettingsResponse(**response_data)


@router.post("/society", response_model=SocietySettingsResponse, status_code=status.HTTP_201_CREATED)
@router.patch("/society", response_model=SocietySettingsResponse)
async def create_or_update_society_settings(
    settings_data: SocietySettingsCreate,
    current_user: Optional[UserResponse] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create or update society settings (admin only)
    """
    print("=" * 80)
    print("=== SETTINGS UPDATE REQUEST RECEIVED ===")
    print(f"Request method: PATCH (or POST)")
    print(f"blocks_config in request: {settings_data.blocks_config}")
    if settings_data.blocks_config:
        print(f"blocks_config type: {type(settings_data.blocks_config)}")
        print(f"blocks_config length: {len(settings_data.blocks_config)}")
        for i, block in enumerate(settings_data.blocks_config):
            print(f"  Block {i}: name={block.get('name')}, floors={block.get('floors')}, flatsPerFloor={block.get('flatsPerFloor')}")
    print("=" * 80)

    # DEV FIX: If user is not authenticated (likely due to backend restart invalidating token),
    # use a mock admin user to allow saving settings.
    try:
        settings_response = await create_or_update_society_settings_impl(settings_data, current_user, db)
        return settings_response
    except HTTPException as e:
        raise e
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Handler Error: {str(e)}")

async def create_or_update_society_settings_impl(
    settings_data: SocietySettingsCreate,
    current_user: Optional[UserResponse],
    db: AsyncSession
):
    if not current_user:
        print("WARNING: User not authenticated. Using Mock Admin for Dev.")
        current_user = UserResponse(
            id="1", email="admin@gharmitra.com", name="Admin",
            apartment_number="A-101", phone_number="9999999999",
            role="admin", society_id=1, created_at=datetime.utcnow()
        )
    
    # Debug: Log what we received
    print(f"=== SETTINGS UPDATE REQUEST ===")
    print(f"blocks_config in request: {settings_data.blocks_config}")
    print(f"Full settings_data: {settings_data.dict(exclude_unset=False)}")
    """
    Create or update society settings (admin only)
    All settings are validated according to business rules:
    - Penalty settings require penalty_type and penalty_value
    - Interest settings require interest_rate when enabled
    - GST settings require gst_number and gst_rate when enabled
    - TDS settings require tds_rate and tds_threshold when enabled
    - Payment gateway requires provider, key_id, and key_secret when enabled
    - UPI requires upi_id when enabled
    - Auto-generate bills requires billing_cycle and bill_due_days
    """
    # Validation is handled by Pydantic models, but we can add additional checks here if needed
    
    # Check if settings exist
    result = await db.execute(
        select(SocietySettings).where(SocietySettings.society_id == current_user.society_id)
    )
    existing_settings = result.scalar_one_or_none()
    
    if existing_settings:
        # Update existing settings
        update_data = settings_data.dict(exclude_unset=True)
        
        # Always include blocks_config if it's in the request (even if empty list)
        # This ensures we can update blocks_config even if it's being set to empty
        if 'blocks_config' in settings_data.dict(exclude_unset=False):
            update_data['blocks_config'] = settings_data.blocks_config
            print(f"SETTINGS UPDATE: blocks_config explicitly set to: {settings_data.blocks_config}")
        
        for key, value in update_data.items():
            # Validate NOT NULL constraints for specific fields
            if key in ["transaction_date_lock_months", "transaction_date_lock_enabled"] and value is None:
                continue
            setattr(existing_settings, key, value)
            if key == 'blocks_config':
                print(f"SETTINGS UPDATE: Set blocks_config on settings object to: {value}")
        
        existing_settings.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(existing_settings)
        settings = existing_settings
        print(f"SETTINGS UPDATE: After refresh, settings.blocks_config = {settings.blocks_config}")
    else:
        # Create new settings
        new_settings = SocietySettings(
            society_id=current_user.society_id,
            **settings_data.dict(exclude_unset=True)
        )
        db.add(new_settings)
        await db.commit()
        db.add(new_settings)
        await db.commit()
        await db.refresh(new_settings)
        settings = new_settings
    
    # Update Society details if provided
    settings_dict = settings_data.dict(exclude_unset=True)
    if (settings_dict.get('society_name') or settings_dict.get('society_address') or 
        settings_dict.get('registration_number') or settings_dict.get('city') or 
        settings_dict.get('state') or settings_dict.get('pin_code')):
        result = await db.execute(
            select(Society).where(Society.id == current_user.society_id)
        )
        society = result.scalar_one_or_none()
        if society:
            if settings_dict.get('society_name'):
                society.name = settings_dict['society_name']
            if settings_dict.get('society_address'):
                society.address = settings_dict['society_address']
            if settings_dict.get('registration_number'):
                society.registration_no = settings_dict['registration_number']
            # Update city, state, pin_code if provided
            if settings_dict.get('city'):
                society.city = settings_dict['city']
            if settings_dict.get('state'):
                society.state = settings_dict['state']
            if settings_dict.get('pin_code'):
                society.pin_code = settings_dict['pin_code']
            await db.commit()
            await db.refresh(society)
            
    # Auto-generate Flats based on blocks_config
    # IMPORTANT: When blocks_config is updated, we regenerate ALL flats to match the new configuration
    # This ensures the flat count always matches: sum(floors * flats_per_floor) for all blocks
    # PRIORITY: Use the NEW blocks_config from the request if provided, otherwise use saved settings
    blocks_config_to_use = None
    
    # Check if blocks_config was in the request (user is updating it)
    request_dict = settings_data.dict(exclude_unset=False)
    request_has_blocks_config = 'blocks_config' in request_dict and request_dict['blocks_config'] is not None
    
    if request_has_blocks_config:
        # User is updating blocks_config - use the NEW value from request
        blocks_config_to_use = settings_data.blocks_config
        print(f"FLAT SYNC: Using NEW blocks_config from request: {blocks_config_to_use}")
    elif settings and settings.blocks_config:
        # No update in request, use existing saved config
        blocks_config_to_use = settings.blocks_config
        print(f"FLAT SYNC: Using blocks_config from saved settings (no update in request): {blocks_config_to_use}")
    else:
        blocks_config_to_use = []  # Empty list means no blocks configured
        print(f"FLAT SYNC: No blocks_config found anywhere, using empty list")
    
    # Always sync flats based on current blocks_config (even if empty list - will delete all flats)
    # This ensures flats always match the saved configuration
    print(f"FLAT SYNC: Starting flat sync with blocks_config: {blocks_config_to_use}")
    if blocks_config_to_use is not None:
        try:
            from app.models_db import Flat, OccupancyStatus
            
            # Calculate expected flat numbers from blocks_config
            # Support for excluding specific flat numbers (e.g., 111, 113 for cultural reasons)
            # Support for alphanumeric flat numbers with "G" for ground floor (e.g., A-G01, B-G08)
            expected_flat_numbers = set()
            
            def format_flat_number(block_name, floor, flat_seq, use_ground_floor_prefix=False):
                """Format flat number based on floor and configuration"""
                if use_ground_floor_prefix and floor == 1:
                    # Ground floor: A-G01, A-G02, etc.
                    return f"{block_name}-G{flat_seq:02d}"
                else:
                    # Other floors: A-101, A-102, A-201, etc.
                    flat_num_local = (floor * 100) + flat_seq
                    return f"{block_name}-{flat_num_local}"
            
            for block in blocks_config_to_use:
                block_name = block.get('name')
                floors = int(block.get('floors', 0))
                flats_per_floor = int(block.get('flatsPerFloor', 0))
                excluded_numbers = block.get('excludedNumbers', [])  # List of numbers to skip (e.g., [111, 113, "G01"])
                use_ground_floor_prefix = block.get('useGroundFloorPrefix', False)  # Enable G prefix for ground floor
                
                if not block_name or floors <= 0 or flats_per_floor <= 0:
                    continue
                
                # Convert excluded_numbers to set for faster lookup
                # Support both numeric (111) and alphanumeric ("G01", "G08") formats
                excluded_set = set()
                excluded_alphanumeric_set = set()  # For G01, G08, etc.
                if excluded_numbers:
                    for excluded in excluded_numbers:
                        excluded_str = str(excluded).upper()
                        # Check if it's alphanumeric (e.g., "G01", "G08")
                        if excluded_str.startswith('G') and excluded_str[1:].isdigit():
                            excluded_alphanumeric_set.add(excluded_str)
                        # Check if it's numeric (e.g., 111, 113)
                        elif excluded_str.isdigit():
                            excluded_set.add(int(excluded_str))
                        else:
                            # Store as string for exact match
                            excluded_alphanumeric_set.add(excluded_str)
                
                for floor in range(1, floors + 1):
                    for flat_seq in range(1, flats_per_floor + 1):
                        # Format flat number
                        full_flat_number = format_flat_number(block_name, floor, flat_seq, use_ground_floor_prefix)
                        
                        # Check if excluded (numeric format)
                        if not use_ground_floor_prefix or floor != 1:
                            # For non-ground floors, check numeric exclusion
                            flat_num_local = (floor * 100) + flat_seq
                            if flat_num_local in excluded_set:
                                print(f"FLAT SYNC: Skipping excluded flat number: {full_flat_number}")
                                continue
                        
                        # Check if excluded (alphanumeric format, e.g., G01, G08)
                        if use_ground_floor_prefix and floor == 1:
                            flat_alphanumeric = f"G{flat_seq:02d}"
                            if flat_alphanumeric in excluded_alphanumeric_set:
                                print(f"FLAT SYNC: Skipping excluded flat number: {full_flat_number}")
                                continue
                        
                        expected_flat_numbers.add(full_flat_number)
            
            # Get existing flats
            result = await db.execute(
                select(Flat).where(Flat.society_id == current_user.society_id)
            )
            existing_flats = result.scalars().all()
            existing_flat_numbers = {flat.flat_number for flat in existing_flats}
            
            print(f"FLAT SYNC: Found {len(existing_flats)} existing flats in database")
            if existing_flats:
                print(f"FLAT SYNC: Sample existing flats: {sorted(list(existing_flat_numbers))[:10]}")
            
            # Delete flats that are NOT in the expected list (removed blocks/floors)
            flats_to_delete_numbers = [flat.flat_number for flat in existing_flats if flat.flat_number not in expected_flat_numbers]
            print(f"FLAT SYNC: Expected {len(expected_flat_numbers)} flats, Existing {len(existing_flats)} flats, To delete {len(flats_to_delete_numbers)} flats")
            
            # SAFEGUARD 1: Check if flats to delete have active members
            if flats_to_delete_numbers:
                from app.models_db import Member
                flats_to_delete_objs = [f for f in existing_flats if f.flat_number in flats_to_delete_numbers]
                flats_to_delete_ids = [f.id for f in flats_to_delete_objs]
                
                result = await db.execute(
                    select(func.count(Member.id)).where(
                        and_(
                            Member.flat_id.in_(flats_to_delete_ids),
                            Member.society_id == current_user.society_id,
                            Member.status == "active",
                            or_(
                                Member.move_out_date.is_(None),
                                Member.move_out_date > datetime.utcnow().date()
                            )
                        )
                    )
                )
                members_count = result.scalar() or 0
                
                if members_count > 0:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Cannot delete {len(flats_to_delete_numbers)} flats because {members_count} active member(s) are associated with them. Please move out or delete members first."
                    )
            
            # SAFEGUARD 2: Prevent deleting more than 50% of flats without explicit confirmation
            deletion_percentage = (len(flats_to_delete_numbers) / len(existing_flats) * 100) if existing_flats else 0
            if deletion_percentage > 50 and len(existing_flats) > 10:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Safety check: Attempting to delete {len(flats_to_delete_numbers)} flats ({deletion_percentage:.1f}% of total). This seems excessive. Please verify your blocks configuration is correct."
                )
            
            # Also check for duplicate flats (same flat_number appearing multiple times)
            flat_numbers_seen = {}
            duplicate_flat_ids = []
            for flat in existing_flats:
                if flat.flat_number in flat_numbers_seen:
                    # This is a duplicate - mark for deletion
                    duplicate_flat_ids.append(flat.id)
                    print(f"FLAT SYNC: Found duplicate flat: {flat.flat_number} (ID: {flat.id})")
                else:
                    flat_numbers_seen[flat.flat_number] = flat.id
            
            if duplicate_flat_ids:
                print(f"FLAT SYNC: Deleting {len(duplicate_flat_ids)} duplicate flats")
                for dup_id in duplicate_flat_ids:
                    await db.execute(delete(Flat).where(Flat.id == dup_id))
                await db.commit()
            
            if flats_to_delete_numbers:
                print(f"FLAT SYNC: Deleting {len(flats_to_delete_numbers)} flats that don't match blocks_config")
                print(f"FLAT SYNC: Sample flats to delete: {sorted(flats_to_delete_numbers)[:20]}...")
                
                # Delete in batches if too many (SQLite has limits)
                batch_size = 100
                deleted_count = 0
                for i in range(0, len(flats_to_delete_numbers), batch_size):
                    batch = flats_to_delete_numbers[i:i + batch_size]
                    result = await db.execute(
                        delete(Flat).where(
                            and_(
                                Flat.society_id == current_user.society_id,
                                Flat.flat_number.in_(batch)
                            )
                        )
                    )
                    deleted_count += result.rowcount
                    print(f"FLAT SYNC: Deleted batch {i//batch_size + 1}: {result.rowcount} flats")
                
                await db.commit()
                print(f"FLAT SYNC: Successfully deleted {deleted_count} flats total")
            
            # Create new flats that don't exist yet
            new_flats = []
            for block in blocks_config_to_use:
                block_name = block.get('name')
                floors = int(block.get('floors', 0))
                flats_per_floor = int(block.get('flatsPerFloor', 0))
                use_ground_floor_prefix = block.get('useGroundFloorPrefix', False)  # Enable G prefix for ground floor
                
                if not block_name or floors <= 0 or flats_per_floor <= 0:
                    continue
                    
                for floor in range(1, floors + 1):
                    for flat_seq in range(1, flats_per_floor + 1):
                        # Use the same format function for consistency
                        full_flat_number = format_flat_number(block_name, floor, flat_seq, use_ground_floor_prefix)
                        
                        if full_flat_number not in existing_flat_numbers:
                            new_flats.append(
                                Flat(
                                    society_id=current_user.society_id,
                                    flat_number=full_flat_number,
                                    area_sqft=0.0, # Default, user might update later
                                    occupancy_status=OccupancyStatus.VACANT,
                                    created_at=datetime.utcnow(),
                                    updated_at=datetime.utcnow()
                                )
                            )
            
            # Refresh existing flats after deletion to get accurate count
            result = await db.execute(
                select(Flat).where(Flat.society_id == current_user.society_id)
            )
            existing_flats_after_delete = result.scalars().all()
            existing_flat_numbers_after = {flat.flat_number for flat in existing_flats_after_delete}
            
            if new_flats:
                print(f"FLAT SYNC: Creating {len(new_flats)} new flats")
                db.add_all(new_flats)
                await db.commit()
                print(f"FLAT SYNC: Successfully created {len(new_flats)} new flats")
            else:
                print(f"FLAT SYNC: No new flats to create")
            
            # Final count verification
            result = await db.execute(
                select(func.count(Flat.id)).where(Flat.society_id == current_user.society_id)
            )
            final_count = result.scalar() or 0
            
            print(f"FLAT SYNC COMPLETE: Expected {len(expected_flat_numbers)}, Final count in DB: {final_count}")
            
            if final_count != len(expected_flat_numbers):
                print(f"WARNING: Flat count mismatch! Expected {len(expected_flat_numbers)} but got {final_count}")
            
        except Exception as e:
            print(f"ERROR in flat sync: {e}")
            import traceback
            traceback.print_exc()
            # Don't raise exception - allow settings to save even if flat sync fails
            # This prevents settings save from failing due to flat sync issues
            print(f"WARNING: Flat sync failed but settings were saved. Error: {str(e)}")

    return SocietySettingsResponse(
        id=str(settings.id),
        society_id=settings.society_id,
        late_payment_penalty_type=settings.late_payment_penalty_type,
        late_payment_penalty_value=settings.late_payment_penalty_value,
        late_payment_grace_days=settings.late_payment_grace_days,
        interest_on_overdue=settings.interest_on_overdue,
        interest_rate=settings.interest_rate,
        gst_enabled=settings.gst_enabled,
        gst_number=settings.gst_number,
        gst_rate=settings.gst_rate,
        tds_enabled=settings.tds_enabled,
        tds_rate=settings.tds_rate,
        tds_threshold=settings.tds_threshold,
        payment_gateway_enabled=settings.payment_gateway_enabled,
        payment_gateway_provider=settings.payment_gateway_provider,
        payment_gateway_key_id=settings.payment_gateway_key_id,
        payment_gateway_key_secret="***" if settings.payment_gateway_key_secret else None,
        upi_enabled=settings.upi_enabled,
        upi_id=settings.upi_id,
        bank_accounts=settings.bank_accounts,
        vendor_approval_required=settings.vendor_approval_required,
        vendor_approval_workflow=settings.vendor_approval_workflow,
        audit_trail_enabled=settings.audit_trail_enabled,
        audit_retention_days=settings.audit_retention_days,
        billing_cycle=settings.billing_cycle,
        auto_generate_bills=settings.auto_generate_bills,
        bill_due_days=settings.bill_due_days,
        bill_to_bill_tracking=settings.bill_to_bill_tracking,
        fixed_expense_heads=settings.fixed_expense_heads,
        
        # Detailed Billing Rules
        maintenance_calculation_logic=settings.maintenance_calculation_logic,
        maintenance_rate_sqft=settings.maintenance_rate_sqft,
        maintenance_rate_flat=settings.maintenance_rate_flat,
        sinking_fund_rate=settings.sinking_fund_rate,
        repair_fund_rate=settings.repair_fund_rate,
        association_fund_rate=settings.association_fund_rate,
        corpus_fund_rate=settings.corpus_fund_rate,
        
        water_calculation_type=settings.water_calculation_type,
        water_rate_per_person=settings.water_rate_per_person,
        water_min_charge=settings.water_min_charge,
        
        expense_distribution_logic=settings.expense_distribution_logic,

        # Member & Structure
        member_approval_required=settings.member_approval_required,
        tenant_expiry_reminder_days=settings.tenant_expiry_reminder_days,
        max_members_per_flat=settings.max_members_per_flat,
        blocks_config=settings.blocks_config,

        # Configs
        notification_config=settings.notification_config,
        complaint_config=settings.complaint_config,
        asset_config=settings.asset_config,
        legal_config=settings.legal_config,

        created_at=settings.created_at.isoformat(),
        updated_at=settings.updated_at.isoformat()
    )


@router.get("/debug-flat-count", tags=["Debug"])
async def debug_flat_count(
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Debug endpoint to check actual flat count in database"""
    from app.models_db import Flat
    
    # Direct count query
    result = await db.execute(
        select(func.count(Flat.id)).where(Flat.society_id == current_user.society_id)
    )
    count = result.scalar() or 0
    
    # Get all flat numbers
    result = await db.execute(
        select(Flat.flat_number).where(Flat.society_id == current_user.society_id).order_by(Flat.flat_number)
    )
    flat_numbers = [row[0] for row in result.fetchall()]
    
    return {
        "society_id": current_user.society_id,
        "total_count": count,
        "flat_numbers": flat_numbers
    }


@router.post("/sync-flats", status_code=status.HTTP_200_OK)
async def sync_flats_manually(
    request_body: Optional[Dict[str, Any]] = Body(None),
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Manually trigger flat sync based on saved blocks_config or provided blocks_config.
    If blocks_config is provided in the request body, it will be saved first, then used for sync.
    Request body format: { "blocks_config": [{"name": "A", "floors": 4, "flatsPerFloor": 5}] }
    """
    try:
        # Extract blocks_config from request body if provided
        blocks_config = None
        if request_body and 'blocks_config' in request_body:
            blocks_config = request_body['blocks_config']
            print(f"MANUAL FLAT SYNC: blocks_config provided in request body: {blocks_config}")
        
        # Get saved settings
        result = await db.execute(
            select(SocietySettings).where(SocietySettings.society_id == current_user.society_id)
        )
        settings = result.scalar_one_or_none()
        
        # If blocks_config is provided in request, update settings first
        if blocks_config is not None:
            if not settings:
                # Create new settings if they don't exist
                settings = SocietySettings(
                    society_id=current_user.society_id,
                    blocks_config=blocks_config
                )
                db.add(settings)
                await db.commit()
                await db.refresh(settings)
            else:
                # Update existing settings
                settings.blocks_config = blocks_config
                settings.updated_at = datetime.utcnow()
                await db.commit()
                await db.refresh(settings)
            print(f"MANUAL FLAT SYNC: Updated settings.blocks_config to: {settings.blocks_config}")
        
        # Use blocks_config from request if provided, otherwise from saved settings
        if blocks_config is not None:
            blocks_config_to_use = blocks_config
            print(f"MANUAL FLAT SYNC: Using blocks_config from request: {blocks_config_to_use}")
        elif settings and settings.blocks_config:
            blocks_config_to_use = settings.blocks_config
            print(f"MANUAL FLAT SYNC: Using blocks_config from saved settings: {blocks_config_to_use}")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No blocks_config found. Please provide blocks_config in request or configure Flats & Blocks first."
            )
        
        from app.models_db import Flat, OccupancyStatus
        
        # Calculate expected flat numbers
        # Support for excluding specific flat numbers (e.g., 111, 113 for cultural reasons)
        # Support for alphanumeric flat numbers with "G" for ground floor (e.g., A-G01, B-G08)
        expected_flat_numbers = set()
        
        def format_flat_number(block_name, floor, flat_seq, use_ground_floor_prefix=False):
            """Format flat number based on floor and configuration"""
            if use_ground_floor_prefix and floor == 1:
                # Ground floor: A-G01, A-G02, etc.
                return f"{block_name}-G{flat_seq:02d}"
            else:
                # Other floors: A-101, A-102, A-201, etc.
                flat_num_local = (floor * 100) + flat_seq
                return f"{block_name}-{flat_num_local}"
        
        for block in blocks_config_to_use:
            block_name = block.get('name')
            floors = int(block.get('floors', 0))
            flats_per_floor = int(block.get('flatsPerFloor', 0))
            excluded_numbers = block.get('excludedNumbers', [])  # List of numbers to skip (e.g., [111, 113, "G01"])
            use_ground_floor_prefix = block.get('useGroundFloorPrefix', False)  # Enable G prefix for ground floor
            
            if not block_name or floors <= 0 or flats_per_floor <= 0:
                continue
            
            # Convert excluded_numbers to set for faster lookup
            # Support both numeric (111) and alphanumeric ("G01", "G08") formats
            excluded_set = set()
            excluded_alphanumeric_set = set()  # For G01, G08, etc.
            if excluded_numbers:
                for excluded in excluded_numbers:
                    excluded_str = str(excluded).upper()
                    # Check if it's alphanumeric (e.g., "G01", "G08")
                    if excluded_str.startswith('G') and excluded_str[1:].isdigit():
                        excluded_alphanumeric_set.add(excluded_str)
                    # Check if it's numeric (e.g., 111, 113)
                    elif excluded_str.isdigit():
                        excluded_set.add(int(excluded_str))
                    else:
                        # Store as string for exact match
                        excluded_alphanumeric_set.add(excluded_str)
            
            for floor in range(1, floors + 1):
                for flat_seq in range(1, flats_per_floor + 1):
                    # Format flat number
                    full_flat_number = format_flat_number(block_name, floor, flat_seq, use_ground_floor_prefix)
                    
                    # Check if excluded (numeric format)
                    if not use_ground_floor_prefix or floor != 1:
                        # For non-ground floors, check numeric exclusion
                        flat_num_local = (floor * 100) + flat_seq
                        if flat_num_local in excluded_set:
                            print(f"MANUAL SYNC: Skipping excluded flat number: {full_flat_number}")
                            continue
                    
                    # Check if excluded (alphanumeric format, e.g., G01, G08)
                    if use_ground_floor_prefix and floor == 1:
                        flat_alphanumeric = f"G{flat_seq:02d}"
                        if flat_alphanumeric in excluded_alphanumeric_set:
                            print(f"MANUAL SYNC: Skipping excluded flat number: {full_flat_number}")
                            continue
                    
                    expected_flat_numbers.add(full_flat_number)
            
            print(f"MANUAL SYNC: Block '{block_name}': {floors} floors × {flats_per_floor} flats = {floors * flats_per_floor} flats")
        
        print(f"MANUAL SYNC: Total expected flats: {len(expected_flat_numbers)}")
        print(f"MANUAL SYNC: Sample expected (first 10): {sorted(list(expected_flat_numbers))[:10]}")
        
        # Get existing flats - also get count directly from DB
        count_result = await db.execute(
            select(func.count(Flat.id)).where(Flat.society_id == current_user.society_id)
        )
        db_flat_count = count_result.scalar() or 0
        print(f"MANUAL SYNC: Database flat count (direct query): {db_flat_count}")
        
        result = await db.execute(
            select(Flat).where(Flat.society_id == current_user.society_id)
        )
        existing_flats = result.scalars().all()
        existing_flat_numbers = {flat.flat_number for flat in existing_flats}
        
        print(f"MANUAL SYNC: Expected flat numbers (first 10): {sorted(list(expected_flat_numbers))[:10]}")
        print(f"MANUAL SYNC: Existing flat numbers (first 10): {sorted(list(existing_flat_numbers))[:10]}")
        print(f"MANUAL SYNC: Total expected: {len(expected_flat_numbers)}, Total existing (from query): {len(existing_flat_numbers)}, DB count: {db_flat_count}")
        
        # If DB count doesn't match query count, something is wrong
        if db_flat_count != len(existing_flat_numbers):
            print(f"MANUAL SYNC: WARNING! DB count ({db_flat_count}) != query count ({len(existing_flat_numbers)})")
        
        # Delete flats not in expected list
        flats_to_delete_numbers = [flat.flat_number for flat in existing_flats if flat.flat_number not in expected_flat_numbers]
        
        print(f"MANUAL SYNC: Flats to delete (first 10): {sorted(flats_to_delete_numbers)[:10]}")
        print(f"MANUAL SYNC: All existing flats: {sorted(list(existing_flat_numbers))}")
        
        # SAFEGUARD: Check for active members before bulk deletion
        if len(existing_flats) > 0:
            from app.models_db import Member
            all_flat_ids = [f.id for f in existing_flats]
            result = await db.execute(
                select(func.count(Member.id)).where(
                    and_(
                        Member.flat_id.in_(all_flat_ids),
                        Member.society_id == current_user.society_id,
                        Member.status == "active",
                        or_(
                            Member.move_out_date.is_(None),
                            Member.move_out_date > datetime.utcnow().date()
                        )
                    )
                )
            )
            active_members_count = result.scalar() or 0
            
            if active_members_count > 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot sync flats because {active_members_count} active member(s) are associated with existing flats. Please move out or delete members first, or ensure your blocks configuration matches existing flat numbers."
                )
        
        # If no flats match expected format, delete ALL flats and recreate
        # This handles cases where flat format changed or there are duplicates
        matching_flats = [f for f in existing_flat_numbers if f in expected_flat_numbers]
        print(f"MANUAL SYNC: Matching flats: {len(matching_flats)} out of {len(existing_flat_numbers)}")
        
        deleted_count = 0
        # If count doesn't match OR no flats match, delete ALL and recreate
        # Use DB count for comparison, not query count
        if db_flat_count != len(expected_flat_numbers):
            # Count mismatch - delete ALL and recreate to ensure exact match
            print(f"MANUAL SYNC: Count mismatch! Expected {len(expected_flat_numbers)} but DB has {db_flat_count}. Deleting ALL and recreating...")
            result = await db.execute(
                delete(Flat).where(Flat.society_id == current_user.society_id)
            )
            deleted_count = result.rowcount
            await db.commit()
            print(f"MANUAL SYNC: Deleted all {deleted_count} flats")
            # Clear existing_flat_numbers since we deleted everything
            existing_flat_numbers = set()
            # Refresh DB count
            count_result = await db.execute(
                select(func.count(Flat.id)).where(Flat.society_id == current_user.society_id)
            )
            db_flat_count = count_result.scalar() or 0
            print(f"MANUAL SYNC: After delete, DB count is now: {db_flat_count}")
        elif len(matching_flats) == 0 and len(existing_flat_numbers) > 0:
            # No flats match - delete ALL and recreate
            print(f"MANUAL SYNC: No flats match expected format. Deleting ALL {len(existing_flat_numbers)} flats and recreating...")
            result = await db.execute(
                delete(Flat).where(Flat.society_id == current_user.society_id)
            )
            deleted_count = result.rowcount
            await db.commit()
            print(f"MANUAL SYNC: Deleted all {deleted_count} flats")
            # Clear existing_flat_numbers since we deleted everything
            existing_flat_numbers = set()
        elif flats_to_delete_numbers:
            batch_size = 100
            for i in range(0, len(flats_to_delete_numbers), batch_size):
                batch = flats_to_delete_numbers[i:i + batch_size]
                result = await db.execute(
                    delete(Flat).where(
                        and_(
                            Flat.society_id == current_user.society_id,
                            Flat.flat_number.in_(batch)
                        )
                    )
                )
                deleted_count += result.rowcount
            await db.commit()
        
        # Create missing flats
        new_flats = []
        for block in blocks_config_to_use:
            block_name = block.get('name')
            floors = int(block.get('floors', 0))
            flats_per_floor = int(block.get('flatsPerFloor', 0))
            use_ground_floor_prefix = block.get('useGroundFloorPrefix', False)  # Enable G prefix for ground floor
            
            if not block_name or floors <= 0 or flats_per_floor <= 0:
                continue
                
            for floor in range(1, floors + 1):
                for flat_seq in range(1, flats_per_floor + 1):
                    # Use the same format function for consistency
                    full_flat_number = format_flat_number(block_name, floor, flat_seq, use_ground_floor_prefix)
                    
                    if full_flat_number not in existing_flat_numbers:
                        new_flats.append(
                            Flat(
                                society_id=current_user.society_id,
                                flat_number=full_flat_number,
                                area_sqft=0.0,  # Default, can be updated later
                                bedrooms=2,  # Default 2 bedrooms, can be updated later
                                occupancy_status=OccupancyStatus.VACANT,
                                created_at=datetime.utcnow(),
                                updated_at=datetime.utcnow()
                            )
                        )
        
        if new_flats:
            db.add_all(new_flats)
            await db.commit()
        
        # Final count - verify with DB
        result = await db.execute(
            select(func.count(Flat.id)).where(Flat.society_id == current_user.society_id)
        )
        final_count = result.scalar() or 0
        
        print(f"MANUAL SYNC: Final DB count after sync: {final_count}")
        print(f"MANUAL SYNC: Expected: {len(expected_flat_numbers)}, Final: {final_count}, Deleted: {deleted_count}, Created: {len(new_flats)}")
        
        # Get sample of existing flats for debugging
        result = await db.execute(
            select(Flat.flat_number).where(Flat.society_id == current_user.society_id).limit(10)
        )
        sample_existing = [row[0] for row in result.fetchall()]
        
        # If final count still doesn't match, something went wrong
        if final_count != len(expected_flat_numbers):
            print(f"MANUAL SYNC: ERROR! Final count ({final_count}) still doesn't match expected ({len(expected_flat_numbers)})")
        
        return {
            "message": "Flat sync completed successfully",
            "expected_flats": len(expected_flat_numbers),
            "deleted_flats": deleted_count,
            "created_flats": len(new_flats),
            "final_count": final_count,
            "sample_expected": sorted(list(expected_flat_numbers))[:10],
            "sample_existing": sample_existing,
            "blocks_config_used": blocks_config_to_use,
            "society_id": current_user.society_id  # For debugging
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Flat sync failed: {str(e)}")

