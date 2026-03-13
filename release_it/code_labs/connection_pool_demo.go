package main

import (
	"context"
	"database/sql"
	"fmt"
	"sync"
	"time"

	_ "github.com/lib/pq" // PostgreSQL driver
)

// =============================================================================
// PROBLEM DEMONSTRATION: Connection Pool Exhaustion
// =============================================================================
// This code demonstrates the "Production Gap" - what works in testing fails in prod

// ------------------------------------------------------------------
// NAIVE APPROACH: No connection pool management
// ------------------------------------------------------------------
// What most developers do: create connections on demand, no pooling
// Why it fails in production: under load, you exhaust OS file descriptors
// and database connection limits

type NaiveUserService struct {
	// Each request creates a new connection - works fine with 10 users
	// FAILS at 1000 concurrent users
}

func (s *NaiveUserService) GetUserNaive(userID int64) (*User, error) {
	// Staff note: Every call creates a NEW connection. At 1000 req/sec,
	// you'll create 1000 connections/sec. PostgreSQL default max is 100.
	// This is the classic "works in dev, fails in production" pattern.

	db, err := sql.Open("postgres", "user=app dbname=users sslmode=disable")
	if err != nil {
		return nil, fmt.Errorf("opening database: %w", err)
	}
	defer db.Close()

	// This works in test with 1 user. In prod with 1000 concurrent users,
	// the database rejects connections and you get: "too many clients"
	var user User
	err = db.QueryRowContext(context.Background(),
		"SELECT id, name, email FROM users WHERE id = $1", userID).
		Scan(&user.ID, &user.Name, &user.Email)
	if err != nil {
		return nil, fmt.Errorf("querying user: %w", err)
	}
	return &user, nil
}

// ------------------------------------------------------------------
// PRODUCTION APPROACH: Proper connection pooling with bounded concurrency
// ------------------------------------------------------------------

type User struct {
	ID    int64
	Name  string
	Email string
}

// ProductionUserService uses a single shared connection pool
// Why this works: the database/sql package manages a pool of connections
// with proper limits. You still need to bound your concurrent requests though.
type ProductionUserService struct {
	db *sql.DB
}

func NewProductionUserService(connStr string) (*ProductionUserService, error) {
	// Staff note: Set pool limits EARLY, not as an afterthought.
	// These should match your infrastructure (RDS max connections, etc.)

	db, err := sql.Open("postgres", connStr)
	if err != nil {
		return nil, fmt.Errorf("opening database: %w", err)
	}

	// CRITICAL: Set pool limits to match your infrastructure
	// At scale, these numbers matter. PostgreSQL default is 100.
	db.SetMaxOpenConns(25)   // Hard limit - don't exceed this
	db.SetMaxIdleConns(10)   // Keep connections warm
	db.SetConnMaxLifetime(5 * time.Minute) // Prevent stale connections
	db.SetConnMaxIdleTime(1 * time.Minute) // Recycle idle connections

	// Verify connection works BEFORE accepting traffic
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if err := db.PingContext(ctx); err != nil {
		return nil, fmt.Errorf("pinging database: %w", err)
	}

	return &ProductionUserService{db: db}, nil
}

// STILL NAIVE: Even with connection pooling, unbounded concurrency kills you
func (s *ProductionUserService) GetUserUnbounded(userID int64) (*User, error) {
	// This still fails under load because you have 1000 goroutines
	// all waiting for 25 connections. They'll all block and timeout.
	var user User
	err := s.db.QueryRowContext(context.Background(),
		"SELECT id, name, email FROM users WHERE $1", userID).
		Scan(&user.ID, &user.Name, &user.Email)
	if err != nil {
		return nil, fmt.Errorf("querying user: %w", err)
	}
	return &user, nil
}

// ------------------------------------------------------------------
// PRODUCTION APPROACH: Bounded concurrency with semaphore
// ------------------------------------------------------------------
// Staff note: This is what production looks like at scale.
// Use a semaphore to limit concurrent requests, then use the pool.

type BoundedUserService struct {
	db       *sql.DB
	sem      chan struct{} // Semaphore for bounded concurrency
	parallel int           // Max concurrent requests
}

func NewBoundedUserService(connStr string, parallel int) (*BoundedUserService, error) {
	db, err := sql.Open("postgres", connStr)
	if err != nil {
		return nil, fmt.Errorf("opening database: %w", err)
	}

	db.SetMaxOpenConns(25)
	db.SetMaxIdleConns(10)
	db.SetConnMaxLifetime(5 * time.Minute)

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if err := db.PingContext(ctx); err != nil {
		return nil, fmt.Errorf("pinging database: %w", err)
	}

	return &BoundedUserService{
		db:       db,
		sem:      make(chan struct{}, parallel),
		parallel: parallel,
	}, nil
}

func (s *BoundedUserService) GetUser(ctx context.Context, userID int64) (*User, error) {
	// Staff note: This is the KEY pattern for production:
	// 1. Acquire semaphore slot (blocks if at limit)
	// 2. Do work with connection pool
	// 3. Release semaphore slot
	//
	// This prevents connection pool exhaustion under load.
	// At 1000 req/sec with 25 connections, requests queue up
	// instead of failing. You get graceful degradation.

	select {
	case s.sem <- struct{}{}: // Acquire slot
		defer func() { <-s.sem }() // Release on return
	case <-ctx.Done():
		return nil, ctx.Err() // Respect deadline
	}

	// Now use the connection pool safely
	var user User
	err := s.db.QueryRowContext(ctx,
		"SELECT id, name, email FROM users WHERE id = $1", userID).
		Scan(&user.ID, &user.Name, &user.Email)
	if err != nil {
		return nil, fmt.Errorf("querying user: %w", err)
	}
	return &user, nil
}

// ------------------------------------------------------------------
// DEMONSTRATION: Simulating the production failure
// ------------------------------------------------------------------

func main() {
	// This demonstrates what happens in production
	// Naive approach: creates 1000 connections -> FAILS
	// Production approach: uses semaphore -> HANDLES LOAD

	// Simulate 1000 concurrent requests
	concurrency := 1000

	// NAIVE: Would fail with "too many clients"
	// (not actually running this - it would crash)
	fmt.Printf("Naive approach: Would create %d connections -> FAILURE\n", concurrency)

	// PRODUCTION: Bounded approach handles it gracefully
	fmt.Printf("Production approach: Max %d concurrent, rest queue -> GRACEFUL\n", 25)

	// With 1000 requests and 25 connections:
	// - Average wait: 1000/25 = 40 "connection-seconds" of work
	// - If each query takes 10ms, total time = 400ms
	// - With unbounded: 1000 * 10ms = 10,000ms but connections fail
}

// =============================================================================
// STAFF ENGINEER INSIGHT
// =============================================================================
//
// The production gap in this example:
// - TEST: 10 users, sequential -> naive approach works
// - PROD: 1000 concurrent users -> naive approach fails
//
// What you learn from this:
// 1. Connection pooling is NOT optional at scale
// 2. Even with pooling, you need bounded concurrency
// 3. Infrastructure limits (max connections) must be known and respected
// 4. Graceful degradation > sudden failure
//
// At Google/Meta scale: they use proxy layers (PgBouncer, ProxySQL)
// that multiplex thousands of connections into dozens to the actual DB.
