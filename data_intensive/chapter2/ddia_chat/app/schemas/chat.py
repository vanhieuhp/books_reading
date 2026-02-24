from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

class CreateRoomIn(BaseModel):
    room_id: int
    type: str = Field(pattern="^(DM|GROUP)$")
    member_user_ids: List[int]

class SendMessageIn(BaseModel):
    sender_id: int
    content: str
    mentioned_user_ids: List[int] = []  # keep explicit for practice

class MessageOut(BaseModel):
    id: int
    room_id: int
    sender_id: int
    seq: int
    created_at: datetime
    content: str

class RoomListItemOut(BaseModel):
    room_id: int
    last_message_at: Optional[datetime]
    last_message_preview: Optional[str]
    last_sender_id: Optional[int]
    last_message_seq: int
    last_read_seq: int
    unread_count: int

class MarkReadIn(BaseModel):
    user_id: int
    last_read_seq: int

class SearchOut(BaseModel):
    messages: List[MessageOut]