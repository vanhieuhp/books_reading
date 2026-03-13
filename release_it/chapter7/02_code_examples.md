# Annotated Code Examples

## Example 1: Graceful Shutdown - Naive vs Production

The difference between naive and production graceful shutdown implementations is the difference between silent data loss and clean recovery.

### Go Implementation

```go
package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"
)

// ============================================================
// ❌ NAIVE APPROACH - What most developers do
// ============================================================
// Problems:
// 1. No signal handling - killed abruptly by SIGKILL
// 2. No drain time - in-flight requests fail mid-operation
// 3. No connection cleanup - dangling database connections
// 4. No deregistration - load balancer sends traffic to dead instance

func naiveHTTPServer() {
	// Problem: No graceful shutdown
	// When container receives SIGTERM, process is killed immediately
	// All in-flight requests fail
	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Simulate work
		time.Sleep(500 * time.Millisecond)
		w.Write([]byte("ok"))
	})

	// Problem: No timeout, server.Close() blocks forever
	log.Fatal(http.ListenAndServe(":8080", handler))
	// If deployment happens while requests are in-flight:
	// - Requests return 500
	// - Client retries flood the system
	// - Database may have partial writes
}

// ============================================================
// ✅ PRODUCTION APPROACH - What this chapter teaches
// ============================================================

type Server struct {
	httpServer *http.Server
	// Track in-flight requests for graceful drain
	mu           sync.Mutex
	inFlight     int
	shuttingDown bool

	// Graceful shutdown configuration
	shutdownTimeout time.Duration = 30 * time.Second
	drainComplete   chan struct{}
}

func NewServer() *Server {
	return &Server{
		drainComplete: make(chan struct{}),
	}
}

// Start initializes the HTTP server with proper handlers
func (s *Server) Start(addr string) error {
	mux := http.NewServeMux()

	// Health check endpoints - critical for orchestration
	mux.HandleFunc("/health/liveness", s.handleLiveness)
	mux.HandleFunc("/health/readiness", s.handleReadiness)
	mux.HandleFunc("/", s.handleRequest)

	s.httpServer = &http.Server{
		Addr:         addr,
		Handler:      mux,
		// ReadHeaderTimeout: Prevents slowloris attacks
		ReadHeaderTimeout: 10 * time.Second,
		// IdleTimeout: Closes idle connections proactively
		IdleTimeout: 30 * time.Second,
		// These timeouts are critical for production
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 30 * time.Second,
	}

	log.Printf("Server starting on %s", addr)
	return s.httpServer.ListenAndServe()
}

// handleLiveness - Answers: "Is the process alive?"
// Used by: Kubernetes liveness probe, process supervisors
// Staff-level insight: Keep this SIMPLE. Don't check dependencies here.
// Checking DB in liveness can cause restart loops during brief DB issues.
func (s *Server) handleLiveness(w http.ResponseWriter, r *http.Request) {
	// Simple process health - am I running?
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(`{"status":"alive"}`))
}

// handleReadiness - Answers: "Can I handle traffic?"
// Used by: Kubernetes readiness probe, load balancer routing
// Staff-level insight: This is WHERE you check dependencies.
// If DB is down, cache is cold, or init isn't complete, return 503.
func (s *Server) handleReadiness(w http.ResponseWriter, r *http.Request) {
	s.mu.Lock()
	shuttingDown := s.shuttingDown
	s.mu.Lock()

	if shuttingDown {
		// Don't send traffic to instance that's draining
		w.WriteHeader(http.StatusServiceUnavailable)
		w.Write([]byte(`{"status":"draining"}`))
		return
	}

	// Check critical dependencies
	ctx, cancel := context.WithTimeout(r.Context(), 2*time.Second)
	defer cancel()

	// In real implementation, check:
	// - Database connection pool health
	// - Cache availability
	// - Dependency service availability
	if !s.isReady(ctx) {
		w.WriteHeader(http.StatusServiceUnavailable)
		w.Write([]byte(`{"status":"not_ready"}`))
		return
	}

	w.WriteHeader(http.StatusOK)
	w.Write([]byte(`{"status":"ready"}`))
}

// isReady checks if all dependencies are available
// Staff-level: This is where you implement "gradual traffic ramping"
// For example: cache warming, dependency checks
func (s *Server) isReady(ctx context.Context) bool {
	// Check database connectivity
	// Check cache availability
	// Check configuration loaded
	return true
}

// handleRequest tracks in-flight requests for graceful drain
func (s *Server) handleRequest(w http.ResponseWriter, r *http.Request) {
	// Track in-flight requests
	s.mu.Lock()
	s.inFlight++
	s.mu.Unlock()

	// Ensure we decrement when done
	defer func() {
		s.mu.Lock()
		s.inFlight--
		s.mu.Unlock()
	}()

	// Check if we're shutting down - reject new requests
	s.mu.Lock()
	shuttingDown := s.shuttingDown
	s.mu.Unlock()

	if shuttingDown {
		w.WriteHeader(http.StatusServiceUnavailable)
		return
	}

	// Process request...
	time.Sleep(100 * time.Millisecond)
	w.Write([]byte("ok"))
}

// GracefulShutdown implements the full shutdown sequence
// This is what gets called when SIGTERM arrives
func (s *Server) GracefulShutdown() error {
	log.Println("🔄 Starting graceful shutdown...")

	// Step 1: Signal that we should stop accepting new requests
	s.mu.Lock()
	s.shuttingDown = true
	s.mu.Unlock()

	log.Println("🚦 Stopped accepting new requests")

	// Step 2: Wait for in-flight requests to complete (drain)
	// Staff-level insight: This timeout is CRITICAL
	// Too short: requests fail mid-operation (data corruption risk)
	// Too long: deployment takes forever, costs money
	log.Printf("⏳ Draining in-flight requests (max %v)...", s.shutdownTimeout)

	drainTimer := time.NewTimer(s.shutdownTimeout)
	drainDone := make(chan struct{})

	go func() {
		s.mu.Lock()
		// Busy wait for in-flight to reach zero
		for s.inFlight > 0 {
			s.mu.Unlock()
			time.Sleep(100 * time.Millisecond)
			s.mu.Lock()
		}
		s.mu.Unlock()

		log.Println("✅ All in-flight requests completed")
		close(drainDone)
	}()

	// Wait for either drain completion or timeout
	select {
	case <-drainDone:
		drainTimer.Stop()
		log.Println("✅ Drain completed successfully")
	case <-drainTimer.C:
		log.Println("⚠️ Drain timeout - forcing shutdown")
		// Staff-level insight: Force kill after timeout prevents
		// hung deployments but may lose in-flight data
	}

	// Step 3: Close all connections (HTTP, DB, Redis, etc.)
	log.Println("🔌 Closing connections...")
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	if err := s.httpServer.Shutdown(ctx); err != nil {
		log.Printf("❌ Error during server shutdown: %v", err)
	}

	// Step 4: Flush logs, metrics, buffered writers
	log.Println("📝 Flushing buffers...")

	// Step 5: Deregister from service discovery
	// (In real code, this would call consul/etcd/zookeeper)
	log.Println("👋 Deregistering from service discovery...")

	// Step 6: Close database connections, release resources
	log.Println("🧹 Releasing resources...")

	log.Println("✅ Graceful shutdown complete")
	return nil
}

// RunWithGracefulShutdown sets up signal handling and runs the server
func (s *Server) RunWithGracefulShutdown() error {
	// Create channel to receive OS signals
	// SIGTERM = Kubernetes/Cloud-init termination
	// SIGINT  = Ctrl+C during local development
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGTERM, syscall.SIGINT)

	// Start server in goroutine
	serverErr := make(chan error, 1)
	go func() {
		serverErr <- s.Start(":8080")
	}()

	// Wait for either server error or signal
	select {
	case err := <-serverErr:
		// Server error (not graceful shutdown)
		return err
	case sig := <-sigChan:
		log.Printf("📥 Received signal: %v", sig)
	}

	// Graceful shutdown triggered by signal
	return s.GracefulShutdown()
}
```

