# 📘 Chapter 11: Transparency — Code Lab

## 🧪 Lab: Building an Observable Microservice

### 🎯 Goal
Build a Go HTTP service with production-grade observability: structured logging, Prometheus metrics (RED method), health checks, and correlation ID propagation.

### ⏱ Time
~25 minutes

### 🛠 Requirements
- Go 1.21+ installed
- Docker & Docker Compose (for running Prometheus/Grafana)
- Basic familiarity with HTTP handlers

---

## Step 1: Setup the Project

```bash
# Create project directory
mkdir -p observability-lab && cd observability-lab
go mod init observability-lab
```

### Create docker-compose.yml for metrics infrastructure:

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - ./grafana-datasources.yml:/etc/grafana/provisioning/datasources/datasources.yml
```

### Create prometheus.yml:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'observability-lab'
    static_configs:
      - targets: ['host.docker.internal:8080']
```

---

## Step 2: Implement the Observable Service

Create `main.go`:

```go
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"math/rand"
	"net/http"
	"os"
	"os/signal"
	"sync/atomic"
	"syscall"
	"time"

	"github.com/google/uuid"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

// =============================================================================
// STRUCTURED LOGGING
// =============================================================================

type LogEntry struct {
	Timestamp   string                 `json:"timestamp"`
	Level       string                 `json:"level"`
	Event       string                 `json:"event"`
	Correlation string                 `json:"correlation,omitempty"`
	Message     string                 `json:"message"`
	Metadata    map[string]interface{} `json:"metadata,omitempty"`
}

type Logger struct{}

func (l *Logger) Log(level, event, message string, metadata map[string]interface{}) {
	entry := LogEntry{
		Timestamp:   time.Now().UTC().Format(time.RFC3339Nano),
		Level:       level,
		Event:       event,
		Correlation: getCorrelation(),
		Message:     message,
		Metadata:    metadata,
	}

	data, _ := json.Marshal(entry)
	fmt.Println(string(data))
}

// Context key for correlation ID
type contextKey string

const correlationKey contextKey = "correlation"

// getCorrelation extracts correlation from context or generates new one
func getCorrelation() string {
	// Simplified for demo - in production, extract from context
	return uuid.New().String()
}

var logger = &Logger{}

// =============================================================================
// PROMETHEUS METRICS (RED METHOD)
// =============================================================================

var (
	httpRequestsTotal = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "http_requests_total",
			Help: "Total HTTP requests",
		},
		[]string{"method", "path", "status"},
	)

	httpRequestDuration = prometheus.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "http_request_duration_seconds",
			Help:    "HTTP request latency",
			Buckets: []float64{0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1},
		},
		[]string{"method", "path"},
	)

	httpRequestsInFlight = prometheus.NewGauge(
		prometheus.GaugeOpts{
			Name: "http_requests_in_flight",
			Help: "Requests being processed",
		},
	)

	// Business metrics
	ordersTotal = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "orders_total",
			Help: "Total orders processed",
		},
		[]string{"status"}, // success, failed
	)

	activeUsers = prometheus.NewGauge(
		prometheus.GaugeOpts{
			Name: "active_users",
			Help: "Active users",
		},
	)
)

func init() {
	prometheus.MustRegister(httpRequestsTotal)
	prometheus.MustRegister(httpRequestDuration)
	prometheus.MustRegister(httpRequestsInFlight)
	prometheus.MustRegister(ordersTotal)
	prometheus.MustRegister(activeUsers)
}

// =============================================================================
// APPLICATION STATE
// =============================================================================

type AppState struct {
	// Simulated state
	dbConnected   atomic.Bool
	cacheReady    atomic.Bool
	ordersProcessed atomic.Int64
	startTime     time.Time
}

func NewAppState() *AppState {
	state := &AppState{
		startTime: time.Now(),
	}
	// Simulate startup
	state.dbConnected.Store(true)
	state.cacheReady.Store(true)
	return state
}

// =============================================================================
// HEALTH CHECKS
// =============================================================================

type HealthResponse struct {
	Status    string            `json:"status"`
	Checks    map[string]Check `json:"checks"`
	Timestamp time.Time        `json:"timestamp"`
}

type Check struct {
	Status  string `json:"status"`
	Message string `json:"message,omitempty"`
}

// Liveness: Is the process alive?
func livenessHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(HealthResponse{
		Status:    "healthy",
		Timestamp: time.Now(),
	})
}

// Readiness: Can we serve traffic?
func readinessHandler(state *AppState) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		response := HealthResponse{
			Checks:    make(map[string]Check),
			Timestamp: time.Now(),
		}

		// Check database
		if state.dbConnected.Load() {
			response.Checks["database"] = Check{Status: "pass", Message: "Connected"}
		} else {
			response.Checks["database"] = Check{Status: "fail", Message: "Disconnected"}
			response.Status = "unhealthy"
		}

		// Check cache
		if state.cacheReady.Load() {
			response.Checks["cache"] = Check{Status: "pass", Message: "Ready"}
		} else {
			response.Checks["cache"] = Check{Status: "warn", Message: "Not ready"}
			if response.Status == "" {
				response.Status = "degraded"
			}
		}

		if response.Status == "" {
			response.Status = "healthy"
		}

		w.Header().Set("Content-Type", "application/json")
		if response.Status == "healthy" {
			w.WriteHeader(http.StatusOK)
		} else {
			w.WriteHeader(http.StatusServiceUnavailable)
		}
		json.NewEncoder(w).Encode(response)
	}
}

// Startup: Is initialization complete?
func startupHandler(state *AppState) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		elapsed := time.Since(state.startTime)

		response := HealthResponse{
			Checks: map[string]Check{
				"startup": {
					Status:  "pass",
					Message: fmt.Sprintf("Started %v ago", elapsed.Round(time.Second)),
				},
			},
			Timestamp: time.Now(),
		}

		// Simulate slow startup (for demo purposes, complete immediately)
		if elapsed < 30*time.Second && state.ordersProcessed.Load() == 0 {
			response.Status = "starting"
			w.WriteHeader(http.StatusServiceUnavailable)
		} else {
			response.Status = "healthy"
			w.WriteHeader(http.StatusOK)
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(response)
	}
}

// =============================================================================
// MIDDLEWARE
// =============================================================================

func metricsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		httpRequestsInFlight.Inc()
		defer httpRequestsInFlight.Dec()

		start := time.Now()

		// Capture status code
		wrapped := &statusWriter{ResponseWriter: w, statusCode: 200}
		next.ServeHTTP(wrapped, r)

		duration := time.Since(start).Seconds()
		path := r.URL.Path

		// Record metrics
		httpRequestsTotal.WithLabelValues(r.Method, path, fmt.Sprintf("%d", wrapped.statusCode)).Inc()
		httpRequestDuration.WithLabelValues(r.Method, path).Observe(duration)
	})
}

type statusWriter struct {
	http.ResponseWriter
	statusCode int
}

func (sw *statusWriter) WriteHeader(code int) {
	sw.statusCode = code
	sw.ResponseWriter.WriteHeader(code)
}

// =============================================================================
// HANDLERS
// =============================================================================

func orderHandler(state *AppState) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		// Simulate order processing
		latency := time.Duration(50+rand.Intn(200)) * time.Millisecond
		time.Sleep(latency)

		// Simulate random failure (5%)
		success := rand.Float32() > 0.05

		if success {
			state.ordersProcessed.Add(1)
			ordersTotal.WithLabelValues("success").Inc()

			logger.Log("INFO", "ORDER_CREATED", "Order processed successfully", map[string]interface{}{
				"orderId":    uuid.New().String(),
				"latencyMs":  latency.Milliseconds(),
			})

			w.Header().Set("Content-Type", "application/json")
			json.NewEncoder(w).Encode(map[string]string{
				"status":  "success",
				"orderId": uuid.New().String(),
			})
		} else {
			ordersTotal.WithLabelValues("failed").Inc()

			logger.Log("ERROR", "ORDER_FAILED", "Order processing failed", map[string]interface{}{
				"reason": "payment_declined",
			})

			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusPaymentRequired)
			json.NewEncoder(w).Encode(map[string]string{
				"status": "failed",
				"reason": "payment_declined",
			})
		}
	}
}

func userHandler(w http.ResponseWriter, r *http.Request) {
	// Simulate user fetch
	users := []string{"alice", "bob", "charlie", "diana"}
	user := users[rand.Intn(len(users))]

	activeUsers.Inc()
	defer activeUsers.Dec()

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{
		"user":   user,
		"active": "true",
	})
}

// =============================================================================
// MAIN
// =============================================================================

func main() {
	state := NewAppState()

	// Simulate active users (random fluctuation)
	go func() {
		ticker := time.NewTicker(5 * time.Second)
		for range ticker.C {
			activeUsers.Set(float64(10 + rand.Intn(20)))
		}
	}()

	// Router
	mux := http.NewServeMux()

	// Metrics endpoint
	mux.Handle("/metrics", promhttp.Handler())

	// Health checks
	mux.HandleFunc("/health/liveness", livenessHandler)
	mux.HandleFunc("/health/readiness", readinessHandler(state))
	mux.HandleFunc("/health/startup", startupHandler(state))

	// Application endpoints
	mux.HandleFunc("/api/orders", orderHandler(state))
	mux.HandleFunc("/api/user", userHandler)

	// Wrap with metrics
	handler := metricsMiddleware(mux)

	logger.Log("INFO", "SERVER_START", "Starting server", map[string]interface{}{
		"port": 8080,
	})

	// Graceful shutdown
	server := &http.Server{
		Addr:    ":8080",
		Handler: handler,
	}

	go func() {
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			logger.Log("ERROR", "SERVER_ERROR", "Server error", map[string]interface{}{
				"error": err.Error(),
			})
		}
	}()

	// Wait for shutdown signal
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	logger.Log("INFO", "SERVER_SHUTDOWN", "Shutting down server", nil)

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	server.Shutdown(ctx)
}
```

