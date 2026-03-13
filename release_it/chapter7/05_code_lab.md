# 🧪 Code Lab: Building a Production-Ready Instance Manager

## Lab Overview

In this lab, you'll build a production-grade instance manager in Go that demonstrates:
- Graceful shutdown with proper drain handling
- Health checks (readiness vs liveness)
- Staggered startup to prevent connection storms
- Metrics emission for monitoring

**Goal**: Build a service that handles SIGTERM gracefully, tracks in-flight requests, and implements proper health endpoints.

**Time**: ~30-45 minutes

**Requirements**:
- Go 1.21+ installed
- Basic understanding of HTTP servers and context cancellation

---

## Step 1: Project Setup

Create a new Go project:

```bash
mkdir -p ~/instance-lab
cd ~/instance-lab
go mod init instance-lab
```

Create the main file:

```go
// main.go
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

func main() {
	log.Println("Starting Instance Lab...")

	// Your implementation goes here

	log.Println("Server stopped")
}
```

---

## Step 2: Implement the Server with Graceful Shutdown

**Task**: Implement an HTTP server that handles graceful shutdown.

**What to build**:
1. HTTP server with `/health/liveness` and `/health/readiness` endpoints
2. Signal handling for SIGTERM/SIGINT
3. In-flight request tracking
4. Drain timeout mechanism

**Starter code** (add to main.go):

```go
type Server struct {
	mu           sync.Mutex
	inFlight     int
	shuttingDown bool
	drainTimeout time.Duration
	server       *http.Server
}

func NewServer() *Server {
	return &Server{
		drainTimeout: 30 * time.Second,
	}
}

func (s *Server) handleRequest(w http.ResponseWriter, r *http.Request) {
	// TODO Step 2: Track in-flight requests
	// 1. Increment inFlight counter (with mutex)
	// 2. Check if shutting down - if so, return 503
	// 3. Process request (simulate work)
	// 4. Decrement inFlight counter (defer)

	// Simulate request processing
	time.Sleep(100 * time.Millisecond)
	w.Write([]byte(`{"status":"ok","message":"request processed"}`))
}

func (s *Server) handleLiveness(w http.ResponseWriter, r *http.Request) {
	// TODO Step 2: Simple liveness check
	// Just return 200 - process is alive
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(`{"alive":true}`))
}

func (s *Server) handleReadiness(w http.ResponseWriter, r *http.Request) {
	// TODO Step 2: Readiness check
	// Check if we're shutting down - if so, return 503
	// Otherwise return 200

	s.mu.Lock()
	shuttingDown := s.shuttingDown
	s.mu.Unlock()

	if shuttingDown {
		w.WriteHeader(http.StatusServiceUnavailable)
		w.Write([]byte(`{"ready":false,"reason":"draining"}`))
		return
	}

	w.WriteHeader(http.StatusOK)
	w.Write([]byte(`{"ready":true}`))
}
```

**Expected behavior**:
- Server starts on port 8080
- `/health/liveness` always returns 200
- `/health/readiness` returns 200 unless draining

---

## Step 3: Implement Graceful Shutdown

**Task**: Add proper shutdown sequence that drains in-flight requests.

**What to build**:
1. Signal handling setup
2. Drain mechanism with timeout
3. Server shutdown

**Add to main.go**:

