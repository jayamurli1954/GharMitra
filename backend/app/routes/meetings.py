"""Meeting Management API routes - Committee and General Body meetings"""
from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_, or_, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime, date

from app.database import get_db
from app.models.meetings import (
    MeetingCreate,
    MeetingUpdate,
    MeetingResponse,
    MeetingNoticeRequest,
    MeetingNoticeResponse,
    AgendaItemCreate,
    AgendaItemResponse,
    AttendanceRecord,
    MarkAttendanceRequest,
    AttendanceResponse,
    RecordMinutesRequest,
    CreateResolutionRequest,
    ResolutionResponse,
    MeetingDetailsResponse
)
from app.models.user import UserResponse
from app.models_db import (
    Meeting,
    MeetingType,
    MeetingStatus,
    Society,
    MeetingAgendaItem,
    MeetingAttendance,
    MeetingResolution,
    AgendaItemStatus,
    AttendanceStatus,
    ResolutionType,
    ResolutionResult,
    Member
)
from app.dependencies import get_current_user, get_current_admin_user

router = APIRouter()


# ============ HELPER FUNCTIONS ============

def _build_meeting_response(meeting: Meeting, creator, notice_sender=None) -> MeetingResponse:
    """Helper function to build MeetingResponse from Meeting model"""
    return MeetingResponse(
        id=meeting.id,
        society_id=meeting.society_id,
        meeting_type=meeting.meeting_type.value if hasattr(meeting.meeting_type, 'value') else str(meeting.meeting_type),
        meeting_number=meeting.meeting_number,
        meeting_date=meeting.meeting_date,
        meeting_time=meeting.meeting_time,
        meeting_title=meeting.meeting_title,
        venue=meeting.venue,
        status=meeting.status.value if hasattr(meeting.status, 'value') else str(meeting.status),
        total_members_eligible=meeting.total_members_eligible,
        total_members_present=meeting.total_members_present,
        quorum_required=meeting.quorum_required,
        quorum_met=meeting.quorum_met,
        minutes_text=meeting.minutes_text,
        minutes_approved=meeting.minutes_approved,
        minutes_approved_date=meeting.minutes_approved_date,
        recorded_by=meeting.recorded_by,
        recorded_at=meeting.recorded_at,
        notice_sent=meeting.notice_sent,
        notice_sent_at=meeting.notice_sent_at,
        notice_sent_to=meeting.notice_sent_to,
        notice_sent_by=meeting.notice_sent_by,
        notice_sent_by_name=notice_sender.name if notice_sender else None,
        created_by=meeting.created_by,
        created_by_name=creator.name if creator else "Unknown",
        created_at=meeting.created_at,
        updated_at=meeting.updated_at,
        # Legacy fields
        agenda=meeting.agenda,
        attendees_count=meeting.attendees_count,
        chaired_by=meeting.chaired_by
    )


