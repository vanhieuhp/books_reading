package main

import (
	"context"
	"fmt"
	"math/rand"
	"sync"
	"sync/atomic"
	"time"
)

// =============================================================================
// PRODUCTION GAP DETECTOR LAB
// =============================================================================
// This lab demonstrates how to find production bugs BEFORE production.
// We'll simulate Scale, Time, and Diversity axes to expose hidden issues.

// ------------------------------------------------------------------
// THE NAIVE SERVICE: What appears to work in tests
// ------------------------------------------------------------------

type User struct {
	ID    int64
	Name  string
	Email string
}

// NaiveUserStore looks fine but has multiple production bugs:
// 1. No connection pooling (creates new "connection" per request)
// 2. Unbounded cache (grows forever)
// 3. No timeouts (waits forever)
// 4. No error handling for bad data
type NaiveUserStore struct {
	mu    sync.Mutex
	users map[int64]*User
	cache map[string]*User // unbounded cache
}

func NewNaiveUserStore() *NaiveUserStore {
	return &NaiveUserStore{
		users: make(map[int64]*User),
		cache: make(map[string]*User),
	}
}

// BUG 1: This simulates creating a new DB connection every time
// In production: O(n) database connections = connection exhaustion
func (s *NaiveUserStore) CreateUser(id int64, name, email string) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	// Simulate connection setup delay (like real DB)
	time.Sleep(1 * time.Millisecond) // This adds up!

	s.users[id] = &User{ID: id, Name: name, Email: email}

	// BUG 2: Add to cache with NO eviction - unbounded growth
	// In production: OOM after days of running
	s.cache[email] = s.users[id]

	return nil
}

// BUG 3: No timeout - can wait forever
// In production: request hangs indefinitely
func (s *NaiveUserStore) GetUserByEmail(email string) (*User, error) {
	s.mu.Lock()
	defer s.mu.Unlock()

	// Simulate slow query (like real production DB under load)
	time.Sleep(10 * time.Millisecond)

	user, ok := s.cache[email]
	if !ok {
		return nil, fmt.Errorf("user not found")
	}
	return user, nil
}

// BUG 4: No validation - accepts garbage data
// In production: bad data causes crashes or security issues
func (s *NaiveUserStore) UpdateUserName(id int64, name string) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	user, ok := s.users[id]
	if !ok {
		return fmt.Errorf("user not found")
	}

	// No validation! Accepts anything.
	// Production edge case: empty name, SQL injection, etc.
	user.Name = name
	return nil
}

// ------------------------------------------------------------------
// DETECTORS: Tests that expose the production gaps
// ------------------------------------------------------------------

// DetectorConfig configures what production aspects to simulate
type DetectorConfig struct {
	ConcurrentUsers int           // Axis 2: Scale
	Duration        time.Duration // Axis 1: Time
	InputDiversity  int           // Axis 3: Diversity (edge cases)
}

func RunProductionGapTests(cfg DetectorConfig) map[string]bool {
	results := make(map[string]bool)
	store := NewNaiveUserStore()

	var (
		errors      int64
		totalOps    int64
		maxCacheLen int64
		hungOps     int64
	)

	// Test 1: Scale Test - concurrent load
	fmt.Printf("\n=== SCALE TEST ===\n")
	fmt.Printf("Simulating %d concurrent users...\n", cfg.ConcurrentUsers)

	start := time.Now()
	ctx, cancel := context.WithTimeout(context.Background(), cfg.Duration)
	defer cancel()

	var wg sync.WaitGroup
	errorCh := make(chan error, cfg.ConcurrentUsers)

	// Simulate concurrent users (Axis 2: Scale)
	for i := 0; i < cfg.ConcurrentUsers; i++ {
		wg.Add(1)
		go func(userID int64) {
			defer wg.Done()

			// Create users
			err := store.CreateUser(userID, fmt.Sprintf("User-%d", userID), fmt.Sprintf("user%d@test.com", userID))
			if err != nil {
				atomic.AddInt64(&errors, 1)
				errorCh <- err
			}
			atomic.AddInt64(&totalOps, 1)

			// Read users
			_, err = store.GetUserByEmail(fmt.Sprintf("user%d@test.com", userID))
			if err != nil {
				atomic.AddInt64(&errors, 1)
				errorCh <- err
			}
			atomic.AddInt64(&totalOps, 1)

		}(int64(i))
	}

	// Monitor for hung operations
	go func() {
		ticker := time.NewTicker(100 * time.Millisecond)
		defer ticker.Stop()
		for {
			select {
			case <-ctx.Done():
				return
			case <-ticker.C:
				// Check if ops are stuck
				currentOps := atomic.LoadInt64(&totalOps)
				time.Sleep(50 * time.Millisecond)
				if atomic.LoadInt64(&totalOps) == currentOps {
					atomic.AddInt64(&hungOps, 1)
				}
			}
		}
	}()

	wg.Wait()
	time.Sleep(100 * time.Millisecond) // Let monitor finish
	cancel()

	elapsed := time.Since(start)
	opsPerSec := float64(totalOps) / elapsed.Seconds()

	fmt.Printf("Total operations: %d\n", totalOps)
	fmt.Printf("Errors: %d\n", errors)
	fmt.Printf("Duration: %v\n", elapsed)
	fmt.Printf("Ops/sec: %.2f\n", opsPerSec)
	fmt.Printf("Hung operations detected: %d\n", hungOps)

	// Check cache growth (Axis 1: Time)
	store.mu.Lock()
	cacheLen := len(store.cache)
	store.mu.Unlock()
	atomic.StoreInt64(&maxCacheLen, int64(cacheLen))
	fmt.Printf("Cache size: %d (unbounded growth!)\n", cacheLen)

	// Analyze results
	results["scale_test"] = errors > 0 || hungOps > 0
	results["cache_growth"] = cacheLen > cfg.ConcurrentUsers/2
	results["hung_ops"] = hungOps > 0

	return results
}