---

## Step 3: Run and Observe

```bash
# Build and run
go run main.go

# In another terminal, generate load
for i in {1..100}; do
  curl -s http://localhost:8080/api/orders > /dev/null
  curl -s http://localhost:8080/api/user > /dev/null
done
```

### Check the outputs:

```bash
# View structured logs (JSON output!)
curl http://localhost:8080/api/orders

# View Prometheus metrics
curl http://localhost:8080/metrics | grep -E "(http_requests|orders_total)"

# Check health endpoints
curl http://localhost:8080/health/liveness
curl http://localhost:8080/health/readiness
curl http://localhost:8080/health/startup
```

### Expected log output (structured JSON):
```json
{"timestamp":"2024-01-15T10:30:45.123Z","level":"INFO","event":"ORDER_CREATED","correlation":"abc-123","message":"Order processed successfully","metadata":{"orderId":"ord-456","latencyMs":127}}
```

### Expected metrics output:
```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",path="/api/user",status="200"} 52
http_requests_total{method="POST",path="/api/orders",status="200"} 45
http_requests_total{method="POST",path="/api/orders",status="402"} 5

# HELP orders_total Total orders processed
# TYPE orders_total counter
orders_total{status="success"} 45
orders_total{status="failed"} 5
```

---

## Step 4: Verify Prometheus is Scraping