@router.post("/meetings", response_model=MeetingResponse, status_code=status.HTTP_201_CREATED)
async def create_meeting(
    meeting_data: MeetingCreate,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new meeting record with agenda items (admin only)
    Supports MC, AGM, EGM, SGM, committee, and general_body meeting types
    """
    # Convert string to enum
    meeting_type_map = {
        "MC": MeetingType.MC,
        "AGM": MeetingType.AGM,
        "EGM": MeetingType.EGM,
        "SGM": MeetingType.SGM,
        "committee": MeetingType.COMMITTEE,
        "general_body": MeetingType.GENERAL_BODY
    }
    meeting_type_enum = meeting_type_map.get(meeting_data.meeting_type)
    if not meeting_type_enum:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid meeting_type: {meeting_data.meeting_type}"
        )
    
    # Generate meeting number if not provided
    meeting_number = None
    if meeting_data.meeting_type in ["MC", "AGM", "EGM", "SGM"]:
        # Get count of meetings of this type for numbering
        result = await db.execute(
            select(func.count(Meeting.id)).where(
                and_(
                    Meeting.society_id == current_user.society_id,
                    Meeting.meeting_type == meeting_type_enum
                )
            )
        )
        count = result.scalar() or 0
        year = meeting_data.meeting_date.year
        meeting_number = f"{meeting_data.meeting_type}/{year}/{count + 1:03d}"
    
    new_meeting = Meeting(
        society_id=current_user.society_id,
        meeting_type=meeting_type_enum,
        meeting_number=meeting_number,
        meeting_date=meeting_data.meeting_date,
        meeting_time=meeting_data.meeting_time,
        meeting_title=meeting_data.meeting_title,
        venue=meeting_data.venue,
        agenda=meeting_data.agenda,  # Legacy field
        attendees_count=meeting_data.attendees_count,  # Legacy field
        chaired_by=meeting_data.chaired_by,  # Legacy field
        notice_sent_to=meeting_data.notice_sent_to,
        status=MeetingStatus.SCHEDULED,
        created_by=int(current_user.id),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(new_meeting)
    await db.flush()  # Flush to get the ID
    
    # Create agenda items if provided
    if meeting_data.agenda_items:
        for agenda_item_data in meeting_data.agenda_items:
            agenda_item = MeetingAgendaItem(
                meeting_id=new_meeting.id,
                society_id=current_user.society_id,
                item_number=agenda_item_data.item_number,
                item_title=agenda_item_data.item_title,
                item_description=agenda_item_data.item_description,
                status=AgendaItemStatus.PENDING
            )
            db.add(agenda_item)
    
    await db.commit()
    await db.refresh(new_meeting)
    
    # Get creator details
    from app.models_db import User
    result = await db.execute(select(User).where(User.id == int(current_user.id)))
    creator = result.scalar_one()
    
    return _build_meeting_response(meeting=new_meeting, creator=creator, notice_sender=None)


@router.get("/meetings", response_model=List[MeetingResponse])
async def list_meetings(
    meeting_type: Optional[str] = Query(None, description="Filter by type: MC, AGM, EGM, SGM, committee, or general_body"),
    from_date: Optional[date] = Query(None, description="Filter from date"),
    to_date: Optional[date] = Query(None, description="Filter to date"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all meetings with optional filtering by type and date range
    """
    query = select(Meeting).where(Meeting.society_id == current_user.society_id)
    
    # Filter by meeting type
    if meeting_type:
        meeting_type_map = {
            "MC": MeetingType.MC,
            "AGM": MeetingType.AGM,
            "EGM": MeetingType.EGM,
            "SGM": MeetingType.SGM,
            "committee": MeetingType.COMMITTEE,
            "general_body": MeetingType.GENERAL_BODY
        }
        if meeting_type not in meeting_type_map:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid meeting_type. Must be one of: {', '.join(meeting_type_map.keys())}"
            )
        query = query.where(Meeting.meeting_type == meeting_type_map[meeting_type])
    
    # Filter by date range
    if from_date:
        query = query.where(Meeting.meeting_date >= from_date)
    if to_date:
        query = query.where(Meeting.meeting_date <= to_date)
    
    # Order by date descending (most recent first)
    query = query.order_by(Meeting.meeting_date.desc())
    
    result = await db.execute(query)
    meetings = result.scalars().all()
    
    # Get creator and notice sender details
    from app.models_db import User
    user_ids = {meeting.created_by for meeting in meetings}
    user_ids.update({meeting.notice_sent_by for meeting in meetings if meeting.notice_sent_by})
    
    if user_ids:
        result = await db.execute(select(User).where(User.id.in_(user_ids)))
        users = {user.id: user for user in result.scalars().all()}
    else:
        users = {}
    
    response_list = []
    for meeting in meetings:
        creator = users.get(meeting.created_by)
        notice_sender = users.get(meeting.notice_sent_by) if meeting.notice_sent_by else None
        response_list.append(_build_meeting_response(meeting=meeting, creator=creator, notice_sender=notice_sender))
    
    return response_list


