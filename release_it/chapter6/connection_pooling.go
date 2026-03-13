package main

import (
	"context"
	"fmt"
	"net"
	"net/http"
	"os"
	"sync"
	"time"

	"github.com/jackc/pgx/v4/pgxpool"
)

// ❌ NAIVE APPROACH: Creating new connection for each request
// Problem: TCP handshake overhead (~30-50ms per connection)
// At scale: Connection exhaustion, latency spikes, potential cascade failures
func naiveHTTPClient() {
	// Creating a new HTTP client WITHOUT timeout or connection reuse
	// This is what most junior developers do
	client := &http.Client{
		// NO Transport means default with limited connections
		// Each request gets new TCP connection
	}

	for i := 0; i < 100; i++ {
		go func() {
			resp, err := client.Get("https://api.example.com/data")
			if err != nil {
				fmt.Println("Error:", err)
				return
			}
			defer resp.Body.Close()
			// Process response...
		}()
	}
}

// ✅ PRODUCTION APPROACH: Properly configured HTTP client
// Why: Connection pooling amortizes TCP handshake cost across requests
// Trade-off: Uses more memory for idle connections, but worth it for latency
func productionHTTPClient() *http.Client {
	// staff-level: This is what separates production-grade code from demos
	return &http.Client{
		// Timeout prevents resource exhaustion from hanging requests
		Timeout: 10 * time.Second,

		// Transport is where connection pooling happens
		Transport: &http.Transport{
			// staff-level: These numbers should be tuned based on your traffic
			// MaxIdleConns: Warm connections kept ready
			MaxIdleConns: 100,

			// MaxIdleConnsPerHost: Connections per destination
			// staff-level: Set to expected concurrent request volume
			MaxIdleConnsPerHost: 50,

			// IdleConnTimeout: How long to keep warm connections
			// staff-level: Balance memory vs. connection reuse
			IdleConnTimeout: 90 * time.Second,

			// ResponseHeaderTimeout: Detect slow responses
			ResponseHeaderTimeout: 5 * time.Second,

			// ExpectContinueTimeout: For large uploads with 100-Continue
			ExpectContinueTimeout: 1 * time.Second,
		},
	}
}

// Database connection pool example (using pgx for PostgreSQL)
// This is a production-ready pattern for database connections
func productionDBPool() (*pgxpool.Pool, error) {
	// staff-level: Database connections are MORE expensive than HTTP
	// because they maintain state and hold resources on the server
	config, err := pgxpool.ParseConfig(os.Getenv("DATABASE_URL"))
	if err != nil {
		return nil, fmt.Errorf("unable to parse database URL: %w", err)
	}

	// staff-level: These should match your expected concurrency
	// Too few = request queuing; Too many = database overwhelm
	config.MinConns = 10
	config.MaxConns = 50

	// How long a connection can be idle before being closed
	config.MaxConnLifetime = time.Hour
	config.MaxConnLifetimeJitter = 5 * time.Minute // staff-level: Jitter prevents thundering herd

	// How long to wait for a connection when pool is exhausted
	config.MaxConnWaitTime = 5 * time.Second

	// health check period
	config.HealthCheckPeriod = 5 * time.Minute

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	pool, err := pgxpool.NewWithConfig(ctx, "", config)
	if err != nil {
		return nil, fmt.Errorf("unable to create connection pool: %w", err)
	}

	// Verify connection works
	if err := pool.Ping(ctx); err != nil {
		return nil, fmt.Errorf("unable to ping database: %w", err)
	}

	return pool, nil
}

// TCP connection benchmark - demonstrates connection overhead
func benchmarkTCPConnection(iterations int) {
	fmt.Printf("Benchmarking %d TCP connections...\n", iterations)

	// Create a listener to accept connections
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		fmt.Printf("Error creating listener: %v\n", err)
		return
	}
	defer listener.Close()

	// Server goroutine
	done := make(chan struct{})
	go func() {
		for {
			conn, err := listener.Accept()
			if err != nil {
				break
			}
			conn.Close()
		}
		close(done)
	}()

	// Client benchmark
	start := time.Now()
	for i := 0; i < iterations; i++ {
		conn, err := net.Dial("tcp", listener.Addr().String())
		if err != nil {
			fmt.Printf("Error connecting: %v\n", err)
			continue
		}
		conn.Close()
	}
	elapsed := time.Since(start)

	fmt.Printf("Total time: %v\n", elapsed)
	fmt.Printf("Avg per connection: %v\n", elapsed/time.Duration(iterations))
}

func main() {
	fmt.Println("=== Connection Pooling Demo ===")
	fmt.Println()

	// Example 1: HTTP client with connection pooling
	client := productionHTTPClient()
	defer client.Close()

	// Simulate concurrent requests
	var wg sync.WaitGroup
	for i := 0; i < 10; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			// In production, this would be actual requests
			// resp, err := client.Get("https://api.example.com/data")
		}()
	}
	wg.Wait()

	fmt.Println("HTTP client example complete")
	fmt.Println()

	// Example 2: TCP connection benchmark
	benchmarkTCPConnection(100)

	fmt.Println()
	fmt.Println("=== Key Takeaways ===")
	fmt.Println("1. Connection pooling prevents TCP handshake overhead on each request")
	fmt.Println("2. Database connections are MORE expensive than HTTP connections")
	fmt.Println("3. Always set timeouts to prevent resource exhaustion")
	fmt.Println("4. Monitor connection pool metrics in production")
}
