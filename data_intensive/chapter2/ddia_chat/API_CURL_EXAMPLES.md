# API Curl Examples

Quick reference for testing the DDIA Chat API endpoints.

**Base URL:** `http://localhost:8000` (adjust if your server runs elsewhere)

---

## Health Check

```bash
curl -X GET "http://localhost:8000/health"
```

---

## 1. Create a Chat Room

### Create a DM (Direct Message) Room
```bash
curl -X POST "http://localhost:8000/chat/rooms" \
  -H "Content-Type: application/json" \
  -d '{
    "room_id": 1,
    "type": "DM",
    "member_user_ids": [1, 2]
  }'
```

### Create a GROUP Room
```bash
curl -X POST "http://localhost:8000/chat/rooms" \
  -H "Content-Type: application/json" \
  -d '{
    "room_id": 2,
    "type": "GROUP",
    "member_user_ids": [1, 2, 3, 4, 5]
  }'
```

**Note:** `room_id` must be unique. `type` must be either `"DM"` or `"GROUP"`.

---

## 2. List Rooms for a User

```bash
curl -X GET "http://localhost:8000/chat/rooms?user_id=1&limit=50"
```

**Query Parameters:**
- `user_id` (required): The user ID to get rooms for
- `limit` (optional): Number of rooms to return (1-200, default: 50)

---

## 3. Send a Message

### Simple Message (no mentions)
```bash
curl -X POST "http://localhost:8000/chat/rooms/1/messages" \
  -H "Content-Type: application/json" \
  -d '{
    "sender_id": 1,
    "content": "Hello! This is a test message.",
    "mentioned_user_ids": []
  }'
```

### Message with Mentions
```bash
curl -X POST "http://localhost:8000/chat/rooms/2/messages" \
  -H "Content-Type: application/json" \
  -d '{
    "sender_id": 1,
    "content": "Hey @2 @3, can you check this out?",
    "mentioned_user_ids": [2, 3]
  }'
```

**Path Parameters:**
- `room_id`: The room ID to send the message to

**Body:**
- `sender_id`: User ID of the sender (must be a room member)
- `content`: Message text
- `mentioned_user_ids`: Array of user IDs mentioned in the message

---

## 4. Get Messages from a Room

### Get Latest Messages
```bash
curl -X GET "http://localhost:8000/chat/rooms/1/messages?user_id=1&limit=50"
```

### Get Messages with Pagination (before a specific sequence)
```bash
curl -X GET "http://localhost:8000/chat/rooms/1/messages?user_id=1&limit=10&before_seq=5"
```

**Path Parameters:**
- `room_id`: The room ID

**Query Parameters:**
- `user_id` (required): User ID (must be a room member)
- `limit` (optional): Number of messages to return (1-200, default: 50)
- `before_seq` (optional): Get messages before this sequence number (for pagination)

---

## 5. Mark Messages as Read

```bash
curl -X POST "http://localhost:8000/chat/rooms/1/read" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 2,
    "last_read_seq": 5
  }'
```

**Path Parameters:**
- `room_id`: The room ID

**Body:**
- `user_id`: User ID (must be a room member)
- `last_read_seq`: The sequence number up to which the user has read

---

## 6. Search Messages in a Room

```bash
curl -X GET "http://localhost:8000/chat/rooms/2/search?user_id=1&q=hello&limit=20"
```

**Path Parameters:**
- `room_id`: The room ID

**Query Parameters:**
- `user_id` (required): User ID (must be a room member)
- `q` (required): Search query (1-100 characters)
- `limit` (optional): Number of results to return (1-100, default: 20)

---

## Example Workflow

```bash
# 1. Create a room
curl -X POST "http://localhost:8000/chat/rooms" \
  -H "Content-Type: application/json" \
  -d '{"room_id": 1, "type": "GROUP", "member_user_ids": [1, 2, 3]}'

# 2. Send a few messages
curl -X POST "http://localhost:8000/chat/rooms/1/messages" \
  -H "Content-Type: application/json" \
  -d '{"sender_id": 1, "content": "First message", "mentioned_user_ids": []}'

curl -X POST "http://localhost:8000/chat/rooms/1/messages" \
  -H "Content-Type: application/json" \
  -d '{"sender_id": 2, "content": "Second message", "mentioned_user_ids": [1]}'

# 3. List rooms for user 1
curl -X GET "http://localhost:8000/chat/rooms?user_id=1"

# 4. Get messages
curl -X GET "http://localhost:8000/chat/rooms/1/messages?user_id=1"

# 5. Mark as read
curl -X POST "http://localhost:8000/chat/rooms/1/read" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "last_read_seq": 2}'

# 6. Search
curl -X GET "http://localhost:8000/chat/rooms/1/search?user_id=1&q=message"
```

---

## Tips

- Make sure your FastAPI server is running: `uvicorn app.main:app --reload`
- All endpoints return JSON
- Error responses include details in the `detail` field
- User IDs and room IDs are integers (BigInteger in the database)
- The `sender_id` must be a member of the room for sending messages
- Sequence numbers start at 1 and increment per room