@router.get("/meetings/{meeting_id}", response_model=MeetingResponse)
async def get_meeting(
    meeting_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific meeting"""
    result = await db.execute(
        select(Meeting).where(
            and_(
                Meeting.id == int(meeting_id),
                Meeting.society_id == current_user.society_id
            )
        )
    )
    meeting = result.scalar_one_or_none()
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )
    
    # Get creator and notice sender details
    from app.models_db import User
    user_ids = {meeting.created_by}
    if meeting.notice_sent_by:
        user_ids.add(meeting.notice_sent_by)
    
    result = await db.execute(select(User).where(User.id.in_(user_ids)))
    users = {user.id: user for user in result.scalars().all()}
    
    creator = users.get(meeting.created_by)
    notice_sender = users.get(meeting.notice_sent_by) if meeting.notice_sent_by else None
    
    return _build_meeting_response(meeting=meeting, creator=creator, notice_sender=notice_sender)


@router.patch("/meetings/{meeting_id}", response_model=MeetingResponse)
async def update_meeting(
    meeting_id: str,
    meeting_data: MeetingUpdate,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a meeting (admin only)"""
    result = await db.execute(
        select(Meeting).where(
            and_(
                Meeting.id == int(meeting_id),
                Meeting.society_id == current_user.society_id
            )
        )
    )
    meeting = result.scalar_one_or_none()
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )
    
    # Update fields
    update_data = meeting_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(meeting, key, value)
    meeting.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(meeting)
    
    # Get creator and notice sender details
    from app.models_db import User
    user_ids = {meeting.created_by}
    if meeting.notice_sent_by:
        user_ids.add(meeting.notice_sent_by)
    
    result = await db.execute(select(User).where(User.id.in_(user_ids)))
    users = {user.id: user for user in result.scalars().all()}
    
    creator = users.get(meeting.created_by)
    notice_sender = users.get(meeting.notice_sent_by) if meeting.notice_sent_by else None
    
    return _build_meeting_response(meeting=meeting, creator=creator, notice_sender=notice_sender)