```go
func (s *Server) gracefulShutdown() error {
	log.Println("🔄 Starting graceful shutdown...")

	// Step 1: Stop accepting new requests
	s.mu.Lock()
	s.shuttingDown = true
	s.mu.Unlock()

	log.Println("🚦 Stopped accepting new requests")

	// Step 2: Wait for in-flight requests to complete
	log.Printf("⏳ Draining in-flight requests (max %v)...", s.drainTimeout)

	drainTimer := time.NewTimer(s.drainTimeout)
	drainDone := make(chan struct{})

	go func() {
		s.waitForDrain()
		close(drainDone)
	}()

	select {
	case <-drainDone:
		drainTimer.Stop()
		log.Println("✅ Drain completed - all requests finished")
	case <-drainTimer.C:
		log.Println("⚠️ Drain timeout - forcing shutdown")
	}

	// Step 3: Close HTTP server
	log.Println("🔌 Closing HTTP server...")
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	if err := s.server.Shutdown(ctx); err != nil {
		log.Printf("❌ Server shutdown error: %v", err)
	}

	log.Println("✅ Graceful shutdown complete")
	return nil
}

func (s *Server) waitForDrain() {
	for {
		s.mu.Lock()
		count := s.inFlight
		s.mu.Unlock()

		if count == 0 {
			return
		}

		log.Printf("⏳ Waiting for %d in-flight requests...", count)
		time.Sleep(500 * time.Millisecond)
	}
}
```

**Test it**:

```bash
go run main.go &
SERVER_PID=$!
sleep 2

# Make a request
curl http://localhost:8080/

# Send SIGTERM
kill $SERVER_PID

# Watch the graceful shutdown logs
```

**Expected output**:
```
🔄 Starting graceful shutdown...
🚦 Stopped accepting new requests
⏳ Draining in-flight requests (max 30s)...
✅ Drain completed - all requests finished
🔌 Closing HTTP server...
✅ Graceful shutdown complete
```

---

## Step 4: Add Metrics and Monitoring

**Task**: Emit metrics so operations can observe the instance lifecycle.

**What to build**:
1. Request counter (total, success, failed)
2. In-flight gauge
3. Response time histogram

**Add metrics structure**:

```go
type Metrics struct {
	mu           sync.Mutex
	requestsTotal    int
	requestsSuccess  int
	requestsFailed   int
	inflightGauge   int
	responseTimes   []time.Duration // Rolling window
}

func NewMetrics() *Metrics {
	return &Metrics{
		responseTimes: make([]time.Duration, 0, 1000),
	}
}

func (m *Metrics) RecordRequest(success bool, duration time.Duration) {
	m.mu.Lock()
	defer m.mu.Unlock()

	m.requestsTotal++
	if success {
		m.requestsSuccess++
	} else {
		m.requestsFailed++
	}

	// Keep only last 1000 response times
	m.responseTimes = append(m.responseTimes, duration)
	if len(m.responseTimes) > 1000 {
		m.responseTimes = m.responseTimes[1:]
	}
}

func (m *Metrics) GetStats() map[string]interface{} {
	m.mu.Lock()
	defer m.mu.Unlock()

	// Calculate p50, p95, p99
	var sorted []time.Duration
	sorted = make([]time.Duration, len(m.responseTimes))
	copy(sorted, m.responseTimes)
	// (In real code, use sort.Slice)

	return map[string]interface{}{
		"requests_total":   m.requestsTotal,
		"requests_success": m.requestsSuccess,
		"requests_failed":  m.requestsFailed,
		"inflight":         m.inflightGauge,
	}
}
```

Add `/metrics` endpoint:

```go
func (s *Server) handleMetrics(w http.ResponseWriter, r *http.Request) {
	stats := s.metrics.GetStats()
	w.WriteHeader(http.StatusOK)
	fmt.Fprintf(w, `{"total":%d,"success":%d,"failed":%d,"inflight":%d}`,
		stats["requests_total"],
		stats["requestsSuccess"],
		stats["requestsFailed"],
		stats["inflight"],
	)
}
```

---

## Step 5: Implement Staggered Startup (Bonus Challenge)

**Task**: Create a simulation that demonstrates staggered vs simultaneous startup.

Add a standalone program that shows the difference:

```go
// startup_sim.go
package main

import (
	"fmt"
	"log"
	"math/rand"
	"time"
)

type Instance struct {
	ID          int
	StartTime   time.Time
	ReadyTime   time.Time
	ConnectTime time.Duration
}

func startAllAtOnce(instanceCount int) []Instance {
	instances := make([]Instance, instanceCount)

	log.Printf("Starting %d instances simultaneously...", instanceCount)
	start := time.Now()

	for i := 0; i < instanceCount; i++ {
		go func(id int) {
			// Simulate connection pool creation
			connectTime := time.Duration(100+rand.Intn(200)) * time.Millisecond
			time.Sleep(connectTime)

			instances[id] = Instance{
				ID:          id,
				StartTime:   start,
				ReadyTime:   time.Now(),
				ConnectTime: connectTime,
			}
		}(i)
	}

	// Wait for all
	time.Sleep(1 * time.Second)

	return instances
}

func startStaggered(instanceCount int, baseDelay time.Duration) []Instance {
	instances := make([]Instance, instanceCount)

	log.Printf("Starting %d instances with stagger...", instanceCount)
	start := time.Now()

	for i := 0; i < instanceCount; i++ {
		// Exponential backoff with jitter
		delay := baseDelay * time.Duration(i)
		jitter := time.Duration(rand.Float64() * float64(delay) * 0.3)

		go func(id int, delay time.Duration) {
			if delay > 0 {
				time.Sleep(delay)
			}

			connectTime := time.Duration(100+rand.Intn(200)) * time.Millisecond
			time.Sleep(connectTime)

			instances[id] = Instance{
				ID:          id,
				StartTime:   start,
				ReadyTime:   time.Now(),
				ConnectTime: connectTime,
			}
		}(i, delay+jitter)
	}

	// Wait for all
	time.Sleep(5 * time.Second)

	return instances
}

func main() {
	rand.Seed(time.Now().UnixNano())

	// Run simultaneous startup
	simultaneous := startAllAtOnce(10)
	totalTime := time.Since(simultaneous[0].StartTime)
	fmt.Printf("Simultaneous: All started in %v\n", totalTime)

	// Run staggered startup
	staggered := startStaggered(10, 500*time.Millisecond)
	totalTime = time.Since(staggered[0].StartTime)
	fmt.Printf("Staggered: All started in %v\n", totalTime)
}
```

---

## Step 6: Verify Your Implementation

### Test graceful shutdown:

```bash
# Terminal 1: Start server
go run main.go

# Terminal 2: Send continuous requests
for i in {1..100}; do
  curl -s http://localhost:8080/ > /dev/null
  echo "Request $i done"
done &

# Terminal 1: Watch logs, then kill
# Press Ctrl+C or: kill -TERM $(pgrep main)
```

### Test health endpoints:

```bash
# Check liveness
curl http://localhost:8080/health/liveness
# Expected: {"alive":true}

# Check readiness
curl http://localhost:8080/health/readiness
# Expected: {"ready":true}

# During shutdown
# Expected: {"ready":false,"reason":"draining"}
```

### Check metrics:

```bash
curl http://localhost:8080/metrics
# Expected: {"total":N,"success":M,"failed":K,"inflight":0}
```

---

## 🎯 Success Criteria

| Criterion | How to Verify |
|-----------|---------------|
| Graceful shutdown works | Send requests while killing server - all complete |
| Liveness always 200 | `/health/liveness` returns 200 even during drain |
| Readiness 503 during drain | `/health/readiness` returns 503 after SIGTERM |
| In-flight tracking | Check metrics show correct in-flight count |
| No resource leaks | Server exits cleanly, no hanging goroutines |

---

## 🔄 Stretch Challenge (Staff-Level Extension)

1. **Add request context cancellation**: Propagate context through requests so shutdown cancels long-running operations
2. **Implement weighted load balancing**: Add an endpoint to get weight, simulate traffic ramping
3. **Add connection pool management**: Simulate database connections with proper cleanup
4. **Create integration test**: Script that verifies the entire lifecycle

---

## Summary

In this lab, you built:
- ✅ HTTP server with proper signal handling
- ✅ Graceful shutdown with drain timeout
- ✅ In-flight request tracking
- ✅ Health check endpoints (liveness + readiness)
- ✅ Metrics emission

These are the building blocks of any production-grade service. The patterns you implemented here apply whether you're running on Kubernetes, ECS, or bare metal.
