"""Meeting and Meeting Minutes models - Comprehensive Meeting Management System"""
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime, date


# ============ REQUEST MODELS ============

class AgendaItemCreate(BaseModel):
    """Model for creating an agenda item"""
    item_number: int = Field(..., ge=1, description="Agenda item number")
    item_title: str = Field(..., min_length=1, max_length=200, description="Title of agenda item")
    item_description: Optional[str] = Field(None, description="Description of agenda item")


class MeetingCreate(BaseModel):
    """Model for creating a meeting"""
    meeting_type: Literal["MC", "AGM", "EGM", "SGM", "committee", "general_body"] = Field(..., description="Type of meeting")
    meeting_date: date = Field(..., description="Date of the meeting")
    meeting_time: Optional[str] = Field(None, max_length=20, description="Time of meeting (e.g., '10:00 AM')")
    meeting_title: str = Field(..., min_length=1, max_length=200, description="Title of the meeting")
    venue: Optional[str] = Field(None, max_length=200, description="Meeting venue/location")
    agenda_items: List[AgendaItemCreate] = Field(default_factory=list, description="List of agenda items")
    notice_sent_to: Literal["all_members", "mc_only"] = Field("all_members", description="Who to send notice to")
    # Legacy fields for backward compatibility
    agenda: Optional[str] = Field(None, description="Legacy: Meeting agenda (use agenda_items instead)")
    attendees_count: Optional[int] = Field(None, ge=0, description="Legacy: Number of attendees")
    chaired_by: Optional[str] = Field(None, max_length=100, description="Name of person who chaired the meeting")


class MeetingUpdate(BaseModel):
    """Model for updating a meeting"""
    meeting_date: Optional[date] = None
    meeting_time: Optional[str] = Field(None, max_length=20)
    meeting_title: Optional[str] = Field(None, min_length=1, max_length=200)
    venue: Optional[str] = Field(None, max_length=200)
    status: Optional[Literal["scheduled", "completed", "cancelled"]] = None
    agenda: Optional[str] = None
    attendees_count: Optional[int] = Field(None, ge=0)
    chaired_by: Optional[str] = Field(None, max_length=100)
    total_members_eligible: Optional[int] = Field(None, ge=0)
    quorum_required: Optional[int] = Field(None, ge=0)
    quorum_met: Optional[bool] = None


class RecordMinutesRequest(BaseModel):
    """Request to record meeting minutes"""
    minutes_text: str = Field(..., description="Full text of meeting minutes")
    agenda_updates: Optional[List[dict]] = Field(default_factory=list, description="Updates to agenda items")


class AttendanceRecord(BaseModel):
    """Model for a single attendance record"""
    member_id: int = Field(..., description="Member ID")
    status: Literal["present", "proxy", "absent"] = Field(..., description="Attendance status")
    proxy_holder_id: Optional[int] = Field(None, description="ID of proxy holder if status is proxy")
    arrival_time: Optional[str] = Field(None, max_length=20, description="Arrival time")
    departure_time: Optional[str] = Field(None, max_length=20, description="Departure time")


class MarkAttendanceRequest(BaseModel):
    """Request to mark attendance"""
    attendees: List[AttendanceRecord] = Field(..., description="List of attendance records")


class CreateResolutionRequest(BaseModel):
    """Request to create a resolution"""
    resolution_title: str = Field(..., min_length=1, max_length=200, description="Title of resolution")
    resolution_text: str = Field(..., description="Full text of resolution")
    resolution_type: Literal["ordinary", "special", "unanimous"] = Field("ordinary", description="Type of resolution")
    proposed_by_id: int = Field(..., description="ID of member who proposed")
    seconded_by_id: int = Field(..., description="ID of member who seconded")
    votes_for: int = Field(..., ge=0, description="Number of votes for")
    votes_against: int = Field(..., ge=0, description="Number of votes against")
    votes_abstain: int = Field(0, ge=0, description="Number of abstentions")
    result: Literal["passed", "rejected", "withdrawn"] = Field(..., description="Result of resolution")
    action_items: Optional[str] = Field(None, description="Action items from resolution")
    assigned_to: Optional[str] = Field(None, max_length=100, description="Person assigned to implement")
    due_date: Optional[date] = Field(None, description="Due date for implementation")


class MeetingNoticeRequest(BaseModel):
    """Model for sending meeting notice"""
    send_email: bool = Field(True, description="Send email notification")
    send_sms: bool = Field(False, description="Send SMS notification (if configured)")
    custom_message: Optional[str] = Field(None, description="Optional custom message to include in notice")


# ============ RESPONSE MODELS ============

class AgendaItemResponse(BaseModel):
    """Model for agenda item response"""
    id: int
    item_number: int
    item_title: str
    item_description: Optional[str] = None
    discussion_summary: Optional[str] = None
    status: str
    resolution_id: Optional[int] = None
    created_at: datetime


class AttendanceResponse(BaseModel):
    """Model for attendance response"""
    id: int
    member_id: int
    member_name: str
    member_flat: Optional[str] = None
    status: str
    proxy_holder_id: Optional[int] = None
    proxy_holder_name: Optional[str] = None
    arrival_time: Optional[str] = None
    departure_time: Optional[str] = None
    created_at: datetime


class ResolutionResponse(BaseModel):
    """Model for resolution response"""
    id: int
    resolution_number: str
    resolution_type: Optional[str] = None
    resolution_title: str
    resolution_text: str
    proposed_by_id: Optional[int] = None
    proposed_by_name: str
    seconded_by_id: Optional[int] = None
    seconded_by_name: str
    votes_for: int
    votes_against: int
    votes_abstain: int
    result: str
    action_items: Optional[str] = None
    assigned_to: Optional[str] = None
    due_date: Optional[date] = None
    implementation_status: str
    created_at: datetime


class MeetingResponse(BaseModel):
    """Model for meeting response"""
    id: int
    society_id: int
    meeting_type: str
    meeting_number: Optional[str] = None
    meeting_date: date
    meeting_time: Optional[str] = None
    meeting_title: str
    venue: Optional[str] = None
    status: str
    total_members_eligible: Optional[int] = None
    total_members_present: int
    quorum_required: Optional[int] = None
    quorum_met: bool
    minutes_text: Optional[str] = None
    minutes_approved: bool
    minutes_approved_date: Optional[date] = None
    recorded_by: Optional[str] = None
    recorded_at: Optional[datetime] = None
    notice_sent: bool
    notice_sent_at: Optional[datetime] = None
    notice_sent_to: Optional[str] = None
    notice_sent_by: Optional[int] = None
    notice_sent_by_name: Optional[str] = None
    created_by: int
    created_by_name: str
    created_at: datetime
    updated_at: datetime
    # Legacy fields
    agenda: Optional[str] = None
    attendees_count: Optional[int] = None
    chaired_by: Optional[str] = None


class MeetingDetailsResponse(BaseModel):
    """Complete meeting details including agenda, attendance, and resolutions"""
    meeting: MeetingResponse
    agenda_items: List[AgendaItemResponse] = Field(default_factory=list)
    attendance: List[AttendanceResponse] = Field(default_factory=list)
    resolutions: List[ResolutionResponse] = Field(default_factory=list)


class MeetingNoticeResponse(BaseModel):
    """Model for meeting notice response"""
    meeting_id: int
    notice_sent: bool
    recipients_count: int
    recipients: List[dict]  # List of recipients with their contact info
    sent_at: datetime
    message: str
