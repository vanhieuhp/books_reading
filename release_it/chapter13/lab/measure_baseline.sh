# measure_baseline.sh
#!/bin/bash
# Measure baseline steady state metrics

echo "============================================"
echo "Measuring Steady State (Baseline)"
echo "============================================"
echo ""

# Function to measure response time
measure_response() {
    local url=$1
    local label=$2

    # Measure response time (average of 5 runs)
    total=0
    for i in {1..5}; do
        # Get response time in milliseconds
        time_ms=$(curl -o /dev/null -s -w "%{time_total}" "$url" 2>/dev/null)
        time_ms=$(echo "$time_ms * 1000" | bc 2>/dev/null || echo "0")
        total=$(echo "$total + $time_ms" | bc 2>/dev/null || echo "0")
    done

    avg=$(echo "scale=2; $total / 5" | bc 2>/dev/null || echo "0")
    echo "$label: ${avg}ms"
}

echo "📊 Response Time Metrics:"
measure_response "http://localhost:8080/health" "  Health check"
measure_response "http://localhost:8080/" "  Root endpoint"
measure_response "http://localhost:8080/api/data" "  Data endpoint"

echo ""
echo "📊 Service Connectivity:"
# Check backend connectivity
if docker exec api-gateway ping -c 1 backend-service &>/dev/null; then
    echo "  ✅ Backend service: reachable"
else
    echo "  ❌ Backend service: unreachable"
fi

echo ""
echo "📊 Container Status:"
docker-compose ps

echo ""
echo "============================================"
echo "Baseline metrics recorded."
echo "============================================"