@router.delete("/meetings/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meeting(
    meeting_id: str,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a meeting (admin only)"""
    try:
        meeting_id_int = int(meeting_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid meeting ID"
        )
    
    # Delete meeting (cascade will handle related records)
    result = await db.execute(
        delete(Meeting).where(
            and_(
                Meeting.id == meeting_id_int,
                Meeting.society_id == current_user.society_id
            )
        )
    )
    await db.commit()
    
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )
    
    return None


@router.post("/meetings/{meeting_id}/send-notice", response_model=MeetingNoticeResponse, status_code=status.HTTP_200_OK)
async def send_meeting_notice(
    meeting_id: str,
    notice_data: MeetingNoticeRequest,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Send meeting notice to all committee members (for committee meetings) 
    or all members (for general body meetings) (admin only)
    """
    # Verify meeting exists and belongs to society
    result = await db.execute(
        select(Meeting).where(
            and_(
                Meeting.id == int(meeting_id),
                Meeting.society_id == current_user.society_id
            )
        )
    )
    meeting = result.scalar_one_or_none()
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )
    
    recipients = []
    
    # Get recipients based on meeting type
    if meeting.meeting_type == MeetingType.COMMITTEE:
        # For committee meetings: Get all users with committee roles
        from app.models_db import User, UserRole
        result = await db.execute(
            select(User).where(
                and_(
                    User.society_id == current_user.society_id,
                    User.role.in_([
                        UserRole.ADMIN,
                        UserRole.SUPER_ADMIN,
                        UserRole.CHAIRMAN,
                        UserRole.SECRETARY,
                        UserRole.TREASURER
                    ])
                )
            )
        )
        committee_users = result.scalars().all()
        
        # Also check for custom role assignments
        from app.models_db import UserRoleAssignment, CustomRole
        result = await db.execute(
            select(UserRoleAssignment).where(
                UserRoleAssignment.society_id == current_user.society_id
            )
        )
        role_assignments = result.scalars().all()
        
        # Get user IDs from role assignments
        assigned_user_ids = {assignment.user_id for assignment in role_assignments}
        
        # Get users with custom role assignments
        if assigned_user_ids:
            result = await db.execute(
                select(User).where(
                    and_(
                        User.society_id == current_user.society_id,
                        User.id.in_(assigned_user_ids)
                    )
                )
            )
            custom_role_users = result.scalars().all()
            # Combine with committee users
            all_committee_users = list(committee_users) + [u for u in custom_role_users if u not in committee_users]
        else:
            all_committee_users = list(committee_users)
        
        for user in all_committee_users:
            recipients.append({
                "id": str(user.id),
                "name": user.name,
                "email": user.email,
                "phone": user.phone_number,
                "role": user.role.value if hasattr(user.role, 'value') else str(user.role)
            })
    
    elif meeting.meeting_type == MeetingType.GENERAL_BODY:
        # For general body meetings: Get all active members
        from app.models_db import Member
        result = await db.execute(
            select(Member).where(
                and_(
                    Member.society_id == current_user.society_id,
                    Member.status == "active"  # Only active members
                )
            )
        )
        members = result.scalars().all()
        
        for member in members:
            recipients.append({
                "id": str(member.id),
                "name": member.name,
                "email": member.email,
                "phone": member.phone_number,
                "flat_number": member.flat.flat_number if member.flat else None,
                "member_type": member.member_type.value if hasattr(member.member_type, 'value') else str(member.member_type)
            })
    
    # Send notifications
    sent_count = 0
    errors = []
    
    # Prepare notice message
    society_name = "Your Society"  # Default, can be fetched from Society model
    result = await db.execute(
        select(Society).where(Society.id == current_user.society_id)
    )
    society = result.scalar_one_or_none()
    if society:
        society_name = society.name
    
    notice_message = f"""
Meeting Notice: {meeting.meeting_title}

Date: {meeting.meeting_date.strftime('%B %d, %Y')}
Venue: {meeting.venue or 'To be announced'}
"""
    
    if meeting.agenda:
        notice_message += f"\nAgenda: {meeting.agenda}\n"
    
    if notice_data.custom_message:
        notice_message += f"\n{notice_data.custom_message}\n"
    
    notice_message += f"\nPlease attend the meeting.\n\n{society_name}"
    
    # Send emails if requested
    if notice_data.send_email:
        for recipient in recipients:
            if recipient.get("email"):
                try:
                    # TODO: Implement actual email sending
                    # For now, we'll just log it
                    # In production, use aiosmtplib or email service
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.info(f"Would send email to {recipient['email']} for meeting {meeting_id}")
                    # await send_email(recipient['email'], f"Meeting Notice: {meeting.meeting_title}", notice_message)
                    sent_count += 1
                except Exception as e:
                    errors.append(f"Failed to send email to {recipient.get('email')}: {str(e)}")
    
    # Send SMS if requested (placeholder for future implementation)
    if notice_data.send_sms:
        for recipient in recipients:
            if recipient.get("phone"):
                try:
                    # TODO: Implement actual SMS sending
                    # For now, we'll just log it
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.info(f"Would send SMS to {recipient['phone']} for meeting {meeting_id}")
                    # await send_sms(recipient['phone'], notice_message)
                    sent_count += 1
                except Exception as e:
                    errors.append(f"Failed to send SMS to {recipient.get('phone')}: {str(e)}")
    
    # Update meeting with notice sent status
    meeting.notice_sent = True
    meeting.notice_sent_at = datetime.utcnow()
    meeting.notice_sent_by = int(current_user.id)
    meeting.updated_at = datetime.utcnow()
    
    await db.commit()
    
    # Get notice sender name
    from app.models_db import User
    result = await db.execute(select(User).where(User.id == int(current_user.id)))
    sender = result.scalar_one()
    
    message = f"Notice sent to {len(recipients)} recipients"
    if errors:
        message += f". {len(errors)} errors occurred."
    
    return MeetingNoticeResponse(
        meeting_id=meeting.id,
        notice_sent=True,
        recipients_count=len(recipients),
        recipients=recipients,
        sent_at=meeting.notice_sent_at,
        message=message
    )


