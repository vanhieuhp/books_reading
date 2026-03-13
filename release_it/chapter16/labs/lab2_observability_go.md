# Lab 2: Building System Observability in Go

## 🎯 Goal

Implement a production-grade observability layer for a Go microservice that demonstrates the concepts from Chapter 16:
- Structured logging with correlation IDs
- Metrics collection
- Distributed tracing context

## ⏱ Time
~30 minutes

## 🛠 Requirements

- Go 1.20+
- Basic understanding of Go concurrency
- Terminal/command line

---

## Step 1: Setup

Create a new Go module and install dependencies:

```bash
mkdir -p chapter16_lab
cd chapter16_lab
go mod init chapter16_lab
go get github.com/prometheus/client_golang/prometheus
go get github.com/prometheus/client_golang/prometheus/promhttp
```

---

## Step 2: Implement the Observability Core

Create `observability.go` with the core observability primitives:

```go
package main

import (
	"context"
	"fmt"
	"log"
	"math/rand"
	"net/http"
	"time"
)

// ============================================================
// TASK 1: Structured Logging with Correlation IDs
// ============================================================

// SystemContext carries observability context through the request lifecycle
// This is critical for the "Systemic View" - tracking interactions across components

type SystemContext struct {
	TraceID    string    // Unique per request - enables tracing across services
	SpanID     string    // Unique per operation - enables timing per step
	Component  string    // Which component is generating this log
	StartedAt  time.Time
	Metadata   map[string]string
}

// NewSystemContext creates a new observability context
// Staff insight: Always generate trace IDs at the edge (API gateway)
// so all downstream services can correlate
func NewSystemContext(traceID, component string) *SystemContext {
	return &SystemContext{
		TraceID:   traceID,
		SpanID:    generateSpanID(),
		Component: component,
		StartedAt: time.Now(),
		Metadata:  make(map[string]string),
	}
}

// Log writes a structured log message
// Staff insight: Structured logs enable machine parsing - crucial for
// correlating logs with metrics and traces during incidents
func (sc *SystemContext) Log(level, message string) {
	elapsed := time.Since(sc.StartedAt).Milliseconds()
	log.Printf("[%s] trace_id=%s span_id=%s component=%s elapsed_ms=%d message=%s metadata=%v",
		level,
		sc.TraceID,
		sc.SpanID,
		sc.Component,
		elapsed,
		message,
		sc.Metadata,
	)
}

func (sc *SystemContext) WithMetadata(key, value string) *SystemContext {
	sc.Metadata[key] = value
	return sc
}

func generateSpanID() string {
	return fmt.Sprintf("%016x", rand.Uint64())
}

// ============================================================
// TASK 2: Metrics Collection
// ============================================================

import "github.com/prometheus/client_golang/prometheus"
import "github.com/prometheus/client_golang/prometheus/promhttp"

// MetricsCollector holds all our custom metrics
// Staff insight: Choose metrics that measure SYSTEM behavior,
// not just component behavior - e.g., end-to-end latency, not just function duration

type MetricsCollector struct {
	// Request metrics
	RequestsTotal    *prometheus.CounterVec
	RequestDuration *prometheus.HistogramVec
	RequestsInFlight *prometheus.Gauge

	// Business metrics (system-level)
	OrdersPlaced   prometheus.Counter
	PaymentSuccess prometheus.Counter
	PaymentFailed  prometheus.Counter
}

func NewMetricsCollector(reg *prometheus.Registry) *MetricsCollector {
	m := &MetricsCollector{
		RequestsTotal: prometheus.NewCounterVec(
			prometheus.CounterOpts{
				Name: "http_requests_total",
				Help: "Total number of HTTP requests",
			},
			[]string{"method", "endpoint", "status"},
		),
		RequestDuration: prometheus.NewHistogramVec(
			prometheus.HistogramOpts{
				Name:    "http_request_duration_seconds",
				Help:    "HTTP request latency in seconds",
				Buckets: []float64{.005, .01, .025, .05, .1, .25, .5, 1},
			},
			[]string{"method", "endpoint"},
		),
		RequestsInFlight: prometheus.NewGauge(
			prometheus.GaugeOpts{
				Name: "http_requests_in_flight",
				Help: "Number of HTTP requests currently being processed",
			},
		),
	}

	reg.MustRegister(m.RequestsTotal, m.RequestDuration, m.RequestsInFlight)

	return m
}

// ============================================================
// TASK 3: Middleware for Observability
// ============================================================

// ObservabilityMiddleware wraps HTTP handlers with full observability
// This is where the "Systemic View" becomes concrete - every request
// is traced, timed, and logged with correlation context

func ObservabilityMiddleware(next http.Handler, metrics *MetricsCollector) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Extract or generate trace ID
		traceID := r.Header.Get("X-Trace-ID")
		if traceID == "" {
			traceID = generateSpanID()
		}

		ctx := r.Context()
		ctx = context.WithValue(ctx, "trace_id", traceID)
		ctx = context.WithValue(ctx, "span_id", generateSpanID())

		// Track in-flight requests (system health indicator)
		metrics.RequestsInFlight.Inc()
		defer metrics.RequestsInFlight.Dec()

		// Timing
		start := time.Now()

		// Capture response status
		rw := &responseWriter{ResponseWriter: w, statusCode: http.StatusOK}
		next.ServeHTTP(rw, r.WithContext(ctx))

		duration := time.Since(start).duration.Seconds()

		// Record metrics
		metrics.RequestsTotal.WithLabelValues(
			r.Method,
			r.URL.Path,
			fmt.Sprintf("%d", rw.statusCode),
		).Inc()

		metrics.RequestDuration.WithLabelValues(
			r.Method,
			r.URL.Path,
		).Observe(duration)

		// Structured log
		log.Printf("[INFO] trace_id=%s method=%s path=%s status=%d duration_ms=%d",
			traceID,
			r.Method,
			r.URL.Path,
			rw.statusCode,
			duration*1000,
		)
	})
}

type responseWriter struct {
	http.ResponseWriter
	statusCode int
}

func (rw *responseWriter) WriteHeader(code int) {
	rw.statusCode = code
	rw.ResponseWriter.WriteHeader(code)
}
```

