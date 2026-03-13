package main

import (
	"context"
	"fmt"
	"log"
	"math/rand"
	"net/http"
	"net/url"
	"sync"
	"sync/atomic"
	"time"
)

// ============================================================
// STRANGLER PATTERN DEMONSTRATION
// ============================================================
//
// This demonstrates the Strangler pattern from Release It! Chapter 15:
// - Build new system beside old
// - Gradually migrate feature by feature
// - Old system fades away
//
// Key concepts:
// 1. Traffic splitting (gradual migration)
// 2. Health monitoring (canary analysis)
// 3. Deterministic routing (consistency)
// 4. Rollback capability (safety net)

// --- Metrics tracking ---

type MigrationMetrics struct {
	legacyRequests  int64
	newRequests     int64
	legacyErrors   int64
	newErrors      int64
	legacyLatencyNs int64
	newLatencyNs   int64

	// Health thresholds
	maxErrorRate    float64
	maxLatencyMs    float64
}

func NewMigrationMetrics() *MigrationMetrics {
	return &MigrationMetrics{
		maxErrorRate:  0.05,  // 5% error rate threshold
		maxLatencyMs: 200,    // 200ms latency threshold
	}
}

func (m *MigrationMetrics) RecordLegacyRequest(latency time.Duration, isError bool) {
	atomic.AddInt64(&m.legacyRequests, 1)
	if isError {
		atomic.AddInt64(&m.legacyErrors, 1)
	}
	atomic.AddInt64(&m.legacyLatencyNs, latency.Nanoseconds())
}

func (m *MigrationMetrics) RecordNewRequest(latency time.Duration, isError bool) {
	atomic.AddInt64(&m.newRequests, 1)
	if isError {
		atomic.AddInt64(&m.newErrors, 1)
	}
	atomic.AddInt64(&m.newLatencyNs, latency.Nanoseconds())
}

func (m *MigrationMetrics) GetStats() (legacyErrors, newErrors float64, legacyLatency, newLatency time.Duration) {
	lr := atomic.LoadInt64(&m.legacyRequests)
	le := atomic.LoadInt64(&m.legacyErrors)
	ll := atomic.LoadInt64(&m.legacyLatencyNs)

	nr := atomic.LoadInt64(&m.newRequests)
	ne := atomic.LoadInt64(&m.newErrors)
	nl := atomic.LoadInt64(&m.newLatencyNs)

	if lr > 0 {
		legacyErrors = float64(le) / float64(lr)
		legacyLatency = time.Duration(ll / lr)
	}
	if nr > 0 {
		newErrors = float64(ne) / float64(nr)
		newLatency = time.Duration(nl / nr)
	}

	return
}

func (m *MigrationMetrics) IsNewSystemHealthy() bool {
	_, newErrors, _, newLatency := m.GetStats()

	if newErrors > m.maxErrorRate {
		log.Printf("NEW SYSTEM UNHEALTHY: Error rate %.2f%% > threshold %.2f%%",
			newErrors*100, m.maxErrorRate*100)
		return false
	}

	if newLatency > time.Duration(m.maxLatencyMs)*time.Millisecond {
		log.Printf("NEW SYSTEM UNHEALTHY: Latency %v > threshold %v",
			newLatency, time.Duration(m.maxLatencyMs)*time.Millisecond)
		return false
	}

	return true
}

// --- Request Router ---

type RequestRouter struct {
	legacyHandler  http.Handler
	newHandler     http.Handler
	metrics        *MigrationMetrics

	mu             sync.RWMutex
	migrationRatio float64 // 0.0 = all legacy, 1.0 = all new
}

func NewRequestRouter(legacy, new http.Handler, metrics *MigrationMetrics) *RequestRouter {
	return &RequestRouter{
		legacyHandler:  legacy,
		newHandler:     new,
		metrics:        metrics,
		migrationRatio: 0.0, // Start with 0% on new system
	}
}

// SetMigrationRatio sets the percentage of traffic to route to new system
// Staff-level: In production, this should be automated with canary analysis
func (r *RequestRouter) SetMigrationRatio(percent float64) {
	r.mu.Lock()
	defer r.mu.Unlock()

	if percent < 0 {
		percent = 0
	} else if percent > 1 {
		percent = 1
	}

	r.migrationRatio = percent
	log.Printf("Migration ratio updated: %.1f%% to new system", percent*100)
}

// ServeHTTP routes requests based on migration ratio
// Uses deterministic hashing for user consistency
func (r *RequestRouter) ServeHTTP(w http.ResponseWriter, req *http.Request) {
	start := time.Now()

	// Determine which system handles this request
	useNew := r.shouldRouteToNew(req)

	var handler http.Handler
	if useNew {
		handler = r.newHandler
	} else {
		handler = r.legacyHandler
	}

	// Execute request
	handler.ServeHTTP(w, req)

	latency := time.Since(start)
	isError := isErrorResponse(w)

	// Record metrics
	if useNew {
		r.metrics.RecordNewRequest(latency, isError)
	} else {
		r.metrics.RecordLegacyRequest(latency, isError)
	}
}

