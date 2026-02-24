#!/usr/bin/env python3
"""
Data generation script for the chat application.

Generates realistic test data including:
- Chat rooms (DM and GROUP types)
- Room members
- Messages with proper sequences
- Mentions
- Read states
- Room summaries

Usage:
    python generate_data.py --num-users 100 --num-rooms 50 --messages-per-room 20
"""

import argparse
import random
import sys
from datetime import datetime, timedelta
from typing import List

from faker import Faker
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.models.chat import (
    ChatRoom,
    RoomMember,
    RoomSeq,
    RoomSummary,
    RoomReadState,
    Message,
    MessageMention,
)

fake = Faker()


def generate_rooms(
    db: Session,
    num_rooms: int,
    num_users: int,
    dm_ratio: float = 0.3,
) -> List[int]:
    """Generate chat rooms with members."""
    room_ids = []
    user_ids = list(range(1, num_users + 1))
    
    print(f"Generating {num_rooms} rooms...")
    
    for i in range(num_rooms):
        room_id = i + 1
        room_type = "DM" if random.random() < dm_ratio else "GROUP"
        
        # Create room
        room = ChatRoom(id=room_id, type=room_type)
        db.add(room)
        
        # Initialize seq and summary
        db.add(RoomSeq(room_id=room_id, last_seq=0))
        db.add(RoomSummary(room_id=room_id, last_message_seq=0))
        
        # Add members
        if room_type == "DM":
            # DM: exactly 2 members
            members = random.sample(user_ids, 2)
        else:
            # GROUP: 3-10 members
            num_members = random.randint(3, min(10, num_users))
            members = random.sample(user_ids, num_members)
        
        for user_id in members:
            role = "admin" if user_id == members[0] else "member"
            db.add(RoomMember(room_id=room_id, user_id=user_id, role=role))
            db.add(RoomReadState(room_id=room_id, user_id=user_id, last_read_seq=0))
        
        room_ids.append(room_id)
        
        if (i + 1) % 10 == 0:
            print(f"  Created {i + 1}/{num_rooms} rooms...")
    
    db.commit()
    print(f"✓ Created {num_rooms} rooms")
    return room_ids


def generate_messages(
    db: Session,
    room_ids: List[int],
    messages_per_room: int,
    mention_probability: float = 0.15,
) -> None:
    """Generate messages for rooms with proper sequences."""
    total_messages = len(room_ids) * messages_per_room
    print(f"Generating ~{total_messages} messages...")
    
    message_count = 0
    
    for room_id in room_ids:
        # Get room members
        stmt = select(RoomMember.user_id).where(RoomMember.room_id == room_id)
        members = [row[0] for row in db.execute(stmt).all()]
        
        if not members:
            continue
        
        # Get current sequence
        seq_stmt = select(RoomSeq.last_seq).where(RoomSeq.room_id == room_id)
        current_seq = db.execute(seq_stmt).scalar_one() or 0
        
        # Generate messages over a time period (last 30 days)
        base_time = datetime.now() - timedelta(days=30)
        
        for i in range(messages_per_room):
            # Increment sequence
            current_seq += 1
            
            # Random time within the period
            time_offset = random.uniform(0, 30 * 24 * 3600)  # seconds
            created_at = base_time + timedelta(seconds=time_offset)
            
            # Random sender from members
            sender_id = random.choice(members)
            
            # Generate message content
            content = fake.text(max_nb_chars=random.randint(10, 500))
            # Sometimes add mentions in content
            if random.random() < mention_probability and len(members) > 1:
                mentioned = random.sample([m for m in members if m != sender_id], 
                                         min(2, len(members) - 1))
                mentions_text = " ".join([f"@{uid}" for uid in mentioned])
                content = f"{content} {mentions_text}"
            
            # Create message
            msg = Message(
                room_id=room_id,
                sender_id=sender_id,
                seq=current_seq,
                content=content,
                created_at=created_at,
            )
            db.add(msg)
            db.flush()  # Get msg.id
            
            # Add mentions if any
            if "@" in content:
                # Extract mentioned user IDs from content
                mentioned_ids = []
                for member_id in members:
                    if f"@{member_id}" in content:
                        mentioned_ids.append(member_id)
                
                for mentioned_id in mentioned_ids:
                    db.add(MessageMention(
                        message_id=msg.id,
                        room_id=room_id,
                        mentioned_user_id=mentioned_id,
                        created_at=created_at,
                    ))
            
            # Update room sequence
            update_seq = (
                update(RoomSeq)
                .where(RoomSeq.room_id == room_id)
                .values(last_seq=current_seq)
            )
            db.execute(update_seq)
            
            # Update room summary (last message)
            preview = content.strip().replace("\n", " ")[:256]
            update_summary = (
                update(RoomSummary)
                .where(RoomSummary.room_id == room_id)
                .values(
                    last_message_seq=current_seq,
                    last_message_at=created_at,
                    last_message_preview=preview,
                    last_sender_id=sender_id,
                )
            )
            db.execute(update_summary)
            
            message_count += 1
            
            if message_count % 100 == 0:
                print(f"  Generated {message_count} messages...")
        
        # Commit per room for better performance
        db.commit()
    
    print(f"✓ Generated {message_count} messages")


