// Chapter 12: Adaptation - Go Code Examples
// Versioning, Feature Flags, and Deployment Patterns
//
// This file demonstrates production-grade implementations of concepts from
// Release It! Chapter 12 - Adaptation
//
// Run: go run code_examples.go

package main

import (
	"context"
	"encoding/json"
	"fmt"
	"math/rand"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync"
	"time"
)

// =============================================================================
// PART 1: API VERSION ROUTER
// =============================================================================

// Version represents an API version with its handler
type Version struct {
	Number       string
	Handler      http.Handler
	Deprecation  time.Time
	IsDeprecated bool
}

// APIVersionRouter routes requests to the appropriate API version
//
// ❌ NAIVE APPROACH: Single handler, no version awareness
// Problems:
//   - Can't evolve API without breaking existing clients
//   - No graceful deprecation path
//   - Clients forced to upgrade on provider's timeline
//
// ✅ PRODUCTION APPROACH: Version-aware routing
// Benefits:
//   - Backward compatibility maintained
//   - Clear deprecation timeline
//   - Client choice on upgrade timing
type APIVersionRouter struct {
	versions    map[string]*Version
	defaultVer  string
	deprecated  map[string]string // old -> new mapping
	mu          sync.RWMutex
}

// NewAPIVersionRouter creates a new versioned API router
func NewAPIVersionRouter(defaultVersion string) *APIVersionRouter {
	return &APIVersionRouter{
		versions:   make(map[string]*Version),
		defaultVer: defaultVersion,
		deprecated: make(map[string]string),
	}
}

// RegisterVersion adds a new API version handler
func (r *APIVersionRouter) RegisterVersion(version string, handler http.Handler, deprecateAt time.Time) {
	r.mu.Lock()
	defer r.mu.Unlock()

	r.versions[version] = &Version{
		Number:      version,
		Handler:     handler,
		Deprecation: deprecateAt,
	}
}

// DeprecateVersion marks a version as deprecated and maps it to a newer version
func (r *APIVersionRouter) DeprecateVersion(oldVersion, newVersion string) {
	r.mu.Lock()
	defer r.mu.Unlock()

	r.deprecated[oldVersion] = newVersion
	if v, ok := r.versions[oldVersion]; ok {
		v.IsDeprecated = true
	}
}

// ServeHTTP routes requests based on version
//
// Staff-level insight: Version detection order should be:
// 1. URL path (most explicit, highest priority)
// 2. Header (Accept: application/vnd.api.v1+json)
// 3. Query parameter (least preferred, easy to test)
func (r *APIVersionRouter) ServeHTTP(w http.ResponseWriter, req *http.Request) {
	version := r.extractVersion(req)

	r.mu.RLock()
	defer r.mu.RUnlock()

	// Check if version exists
	versionHandler, ok := r.versions[version]
	if !ok {
		// Version not found - try default or return error
		if versionHandler, ok = r.versions[r.defaultVer]; !ok {
			http.Error(w, `{"error": "unsupported_api_version", "supported": "`+r.defaultVer+`"}`, http.StatusNotAcceptable)
			return
		}
		w.Header().Set("X-API-Deprecation", "version_not_found_using_default")
	}

	// Add deprecation warning header if applicable
	if versionHandler.IsDeprecated {
		w.Header().Set("X-API-Deprecated", "true")
		w.Header().Set("X-API-Migration-Guide", r.deprecated[version])
		if time.Now().After(versionHandler.Deprecation) {
			http.Error(w, `{"error": "api_version_deprecated"}`, http.StatusGone)
			return
		}
	}

	// Forward to version-specific handler
	versionHandler.ServeHTTP(w, req)
}

// extractVersion determines API version from request
// Priority: URL path > Header > Query param > Default
func (r *APIVersionRouter) extractVersion(req *http.Request) string {
	// 1. Check URL path /api/v1/...
	path := req.URL.Path
	if idx := strings.Index(path, "/v"); idx >= 0 {
		if len(path) > idx+2 && path[idx+1] == 'v' {
			return path[idx+2 : idx+3] // Get "1" from "/v1/"
		}
	}

	// 2. Check Accept header: Accept: application/vnd.api.v1+json
	accept := req.Header.Get("Accept")
	if strings.Contains(accept, "v") {
		for i := range accept {
			if accept[i] == 'v' && i+2 < len(accept) && accept[i+1] == '=' {
				return string(accept[i+2])
			}
		}
	}

	// 3. Check query param: ?version=1
	if v := req.URL.Query().Get("version"); v != "" {
		return v
	}

	// 4. Default version
	return r.defaultVer
}

