#!/bin/bash
# Curl examples for DDIA Chat API
# Default server: http://localhost:8000
# Adjust BASE_URL if your server runs on a different host/port

BASE_URL="http://localhost:8000"

echo "=== Health Check ==="
curl -X GET "${BASE_URL}/health"
echo -e "\n\n"

echo "=== 1. Create a DM Room ==="
curl -X POST "${BASE_URL}/chat/rooms" \
  -H "Content-Type: application/json" \
  -d '{
    "room_id": 1,
    "type": "DM",
    "member_user_ids": [1, 2]
  }'
echo -e "\n\n"

echo "=== 2. Create a GROUP Room ==="
curl -X POST "${BASE_URL}/chat/rooms" \
  -H "Content-Type: application/json" \
  -d '{
    "room_id": 2,
    "type": "GROUP",
    "member_user_ids": [1, 2, 3, 4]
  }'
echo -e "\n\n"

echo "=== 3. List Rooms for User 1 ==="
curl -X GET "${BASE_URL}/chat/rooms?user_id=1&limit=10"
echo -e "\n\n"

echo "=== 4. Send a Message (no mentions) ==="
curl -X POST "${BASE_URL}/chat/rooms/1/messages" \
  -H "Content-Type: application/json" \
  -d '{
    "sender_id": 1,
    "content": "Hello! This is a test message.",
    "mentioned_user_ids": []
  }'
echo -e "\n\n"

echo "=== 5. Send a Message with Mentions ==="
curl -X POST "${BASE_URL}/chat/rooms/2/messages" \
  -H "Content-Type: application/json" \
  -d '{
    "sender_id": 1,
    "content": "Hey @2 @3, can you check this out?",
    "mentioned_user_ids": [2, 3]
  }'
echo -e "\n\n"

echo "=== 6. Get Messages from Room 1 (User 1) ==="
curl -X GET "${BASE_URL}/chat/rooms/1/messages?user_id=1&limit=50"
echo -e "\n\n"

echo "=== 7. Get Messages with Pagination (before_seq) ==="
curl -X GET "${BASE_URL}/chat/rooms/1/messages?user_id=1&limit=10&before_seq=5"
echo -e "\n\n"

echo "=== 8. Mark Messages as Read ==="
curl -X POST "${BASE_URL}/chat/rooms/1/read" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 2,
    "last_read_seq": 3
  }'
echo -e "\n\n"

echo "=== 9. Search Messages in Room ==="
curl -X GET "${BASE_URL}/chat/rooms/2/search?user_id=1&q=check&limit=20"
echo -e "\n\n"

echo "=== 10. List Rooms Again (to see updated unread counts) ==="
curl -X GET "${BASE_URL}/chat/rooms?user_id=1&limit=10"
echo -e "\n\n"
