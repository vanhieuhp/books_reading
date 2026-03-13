// 📘 Chapter 11: Transparency — Annotated Code Examples
// Go Examples: Structured Logging, Metrics, and Health Checks

package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"math/rand"
	"net/http"
	"os"
	"sync"
	"time"

	"github.com/google/uuid"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

// ============================================================================
// EXAMPLE 1: Structured Logging with Correlation IDs
// ============================================================================

// LogEntry represents a structured log message
// Staff-level: JSON structured logging is essential for log aggregation.
// Plain text logs cannot be efficiently searched at scale.
type LogEntry struct {
	Timestamp   string                 `json:"timestamp"`
	Level       string                 `json:"level"`
	Event       string                 `json:"event"`
	Correlation string                 `json:"correlation,omitempty"`
	UserID      string                 `json:"userId,omitempty"`
	Message     string                 `json:"message"`
	Metadata    map[string]interface{} `json:"metadata,omitempty"`
}

// Logger provides structured logging capabilities
// Staff-level: Async logging prevents I/O from blocking request processing.
// Blocking on logs can add 10-100ms latency per request at scale.
type Logger struct {
	output *os.File
	mu     sync.Mutex
}

// NewLogger creates a new structured logger
func NewLogger() *Logger {
	// In production: use async writer (zerolog, zap, or custom buffer)
	return &Logger{
		output: os.Stdout,
	}
}

// Log writes a structured log entry
// Staff-level: Always include correlation ID for distributed tracing.
// This is the single most important field for debugging production issues.
func (l *Logger) Log(level, event, message string, fields map[string]interface{}) {
	// Staff-level: Add correlation ID from context if available
	// but don't fail if missing - some requests may not have it
	correlation, _ := fields["correlation"].(string)

	entry := LogEntry{
		Timestamp:   time.Now().UTC().Format(time.RFC3339Nano),
		Level:       level,
		Event:       event,
		Correlation: correlation,
		Message:     message,
		Metadata:    fields,
	}

	// Staff-level: JSON encoding is standard for log aggregation
	// ELK/EFK stacks expect JSON for efficient parsing
	data, err := json.Marshal(entry)
	if err != nil {
		log.Printf("ERROR: failed to marshal log: %v", err)
		return
	}

	l.mu.Lock()
	defer l.mu.Unlock()
	fmt.Fprintln(l.output, string(data))
}

// WithCorrelation creates a new logger with correlation ID set
// Staff-level: Middleware should extract correlation from request header
// or generate new one if not present.
func WithCorrelation(ctx context.Context, correlationID string) context.Context {
	return context.WithValue(ctx, "correlation", correlationID)
}

// GetCorrelation extracts correlation ID from context
func GetCorrelation(ctx context.Context) string {
	if corr, ok := ctx.Value("correlation").(string); ok {
		return corr
	}
	return ""
}

// ❌ NAIVE APPROACH: Plain text logging
// Problem: Hard to search, parse, or aggregate. Can't filter by field.
func naiveLogging() {
	// What most developers do - plain text, no structure
	log.Printf("User login failed for user123 at %s", time.Now())
	log.Printf("Processing order 456 for customer789")
	log.Printf("Database query took 250ms")

	// Staff-level: This cannot be queried efficiently:
	// - Can't find all errors for user123
	// - Can't aggregate by error type
	// - Can't correlate with distributed traces
	// - Terabytes of text = expensive to search
}

// ✅ PRODUCTION APPROACH: Structured logging with context
func productionLogging() {
	logger := NewLogger()

	// Example: Login failure with full context
	logger.Log("WARN", "LOGIN_FAILED", "Invalid password attempt", map[string]interface{}{
		"correlation": uuid.New().String(),
		"userId":     "user123",
		"ip":         "192.168.1.100",
		"userAgent":  "Mozilla/5.0",
		"reason":     "INVALID_PASSWORD",
		"attempts":   3,
	})

	// Example: Order processing with timing
	start := time.Now()
	logger.Log("INFO", "ORDER_PROCESSING", "Started processing order", map[string]interface{}{
		"correlation": uuid.New().String(),
		"orderId":    "order_456",
		"customerId": "customer789",
		"total":      149.99,
	})

	// ... processing ...

	logger.Log("INFO", "ORDER_COMPLETE", "Order processed successfully", map[string]interface{}{
		"correlation": uuid.New().String(),
		"orderId":     "order_456",
		"durationMs":  time.Since(start).Milliseconds(),
	})

	// Staff-level: Now you can:
	// - Search: event=LOGIN_FAILED AND userId=user123
	// - Aggregate: count by event type, userId
	// - Correlate: join with traces using correlation ID
	// - Alert: notify on error rate > threshold
}