@router.post("/meetings/{meeting_id}/attendance", response_model=List[AttendanceResponse], status_code=status.HTTP_200_OK)
async def mark_attendance(
    meeting_id: str,
    attendance_data: MarkAttendanceRequest,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark attendance for a meeting (admin only)
    """
    # Verify meeting exists
    result = await db.execute(
        select(Meeting).where(
            and_(
                Meeting.id == int(meeting_id),
                Meeting.society_id == current_user.society_id
            )
        )
    )
    meeting = result.scalar_one_or_none()
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )
    
    # Delete existing attendance records for this meeting
    await db.execute(
        delete(MeetingAttendance).where(MeetingAttendance.meeting_id == int(meeting_id))
    )
    
    # Get member details
    member_ids = {record.member_id for record in attendance_data.attendees}
    if attendance_data.attendees:
        proxy_ids = {record.proxy_holder_id for record in attendance_data.attendees if record.proxy_holder_id}
        member_ids.update(proxy_ids)
    
    result = await db.execute(
        select(Member).where(
            and_(
                Member.id.in_(member_ids),
                Member.society_id == current_user.society_id
            )
        )
    )
    members = {member.id: member for member in result.scalars().all()}
    
    # Create attendance records
    attendance_records = []
    total_present = 0
    
    for record in attendance_data.attendees:
        member = members.get(record.member_id)
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Member with ID {record.member_id} not found"
            )
        
        # Get flat number
        flat_number = None
        if member.flat_id:
            from app.models_db import Flat
            flat_result = await db.execute(select(Flat).where(Flat.id == member.flat_id))
            flat = flat_result.scalar_one_or_none()
            flat_number = flat.flat_number if flat else None
        
        # Get proxy holder name if applicable
        proxy_holder_name = None
        if record.status == "proxy" and record.proxy_holder_id:
            proxy_holder = members.get(record.proxy_holder_id)
            proxy_holder_name = proxy_holder.name if proxy_holder else None
        
        # Convert status string to enum
        status_enum_map = {
            "present": AttendanceStatus.PRESENT,
            "proxy": AttendanceStatus.PROXY,
            "absent": AttendanceStatus.ABSENT
        }
        status_enum = status_enum_map.get(record.status)
        if not status_enum:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid attendance status: {record.status}"
            )
        
        attendance = MeetingAttendance(
            meeting_id=int(meeting_id),
            society_id=current_user.society_id,
            member_id=record.member_id,
            member_name=member.name,
            member_flat=flat_number,
            status=status_enum,
            proxy_holder_id=record.proxy_holder_id,
            proxy_holder_name=proxy_holder_name,
            arrival_time=record.arrival_time,
            departure_time=record.departure_time
        )
        db.add(attendance)
        attendance_records.append(attendance)
        
        # Count present (including proxy)
        if record.status in ["present", "proxy"]:
            total_present += 1
    
    # Update meeting attendance counts
    meeting.total_members_present = total_present
    meeting.updated_at = datetime.utcnow()
    
    await db.commit()
    
    # Refresh attendance records to get IDs
    for attendance in attendance_records:
        await db.refresh(attendance)
    
    # Build response
    response_list = []
    for attendance in attendance_records:
        response_list.append(AttendanceResponse(
            id=attendance.id,
            member_id=attendance.member_id,
            member_name=attendance.member_name,
            member_flat=attendance.member_flat,
            status=attendance.status.value if hasattr(attendance.status, 'value') else str(attendance.status),
            proxy_holder_id=attendance.proxy_holder_id,
            proxy_holder_name=attendance.proxy_holder_name,
            arrival_time=attendance.arrival_time,
            departure_time=attendance.departure_time,
            created_at=attendance.created_at
        ))
    
    return response_list


@router.post("/meetings/{meeting_id}/minutes", response_model=MeetingResponse, status_code=status.HTTP_200_OK)
async def record_minutes(
    meeting_id: str,
    minutes_data: RecordMinutesRequest,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Record meeting minutes (admin only)
    """
    # Verify meeting exists
    result = await db.execute(
        select(Meeting).where(
            and_(
                Meeting.id == int(meeting_id),
                Meeting.society_id == current_user.society_id
            )
        )
    )
    meeting = result.scalar_one_or_none()
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )
    
    # Get current user name for recorded_by
    from app.models_db import User
    result = await db.execute(select(User).where(User.id == int(current_user.id)))
    user = result.scalar_one()
    
    # Update meeting with minutes
    meeting.minutes_text = minutes_data.minutes_text
    meeting.recorded_by = user.name
    meeting.recorded_at = datetime.utcnow()
    meeting.updated_at = datetime.utcnow()
    
    # Update agenda items if provided
    if minutes_data.agenda_updates:
        for update in minutes_data.agenda_updates:
            agenda_item_id = update.get("agenda_item_id")
            if agenda_item_id:
                result = await db.execute(
                    select(MeetingAgendaItem).where(
                        and_(
                            MeetingAgendaItem.id == agenda_item_id,
                            MeetingAgendaItem.meeting_id == int(meeting_id)
                        )
                    )
                )
                agenda_item = result.scalar_one_or_none()
                if agenda_item:
                    if "discussion_summary" in update:
                        agenda_item.discussion_summary = update["discussion_summary"]
                    if "status" in update:
                        status_map = {
                            "pending": AgendaItemStatus.PENDING,
                            "discussed": AgendaItemStatus.DISCUSSED,
                            "resolved": AgendaItemStatus.RESOLVED,
                            "deferred": AgendaItemStatus.DEFERRED,
                            "withdrawn": AgendaItemStatus.WITHDRAWN
                        }
                        status_enum = status_map.get(update["status"])
                        if status_enum:
                            agenda_item.status = status_enum
    
    await db.commit()
    await db.refresh(meeting)
    
    # Get creator and notice sender
    user_ids = {meeting.created_by}
    if meeting.notice_sent_by:
        user_ids.add(meeting.notice_sent_by)
    
    result = await db.execute(select(User).where(User.id.in_(user_ids)))
    users = {user.id: user for user in result.scalars().all()}
    
    creator = users.get(meeting.created_by)
    notice_sender = users.get(meeting.notice_sent_by) if meeting.notice_sent_by else None
    
    return _build_meeting_response(meeting=meeting, creator=creator, notice_sender=notice_sender)