// shouldRouteToNew determines routing destination
// Uses deterministic hashing for user consistency
func (r *RequestRouter) shouldRouteToNew(req *http.Request) bool {
	r.mu.RLock()
	ratio := r.migrationRatio
	r.mu.RUnlock()

	if ratio == 0 {
		return false
	}
	if ratio >= 1 {
		return true
	}

	// Get user ID for consistent routing
	// Staff-level: In production, use better hashing (consistent hashing)
	userID := req.Header.Get("X-User-ID")
	if userID == "" {
		// No user ID = use random for backwards compatibility
		return rand.Float64() < ratio
	}

	// Deterministic hash-based routing
	hash := 0
	for _, c := range userID {
		hash = hash*31 + int(c)
	}
	return float64(hash%100)/100.0 < ratio
}

// isErrorResponse checks if response indicates an error
func isErrorResponse(w http.ResponseWriter) bool {
	// Simple check - in production, you'd use a response wrapper
	// to capture actual status code
	// For demo, we'll use a small random error rate simulation
	return rand.Float64() < 0.02 // 2% simulated error rate
}

// --- Mock Handlers ---

func legacyHandler(w http.ResponseWriter, req *http.Request) {
	// Simulate legacy system (slower, sometimes errors)
	latency := 50 + rand.Intn(100) // 50-150ms
	time.Sleep(time.Duration(latency) * time.Millisecond)

	w.Header().Set("X-System", "legacy")
	fmt.Fprintf(w, `{"message": "Legacy system response", "latency_ms": %d}`, latency)
}

func newHandler(w http.ResponseWriter, req *http.Request) {
	// Simulate new system (faster, more reliable)
	latency := 10 + rand.Intn(30) // 10-40ms
	time.Sleep(time.Duration(latency) * time.Millisecond)

	w.Header().Set("X-System", "new")
	fmt.Fprintf(w, `{"message": "New system response", "latency_ms": %d}`, latency)
}

// --- Canary Analysis ---

type CanaryAnalyzer struct {
	metrics *MigrationMetrics
}

func (c *CanaryAnalyzer) ShouldIncreaseMigration() (bool, string) {
	legacyErrors, newErrors, legacyLatency, newLatency := c.metrics.GetStats()

	log.Printf("Canary Analysis: Legacy errors=%.2f%% latency=%v, New errors=%.2f%% latency=%v",
		legacyErrors*100, legacyLatency, newErrors*100, newLatency)

	// Check error rate
	if newErrors > c.metrics.maxErrorRate*1.5 {
		return false, fmt.Sprintf("New system error rate %.2f%% too high (threshold: %.2f%%)",
			newErrors*100, c.metrics.maxErrorRate*100)
	}

	// Check latency
	if newLatency > time.Duration(c.metrics.maxLatencyMs*2)*time.Millisecond {
		return false, fmt.Sprintf("New system latency %v too high (threshold: %v)",
			newLatency, time.Duration(c.metrics.maxLatencyMs)*time.Millisecond)
	}

	// New system is healthier than legacy - safe to increase
	if newErrors < legacyErrors && newLatency < legacyLatency {
		return true, "New system outperforming legacy"
	}

	return true, "New system meeting thresholds"
}

// --- Demo Runner ---

func main() {
	rand.Seed(time.Now().UnixNano())

	log.SetFlags(log.LstdFlags | log.Lshortfile)

	metrics := NewMigrationMetrics()

	legacy := http.HandlerFunc(legacyHandler)
	new := http.HandlerFunc(newHandler)
	router := NewRequestRouter(legacy, new, metrics)
	analyzer := CanaryAnalyzer{metrics: metrics}

	// Simulate migration process
	log.Println("=" * 60)
	log.Println("STRANGLER PATTERN DEMO")
	log.Println("=" * 60)

	migrationSteps := []float64{0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0}

	for _, targetRatio := range migrationSteps {
		log.Println("")
		log.Printf("--- Migrating to %.0f%% ---\n", targetRatio*100)

		router.SetMigrationRatio(targetRatio)

		// Simulate traffic
		for i := 0; i < 100; i++ {
			req := &http.Request{
				Method: "GET",
				URL:    &url.URL{Path: "/api/data"},
				Header: http.Header{
					"X-User-ID": []string{fmt.Sprintf("user-%d", i%20)},
				},
			}

			rw := &mockResponseWriter{header: make(http.Header)}
			router.ServeHTTP(rw, req)
		}

		// Check if new system is healthy
		canaryOk, reason := analyzer.ShouldIncreaseMigration()
		if !canaryOk {
			log.Printf("CANARY FAILED: %s - Rolling back!", reason)
			router.SetMigrationRatio(targetRatio - 0.1)
			log.Println("Rollback complete. Migration paused.")
			break
		}

		log.Printf("Canary analysis: %s", reason)
		log.Printf("Migration progress: %.0f%% complete", targetRatio*100)
	}

	log.Println("")
	log.Println("=" * 60)
	log.Println("MIGRATION COMPLETE")
	log.Println("=" * 60)
}

// --- Mock Response Writer ---

type mockResponseWriter struct {
	header http.Header
	status int
}

func (m *mockResponseWriter) Header() http.Header {
	return m.header
}

func (m *mockResponseWriter) WriteHeader(status int) {
	m.status = status
}

func (m *mockResponseWriter) Write(b []byte) (int, error) {
	return len(b), nil
}