// ============================================================================
// EXAMPLE 2: Prometheus Metrics with RED Method
// ============================================================================

var (
	// Staff-level: Define metrics at package level for reuse
	// RED Method metrics - one set per service

	httpRequestsTotal = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "http_requests_total",
			Help: "Total number of HTTP requests",
		},
		[]string{"method", "path", "status"}, // Labels for grouping
	)

	httpRequestDuration = prometheus.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "http_request_duration_seconds",
			Help:    "HTTP request latency in seconds",
			Buckets: []float64{0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1}, // Latency buckets
		},
		[]string{"method", "path"},
	)

	httpRequestsInFlight = prometheus.NewGauge(
		prometheus.GaugeOpts{
			Name: "http_requests_in_flight",
			Help: "Number of HTTP requests currently being processed",
		},
	)

	// Business metrics - crucial for understanding user impact
	ordersTotal = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "orders_total",
			Help: "Total number of orders processed",
		},
		[]string{"status"}, // success, failed, cancelled
	)

	activeUsers = prometheus.NewGauge(
		prometheus.GaugeOpts{
			Name: "active_users",
			Help: "Number of currently active users",
		},
	)
)

func init() {
	// Register metrics with Prometheus
	prometheus.MustRegister(httpRequestsTotal)
	prometheus.MustRegister(httpRequestDuration)
	prometheus.MustRegister(httpRequestsInFlight)
	prometheus.MustRegister(ordersTotal)
	prometheus.MustRegister(activeUsers)
}

// MetricsMiddleware wraps HTTP handlers with RED metrics
// Staff-level: This is the standard pattern for instrumenting HTTP services.
// Captures Rate, Errors, and Duration per endpoint.
func MetricsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Track in-flight requests (for load estimation)
		httpRequestsInFlight.Inc()
		defer httpRequestsInFlight.Dec()

		start := time.Now()

		// Extract route pattern (not raw path to reduce cardinality)
		// Staff-level: High cardinality labels (like exact URL paths with IDs)
		// can cause Prometheus memory issues. Use route patterns instead.
		path := r.URL.Path
		if r.URL.Query().Has("id") {
			path = r.URL.Path + "/:id" // Normalize
		}

		// Wrap response writer to capture status code
		wrapped := &responseWriter{ResponseWriter: w, statusCode: http.StatusOK}
		next.ServeHTTP(wrapped, r)

		// Record metrics after request completes
		duration := time.Since(start).Seconds()

		// Rate: Total requests
		httpRequestsTotal.WithLabelValues(r.Method, path, fmt.Sprintf("%d", wrapped.statusCode)).Inc()

		// Duration: Histogram with latency buckets
		httpRequestDuration.WithLabelValues(r.Method, path).Observe(duration)

		// Staff-level: Error rate is implicit - filter by status >= 500
		// You can also explicitly track: errors_total{type="validation", "timeout", etc.}
	})
}

// responseWriter wrapper to capture status code
type responseWriter struct {
	http.ResponseWriter
	statusCode int
}

func (rw *responseWriter) WriteHeader(code int) {
	rw.statusCode = code
	rw.ResponseWriter.WriteHeader(code)
}

// ❌ NAIVE APPROACH: No metrics, just logs
// Problem: Can't aggregate, can't alert, can't do capacity planning
func naiveMetrics() {
	// Just logging - no quantitative understanding
	log.Println("Processing request")

	// Staff-level: This tells you NOTHING about:
	// - Request rate (is traffic increasing?)
	// - Error rate (are things breaking?)
	// - Latency distribution (is p99 degrading?)
	// - Capacity (are we about to overload?)
}