@router.post("/meetings/{meeting_id}/resolutions", response_model=ResolutionResponse, status_code=status.HTTP_201_CREATED)
async def create_resolution(
    meeting_id: str,
    resolution_data: CreateResolutionRequest,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a resolution for a meeting (admin only)
    """
    # Verify meeting exists
    result = await db.execute(
        select(Meeting).where(
            and_(
                Meeting.id == int(meeting_id),
                Meeting.society_id == current_user.society_id
            )
        )
    )
    meeting = result.scalar_one_or_none()
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )
    
    # Get member details
    member_ids = {resolution_data.proposed_by_id, resolution_data.seconded_by_id}
    result = await db.execute(
        select(Member).where(
            and_(
                Member.id.in_(member_ids),
                Member.society_id == current_user.society_id
            )
        )
    )
    members = {member.id: member for member in result.scalars().all()}
    
    proposed_by = members.get(resolution_data.proposed_by_id)
    seconded_by = members.get(resolution_data.seconded_by_id)
    
    if not proposed_by:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Member with ID {resolution_data.proposed_by_id} not found"
        )
    if not seconded_by:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Member with ID {resolution_data.seconded_by_id} not found"
        )
    
    # Generate resolution number
    result = await db.execute(
        select(func.count(MeetingResolution.id)).where(
            and_(
                MeetingResolution.society_id == current_user.society_id,
                MeetingResolution.meeting_id == int(meeting_id)
            )
        )
    )
    count = result.scalar() or 0
    year = meeting.meeting_date.year
    resolution_number = f"RES/{year}/{count + 1:03d}"
    
    # Convert enums
    resolution_type_map = {
        "ordinary": ResolutionType.ORDINARY,
        "special": ResolutionType.SPECIAL,
        "unanimous": ResolutionType.UNANIMOUS
    }
    resolution_type_enum = resolution_type_map.get(resolution_data.resolution_type)
    
    result_map = {
        "passed": ResolutionResult.PASSED,
        "rejected": ResolutionResult.REJECTED,
        "withdrawn": ResolutionResult.WITHDRAWN
    }
    result_enum = result_map.get(resolution_data.result)
    
    if not result_enum:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid resolution result: {resolution_data.result}"
        )
    
    # Create resolution
    resolution = MeetingResolution(
        meeting_id=int(meeting_id),
        society_id=current_user.society_id,
        resolution_number=resolution_number,
        resolution_type=resolution_type_enum,
        resolution_title=resolution_data.resolution_title,
        resolution_text=resolution_data.resolution_text,
        proposed_by_id=resolution_data.proposed_by_id,
        proposed_by_name=proposed_by.name,
        seconded_by_id=resolution_data.seconded_by_id,
        seconded_by_name=seconded_by.name,
        votes_for=resolution_data.votes_for,
        votes_against=resolution_data.votes_against,
        votes_abstain=resolution_data.votes_abstain,
        result=result_enum,
        action_items=resolution_data.action_items,
        assigned_to=resolution_data.assigned_to,
        due_date=resolution_data.due_date
    )
    
    db.add(resolution)
    await db.commit()
    await db.refresh(resolution)
    
    return ResolutionResponse(
        id=resolution.id,
        resolution_number=resolution.resolution_number,
        resolution_type=resolution.resolution_type.value if resolution.resolution_type and hasattr(resolution.resolution_type, 'value') else None,
        resolution_title=resolution.resolution_title,
        resolution_text=resolution.resolution_text,
        proposed_by_id=resolution.proposed_by_id,
        proposed_by_name=resolution.proposed_by_name,
        seconded_by_id=resolution.seconded_by_id,
        seconded_by_name=resolution.seconded_by_name,
        votes_for=resolution.votes_for,
        votes_against=resolution.votes_against,
        votes_abstain=resolution.votes_abstain,
        result=resolution.result.value if hasattr(resolution.result, 'value') else str(resolution.result),
        action_items=resolution.action_items,
        assigned_to=resolution.assigned_to,
        due_date=resolution.due_date,
        implementation_status=resolution.implementation_status.value if hasattr(resolution.implementation_status, 'value') else str(resolution.implementation_status),
        created_at=resolution.created_at
    )


@router.get("/meetings/{meeting_id}/details", response_model=MeetingDetailsResponse)
async def get_meeting_details(
    meeting_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get complete meeting details including agenda items, attendance, and resolutions
    """
    # Get meeting with relationships
    result = await db.execute(
        select(Meeting)
        .options(
            selectinload(Meeting.agenda_items),
            selectinload(Meeting.attendance),
            selectinload(Meeting.resolutions)
        )
        .where(
            and_(
                Meeting.id == int(meeting_id),
                Meeting.society_id == current_user.society_id
            )
        )
    )
    meeting = result.scalar_one_or_none()
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )
    
    # Get creator and notice sender
    from app.models_db import User
    user_ids = {meeting.created_by}
    if meeting.notice_sent_by:
        user_ids.add(meeting.notice_sent_by)
    
    result = await db.execute(select(User).where(User.id.in_(user_ids)))
    users = {user.id: user for user in result.scalars().all()}
    
    creator = users.get(meeting.created_by)
    notice_sender = users.get(meeting.notice_sent_by) if meeting.notice_sent_by else None
    
    # Build meeting response
    meeting_response = _build_meeting_response(meeting=meeting, creator=creator, notice_sender=notice_sender)
    
    # Build agenda items response
    agenda_items = []
    for item in meeting.agenda_items:
        agenda_items.append(AgendaItemResponse(
            id=item.id,
            item_number=item.item_number,
            item_title=item.item_title,
            item_description=item.item_description,
            discussion_summary=item.discussion_summary,
            status=item.status.value if hasattr(item.status, 'value') else str(item.status),
            resolution_id=item.resolution_id,
            created_at=item.created_at
        ))
    
    # Build attendance response
    attendance = []
    for att in meeting.attendance:
        attendance.append(AttendanceResponse(
            id=att.id,
            member_id=att.member_id,
            member_name=att.member_name,
            member_flat=att.member_flat,
            status=att.status.value if hasattr(att.status, 'value') else str(att.status),
            proxy_holder_id=att.proxy_holder_id,
            proxy_holder_name=att.proxy_holder_name,
            arrival_time=att.arrival_time,
            departure_time=att.departure_time,
            created_at=att.created_at
        ))
    
    # Build resolutions response
    resolutions = []
    for res in meeting.resolutions:
        resolutions.append(ResolutionResponse(
            id=res.id,
            resolution_number=res.resolution_number,
            resolution_type=res.resolution_type.value if res.resolution_type and hasattr(res.resolution_type, 'value') else None,
            resolution_title=res.resolution_title,
            resolution_text=res.resolution_text,
            proposed_by_id=res.proposed_by_id,
            proposed_by_name=res.proposed_by_name,
            seconded_by_id=res.seconded_by_id,
            seconded_by_name=res.seconded_by_name,
            votes_for=res.votes_for,
            votes_against=res.votes_against,
            votes_abstain=res.votes_abstain,
            result=res.result.value if hasattr(res.result, 'value') else str(res.result),
            action_items=res.action_items,
            assigned_to=res.assigned_to,
            due_date=res.due_date,
            implementation_status=res.implementation_status.value if hasattr(res.implementation_status, 'value') else str(res.implementation_status),
            created_at=res.created_at
        ))
    
    return MeetingDetailsResponse(
        meeting=meeting_response,
        agenda_items=agenda_items,
        attendance=attendance,
        resolutions=resolutions
    )

