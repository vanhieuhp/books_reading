package main

import (
	"fmt"
	"io"
	"log"
	"net/http"
	"time"
)

// =============================================================================
// NAIVE HTTP CLIENT - What Most Devs Do
// =============================================================================
// This client has NO resilience features:
// - No timeout - can hang forever on slow/failed services
// - No retry - fails immediately on any error
// - No circuit breaker - hammers failing service repeatedly
// - No connection pooling - creates new connection every time

// NaiveHTTPClient wraps http.Client with no timeout
type NaiveHTTPClient struct {
	client *http.Client
}

// NewNaiveHTTPClient creates a client with NO timeout configured
// WHY THIS IS PROBLEMATIC:
// - If the downstream service hangs, this will block indefinitely
// - No way to detect failure quickly
// - Consumes resources while waiting
func NewNaiveHTTPClient() *NaiveHTTPClient {
	return &NaiveHTTPClient{
		client: &http.Client{
			// BUG: No Timeout set - this is the critical flaw!
			// Default http.Client has no timeout, can hang forever
		},
	}
}

// Get makes a GET request with no resilience
// PROBLEM DEMONSTRATED:
// 1. No timeout - can hang for minutes/hours
// 2. No retry - single attempt only
// 3. No circuit breaker - keeps hammering failing service
func (c *NaiveHTTPClient) Get(url string) ([]byte, error) {
	log.Printf("[NAIVE] Requesting: %s", url)

	// Problem: This can block indefinitely!
	// If the server is down, the OS TCP keepalive will eventually
	// timeout (usually 2+ minutes), but by then resources are exhausted
	resp, err := c.client.Get(url)
	if err != nil {
		log.Printf("[NAIVE] Error: %v", err)
		return nil, fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	// Read response body
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	log.Printf("[NAIVE] Success: status=%d, body_len=%d", resp.StatusCode, len(body))
	return body, nil
}

// simulateFailingService runs a simple HTTP server that hangs
type simulateFailingService struct {
	hangDuration time.Duration
}

func (s *simulateFailingService) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	// Simulate a service that's slow to respond
	time.Sleep(s.hangDuration)
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(`{"status": "ok"}`))
}

func main() {
	fmt.Println("========================================")
	fmt.Println("  NAIVE HTTP CLIENT DEMONSTRATION")
	fmt.Println("========================================")
	fmt.Println()
	fmt.Println("This client has NO timeout - watch what happens when we")
	fmt.Println("try to connect to a service that doesn't exist or is down.")
	fmt.Println()

	client := NewNaiveHTTPClient()

	// Test 1: Try to connect to a non-existent service
	// This WILL HANG for a long time (OS-level TCP timeout)
	fmt.Println("--- Test 1: Connecting to non-existent service ---")
	fmt.Println("Expected: Will hang for 2+ minutes (OS TCP timeout)")
	fmt.Println()

	start := time.Now()

	// This will try to connect to localhost:9999 which doesn't exist
	// The OS will retry several times before giving up
	_, err := client.Get("http://localhost:9999/api/data")
	elapsed := time.Since(start)

	fmt.Printf("\nResult: Failed after %v\n", elapsed)
	if err != nil {
		fmt.Printf("Error: %v\n", err)
	}

	fmt.Println()
	fmt.Println("--- Test 2: What happens with valid but slow service ---")
	fmt.Println("Starting a slow server on :8888...")

	// Start a slow server
	simulatedService := &simulateFailingService{hangDuration: 10 * time.Second}
	go http.ListenAndServe(":8888", simulatedService)

	time.Sleep(1 * time.Second) // Wait for server to start

	fmt.Println("Making request (will take 10 seconds)...")
	start = time.Now()

	_, err = client.Get("http://localhost:8888/slow")
	elapsed = time.Since(start)

	fmt.Printf("\nResult: Request completed after %v\n", elapsed)
	if err != nil {
		fmt.Printf("Error: %v\n", err)
	}

	fmt.Println()
	fmt.Println("========================================")
	fmt.Println("  PROBLEM SUMMARY")
	fmt.Println("========================================")
	fmt.Println("1. No timeout = indefinite hang")
	fmt.Println("2. No retry = single point of failure")
	fmt.Println("3. No circuit breaker = resource exhaustion")
	fmt.Println()
	fmt.Println("See resilient_client.go for the fix!")
}