// ✅ PRODUCTION APPROACH: Comprehensive RED metrics
func productionMetrics() {
	// Staff-level: With these metrics, you can:
	//
	// RATE (requests/sec):
	//   rate(http_requests_total[5m]) by (path)
	//   → Alert if > 2x baseline
	//
	// ERRORS (error rate):
	//   sum(rate(http_requests_total{status=~"5.."}[5m])) /
	//   sum(rate(http_requests_total[5m]))
	//   → Alert if > 1%
	//
	// DURATION (latency):
	//   histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))
	//   → Alert if p99 > 500ms

	// Simulate request
	httpRequestsInFlight.Inc()
	defer httpRequestsInFlight.Dec()

	start := time.Now()
	// ... process request ...
	duration := time.Since(start).Seconds()

	httpRequestsTotal.WithLabelValues("POST", "/api/orders", "200").Inc()
	httpRequestDuration.WithLabelValues("POST", "/api/orders").Observe(duration)

	// Business metric
	ordersTotal.WithLabelValues("success").Inc()
}

// ============================================================================
// EXAMPLE 3: Health Checks (Liveness, Readiness, Startup)
// ============================================================================

// HealthCheckResult represents the result of a health check
type HealthCheckResult struct {
	Status    string            `json:"status"` // healthy, unhealthy, degraded
	Checks    map[string]Check  `json:"checks"`
	Timestamp time.Time         `json:"timestamp"`
}

type Check struct {
	Status  string `json:"status"` // pass, fail, warn
	Message string `json:"message,omitempty"`
	Latency string `json:"latency,omitempty"`
}

// AppState holds the application's current state
// Staff-level: Proper health checks require understanding dependencies.
type AppState struct {
	started       time.Time
	dbPool        *mockDBPool
	cache         *mockCache
	externalAPI   *mockExternalAPI
	initializationComplete bool
}

type mockDBPool struct{ connected bool }
type mockCache struct{ ready bool }
type mockExternalAPI struct{ available bool }

func NewAppState() *AppState {
	return &AppState{
		started: time.Now(),
	}
}

// LivenessCheck: Is the process alive?
// Staff-level: Kubernetes uses this to detect hung processes.
// Should be extremely simple - no dependencies checked.
// If this fails, Kubernetes will restart your pod.
func (s *AppState) LivenessCheck() HealthCheckResult {
	return HealthCheckResult{
		Status: "healthy",
		Checks: map[string]Check{
			"process": {
				Status:  "pass",
				Message: "Process is running",
			},
		},
		Timestamp: time.Now(),
	}
}

// ReadinessCheck: Can this pod serve traffic?
// Staff-level: This is crucial for Kubernetes rolling deployments.
// If DB is down, cache is cold, or external API is unreachable,
// return unhealthy to prevent traffic from routing here.
func (s *AppState) ReadinessCheck() HealthCheckResult {
	checks := make(map[string]Check)
	allHealthy := true

	// Check database connectivity
	// Staff-level: Don't check every query - just verify connection
	dbStatus := "pass"
	dbMessage := "Database connected"
	if !s.dbPool.connected {
		dbStatus = "fail"
		dbMessage = "Database connection failed"
		allHealthy = false
	}
	checks["database"] = Check{Status: dbStatus, Message: dbMessage}

	// Check cache availability
	cacheStatus := "pass"
	cacheMessage := "Cache available"
	if !s.cache.ready {
		cacheStatus = "warn" // Cache is nice-to-have, not critical
		cacheMessage = "Cache not ready - degraded performance"
	}
	checks["cache"] = Check{Status: cacheStatus, Message: cacheMessage}

	// Check external dependencies
	apiStatus := "pass"
	apiMessage := "External API available"
	if !s.externalAPI.available {
		apiStatus = "fail"
		apiMessage = "External API unavailable"
		allHealthy = false
	}
	checks["external_api"] = Check{Status: apiStatus, Message: apiMessage}

	// Check initialization complete
	initStatus := "pass"
	if !s.initializationComplete {
		initStatus = "fail"
		allHealthy = false
	}
	checks["initialization"] = Check{Status: initStatus, Message: "Initialization complete"}

	status := "healthy"
	if !allHealthy {
		status = "unhealthy"
	}

	return HealthCheckResult{
		Status:    status,
		Checks:    checks,
		Timestamp: time.Now(),
	}
}