// Test 2: Diversity Test - edge cases
func RunDiversityTests(store *NaiveUserStore, numEdgeCases int) map[string]bool {
	results := make(map[string]bool)

	fmt.Printf("\n=== DIVERSITY TEST ===\n")
	fmt.Printf("Testing %d edge cases...\n", numEdgeCases)

	edgeCases := []struct {
		name  string
		id    int64
		value string
	}{
		{"empty string", 1, ""},
		{"very long string", 2, string(make([]byte, 10000))},
		{"special characters", 3, "<script>alert('xss')</script>"},
		{"null bytes", 4, "user\x00name"},
		{"unicode", 5, "用户名"},
		{"sql injection", 6, "'; DROP TABLE users; --"},
	}

	for _, tc := range edgeCases {
		err := store.UpdateUserName(tc.id, tc.value)
		if err != nil {
			fmt.Printf("  Rejected %s: %v (GOOD - should validate)\n", tc.name, err)
			results[tc.name+"_rejected"] = true
		} else {
			fmt.Printf("  Accepted %s: (BAD - no validation!)\n", tc.name)
			results[tc.name+"_accepted"] = true
		}
	}

	// Check how many were accepted without validation
	noValidationCount := 0
	for k, v := range results {
		if v && contains(k, "_accepted") {
			noValidationCount++
		}
	}
	results["no_validation"] = noValidationCount > 0

	return results
}

func contains(s, substr string) bool {
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}

// ------------------------------------------------------------------
// PRODUCTION-APPROACH: Fixed version
// ------------------------------------------------------------------

type ProductionUserStore struct {
	mu       sync.Mutex
	users    map[int64]*User
	cache    boundedCache
	parallel int           // Semaphore limit
	sem      chan struct{}
}

type boundedCache struct {
	data map[string]*User
	max  int
}

func NewProductionUserStore(maxCache int, parallel int) *ProductionUserStore {
	return &ProductionUserStore{
		users: make(map[int64]*User),
		cache: boundedCache{
			data: make(map[string]*User),
			max:  maxCache,
		},
		parallel: parallel,
		sem:      make(chan struct{}, parallel),
	}
}

func (s *ProductionUserStore) CreateUser(ctx context.Context, id int64, name, email string) error {
	// Validate input (Axis 3: Diversity)
	if name == "" {
		return fmt.Errorf("name cannot be empty")
	}
	if len(name) > 1000 {
		return fmt.Errorf("name too long")
	}

	// Semaphore for bounded concurrency (Axis 2: Scale)
	select {
	case s.sem <- struct{}{}:
		defer func() { <-s.sem }()
	case <-ctx.Done():
		return ctx.Err()
	}

	s.mu.Lock()
	defer s.mu.Unlock()

	// Bounded cache (Axis 1: Time)
	if len(s.cache.data) >= s.cache.max {
		// Simple eviction - in production use LRU
		for k := range s.cache.data {
			delete(s.cache.data, k)
			break
		}
	}

	s.users[id] = &User{ID: id, Name: name, Email: email}
	s.cache.data[email] = s.users[id]

	return nil
}

// ------------------------------------------------------------------
// MAIN: Run the demonstration
// ------------------------------------------------------------------

func main() {
	fmt.Println("========================================")
	fmt.Println("PRODUCTION GAP DETECTOR")
	fmt.Println("========================================")

	// Configuration simulating production:
	// - 100 concurrent users (Axis 2: Scale)
	// - 10 second test (Axis 1: Time - compressed)
	// - Edge case inputs (Axis 3: Diversity)
	cfg := DetectorConfig{
		ConcurrentUsers: 100,
		Duration:        10 * time.Second,
		InputDiversity:  10,
	}

	results := RunProductionGapTests(cfg)

	fmt.Println("\n=== RESULTS ===")
	for k, v := range results {
		status := "PASS"
		if v {
			status = "FAIL (production gap found!)"
		}
		fmt.Printf("  %s: %s\n", k, status)
	}

	// Diversity test
	store := NewNaiveUserStore()
	for i := int64(0); i < 10; i++ {
		store.CreateUser(i, fmt.Sprintf("User-%d", i), fmt.Sprintf("user%d@test.com", i))
	}
	diversityResults := RunDiversityTests(store, 10)

	fmt.Println("\n=== DIVERSITY RESULTS ===")
	for k, v := range diversityResults {
		if contains(k, "_accepted") && v {
			fmt.Printf("  %s: UNSAFE - no validation\n", k)
		}
	}

	// Summary
	fmt.Println("\n========================================")
	fmt.Println("PRODUCTION GAPS DETECTED:")
	if results["scale_test"] {
		fmt.Println("  - Scale: Concurrency issues under load")
	}
	if results["cache_growth"] {
		fmt.Println("  - Time: Memory leak from unbounded cache")
	}
	if results["hung_ops"] {
		fmt.Println("  - Scale: Operations hanging under contention")
	}
	if diversityResults["no_validation"] {
		fmt.Println("  - Diversity: No input validation (security risk)")
	}
	fmt.Println("========================================")

	// Prevent unused import warning
	_ = rand.Int()
}
