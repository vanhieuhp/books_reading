# Chapter 9 Code Lab: Building a Control Plane Service Registry

## 🧪 Lab: Building a Production-Grade Service Registry

**Goal:** Implement a production-grade service registry with health checks in Go

**⏱ Time:** ~30-45 minutes

**🛠 Requirements:**
- Go 1.20+
- Basic understanding of Go concurrency (goroutines, channels, mutexes)

---

## Learning Objectives

By completing this lab, you will:
1. Understand the difference between naive and production-grade service discovery
2. Implement health checking with TTL and timeout detection
3. Add background health checker goroutines
4. Integrate circuit breaker patterns for fault tolerance

---

## Step 1: Setup

Create a new Go module:

```bash
mkdir control-plane-lab
cd control-plane-lab
go mod init control-plane-lab
```

Create the main file:

```bash
touch main.go
```

---

## Step 2: Implement Naive Registry (with problems)

Add this to `main.go`:

```go
package main

import (
	"fmt"
	"sync"
)

// Naive service registry - no health checks, no TTL
type NaiveRegistry struct {
	services map[string][]string
	mu       sync.Mutex
}

func NewNaiveRegistry() *NaiveRegistry {
	return &NaiveRegistry{
		services: make(map[string][]string),
	}
}

func (r *NaiveRegistry) Register(serviceName, address string) {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.services[serviceName] = append(r.services[serviceName], address)
}

func (r *NaiveRegistry) Discover(serviceName string) []string {
	r.mu.Lock()
	defer r.mu.Unlock()
	return r.services[serviceName]
}

func main() {
	registry := NewNaiveRegistry()

	// Register services
	registry.Register("users", "10.0.0.1:8080")
	registry.Register("users", "10.0.0.2:8080")
	registry.Register("orders", "10.0.1.1:8080")

	// Discover - returns ALL instances including dead ones
	instances := registry.Discover("users")
	fmt.Printf("Found %d users instances: %v\n", len(instances), instances)
}
```

**Run:**
```bash
go run main.go
```

**Expected output:**
```
Found 2 users instances: [10.0.0.1:8080 10.0.0.2:8080]
```

**Problems to identify:**
1. No validation of inputs
2. No thread safety
3. Returns ALL instances including crashed ones
4. No heartbeat mechanism
5. No TTL/expiration

---

## Step 3: Add Health Check Types

Let's implement a production-grade registry with health checking:

```go
package main

import (
	"fmt"
	"sync"
	"time"
)

// Health check types
type HealthStatus int

const (
	StatusUnknown HealthStatus = iota
	StatusHealthy
	StatusUnhealthy
)

type ServiceInstance struct {
	ID       string
	Address  string
	Port     int
	Status   HealthStatus
	LastSeen time.Time
	Metadata map[string]string
}

type RegistryWithHealth struct {
	instances map[string]map[string]*ServiceInstance // service -> address -> instance
	mu        sync.RWMutex

	heartbeatTimeout time.Duration
}

func NewRegistryWithHealth() *RegistryWithHealth {
	return &RegistryWithHealth{
		instances:        make(map[string]map[string]*ServiceInstance),
		heartbeatTimeout: 30 * time.Second,
	}
}

func (r *RegistryWithHealth) Register(serviceName string, instance ServiceInstance) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	if r.instances[serviceName] == nil {
		r.instances[serviceName] = make(map[string]*ServiceInstance)
	}

	instance.Status = StatusHealthy
	instance.LastSeen = time.Now()
	r.instances[serviceName][instance.Address] = &instance

	return nil
}

func (r *RegistryWithHealth) Heartbeat(serviceName, address string) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	serviceInstances, ok := r.instances[serviceName]
	if !ok {
		return fmt.Errorf("service not found: %s", serviceName)
	}

	instance, ok := serviceInstances[address]
	if !ok {
		return fmt.Errorf("instance not found: %s", address)
	}

	instance.LastSeen = time.Now()
	instance.Status = StatusHealthy

	return nil
}

// Discover only returns healthy instances
func (r *RegistryWithHealth) Discover(serviceName string) []*ServiceInstance {
	r.mu.RLock()
	defer r.mu.RUnlock()

	var healthy []*ServiceInstance

	serviceInstances, ok := r.instances[serviceName]
	if !ok {
		return healthy
	}

	for _, instance := range serviceInstances {
		if instance.Status == StatusHealthy {
			healthy = append(healthy, instance)
		}
	}

	return healthy
}

func main() {
	registry := NewRegistryWithHealth()

	// Register instances
	registry.Register("users", ServiceInstance{
		ID:      "users",
		Address: "10.0.0.1",
		Port:    8080,
	})

	registry.Register("users", ServiceInstance{
		ID:      "users",
		Address: "10.0.0.2",
		Port:    8080,
	})

	// Simulate heartbeat from instance 1 only
	registry.Heartbeat("users", "10.0.0.1")

	// Discover - should only return healthy instance
	instances := registry.Discover("users")
	fmt.Printf("Healthy instances: %d\n", len(instances))
	for _, i := range instances {
		fmt.Printf("  - %s:%d (status: %v)\n", i.Address, i.Port, i.Status)
	}
}
```

