package main

import (
	"context"
	"fmt"
	"runtime"
	"sync"
	"time"
)

// =============================================================================
// PROBLEM DEMONSTRATION: Memory Leaks and Resource Management
// =============================================================================
// This demonstrates Axis 1 (Time) of the production gap:
// - Test runs for minutes -> leaks are invisible
// - Production runs for days -> leaks crash the system

// ------------------------------------------------------------------
// NAIVE APPROACH: Resource leaks that accumulate over time
// ------------------------------------------------------------------

type NaiveCache struct {
	mu    sync.Mutex
	items map[string]interface{}
}

func NewNaiveCache() *NaiveCache {
	// Staff note: This looks fine but has a subtle bug.
	// The map grows forever - no eviction, no size limit.
	// In test (5 minute run), this is fine.
	// In production (30 day run), this consumes all memory.
	return &NaiveCache{
		items: make(map[string]interface{}),
	}
}

func (c *NaiveCache) Set(key string, value interface{}) {
	c.mu.Lock()
	defer c.mu.Unlock()
	// BUG: Never removes items - grows unbounded
	c.items[key] = value
}

func (c *NaiveCache) Get(key string) (interface{}, bool) {
	c.mu.Lock()
	defer c.mu.Unlock()
	val, ok := c.items[key]
	return val, ok
}

// PROBLEM: This cache will eventually consume all available memory.
// At 1KB per entry and 1000 entries/second:
// - 1 hour: 3.6M entries = 3.6GB
// - 1 day: 86M entries = 86GB
// - Crash: OOM killer

// ------------------------------------------------------------------
// PRODUCTION APPROACH: Bounded cache with eviction
// ------------------------------------------------------------------

type BoundedCache struct {
	mu           sync.Mutex
	items        map[string]interface{}
	maxSize      int
	evictCount   int
	accessOrder  []string // Simple LRU tracking
}

func NewBoundedCache(maxSize int) *BoundedCache {
	return &BoundedCache{
		items:   make(map[string]interface{}, maxSize),
		maxSize: maxSize,
	}
}

func (c *BoundedCache) Set(key string, value interface{}) {
	c.mu.Lock()
	defer c.mu.Unlock()

	// Already exists - just update
	if _, ok := c.items[key]; ok {
		c.items[key] = value
		return
	}

	// Evict if at capacity (simple FIFO - use ring buffer for true LRU)
	for len(c.items) >= c.maxSize && len(c.items) > 0 {
		// Remove oldest item
		oldest := c.accessOrder[0]
		delete(c.items, oldest)
		c.accessOrder = c.accessOrder[1:]
		c.evictCount++
	}

	c.items[key] = value
	c.accessOrder = append(c.accessOrder, key)
}

func (c *BoundedCache) Get(key string) (interface{}, bool) {
	c.mu.Lock()
	defer c.mu.Unlock()
	val, ok := c.items[key]
	return val, ok
}

func (c *BoundedCache) Stats() (size, evictions int) {
	c.mu.Lock()
	defer c.mu.Unlock()
	return len(c.items), c.evictCount
}

// ------------------------------------------------------------------
// NAIVE APPROACH: goroutine leaks
// ------------------------------------------------------------------

// SpawnGoroutinesNaive demonstrates a common mistake:
// spawning goroutines without any way to stop them

func SpawnGoroutinesNaive() {
	// Staff note: This is what most developers write.
	// It works fine in short-lived tests.
	// In production HTTP servers, this leaks goroutines on each request.

	for i := 0; i < 100; i++ {
		go func() {
			// Simulate work - but no way to cancel!
			time.Sleep(10 * time.Millisecond)
			// This goroutine just dies
		}()
	}
	// The goroutines are still running even after this function returns!
	// In a long-running server, these accumulate.
}

// ------------------------------------------------------------------
// PRODUCTION APPROACH: goroutine lifecycle management
// ------------------------------------------------------------------

type WorkerPool struct {
	jobs    chan func() // Buffered job queue
	workers int
	wg      sync.WaitGroup
	ctx     context.Context
	cancel  context.CancelFunc
}

func NewWorkerPool(workers, queueSize int) *WorkerPool {
	ctx, cancel := context.WithCancel(context.Background())
	return &WorkerPool{
		jobs:    make(chan func(), queueSize),
		workers: workers,
		ctx:     ctx,
		cancel:  cancel,
	}
}

func (p *WorkerPool) Start() {
	// Staff note: Proper lifecycle management.
	// - Fixed number of workers (not unbounded goroutines)
	// - Context for cancellation
	// - WaitGroup for graceful shutdown

	for i := 0; i < p.workers; i++ {
		p.wg.Add(1)
		go func() {
			defer p.wg.Done()
			for {
				select {
				case job, ok := <-p.jobs:
					if !ok {
						return // Channel closed
					}
					job()
				case <-p.ctx.Done():
					return // Cancelled
				}
			}
		}()
	}
}

func (p *WorkerPool) Submit(job func()) bool {
	select {
	case p.jobs <- job:
		return true
	case <-p.ctx.Done():
		return false
	default:
		return false // Queue full - reject
	}
}

func (p *WorkerPool) Stop() {
	// Graceful shutdown: wait for in-flight work
	p.cancel()        // Tell workers to stop
	close(p.jobs)     // Drain queue
	p.wg.Wait()       // Wait for workers to finish
}

// ------------------------------------------------------------------
// DEMONSTRATION: Memory growth comparison
// ------------------------------------------------------------------

func demonstrateMemoryLeak() {
	// Show memory stats
	printMemStats := func(label string) {
		var m runtime.MemStats
		runtime.ReadMemStats(&m)
		fmt.Printf("%s: Alloc = %v MiB", label, m.Alloc/1024/1024)
	}

	// NAIVE CACHE: Unbounded growth
	fmt.Println("\n=== NAIVE CACHE (unbounded) ===")
	naive := NewNaiveCache()
	for i := 0; i < 100000; i++ {
		naive.Set(fmt.Sprintf("key-%d", i), make([]byte, 1024)) // 1KB per entry
		if i%10000 == 0 {
			printMemStats(fmt.Sprintf("After %d entries", i))
			fmt.Println()
		}
	}

	// PRODUCTION CACHE: Bounded
	fmt.Println("\n=== PRODUCTION CACHE (bounded) ===")
	production := NewBoundedCache(1000) // Max 1000 entries
	for i := 0; i < 100000; i++ {
		production.Set(fmt.Sprintf("key-%d", i), make([]byte, 1024))
		if i%10000 == 0 {
			size, evictions := production.Stats()
			printMemStats(fmt.Sprintf("After %d entries", i))
			fmt.Printf(" | Size: %d, Evictions: %d\n", size, evictions)
		}
	}
}

// =============================================================================
// STAFF ENGINEER INSIGHT
// =============================================================================
//
// The production gap in this example:
// - TEST: Runs for minutes, memory leak is invisible
// - PROD: Runs for days, memory grows until OOM
//
// What you learn from this:
// 1. Always bound resources (caches, pools, queues)
// 2. Implement proper lifecycle management (start/stop)
// 3. Use context for cancellation propagation
// 4. Monitor memory usage in production
//
// At Netflix scale: They use Hystrix and cache eviction policies
// that consider both size AND time (TTL).
//
// The 2013 time bomb (chapter mentions): A library that accumulated
// data over 248 days (2^31 milliseconds) caused cascading failures.
// This is Axis 1 (Time) in action.

func main() {
	// Demonstrate the memory difference
	// In real test, this would show the naive cache consuming GBs
	// while bounded cache stays constant

	fmt.Println("Memory leak demonstration complete")
}