---

## Step 3: Implement a Simple Service with Observability

Create `service.go` demonstrating the full observability stack:

```go
// ============================================================
// DEMO SERVICE: Order Processing with Full Observability
// ============================================================

// OrderService demonstrates systemic observability
// Each operation logs with context, records metrics, handles errors gracefully

type OrderService struct {
	metrics *MetricsCollector
}

func NewOrderService(metrics *MetricsCollector) *OrderService {
	return &OrderService{metrics: metrics}
}

// ProcessOrder demonstrates the full observability flow
// Staff insight: This is what "designing for the system" looks like in practice
func (os *OrderService) ProcessOrder(ctx context.Context, orderID string) error {
	sysCtx := NewSystemContext(
		ctx.Value("trace_id").(string),
		"order-service",
	)
	sysCtx.WithMetadata("order_id", orderID)

	sysCtx.Log("INFO", "Starting order processing")

	// Step 1: Validate order
	if err := os.validateOrder(ctx, orderID); err != nil {
		sysCtx.LogError(err)
		return err
	}

	// Step 2: Process payment
	if err := os.processPayment(ctx, orderID); err != nil {
		sysCtx.LogError(err)
		os.metrics.PaymentFailed.Inc()
		return err
	}
	os.metrics.PaymentSuccess.Inc()

	// Step 3: Reserve stock
	if err := os.reserveStock(ctx, orderID); err != nil {
		sysCtx.LogError(err)
		return err
	}

	// Step 4: Create shipment
	if err := os.createShipment(ctx, orderID); err != nil {
		sysCtx.LogError(err)
		return err
	}

	os.metrics.OrdersPlaced.Inc()
	sysCtx.Log("INFO", "Order processed successfully")

	return nil
}

func (os *OrderService) validateOrder(ctx context.Context, orderID string) error {
	// Simulate validation
	time.Sleep(time.Millisecond * 50)
	return nil
}

func (os *OrderService) processPayment(ctx context.Context, orderID string) error {
	// Simulate payment processing - could fail
	if rand.Float32() < 0.1 {
		return fmt.Errorf("payment declined")
	}
	time.Sleep(time.Millisecond * 100)
	return nil
}

func (os *OrderService) reserveStock(ctx context.Context, orderID string) error {
	time.Sleep(time.Millisecond * 50)
	return nil
}

func (os *OrderService) createShipment(ctx context.Context, orderID string) error {
	time.Sleep(time.Millisecond * 50)
	return nil
}
```