// =============================================================================
// PART 2: FEATURE FLAG SERVICE
// =============================================================================

// FeatureFlag represents a single feature flag
type FeatureFlag struct {
	Name        string
	Description string
	Enabled     bool

	// Targeting rules
	RolloutPercent    int            // 0-100 percentage
	UserGroups        map[string]bool // whitelist groups
	WhitelistedUsers  map[string]bool // specific user IDs
	TargetEnvironments []string       // dev, staging, prod

	// Metadata
	CreatedAt   time.Time
	ExpiresAt  *time.Time
	CreatedBy  string
}

// FeatureFlagService manages feature flags at runtime
//
// ❌ NAIVE APPROACH: Environment variables or config files
// Problems:
//   - Requires restart to change
//   - No gradual rollout capability
//   - No A/B testing support
//   - No audit trail
//
// ✅ PRODUCTION APPROACH: Runtime feature flag service
// Benefits:
//   - Instant toggle without deployment
//   - Percentage-based rollout
//   - User segment targeting
//   - Audit logging
//   - Integration with analytics (for A/B testing)
type FeatureFlagService struct {
	flags map[string]*FeatureFlag
	mu    sync.RWMutex

	// Optional: external service integration
	evalCache   map[string]bool // userID+flag -> result
	cacheExpiry time.Time
}

// NewFeatureFlagService creates a new feature flag service
func NewFeatureFlagService() *FeatureFlagService {
	return &FeatureFlagService{
		flags:     make(map[string]*FeatureFlag),
		evalCache: make(map[string]bool),
	}
}

// CreateFlag registers a new feature flag
func (s *FeatureFlagService) CreateFlag(flag *FeatureFlag) {
	s.mu.Lock()
	defer s.mu.Unlock()

	flag.CreatedAt = time.Now()
	s.flags[flag.Name] = flag
	s.evalCache = make(map[string]bool) // invalidate cache
}

// SetEnabled toggles a flag on/off
func (s *FeatureFlagService) SetEnabled(name string, enabled bool) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	if _, ok := s.flags[name]; !ok {
		return fmt.Errorf("flag %s not found", name)
	}

	s.flags[name].Enabled = enabled
	s.evalCache = make(map[string]bool) // invalidate cache
	return nil
}

// SetRolloutPercentage sets gradual rollout percentage
func (s *FeatureFlagService) SetRolloutPercentage(name string, percent int) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	if flag, ok := s.flags[name]; !ok {
		return fmt.Errorf("flag %s not found", name)
	} else if percent < 0 || percent > 100 {
		return fmt.Errorf("percentage must be 0-100")
	} else {
		flag.RolloutPercent = percent
	}

	s.evalCache = make(map[string]bool)
	return nil
}

// IsEnabled evaluates if a feature is enabled for a given user/context
//
// Staff-level insight: Evaluation should be:
// 1. Fast (in-memory lookup)
// 2. Deterministic (same input = same output)
// 3. Auditable (log every evaluation in production)
func (s *FeatureFlagService) IsEnabled(ctx context.Context, flagName, userID, env string) bool {
	s.mu.RLock()
	defer s.mu.RUnlock()

	flag, ok := s.flags[flagName]
	if !ok {
		return false // Flag doesn't exist = disabled
	}

	// Check cache first
	cacheKey := fmt.Sprintf("%s:%s", userID, flagName)
	if result, ok := s.evalCache[cacheKey]; ok {
		return result
	}

	// Evaluate rules in order of priority
	result := s.evaluateFlag(flag, userID, env)

	// Cache result (with TTL in production)
	s.evalCache[cacheKey] = result

	return result
}