**Run:**
```bash
go run main.go
```

**Expected output:**
```
Healthy instances: 1
  - 10.0.0.1:8080 (status: 1)
```

**Observation:** Instance 2 is not returned because it never sent a heartbeat — it's implicitly unhealthy.

---

## Step 4: Add Background Health Checker

Add automatic health checking that runs in the background:

```go
// Add these methods to RegistryWithHealth

func (r *RegistryWithHealth) StartHealthChecker(ctx context.Context) {
	ticker := time.NewTicker(10 * time.Second)
	defer ticker.Stop()

	fmt.Println("[HealthChecker] Started")

	for {
		select {
		case <-ctx.Done():
			fmt.Println("[HealthChecker] Stopped")
			return
		case <-ticker.C:
			r.checkHealth()
		}
	}
}

func (r *RegistryWithHealth) checkHealth() {
	r.mu.Lock()
	defer r.mu.Unlock()

	now := time.Now()
	checkCount := 0
	unhealthyCount := 0

	for _, instances := range r.instances {
		for addr, instance := range instances {
			checkCount++
			elapsed := now.Sub(instance.LastSeen)
			if elapsed > r.heartbeatTimeout {
				if instance.Status != StatusUnhealthy {
					instance.Status = StatusUnhealthy
					unhealthyCount++
					fmt.Printf("[HealthCheck] Instance %s:%d is UNHEALTHY (no heartbeat for %v)\n",
						instance.Address, instance.Port, elapsed)
				}
			}
		}
	}

	if checkCount > 0 {
		fmt.Printf("[HealthCheck] Checked %d instances, %d marked unhealthy\n", checkCount, unhealthyCount)
	}
}
```

Update main to use the health checker:

```go
func main() {
	registry := NewRegistryWithHealth()

	// Register instances
	registry.Register("users", ServiceInstance{
		ID:      "users",
		Address: "10.0.0.1",
		Port:    8080,
	})

	registry.Register("users", ServiceInstance{
		ID:      "users",
		Address: "10.0.0.2",
		Port:    8080,
	})

	// Start health checker in background
	ctx, cancel := context.WithCancel(context.Background())
	go registry.StartHealthChecker(ctx)

	// Initial discovery - both should be healthy
	fmt.Println("\n=== Initial Discovery ===")
	instances := registry.Discover("users")
	fmt.Printf("Healthy instances: %d\n", len(instances))

	// Wait and observe health check kick in
	fmt.Println("\n=== Waiting for health check... ===")
	time.Sleep(15 * time.Second)

	// After health check, instances without heartbeat should be unhealthy
	fmt.Println("\n=== After Health Check ===")
	instances = registry.Discover("users")
	fmt.Printf("Healthy instances: %d\n", len(instances))

	// Send heartbeat to restore instance 2
	fmt.Println("\n=== Sending heartbeat to instance 2 ===")
	registry.Heartbeat("users", "10.0.0.2")

	time.Sleep(3 * time.Second)
	instances = registry.Discover("users")
	fmt.Printf("Healthy instances after heartbeat: %d\n", len(instances))

	cancel()
	time.Sleep(1 * time.Second)
}
```

**Run:**
```bash
go run main.go
```

**Expected output:**
```
=== Initial Discovery ===
Healthy instances: 2

=== Waiting for health check...
[HealthChecker] Started
[HealthCheck] Checked 2 instances, 0 marked unhealthy
[HealthCheck] Checked 2 instances, 1 marked unhealthy
[HealthCheck] Instance 10.0.0.2:8080 is UNHEALTHY (no heartbeat for 30.0001234s)

=== After Health Check ===
Healthy instances: 1

=== Sending heartbeat to instance 2 ===
[HealthCheck] Checked 2 instances, 0 marked unhealthy

Healthy instances after heartbeat: 2
```

---

## Step 5: Add Circuit Breaker Integration

This is the staff-level extension - adding circuit breaker for fault tolerance:

```go
// Circuit breaker states for service calls
type CircuitState int

const (
	CircuitClosed CircuitState = iota
	CircuitOpen
	CircuitHalfOpen
)

type CircuitBreaker struct {
	failures        int
	threshold       int
	timeout         time.Duration
	state           CircuitState
	lastFailureTime time.Time
	mu              sync.Mutex
}

func NewCircuitBreaker(threshold int, timeout time.Duration) *CircuitBreaker {
	return &CircuitBreaker{
		threshold: threshold,
		timeout:   timeout,
		state:     CircuitClosed,
	}
}

func (cb *CircuitBreaker) RecordSuccess() {
	cb.mu.Lock()
	defer cb.mu.Unlock()
	cb.failures = 0
	cb.state = CircuitClosed
}

func (cb *CircuitBreaker) RecordFailure() {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	cb.failures++
	cb.lastFailureTime = time.Now()

	if cb.failures >= cb.threshold {
		cb.state = CircuitOpen
		fmt.Printf("[CircuitBreaker] OPEN after %d failures\n", cb.failures)
	}
}

func (cb *CircuitBreaker) AllowRequest() bool {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	switch cb.state {
	case CircuitClosed:
		return true
	case CircuitOpen:
		// Check if timeout expired, move to half-open
		if time.Since(cb.lastFailureTime) > cb.timeout {
			cb.state = CircuitHalfOpen
			fmt.Printf("[CircuitBreaker] HALF-OPEN after timeout (%v)\n", cb.timeout)
			return true
		}
		return false
	case CircuitHalfOpen:
		return true
	}
	return false
}

func (cb *CircuitBreaker) String() string {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	stateNames := []string{"CLOSED", "OPEN", "HALF-OPEN"}
	return fmt.Sprintf("CircuitBreaker(state=%s, failures=%d/%d)", stateNames[cb.state], cb.failures, cb.threshold)
}
```

Add a method to use the circuit breaker with service calls:

```go
type ServiceClient struct {
	registry  *RegistryWithHealth
	circuit   *CircuitBreaker
	serviceName string
}

func NewServiceClient(registry *RegistryWithHealth, serviceName string) *ServiceClient {
	return &ServiceClient{
		registry: circuit:   New registry,
		CircuitBreaker(3, 5*time.Second), // Open after 3 failures, test after 5s
		serviceName: serviceName,
	}
}

func (c *ServiceClient) CallService(endpoint string) error {
	// Check circuit breaker first
	if !c.circuit.AllowRequest() {
		return fmt.Errorf("circuit open - request blocked")
	}

	// Get healthy instances
	instances := c.registry.Discover(c.serviceName)
	if len(instances) == 0 {
		c.circuit.RecordFailure()
		return fmt.Errorf("no healthy instances available")
	}

	// In real implementation, you'd make HTTP/gRPC call here
	// For demo, simulate success
	fmt.Printf("[Client] Calling %s (circuit: %s)\n", c.serviceName, c.circuit)

	// Simulate occasional failures
	// failureRate := 0.3
	// if rand.Float64() < failureRate {
	//     c.circuit.RecordFailure()
	//     return fmt.Errorf("request failed")
	// }

	c.circuit.RecordSuccess()
	return nil
}
```

Add to main:

```go
func main() {
	// ... previous setup ...

	// Create service client with circuit breaker
	client := NewServiceClient(registry, "users")

	// Simulate some calls
	fmt.Println("\n=== Testing Circuit Breaker ===")
	for i := 0; i < 10; i++ {
		err := client.CallService("/api/users")
		if err != nil {
			fmt.Printf("Call %d failed: %v\n", i+1, err)
		} else {
			fmt.Printf("Call %d succeeded\n", i+1)
		}
		time.Sleep(500 * time.Millisecond)
	}

	fmt.Printf("\nFinal circuit state: %s\n", client.circuit)
}
```

---

## Step 6: Stretch Challenge (Staff-Level)

Try these extensions:

### 1. Add Service Versioning
- Add version metadata to ServiceInstance
- Add a method to discover instances by version
- This enables canary deployments

### 2. Implement Regional Routing
- Add region/availability zone to metadata
- Prefer same-region instances in Discover
- Fallback to other regions

### 3. Add Metrics Export
- Add Prometheus metrics for:
  - Registry query latency
  - Instance count by service
  - Health check success/failure rates

### 4. Implement Leader Election
- For HA registry with multiple instances
- Use etcd or Consul for consensus
- Only leader handles writes

---

## Solution Reference

Full solution available in `chapter9/code_examples.go` in the course repository.

---

## Key Takeaways

1. **Naive registries return ALL instances** — even crashed ones
2. **Health checks require TTL/timeout** — instances must prove they're alive
3. **Background health checkers** detect failures even without heartbeats
4. **Circuit breakers** prevent cascading failures
5. **Thread safety is essential** — concurrent access requires proper locking

---

## Cleanup

```bash
cd ..
rm -rf control-plane-lab
```

---

*This lab is part of the Chapter 9: Control Plane course from "Release It!" by Michael Nygard*