// StartupCheck: Has the application finished starting?
// Staff-level: Used for slow-starting applications (like JVM services).
// Kubernetes will wait for this to pass before sending traffic.
func (s *AppState) StartupCheck() HealthCheckResult {
	elapsed := time.Since(s.started)

	status := "healthy"
	message := "Startup complete"

	// Staff-level: Allow up to 30 seconds for startup
	if elapsed < 30*time.Second && !s.initializationComplete {
		status = "unhealthy"
		message = fmt.Sprintf("Starting up... (%ds elapsed)", int(elapsed.Seconds()))
	}

	return HealthCheckResult{
		Status: status,
		Checks: map[string]Check{
			"startup": {
				Status:  "pass",
				Message: message,
				Latency: elapsed.String(),
			},
		},
		Timestamp: time.Now(),
	}
}

// ❌ NAIVE APPROACH: One health check for everything
// Problem: Kubernetes can't make nuanced routing decisions
func naiveHealthCheck() {
	// Most developers do this - one endpoint, checks everything
	// Issues:
	// - Can't distinguish "restart me" from "don't send traffic"
	// - Slow checks block liveness probes
	// - No degradation indication
}

// ✅ PRODUCTION APPROACH: Three separate health checks
func productionHealthCheck() {
	state := NewAppState()

	// Liveness: Is process alive?
	// - No dependencies
	// - Very fast (< 100ms)
	// - Kubernetes calls every 10-30s
	liveness := state.LivenessCheck()

	// Readiness: Can we serve traffic?
	// - Checks critical dependencies
	// - Medium speed (< 1s)
	// - Kubernetes calls before routing
	readiness := state.ReadinessCheck()

	// Startup: Are we ready to accept traffic?
	// - For slow-starting apps
	// - Kubernetes waits for pass
	startup := state.StartupCheck()

	_ = liveness
	_ = readiness
	_ = startup
}

// ============================================================================
// HTTP Handlers for health endpoints
// ============================================================================

func livenessHandler(w http.ResponseWriter, r *http.Request) {
	state := NewAppState() // In real app, get from context
	result := state.LivenessCheck()
	w.Header().Set("Content-Type", "application/json")
	if result.Status == "healthy" {
		w.WriteHeader(http.StatusOK)
	} else {
		w.WriteHeader(http.StatusServiceUnavailable)
	}
	json.NewEncoder(w).Encode(result)
}

func readinessHandler(w http.ResponseWriter, r *http.Request) {
	state := NewAppState()
	result := state.ReadinessCheck()
	w.Header().Set("Content-Type", "application/json")
	if result.Status == "healthy" {
		w.WriteHeader(http.StatusOK)
	} else {
		w.WriteHeader(http.StatusServiceUnavailable)
	}
	json.NewEncoder(w).Encode(result)
}

func startupHandler(w http.ResponseWriter, r *http.Request) {
	state := NewAppState()
	result := state.StartupCheck()
	w.Header().Set("Content-Type", "application/json")
	if result.Status == "healthy" {
		w.WriteHeader(http.StatusOK)
	} else {
		w.WriteHeader(http.StatusServiceUnavailable)
	}
	json.NewEncoder(w).Encode(result)
}

func metricsHandler() http.Handler {
	return promhttp.Handler()
}

// ============================================================================
// Main: Wire up all the pieces
// ============================================================================

func main() {
	// Structured logging demo
	productionLogging()

	// Metrics demo
	productionMetrics()

	// Health checks demo
	productionHealthCheck()

	// HTTP server with observability
	http.Handle("/metrics", metricsHandler())
	http.HandleFunc("/health/liveness", livenessHandler)
	http.HandleFunc("/health/readiness", readinessHandler)
	http.HandleFunc("/health/startup", startupHandler)
	http.Handle("/", MetricsMiddleware(http.DefaultServeMux))

	log.Println("Server starting on :8080")
	log.Fatal(http.ListenAndServe(":8080", nil))
}

// Suppress unused warnings for demo
var _ = rand.Int
