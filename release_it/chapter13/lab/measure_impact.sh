# measure_impact.sh
#!/bin/bash
# Measure chaos impact

echo "============================================"
echo "📊 Measuring Chaos Impact"
echo "============================================"
echo ""

echo "1. Error Rate During Chaos:"
ERRORS=0
TOTAL=20

for i in $(seq 1 $TOTAL); do
    http_code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/api/data 2>/dev/null)
    if [ "$http_code" != "200" ]; then
        ((ERRORS++))
    fi
done

error_pct=$(echo "scale=2; ($ERRORS * 100) / $TOTAL" | bc)
echo "   Total requests: $TOTAL"
echo "   Failed requests: $ERRORS"
echo "   Error rate: ${error_pct}%"

echo ""
echo "2. Latency During Chaos:"

# Measure latency
for i in {1..5}; do
    time_ms=$(curl -o /dev/null -s -w "%{time_total}" http://localhost:8080/api/data 2>/dev/null)
    time_ms=$(echo "$time_ms * 1000" | bc 2>/dev/null || echo "0")
    echo "   Request $i: ${time_ms}ms"
done

echo ""
echo "3. Container Logs During Chaos:"
echo "   --- API Gateway ---"
docker-compose logs --tail=5 api-gateway 2>/dev/null || echo "   (no logs available)"

echo ""
echo "4. Current Container Status:"
docker-compose ps

echo ""
echo "============================================"
echo "Impact measurement complete."
echo "============================================"