// evaluateFlag checks if flag is enabled for user
func (s *FeatureFlagService) evaluateFlag(flag *FeatureFlag, userID, env string) bool {
	// Rule 1: If globally disabled, return false
	if !flag.Enabled {
		return false
	}

	// Rule 2: Check environment targeting
	if len(flag.TargetEnvironments) > 0 {
		envAllowed := false
		for _, e := range flag.TargetEnvironments {
			if e == env {
				envAllowed = true
				break
			}
		}
		if !envAllowed {
			return false
		}
	}

	// Rule 3: Check whitelist (exact match)
	if flag.WhitelistedUsers[userID] {
		return true
	}

	// Rule 4: Check user groups
	if len(flag.UserGroups) > 0 {
		// In production, fetch user's groups from identity provider
		// For now, assume userID hash determines group membership
		userGroup := fmt.Sprintf("group_%d", hash(userID)%10)
		if flag.UserGroups[userGroup] {
			return true
		}
	}

	// Rule 5: Percentage rollout (deterministic based on userID hash)
	if flag.RolloutPercent > 0 {
		userHash := hash(userID + flag.Name)
		percentile := userHash % 100
		if percentile < flag.RolloutPercent {
			return true
		}
	}

	// Rule 6: If enabled but no specific rules, use rollout percentage
	if flag.RolloutPercent == 100 {
		return true
	}

	return false
}

// Simple hash function for deterministic sampling
func hash(s string) int {
	h := 0
	for i, c := range s {
		h = h*31 + int(c)*(i+1)
	}
	if h < 0 {
		h = -h
	}
	return h
}

// =============================================================================
// PART 3: DEPLOYMENT HEALTH CHECK
// =============================================================================

// HealthCheckResult contains the outcome of a deployment health check
type HealthCheckResult struct {
	Passed          bool
	ChecksPassed    int
	ChecksFailed    int
	LatencyMs       int64
	FailureReasons  []string
}

// DeploymentHealthChecker validates system readiness before/after deployment
//
// ❌ NAIVE APPROACH: Wait X seconds and assume healthy
// Problems:
//   - No actual validation
//   - Can't catch subtle issues
//   - Blind to actual system state
//
// ✅ PRODUCTION APPROACH: Multi-layered health checks
// Benefits:
//   - Validates actual system state
//   - Catches issues before customers
//   - Provides confidence in deployment
type DeploymentHealthChecker struct {
	httpClient *http.Client
	checks     []HealthCheck
}

// HealthCheck defines a single health validation
type HealthCheck interface {
	Name() string
	Check(ctx context.Context) (bool, string)
}

// NewDeploymentHealthChecker creates a health checker
func NewDeploymentHealthChecker() *DeploymentHealthChecker {
	return &DeploymentHealthChecker{
		httpClient: &http.Client{
			Timeout: 10 * time.Second,
		},
		checks: make([]HealthCheck, 0),
	}
}

// AddCheck registers a new health check
func (c *DeploymentHealthChecker) AddCheck(check HealthCheck) {
	c.checks = append(c.checks, check)
}

// RunAll executes all health checks
func (c *DeploymentHealthChecker) RunAll(ctx context.Context) *HealthCheckResult {
	start := time.Now()
	result := &HealthCheckResult{
		FailureReasons: make([]string, 0),
	}

	for _, check := range c.checks {
		passed, reason := check.Check(ctx)
		if passed {
			result.ChecksPassed++
		} else {
			result.ChecksFailed++
			result.FailureReasons = append(result.FailureReasons,
				fmt.Sprintf("%s: %s", check.Name(), reason))
		}
	}

	result.LatencyMs = time.Since(start).Milliseconds()
	result.Passed = result.ChecksFailed == 0

	return result
}

// Example health checks

type HTTPHealthCheck struct {
	URL    string
	Status int
}

func (h *HTTPHealthCheck) Name() string { return "http_health_endpoint" }

func (h *HTTPHealthCheck) Check(ctx context.Context) (bool, string) {
	req, err := http.NewRequestWithContext(ctx, "GET", h.URL, nil)
	if err != nil {
		return false, err.Error()
	}

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return false, fmt.Sprintf("connection failed: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != h.Status {
		return false, fmt.Sprintf("expected %d, got %d", h.Status, resp.StatusCode)
	}

	return true, "OK"
}

type LatencyCheck struct {
	URL           string
	MaxLatencyMs  int
	SampleSize    int
}

func (l *LatencyCheck) Name() string { return "latency_check" }