---

## Step 4: Run and Observe

Create `main.go` that ties everything together:

```go
package main

import (
	"context"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"
)

func main() {
	fmt.Println("=== Chapter 16 Lab: System Observability ===\n")

	// Setup metrics registry
	reg := prometheus.NewRegistry()
	metrics := NewMetricsCollector(reg)

	// Create service
	orderService := NewOrderService(metrics)

	// Setup HTTP server with observability
	mux := http.NewServeMux()
	mux.HandleFunc("/order", func(w http.ResponseWriter, r *http.Request) {
		orderID := r.URL.Query().Get("id")
		if orderID == "" {
			orderID = "default"
		}

		traceID := r.Header.Get("X-Trace-ID")
		if traceID == "" {
			traceID = generateSpanID()
		}

		ctx := context.WithValue(r.Context(), "trace_id", traceID)

		if err := orderService.ProcessOrder(ctx, orderID); err != nil {
			w.WriteHeader(http.StatusInternalServerError)
			fmt.Fprintf(w, "Error: %v", err)
			return
		}

		fmt.Fprintf(w, "Order %s processed successfully", orderID)
	})

	// Metrics endpoint
	mux.Handle("/metrics", promhttp.HandlerFor(reg, promhttp.HandlerOpts{}))

	// Wrap with observability middleware
	handler := ObservabilityMiddleware(mux, metrics)

	// Start server
	srv := &http.Server{
		Addr:    ":8080",
		Handler: handler,
	}

	go func() {
		fmt.Println("Server starting on :8080")
		fmt.Println("Try: curl http://localhost:8080/order?id=123")
		fmt.Println("Metrics: curl http://localhost:8080/metrics")
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatal(err)
		}
	}()

	// Wait for interrupt
	sig := make(chan os.Signal, 1)
	signal.Notify(sig, syscall.SIGINT, syscall.SIGTERM)
	<-sig

	fmt.Println("\nShutting down...")
	srv.Shutdown(context.Background())
}
```

---

## Step 5: Verify Your Work

Run the service:

```bash
go run main.go
```

Test it:

```bash
# Normal request
curl http://localhost:8080/order?id=123

# With custom trace ID (for testing distributed tracing)
curl -H "X-Trace-ID: test-abc-123" http://localhost:8080/order?id=456

# Check metrics
curl http://localhost:8080/metrics | grep -E "(http_requests|orders_placed|payment)"
```

Expected metrics output:
```
# HELP http_requests_total Total number of HTTP requests
# TYPE http_requests_total counter
http_requests_total{endpoint="/order",method="GET",status="200"} 2
http_requests_total{endpoint="/metrics",method="GET",status="200"} 1

# HELP orders_placed Total number of orders placed
# TYPE orders_placed counter
orders_placed 2

# HELP payment_success Total payment successes
# TYPE payment_success counter
payment_success 2
```

---

## Step 6: Stretch Challenge

Implement ONE of these:

1. **Add latency histogram for each step** in order processing
   - Hint: Modify `OrderService` to record duration per step

2. **Add error classification** - categorize errors as:
   - `retryable` (network blip)
   - `business` (payment declined)
   - `internal` (bugs)
   - Hint: Use structured error types

3. **Add custom span context** that tracks the full request lifecycle
   - Hint: Use `context.WithValue` to propagate span IDs

---

## Solution Key Points

The solution demonstrates Chapter 16's key principles:

| Principle | Implementation |
|-----------|-----------------|
| **Systemic View** | Trace ID propagates across all components |
| **Feedback Loops** | Metrics enable detecting system behavior patterns |
| **Human-Centered** | Structured logs are readable by operators |
| **Design for Failure** | Error handling includes context for debugging |

---

## Why This Matters (Staff Perspective)

This observability layer is the **foundation** for:

1. **Incident Response**: When things break, trace IDs let you correlate logs across services
2. **Capacity Planning**: Metrics reveal usage patterns
3. **A/B Testing**: Correlation IDs enable analyzing feature impact
4. **SLA Monitoring**: End-to-end latency metrics prove compliance

The code is "boring" (not clever) because **operability is the feature** — and that's exactly what Chapter 16 teaches.