1. Open http://localhost:3000 (Grafana)
2. Login: admin/admin
3. Add Prometheus datasource: http://prometheus:9090
4. Query these PromQL expressions:

```promql
# Rate of requests per second
rate(http_requests_total[1m])

# Error rate
sum(rate(http_requests_total{status=~"5.."}[1m])) / sum(rate(http_requests_total[1m]))

# p99 latency
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[1m]))

# Orders success rate
sum(rate(orders_total{status="success"}[1m])) / sum(rate(orders_total[1m]))
```

---

## Step 5: Observe What Happens When Things Go Wrong

Let's simulate failures to see the observability in action:

```bash
# Check health during normal operation
curl http://localhost:8080/health/readiness | jq .

# Now let's see what happens with load
for i in {1..50}; do
  curl -s http://localhost:8080/api/orders > /dev/null &
done
wait

# Watch metrics change
curl -s http://localhost:8080/metrics | grep orders_total
```

---

## Step 6: Staff-Level Extension

### Challenge 1: Add Distributed Tracing
Add OpenTelemetry and propagate trace context:

```go
// Add to handlers
traceID := uuid.New().String()
spanID := uuid.New().String()

logger.Log("INFO", "REQUEST", "Processing request", map[string]interface{}{
    "traceId": traceID,
    "spanId":  spanID,
})
```

### Challenge 2: Create an Alert
In Prometheus, add an alert rule:

```yaml
groups:
- name: observability-lab
  rules:
  - alert: HighErrorRate
    expr: sum(rate(orders_total{status="failed"}[5m])) / sum(rate(orders_total[5m])) > 0.1
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Error rate above 10%"
```

### Challenge 3: Add USE Method Metrics
Add resource metrics:

```go
// Add these metrics
var (
    cpuUsage = prometheus.NewGauge(prometheus.GaugeOpts{
        Name: "process_cpu_seconds",
        Help: "CPU usage",
    })
    memoryUsage = prometheus.NewGauge(prometheus.GaugeOpts{
        Name: "process_resident_memory_bytes",
        Help: "Memory usage",
    })
)
```

---

## Summary

In this lab, you built:

| Component | What You Implemented |
|-----------|---------------------|
| Structured Logging | JSON logs with event types, correlation IDs |
| RED Metrics | Rate, Errors, Duration per endpoint |
| Health Checks | Liveness, Readiness, Startup |
| Business Metrics | Orders processed, active users |
| Middleware | Automatic metrics collection |

### Key Takeaways

1. **Correlation IDs** link logs across services
2. **RED method** gives you per-service visibility
3. **Health checks** enable Kubernetes orchestration
4. **Metrics over logs** for alerting (faster, more efficient)

The observability stack you built is production-grade. Next steps: add OpenTelemetry for distributed tracing and integrate with your real infrastructure.