### Key Production Patterns Explained

| Pattern | Why It Matters |
|---------|----------------|
| `sync.Mutex` for in-flight tracking | Prevents race condition between new requests and drain |
| Separate liveness/readiness | Liveness should be dumb; readiness checks dependencies |
| Context propagation | Ensures request-scoped cancellation works during shutdown |
| Timeout on drain | Prevents infinite hang; force kill after threshold |
| Signal handling | Must handle SIGTERM (containers) not just SIGINT (Ctrl+C) |

## Example 2: Staggered Startup - Connection Storm Prevention

### Go Implementation

```go
package main

import (
	"context"
	"fmt"
	"log"
	"math/rand"
	"sync"
	"time"
)

// ============================================================
// ❌ NAIVE APPROACH - Simultaneous startup causes connection storm
// ============================================================

// StartAllAtOnce starts all instances simultaneously
// Problem: When N instances start together:
// - Database receives N * pool_size connection requests
// - Cache (Redis) gets massive key miss storm
// - Service discovery gets registration burst
// - Network bandwidth spikes
// Result: Cascading failure, potential outage
func startAllAtOnce(instanceCount int, db *Database) {
	// All instances initialize at the same time = DISASTER
	for i := 0; i < instanceCount; i++ {
		go func(instanceID int) {
			log.Printf("Instance %d starting...", instanceID)

			// This runs concurrently for ALL instances
			db.Connect()           // Connection storm!
			db.WarmCache()         // Cache miss storm!
			db.RegisterWithLD()    // Registration burst!
		}(i)
	}
}

// ============================================================
// ✅ PRODUCTION APPROACH - Staggered startup with exponential backoff
// ============================================================

type InstanceConfig struct {
	InstanceID       int
	StartupDelay     time.Duration // Delay before this instance starts
	ConnectTimeout   time.Duration
	HealthCheckURL  string
	MaxRetries      int
}

type InstanceManager struct {
	instances map[int]*Instance
	mu        sync.RWMutex

	// Configuration for staggered startup
	baseDelay        time.Duration = 5 * time.Second  // Base delay between instances
	maxDelay         time.Duration = 60 * time.Second // Cap on delay
	jitterFactor     float64       = 0.3              // Random jitter to prevent thundering herd

	// Gradual traffic ramping
	initialWeight    int           = 10              // Start with 10% traffic
	weightIncrement  int           = 10              // Increase by 10% each interval
	weightInterval   time.Duration = 10 * time.Second // Wait between weight increases
}

func NewInstanceManager() *InstanceManager {
	return &InstanceManager{
		instances: make(map[int]*Instance),
	}
}

// Instance represents a single service instance
type Instance struct {
	ID            int
	Status        string // "starting", "healthy", "draining", "stopped"
	Weight        int    // Traffic weight for load balancer

	// Dependencies
	db      *Database
	healthy bool
}

// StartWithStagger introduces delays between instance starts
// This prevents connection storms and allows gradual warming
func (m *InstanceManager) StartWithStagger(instanceConfigs []InstanceConfig) error {
	log.Printf("🚀 Starting %d instances with staggered startup...", len(instanceConfigs))

	var wg sync.WaitGroup

	for i, config := range instanceConfigs {
		wg.Add(1)

		// Calculate stagger delay
		// First instance starts immediately
		// Each subsequent instance delays by: baseDelay * (i ^ exponent) + jitter
		// This creates an exponential curve: 0s, 5s, 15s, 35s, 60s (capped)
		delay := m.calculateStaggerDelay(i)

		go func(cfg InstanceConfig, delay time.Duration) {
			defer wg.Done()

			if delay > 0 {
				log.Printf("Instance %d: Waiting %v before starting...", cfg.InstanceID, delay)
				time.Sleep(delay)
			}

			m.startInstance(cfg)
		}(config, delay)
	}

	wg.Wait()
	log.Println("✅ All instances started")

	return nil
}

// calculateStaggerDelay computes the delay for instance i
// Uses exponential backoff with jitter to prevent thundering herd
func (m *InstanceManager) calculateStaggerDelay(instanceIndex int) time.Duration {
	if instanceIndex == 0 {
		return 0 // First instance starts immediately
	}

	// Exponential backoff: base * 2^(index-1)
	// But capped at maxDelay to prevent unreasonable wait times
	rawDelay := m.baseDelay * time.Duration(1<<uint(instanceIndex-1))
	if rawDelay > m.maxDelay {
		rawDelay = m.maxDelay
	}

	// Add jitter to prevent synchronized retries
	// If all instances fail at once, they'll all retry at the same time
	jitter := time.Duration(rand.Float64() * m.jitterFactor * float64(rawDelay))

	return rawDelay + jitter
}

// startInstance performs the actual instance startup sequence
func (m *InstanceManager) startInstance(config InstanceConfig) error {
	instance := &Instance{
		ID:     config.InstanceID,
		Status: "starting",
		db:     &Database{},
	}

	m.mu.Lock()
	m.instances[config.InstanceID] = instance
	m.mu.Unlock()

	log.Printf("Instance %d: Starting initialization...", config.InstanceID)

	ctx, cancel := context.WithTimeout(context.Background(), config.ConnectTimeout)
	defer cancel()

	// Step 1: Initialize connection pool (NOT connect yet)
	if err := instance.db.InitPool(ctx); err != nil {
		log.Printf("Instance %d: ❌ Pool init failed: %v", config.InstanceID, err)
		instance.Status = "failed"
		return err
	}

	// Step 2: Connect and verify
	if err := instance.db.Connect(ctx); err != nil {
		log.Printf("Instance %d: ❌ Connect failed: %v", config.InstanceID, err)
		instance.Status = "failed"
		return err
	}

	// Step 3: Warm cache before accepting traffic
	// Staff-level insight: This is the key to avoiding cache miss storms
	// Without warming, first request to each key causes DB load
	log.Printf("Instance %d: Warming cache...", config.InstanceID)
	if err := instance.db.WarmCache(ctx); err != nil {
		log.Printf("Instance %d: ⚠️ Cache warm failed (non-fatal): %v", config.InstanceID, err)
		// Don't fail startup - cache miss is recoverable
	}

	// Step 4: Register with load balancer with INITIAL WEIGHT
	// Start at 10% traffic, increase gradually
	instance.Weight = m.initialWeight
	instance.healthy = true

	// In real code: call load balancer API to register with weight
	// e.g., AWS ALB target group weight, Consul service registration with meta
	log.Printf("Instance %d: Registered with weight %d%%", config.InstanceID, instance.Weight)
	instance.Status = "healthy"

	// Step 5: Gradual traffic ramp-up
	// This prevents the "pre-warming failure" scenario
	m.rampUpTraffic(instance, config.InstanceID)

	return nil
}

// rampUpTraffic gradually increases traffic to the instance
// This is how you prevent pre-warming failures in production
func (m *InstanceManager) rampUpTraffic(instance *Instance, instanceID int) {
	if instance.Weight >= 100 {
		return // Already at full weight
	}

	// Schedule weight increases
	go func() {
		for weight := m.initialWeight; weight <= 100; weight += m.weightIncrement {
			select {
			case <-time.After(m.weightInterval):
				m.mu.Lock()
				if instance.Status == "healthy" {
					instance.Weight = weight
					// Update load balancer weight
					log.Printf("Instance %d: 📈 Increased weight to %d%%", instanceID, weight)
				}
				m.mu.Unlock()
			}
		}
	}()
}

// Database simulates a database connection
type Database struct {
	connected bool
	poolSize  int
}

func (d *Database) InitPool(ctx context.Context) error {
	// Simulate pool initialization
	time.Sleep(100 * time.Millisecond)
	d.poolSize = 10 // Default pool size
	log.Printf("Database pool initialized with size %d", d.poolSize)
	return nil
}

func (d *Database) Connect(ctx context.Context) error {
	// Simulate connection with timeout
	time.Sleep(200 * time.Millisecond)
	d.connected = true
	log.Println("Database connected")
	return nil
}

func (d *Database) WarmCache(ctx context.Context) error {
	// Simulate cache warming - loading hot keys
	time.Sleep(500 * time.Millisecond)
	log.Println("Cache warmed")
	return nil
}

// Example usage
func main() {
	manager := NewInstanceManager()

	// Create 5 instance configs
	configs := make([]InstanceConfig, 5)
	for i := range configs {
		configs[i] = InstanceConfig{
			InstanceID:      i,
			StartupDelay:     time.Duration(i) * 5 * time.Second,
			ConnectTimeout:   30 * time.Second,
			MaxRetries:      3,
		}
	}

	db := &Database{}
	if err := manager.StartWithStagger(configs); err != nil {
		log.Printf("Startup failed: %v", err)
	}

	// Keep main goroutine alive
	select {}
}
```

### Key Patterns Explained

| Pattern | Purpose | Production Impact |
|---------|---------|-------------------|
| Exponential backoff delay | Space out instance starts | Prevents connection storms |
| Jitter | Randomize timing | Prevents thundering herd on retry |
| Initial weight 10% | Start with minimal traffic | Catches issues before full load |
| Gradual ramp-up | Increase traffic over time | Allows monitoring of behavior |
| Cache warming | Pre-populate hot cache | Prevents cache miss storms |
