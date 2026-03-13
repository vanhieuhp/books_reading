# chaos_network_partition.sh
#!/bin/bash
# Inject network partition chaos

set -e

CONTAINER_NAME="api-gateway"
BACKEND_NAME="backend-service"

echo "============================================"
echo "💥 Chaos: Network Partition Injection"
echo "============================================"
echo ""

echo "Step 1: Confirm baseline connectivity..."
docker exec $CONTAINER_NAME ping -c 1 $BACKEND_NAME &>/dev/null && echo "  ✅ Backend reachable" || echo "  ❌ Backend unreachable"

echo ""
echo "Step 2: Injecting network partition..."
# Block traffic to backend by adding invalid entry to /etc/hosts
docker exec $CONTAINER_NAME sh -c "echo '127.0.0.1 $BACKEND_NAME' >> /etc/hosts"
echo "  ✅ Added /etc/hosts entry to block $BACKEND_NAME"

echo ""
echo "Step 3: Testing connectivity during chaos..."

for i in {1..5}; do
    echo "  Attempt $i:"
    if docker exec $CONTAINER_NAME ping -c 1 $BACKEND_NAME &>/dev/null; then
        echo "    → Backend: REACHABLE (unexpected)"
    else
        echo "    → Backend: UNREACHABLE (expected)"
    fi
    sleep 1
done

echo ""
echo "Step 4: Impact on API requests..."

# Test API response during partition
for i in {1..3}; do
    response=$(curl -s -w "\n%{http_code}" http://localhost:8080/api/data 2>/dev/null)
    http_code=$(echo "$response" | tail -1)
    body=$(echo "$response" | head -n -1)
    echo "  Request $i: HTTP $http_code"
    sleep 1
done

echo ""
echo "============================================"
echo "⚠️  Network partition is ACTIVE"
echo "To clean up: docker-compose restart api-gateway"
echo "============================================"
