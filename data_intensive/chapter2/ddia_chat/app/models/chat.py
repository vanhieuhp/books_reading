from sqlalchemy import (
BigInteger, Boolean, CheckConstraint, Column, DateTime, ForeignKey, Index,
Integer, String, Text, UniqueConstraint, func
)

from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import relationship
from app.models.base import Base

class ChatRoom(Base):
    __tablename__ = "chat_room"

    id = Column(BigInteger, primary_key = True)
    type = Column(String(16), nullable = False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    members = relationship("RoomMember", back_populates="room")

class RoomMember(Base):
    __tablename__ = "room_member"

    room_id = Column(BigInteger, ForeignKey("chat_room.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(BigInteger, primary_key=True)
    role = Column(String(16), nullable=False, default="member")  # member/admin
    joined_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    room = relationship("ChatRoom", back_populates="members")

    __table_args__ = (
        Index("ix_room_member_user_room", "user_id", "room_id"),
    )

class RoomSeq(Base):
    """
    Monotonic per-room sequence. This is the backbone for:
    - stable paging
    - unread_count = last_message_seq - last_read_seq
    """
    __tablename__ = "room_seq"

    room_id = Column(BigInteger, ForeignKey("chat_room.id", ondelete="CASCADE"), primary_key=True)
    last_seq = Column(BigInteger, nullable=False, default=0)

class RoomSummary(Base):
    """
    Denormalized room-level summary (NOT per-user inbox) — scales for large rooms.
    """
    __tablename__ = "room_summary"

    room_id = Column(BigInteger, ForeignKey("chat_room.id", ondelete="CASCADE"), primary_key=True)
    last_message_seq = Column(BigInteger, nullable=False, default=0)
    last_message_at = Column(DateTime(timezone=True))
    last_message_preview = Column(String(256))
    last_sender_id = Column(BigInteger)

class RoomReadState(Base):
    __tablename__ = "room_read_state"

    room_id = Column(BigInteger, ForeignKey("chat_room.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(BigInteger, primary_key=True)
    last_read_seq = Column(BigInteger, nullable=False, default=0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_read_state_user_room", "user_id", "room_id"),
    )

class Message(Base):
    __tablename__ = "message"

    id = Column(BigInteger, primary_key=True)
    room_id = Column(BigInteger, ForeignKey("chat_room.id", ondelete="CASCADE"), nullable=False)
    sender_id = Column(BigInteger, nullable=False)

    # monotonic sequence per room
    seq = Column(BigInteger, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    content = Column(Text, nullable=False)

    edited_at = Column(DateTime(timezone=True))
    deleted = Column(Boolean, nullable=False, default=False)

    # Postgres full-text search vector (maintained via trigger)
    search_vector = Column(TSVECTOR)

    __table_args__ = (
        UniqueConstraint("room_id", "seq", name="uq_message_room_seq"),
        Index("ix_message_room_seq_desc", "room_id", "seq"),
        Index("ix_message_search_vector_gin", "search_vector", postgresql_using="gin"),
        CheckConstraint("seq > 0", name="ck_message_seq_positive"),
    )

class MessageMention(Base):
    __tablename__ = "message_mention"

    id = Column(BigInteger, primary_key=True)
    message_id = Column(BigInteger, ForeignKey("message.id", ondelete="CASCADE"), nullable=False)
    room_id = Column(BigInteger, nullable=False)
    mentioned_user_id = Column(BigInteger, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_mention_user_created", "mentioned_user_id", "created_at"),
        Index("ix_mention_room_message", "room_id", "message_id"),
    )