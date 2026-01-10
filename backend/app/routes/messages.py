"""Messages API routes - Basic implementation"""
from fastapi import APIRouter, HTTPException, Depends, status, Body
from typing import List, Optional, Literal
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from app.database import get_db
from app.models.user import UserResponse
from app.models_db import ChatRoom, Message
from app.dependencies import get_current_user, get_current_admin_user

router = APIRouter()


class ChatRoomCreate(BaseModel):
    """Model for creating a chat room"""
    name: str = Field(..., min_length=1, max_length=100)
    type: Literal["general", "maintenance", "announcements"] = "general"
    description: Optional[str] = None


class MessageCreate(BaseModel):
    """Model for creating a message"""
    text: Optional[str] = Field(None, min_length=1, max_length=2000)
    content: Optional[str] = Field(None, min_length=1, max_length=2000)
    
    def get_content(self) -> str:
        """Get content from either text or content field"""
        return self.content or self.text or ""


class MessageResponse(BaseModel):
    """Model for message response"""
    id: str
    room_id: str
    sender_id: str
    sender_name: str
    content: str
    created_at: datetime


class ChatRoomResponse(BaseModel):
    """Model for chat room response"""
    id: str
    name: str
    type: Literal["general", "maintenance", "announcements"]
    description: Optional[str] = None
    created_at: datetime
    last_message_at: Optional[datetime] = None


@router.get("/rooms", response_model=List[ChatRoomResponse])
async def list_chat_rooms(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all chat rooms for the current user's society"""
    result = await db.execute(
        select(ChatRoom)
        .where(ChatRoom.society_id == current_user.society_id)
        .order_by(ChatRoom.created_at.desc())
    )
    rooms = result.scalars().all()

    return [
        ChatRoomResponse(
            id=str(room.id),
            name=room.name,
            type=room.type.value if hasattr(room.type, 'value') else str(room.type),
            description=room.description,
            created_at=room.created_at,
            last_message_at=room.last_message_at
        )
        for room in rooms
    ]


@router.post("/rooms", response_model=ChatRoomResponse, status_code=status.HTTP_201_CREATED)
async def create_chat_room(
    room_data: ChatRoomCreate,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new chat room (admin only)"""
    new_room = ChatRoom(
        society_id=current_user.society_id,
        name=room_data.name,
        type=room_data.type,
        description=room_data.description,
        created_at=datetime.utcnow(),
        last_message_at=None
    )

    db.add(new_room)
    await db.commit()
    await db.refresh(new_room)

    return ChatRoomResponse(
        id=str(new_room.id),
        name=new_room.name,
        type=new_room.type.value if hasattr(new_room.type, 'value') else str(new_room.type),
        description=new_room.description,
        created_at=new_room.created_at,
        last_message_at=new_room.last_message_at
    )


@router.get("/rooms/{room_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    room_id: str,
    limit: int = 100,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get messages in a chat room"""
    # First verify room exists and belongs to user's society
    room_result = await db.execute(
        select(ChatRoom)
        .where(ChatRoom.id == int(room_id))
        .where(ChatRoom.society_id == current_user.society_id)
    )
    room = room_result.scalar_one_or_none()
    
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat room not found or access denied"
        )
    
    result = await db.execute(
        select(Message)
        .where(Message.room_id == int(room_id))
        .order_by(Message.created_at.asc())
        .limit(limit)
    )
    messages = result.scalars().all()

    return [
        MessageResponse(
            id=str(message.id),
            room_id=str(message.room_id),
            sender_id=str(message.sender_id),
            sender_name=message.sender_name,
            content=message.content,
            created_at=message.created_at
        )
        for message in messages
    ]


@router.post("/rooms/{room_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    room_id: str,
    message_data: MessageCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Send a message to a chat room"""
    # Get content from either text or content field
    content = message_data.get_content()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message content is required (provide 'text' or 'content' field)"
        )
    # Convert room_id to int
    try:
        room_id_int = int(room_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid room ID"
        )

    # Verify room exists and belongs to user's society
    result = await db.execute(
        select(ChatRoom)
        .where(ChatRoom.id == room_id_int)
        .where(ChatRoom.society_id == current_user.society_id)
    )
    room = result.scalar_one_or_none()

    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat room not found or access denied"
        )

    # Convert current_user.id (string) to integer for database
    try:
        sender_id_int = int(current_user.id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID"
        )

    # Create message
    new_message = Message(
        room_id=room_id_int,
        sender_id=sender_id_int,
        sender_name=current_user.name,
        content=content,
        created_at=datetime.utcnow()
    )

    db.add(new_message)

    # Update room's last message time
    room.last_message_at = datetime.utcnow()

    await db.commit()
    await db.refresh(new_message)

    return MessageResponse(
        id=str(new_message.id),
        room_id=str(new_message.room_id),
        sender_id=str(new_message.sender_id),
        sender_name=new_message.sender_name,
        content=new_message.content,
        created_at=new_message.created_at
    )


class ChatRoomUpdate(BaseModel):
    """Model for updating a chat room"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    type: Optional[Literal["general", "maintenance", "announcements"]] = None
    description: Optional[str] = None


@router.put("/rooms/{room_id}", response_model=ChatRoomResponse)
async def update_chat_room(
    room_id: str,
    room_data: ChatRoomUpdate,
    current_user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a chat room (admin only)"""
    try:
        room_id_int = int(room_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid room ID"
        )

    result = await db.execute(
        select(ChatRoom)
        .where(ChatRoom.id == room_id_int)
        .where(ChatRoom.society_id == current_user.society_id)
    )
    room = result.scalar_one_or_none()

    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat room not found"
        )

    if room_data.name is not None:
        room.name = room_data.name
    if room_data.type is not None:
        room.type = room_data.type
    if room_data.description is not None:
        room.description = room_data.description

    await db.commit()
    await db.refresh(room)

    return ChatRoomResponse(
        id=str(room.id),
        name=room.name,
        type=room.type.value if hasattr(room.type, 'value') else str(room.type),
        description=room.description,
        created_at=room.created_at,
        last_message_at=room.last_message_at
    )