func (l *LatencyCheck) Check(ctx context.Context) (bool, string) {
	latencies := make([]int64, l.SampleSize)

	for i := 0; i < l.SampleSize; i++ {
		start := time.Now()
		req, _ := http.NewRequestWithContext(ctx, "GET", l.URL, nil)
		resp, err := http.DefaultClient.Do(req)
		elapsed := time.Since(start).Milliseconds()

		if err != nil {
			return false, fmt.Sprintf("request failed: %v", err)
		}
		resp.Body.Close()
		latencies[i] = elapsed
	}

	// Calculate p95
	p95 := calculatePercentile(latencies, 95)
	if p95 > int64(l.MaxLatencyMs) {
		return false, fmt.Sprintf("p95 latency %dms exceeds threshold %dms", p95, l.MaxLatencyMs)
	}

	return true, fmt.Sprintf("p95: %dms", p95)
}

func calculatePercentile(values []int64, percentile int) int64 {
	if len(values) == 0 {
		return 0
	}

	// Sort copy
	sorted := make([]int64, len(values))
	copy(sorted, values)
	quickSort(sorted, 0, len(sorted)-1)

	idx := (len(sorted) * percentile) / 100
	if idx >= len(sorted) {
		idx = len(sorted) - 1
	}
	return sorted[idx]
}

func quickSort(arr []int64, low, high int) {
	if low < high {
		pivot := arr[high]
		i := low
		for j := low; j < high; j++ {
			if arr[j] < pivot {
				arr[i], arr[j] = arr[j], arr[i]
				i++
			}
		}
		arr[i], arr[high] = arr[high], arr[i]
		quickSort(arr, low, i-1)
		quickSort(arr, i+1, high)
	}
}

// =============================================================================
// PART 4: ROLLBACK CONTROLLER
// =============================================================================

// RollbackController manages automated and manual rollbacks
//
// Staff-level insight: Rollback should be:
// 1. Fast (seconds, not minutes)
// 2. Automated (no human in the critical path)
// 3. Idempotent (can run multiple times safely)
// 4. Auditable (log every action)
type RollbackController struct {
	mu           sync.RWMutex
	history      []RollbackEvent
	maxHistory   int
	alertWebhook string
}

// RollbackEvent records a rollback action
type RollbackEvent struct {
	Timestamp    time.Time
	Trigger      string // "manual" or "automated"
	Reason       string
	VersionFrom  string
	VersionTo    string
	DurationMs   int64
	Success      bool
}

// NewRollbackController creates a rollback controller
func NewRollbackController() *RollbackController {
	return &RollbackController{
		history:    make([]RollbackEvent, 0),
		maxHistory: 100,
	}
}

// TriggerRollback initiates a rollback to a previous version
func (r *RollbackController) TriggerRollback(ctx context.Context, trigger, reason, fromVersion, toVersion string) (*RollbackEvent, error) {
	r.mu.Lock()
	defer r.mu.Unlock()

	start := time.Now()

	event := RollbackEvent{
		Timestamp:   start,
		Trigger:     trigger,
		Reason:      reason,
		VersionFrom: fromVersion,
		VersionTo:   toVersion,
	}

	// In production: actually perform the rollback
	// 1. Notify load balancer to stop routing to fromVersion
	// 2. Scale up toVersion if needed
	// 3. Verify health of toVersion
	// 4. Update configuration
	//
	// This is a simulation
	success := r.performRollback(ctx, fromVersion, toVersion)

	event.DurationMs = time.Since(start).Milliseconds()
	event.Success = success

	r.history = append(r.history, event)
	if len(r.history) > r.maxHistory {
		r.history = r.history[1:]
	}

	// Alert on failure
	if !success && r.alertWebhook != "" {
		r.sendAlert(event)
	}

	return &event, nil
}

// performRollback executes the actual rollback logic
// In production, this would interact with:
// - Kubernetes/ECS for container orchestration
// - Load balancer API for traffic routing
// - Database for state changes
// - Monitoring for verification
func (r *RollbackController) performRollback(ctx context.Context, from, to string) bool {
	// Simulate rollback operation
	// In reality: orchestrator.RollbackTo(ctx, to)
	time.Sleep(100 * time.Millisecond) // Simulated latency

	// Simulate 95% success rate
	return rand.Float32() > 0.05
}