def generate_read_states(
    db: Session,
    room_ids: List[int],
    read_probability: float = 0.7,
) -> None:
    """Generate realistic read states (some users haven't read all messages)."""
    print("Generating read states...")
    
    read_count = 0
    
    for room_id in room_ids:
        # Get room members and last message seq
        stmt = (
            select(RoomMember.user_id, RoomSummary.last_message_seq)
            .join(RoomSummary, RoomSummary.room_id == RoomMember.room_id)
            .where(RoomMember.room_id == room_id)
        )
        results = db.execute(stmt).all()
        
        for user_id, last_seq in results:
            if last_seq == 0:
                continue
            
            # Some users haven't read all messages
            if random.random() < read_probability:
                # Read up to a random point (0 to last_seq)
                read_seq = random.randint(0, last_seq)
            else:
                # Unread: read up to some point before last
                if last_seq > 10:
                    read_seq = random.randint(0, max(0, last_seq - random.randint(1, 10)))
                else:
                    read_seq = 0
            
            # Update read state
            update_read = (
                update(RoomReadState)
                .where(
                    RoomReadState.room_id == room_id,
                    RoomReadState.user_id == user_id,
                )
                .values(last_read_seq=read_seq)
            )
            db.execute(update_read)
            read_count += 1
    
    db.commit()
    print(f"✓ Updated {read_count} read states")


def main():
    parser = argparse.ArgumentParser(description="Generate test data for chat application")
    parser.add_argument(
        "--num-users",
        type=int,
        default=50,
        help="Number of users to generate (default: 50)",
    )
    parser.add_argument(
        "--num-rooms",
        type=int,
        default=20,
        help="Number of chat rooms to generate (default: 20)",
    )
    parser.add_argument(
        "--messages-per-room",
        type=int,
        default=10,
        help="Average number of messages per room (default: 10)",
    )
    parser.add_argument(
        "--dm-ratio",
        type=float,
        default=0.3,
        help="Ratio of DM rooms vs GROUP rooms (default: 0.3)",
    )
    parser.add_argument(
        "--mention-probability",
        type=float,
        default=0.15,
        help="Probability of a message containing mentions (default: 0.15)",
    )
    parser.add_argument(
        "--read-probability",
        type=float,
        default=0.7,
        help="Probability that users have read messages (default: 0.7)",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing data before generating (WARNING: deletes all data)",
    )
    
    args = parser.parse_args()
    
    db = SessionLocal()
    
    try:
        if args.clear:
            print("⚠️  WARNING: Clearing all existing data...")
            response = input("Are you sure? Type 'yes' to continue: ")
            if response.lower() != "yes":
                print("Cancelled.")
                return
            
            # Delete in reverse order of dependencies
            db.execute("DELETE FROM message_mention")
            db.execute("DELETE FROM message")
            db.execute("DELETE FROM room_read_state")
            db.execute("DELETE FROM room_summary")
            db.execute("DELETE FROM room_seq")
            db.execute("DELETE FROM room_member")
            db.execute("DELETE FROM chat_room")
            db.commit()
            print("✓ Cleared existing data")
        
        # Generate data
        room_ids = generate_rooms(
            db,
            args.num_rooms,
            args.num_users,
            args.dm_ratio,
        )
        
        generate_messages(
            db,
            room_ids,
            args.messages_per_room,
            args.mention_probability,
        )
        
        generate_read_states(
            db,
            room_ids,
            args.read_probability,
        )
        
        print("\n✅ Data generation complete!")
        print(f"   Users: {args.num_users}")
        print(f"   Rooms: {len(room_ids)}")
        print(f"   Messages: ~{len(room_ids) * args.messages_per_room}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}", file=sys.stderr)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
