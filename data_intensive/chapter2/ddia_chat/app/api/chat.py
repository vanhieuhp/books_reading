from sqlalchemy import select, update, func, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_db
from app.models.chat import (
    ChatRoom, RoomMember, RoomSeq, RoomSummary, RoomReadState,
    Message, MessageMention
)

from app.schemas.chat import (
    CreateRoomIn, SendMessageIn, MessageOut,
    RoomListItemOut, MarkReadIn, SearchOut
)

router = APIRouter(prefix="/chat", tags=["chat"])

def ensure_member(db: Session, room_id: int, user_id: int) -> None:
    q = select(RoomMember).where(RoomMember.room_id == room_id, RoomMember.user_id == user_id)
    if db.execute(q).scalar_one_or_none() is None:
        raise HTTPException(status_code=403, detail="Not a room member")

@router.post("/rooms")
def create_room(payload: CreateRoomIn, db: Session = Depends(get_db)):
    room = ChatRoom(id=payload.room_id, type=payload.type)
    db.add(room)

    # init seq + summary
    db.add(RoomSeq(room_id=payload.room_id, last_seq=0))
    db.add(RoomSummary(room_id=payload.room_id, last_message_seq=0))

    for uid in payload.member_user_ids:
        db.add(RoomMember(room_id=payload.room_id, user_id=uid, role="member"))
        db.add(RoomReadState(room_id=payload.room_id, user_id=uid, last_read_seq=0))

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Room already exists or invalid members")
    return {"room_id": payload.room_id}

@router.get("/rooms", response_model=list[RoomListItemOut])
def list_rooms(
    user_id: int = Query(...),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    # Large-room friendly: join membership + room_summary + read_state, no message scans.
    stmt = (
        select(
            RoomMember.room_id,
            RoomSummary.last_message_at,
            RoomSummary.last_message_preview,
            RoomSummary.last_sender_id,
            RoomSummary.last_message_seq,
            func.coalesce(RoomReadState.last_read_seq, 0).label("last_read_seq"),
            func.greatest(
                RoomSummary.last_message_seq - func.coalesce(RoomReadState.last_read_seq, 0),
                0
            ).label("unread_count"),
        ).join(RoomSummary, RoomSummary.room_id == RoomMember.room_id)
        .outerjoin(
            RoomReadState,
            (RoomReadState.room_id == RoomMember.room_id) & (RoomReadState.user_id == user_id),
        )
        .where(RoomMember.user_id == user_id)
        .order_by(RoomSummary.last_message_at.desc().nullslast())
        .limit(limit)
    )

    rows = db.execute(stmt).all()

    return [
        RoomListItemOut(
            room_id=r.room_id,
            last_message_at=r.last_message_at,
            last_message_preview=r.last_message_preview,
            last_sender_id=r.last_sender_id,
            last_message_seq=r.last_message_seq or 0,
            last_read_seq=r.last_read_seq or 0,
            unread_count=r.unread_count or 0,
        )
        for r in rows
    ]


@router.get("/rooms/{room_id}/messages", response_model=list[MessageOut])
def get_last_messages(
    room_id: int,
    user_id: int = Query(...),
    limit: int = Query(50, ge=1, le=200),
    before_seq: int | None = Query(None, ge=1),
    db: Session = Depends(get_db),
):
    ensure_member(db, room_id, user_id)

    stmt = select(Message).where(Message.room_id == room_id, Message.deleted == False)
    if before_seq is not None:
        stmt = stmt.where(Message.seq < before_seq)

    stmt = stmt.order_by(Message.seq.desc()).limit(limit)
    msgs = db.execute(stmt).scalars().all()
    return [
        MessageOut(
            id=m.id, room_id=m.room_id, sender_id=m.sender_id,
            seq=m.seq, created_at=m.created_at, content=m.content
        )
        for m in msgs
    ]


@router.post("/rooms/{room_id}/messages", response_model=MessageOut)
def send_message(room_id: int, payload: SendMessageIn, db: Session = Depends(get_db)):
    # Sender must be member
    ensure_member(db, room_id, payload.sender_id)

    # Transaction:
    # 1) increment seq atomically
    # 2) insert message
    # 3) update room_summary once
    # 4) insert mentions (optional)

    try:
        # lock row & increment last_seq
        seq_stmt = (
            update(RoomSeq)
            .where(RoomSeq.room_id == room_id)
            .values(last_seq=RoomSeq.last_seq + 1)
            .returning(RoomSeq.last_seq)
        )
        new_seq = db.execute(seq_stmt).scalar_one()

        msg = Message(
            room_id=room_id,
            sender_id=payload.sender_id,
            seq=new_seq,
            content=payload.content,
        )
        db.add(msg)
        db.flush()  # to get msg.id

        preview = payload.content.strip().replace("\n", " ")
        preview = preview[:256]

        sum_stmt = (
            update(RoomSummary)
            .where(RoomSummary.room_id == room_id)
            .values(
                last_message_seq=new_seq,
                last_message_at=func.now(),
                last_message_preview=preview,
                last_sender_id=payload.sender_id,
            )
        )
        db.execute(sum_stmt)

        # Mentions: explicit list for practice
        for uid in set(payload.mentioned_user_ids):
            db.add(MessageMention(message_id=msg.id, room_id=room_id, mentioned_user_id=uid))

        db.commit()

        db.refresh(msg)
        return MessageOut(
            id=msg.id, room_id=msg.room_id, sender_id=msg.sender_id,
            seq=msg.seq, created_at=msg.created_at, content=msg.content
        )

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Sequence conflict or invalid room")

@router.post("/rooms/{room_id}/read")
def mark_read(room_id: int, payload: MarkReadIn, db: Session = Depends(get_db)):
    ensure_member(db, room_id, payload.user_id)

    # Upsert read state
    # For simplicity in SQLAlchemy: try update, if 0 rows -> insert
    upd = (
        update(RoomReadState)
        .where(RoomReadState.room_id == room_id, RoomReadState.user_id == payload.user_id)
        .values(last_read_seq=payload.last_read_seq)
    )
    res = db.execute(upd)
    if res.rowcount == 0:
        db.add(RoomReadState(room_id=room_id, user_id=payload.user_id, last_read_seq=payload.last_read_seq))

    db.commit()
    return {"ok": True}

@router.get("/rooms/{room_id}/search", response_model=SearchOut)
def search_messages(
    room_id: int,
    user_id: int = Query(...),
    q: str = Query(..., min_length=1, max_length=100),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    ensure_member(db, room_id, user_id)

    # Postgres full-text search using plainto_tsquery
    # ORDER BY ts_rank for better results
    ts_query = func.plainto_tsquery("simple", q)
    stmt = (
        select(Message)
        .where(
            Message.room_id == room_id,
            Message.deleted == False,
            Message.search_vector.op("@@")(ts_query),
        )
        .order_by(func.ts_rank(Message.search_vector, ts_query).desc(), Message.seq.desc())
        .limit(limit)
    )

    msgs = db.execute(stmt).scalars().all()
    return SearchOut(
        messages=[
            MessageOut(
                id=m.id, room_id=m.room_id, sender_id=m.sender_id,
                seq=m.seq, created_at=m.created_at, content=m.content
            )
            for m in msgs
        ]
    )