func (r *RollbackController) sendAlert(event RollbackEvent) {
	// In production: send to PagerDuty, Slack, etc.
	fmt.Printf("ALERT: Rollback failed! Event: %+v\n", event)
}

// GetHistory returns recent rollback events
func (r *RollbackController) GetHistory() []RollbackEvent {
	r.mu.RLock()
	defer r.mu.RUnlock()

	result := make([]RollbackEvent, len(r.history))
	copy(result, r.history)
	return result
}

// =============================================================================
// PART 5: DEMONSTRATION
// =============================================================================

func main() {
	fmt.Println("=" * 70)
	fmt.Println("Chapter 12: Adaptation - Code Examples")
	fmt.Println("=" * 70)

	// Demo 1: API Version Router
	fmt.Println("\n[1] API Version Router Demo")
	fmt.Println("-" * 40)

	router := NewAPIVersionRouter("2")

	// Register v1 handler
	router.RegisterVersion("1", http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		json.NewEncoder(w).Encode(map[string]string{"version": "1", "data": "legacy"})
	}), time.Now().Add(30*24*time.Hour))

	// Register v2 handler (current)
	router.RegisterVersion("2", http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		json.NewEncoder(w).Encode(map[string]string{"version": "2", "data": "current"})
	}), time.Time{})

	// Deprecate v1
	router.DeprecateVersion("1", "2")

	// Test requests
	testReq, _ := http.NewRequest("GET", "/api/v1/users", nil)
	rec := httptest.NewRecorder()
	router.ServeHTTP(rec, testReq)
	fmt.Printf("Request to /v1/: %s\n", rec.Body.String())

	testReq2, _ := http.NewRequest("GET", "/api/v2/users", nil)
	rec2 := httptest.NewRecorder()
	router.ServeHTTP(rec2, testReq2)
	fmt.Printf("Request to /v2/: %s\n", rec2.Body.String())

	// Demo 2: Feature Flags
	fmt.Println("\n[2] Feature Flag Service Demo")
	fmt.Println("-" * 40)

	ff := NewFeatureFlagService()

	// Create flags
	ff.CreateFlag(&FeatureFlag{
		Name:                "new-checkout",
		Description:         "New checkout flow",
		Enabled:             true,
		RolloutPercent:      10,
		TargetEnvironments:  []string{"production"},
		WhitelistedUsers:    map[string]bool{"user123": true},
		UserGroups:          map[string]bool{"beta_testers": true},
		CreatedBy:           "alice",
	})

	ctx := context.Background()

	// Test with whitelisted user
	fmt.Printf("user123 (whitelisted): %v\n", ff.IsEnabled(ctx, "new-checkout", "user123", "production"))

	// Test with random users (some will be in 10% rollout)
	for _, user := range []string{"user100", "user200", "user300"} {
		enabled := ff.IsEnabled(ctx, "new-checkout", user, "production")
		fmt.Printf("%s (10%% rollout): %v\n", user, enabled)
	}

	// Test environment targeting
	fmt.Printf("staging user: %v\n", ff.IsEnabled(ctx, "new-checkout", "user100", "staging"))

	// Demo 3: Health Checker
	fmt.Println("\n[3] Deployment Health Checker Demo")
	fmt.Println("-" * 40)

	checker := NewDeploymentHealthChecker()
	checker.AddCheck(&HTTPHealthCheck{
		URL:    "http://httpbin.org/status/200",
		Status: 200,
	})

	result := checker.RunAll(ctx)
	fmt.Printf("Health Check Result: Passed=%v, Passed=%d, Failed=%d, Latency=%dms\n",
		result.Passed, result.ChecksPassed, result.ChecksFailed, result.LatencyMs)

	// Demo 4: Rollback Controller
	fmt.Println("\n[4] Rollback Controller Demo")
	fmt.Println("-" * 40)

	rb := NewRollbackController()

	event, err := rb.TriggerRollback(ctx, "manual", "High error rate detected", "v2.1", "v2.0")
	if err != nil {
		fmt.Printf("Rollback error: %v\n", err)
	} else {
		fmt.Printf("Rollback completed: %+v\n", *event)
	}

	history := rb.GetHistory()
	fmt.Printf("Rollback history: %d events\n", len(history))

	fmt.Println("\n" + "=" * 70)
	fmt.Println("All demos completed!")
	fmt.Println("=" * 70)
}
