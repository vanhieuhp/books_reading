# Staff-Level Go Patterns Library

## Pattern: Context Propagation (always required in production Go)
```go
// ❌ Naive — no context, no cancellation
func fetchData(url string) ([]byte, error) {
    resp, err := http.Get(url)
    ...
}

// ✅ Production — context propagation + timeout
func fetchData(ctx context.Context, url string) ([]byte, error) {
    // Staff note: Always accept context as first arg.
    // This enables distributed tracing, cancellation, and deadline propagation.
    ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
    defer cancel()

    req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
    if err != nil {
        return nil, fmt.Errorf("creating request: %w", err)
    }

    resp, err := http.DefaultClient.Do(req)
    if err != nil {
        return nil, fmt.Errorf("executing request: %w", err)
    }
    defer resp.Body.Close()

    return io.ReadAll(resp.Body)
}
```

## Pattern: Error Wrapping (structured, inspectable errors)
```go
// ❌ Naive — loses context
return nil, err

// ✅ Production — wrap with context, preserve chain
return nil, fmt.Errorf("fetchUser(id=%d): %w", id, err)

// ✅ Custom error types for programmatic inspection
type NotFoundError struct {
    Resource string
    ID       int64
}
func (e *NotFoundError) Error() string {
    return fmt.Sprintf("%s with id=%d not found", e.Resource, e.ID)
}

// Caller can type-assert:
var notFound *NotFoundError
if errors.As(err, &notFound) {
    // handle 404 path
}
```

## Pattern: Worker Pool (bounded concurrency)
```go
// Staff note: Unbounded goroutines will OOM under load.
// Always bound concurrency with semaphore or worker pool.

func processItems(ctx context.Context, items []Item, concurrency int) error {
    sem := make(chan struct{}, concurrency) // semaphore
    var wg sync.WaitGroup
    var mu sync.Mutex
    var errs []error

    for _, item := range items {
        item := item // capture loop variable (pre-Go 1.22)
        select {
        case sem <- struct{}{}:
        case <-ctx.Done():
            return ctx.Err()
        }

        wg.Add(1)
        go func() {
            defer wg.Done()
            defer func() { <-sem }()

            if err := process(ctx, item); err != nil {
                mu.Lock()
                errs = append(errs, fmt.Errorf("item %v: %w", item.ID, err))
                mu.Unlock()
            }
        }()
    }

    wg.Wait()
    return errors.Join(errs...)
}
```

## Pattern: Interface Design (accept interfaces, return structs)
```go
// ✅ Staff-level Go: small interfaces, accept them in functions
type Store interface {
    Get(ctx context.Context, key string) ([]byte, error)
    Set(ctx context.Context, key string, val []byte, ttl time.Duration) error
}

// Function accepts interface — testable, swappable
func NewUserService(store Store, logger *slog.Logger) *UserService {
    return &UserService{store: store, logger: logger}
}

// Concrete struct is returned (not interface) — lets callers access full API
type UserService struct {
    store  Store
    logger *slog.Logger
}
```

## Pattern: Structured Logging (slog, post Go 1.21)
```go
// ❌ fmt.Println / log.Printf — unstructured, unsearchable
log.Printf("user %d logged in from %s", userID, ip)

// ✅ slog — structured, queryable in log systems
logger.InfoContext(ctx, "user login",
    slog.Int64("user_id", userID),
    slog.String("ip", ip),
    slog.String("trace_id", traceID(ctx)),
)
```

## Pattern: Graceful Shutdown
```go
func main() {
    srv := &http.Server{Addr: ":8080", Handler: router}

    // Separate goroutine for server
    go func() {
        if err := srv.ListenAndServe(); err != http.ErrServerClosed {
            log.Fatal(err)
        }
    }()

    // Wait for OS signal
    quit := make(chan os.Signal, 1)
    signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
    <-quit

    // 30s grace period for in-flight requests
    ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer cancel()
    if err := srv.Shutdown(ctx); err != nil {
        log.Printf("forced shutdown: %v", err)
    }
}
```

## Pattern: Table-Driven Tests (staff standard)
```go
func TestCalculate(t *testing.T) {
    tests := []struct {
        name    string
        input   Input
        want    Output
        wantErr bool
    }{
        {
            name:  "happy path",
            input: Input{A: 1, B: 2},
            want:  Output{Sum: 3},
        },
        {
            name:    "division by zero",
            input:   Input{A: 1, B: 0},
            wantErr: true,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got, err := Calculate(tt.input)
            if (err != nil) != tt.wantErr {
                t.Errorf("err = %v, wantErr %v", err, tt.wantErr)
            }
            if !tt.wantErr && got != tt.want {
                t.Errorf("got %v, want %v", got, tt.want)
            }
        })
    }
}
```