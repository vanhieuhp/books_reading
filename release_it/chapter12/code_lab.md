# Chapter 12: Adaptation — Hands-On Code Lab

## 🧪 Lab Overview

This lab provides hands-on exercises to reinforce the concepts from Chapter 12. Each lab builds progressively on the concepts of versioning, deployment strategies, and feature flags.

**⏱ Estimated Time**: 30-45 minutes per lab
**🛠 Requirements**: Go 1.18+, Python 3.8+ (for visualizations)

---

## Lab 1: Build an API Version Router

### 🎯 Goal
Implement an API version router that handles multiple API versions simultaneously, supports deprecation, and routes requests appropriately.

### ⏱ Time: ~20 mins

### Step 1: Setup

```bash
mkdir -p lab1_version_router && cd lab1_version_router
go mod init version-router
```

### Step 2: Implement Basic Version Extraction

Create `version.go` with the following skeleton:

```go
package main

import (
	"fmt"
	"net/http"
	"strings"
)

// TODO: Extract version from request using this priority:
// 1. URL path: /api/v1/users
// 2. Header: X-API-Version: 1
// 3. Query param: ?version=1
// 4. Default: return error or use default

func extractVersion(req *http.Request) string {
	// Your implementation here
}

func main() {
	// Test cases
	testCases := []struct {
		name     string
		path     string
		header   string
		query    string
		expected string
	}{
		{"URL path v1", "/api/v1/users", "", "", "1"},
		{"URL path v2", "/api/v2/users", "", "", "2"},
		{"Header version", "/api/users", "1", "", "1"},
		{"Query param", "/api/users", "", "version=2", "2"},
		{"No version", "/api/users", "", "", ""},
	}

	for _, tc := range testCases {
		req := &http.Request{
			URL: &url.URL{Path: tc.path},
		}
		if tc.header != "" {
			req.Header = http.Header{"X-API-Version": []string{tc.header}}
		}
		if tc.query != "" {
			req.URL.RawQuery = tc.query
		}

		result := extractVersion(req)
		status := "✓ PASS"
		if result != tc.expected {
			status = "✗ FAIL"
		}
		fmt.Printf("%s %s: got=%q expected=%q\n", status, tc.name, result, tc.expected)
	}
}
```

### Step 3: Implement Full Router

Extend the router to:
- Store handlers per version
- Support deprecation warnings
- Return proper HTTP status codes

**Expected Output**:
```
Request to /api/v1/users → {"version":"1","data":"legacy"}
Headers: X-API-Deprecated: true, X-API-Migration-Guide: v2

Request to /api/v2/users → {"version":"2","data":"current"}
```

### Step 4: Verify

Run your router and test:
```bash
go run main.go
```

### 🔧 Stretch Challenge (Staff-Level)

Add support for **content negotiation**:
- Accept: `application/vnd.api.v1+json` (standard)
- Accept: `application/vnd.api.v2+json` (standard)
- Accept: `application/json` (use default)

---

## Lab 2: Build a Feature Flag Service

### 🎯 Goal
Create a feature flag service with percentage-based rollout, user targeting, and environment support.

### ⏱ Time: ~25 mins

### Step 1: Setup

```bash
cd .. && mkdir -p lab2_feature_flags && cd lab2_feature_flags
go mod init feature-flags
```

### Step 2: Implement Core Flag Evaluation

Create `flags.go`:

```go
package main

import (
	"context"
	"fmt"
	"hash/fnv"
)

// FeatureFlag represents a feature flag configuration
type FeatureFlag struct {
	Name               string
	Enabled            bool
	RolloutPercent     int              // 0-100
	WhitelistedUsers  map[string]bool
	TargetEnvironments []string
}

// FeatureFlagService manages feature flags
type FeatureFlagService struct {
	flags map[string]*FeatureFlag
}

// NewFeatureFlagService creates a new service
func NewFeatureFlagService() *FeatureFlagService {
	return &FeatureFlagService{
		flags: make(map[string]*FeatureFlag),
	}
}

// AddFlag registers a new flag
func (s *FeatureFlagService) AddFlag(flag *FeatureFlag) {
	s.flags[flag.Name] = flag
}

// IsEnabled evaluates if feature is enabled
// TODO: Implement evaluation logic with:
// 1. Check if flag exists and is enabled
// 2. Check environment targeting
// 3. Check whitelist (exact match)
// 4. Check percentage rollout (deterministic using hash)
func (s *FeatureFlagService) IsEnabled(ctx context.Context, flagName, userID, env string) bool {
	// Your implementation here
	return false
}

func main() {
	svc := NewFeatureFlagService()

	// Register a flag with 10% rollout
	svc.AddFlag(&FeatureFlag{
		Name:               "new-checkout",
		Enabled:            true,
		RolloutPercent:     10,
		WhitelistedUsers:  map[string]bool{"user-special": true},
		TargetEnvironments: []string{"production", "staging"},
	})

	ctx := context.Background()

	// Test cases
	tests := []struct {
		name     string
		userID   string
		env      string
		expected bool
	}{
		{"whitelisted user", "user-special", "production", true},
		{"production user", "user123", "production", false}, // 90% chance false
		{"staging user", "user456", "staging", false},       // 90% chance false
		{"wrong environment", "user123", "development", false},
		{"disabled flag", "user123", "production", false},   // doesn't exist
	}

	for _, tc := range tests {
		// Run multiple times for percentage-based flags
		results := make([]bool, 10)
		for i := 0; i < 10; i++ {
			results[i] = svc.IsEnabled(ctx, tc.name, tc.userID, tc.env)
		}

		// For deterministic tests
		fmt.Printf("Test %s (user=%s, env=%s): \n", tc.name, tc.userID, tc.env)
		fmt.Printf("  Results: %v\n", results)
	}
}
```

### Step 3: Add Gradual Rollout

Implement deterministic hashing for percentage rollout:

```go
func hashUser(userID, flagName string) int {
	h := fnv.New32a()
	h.Write([]byte(userID + flagName))
	return int(h.Sum32()) % 100
}
```

### Step 4: Add Feature Flag Dashboard (Optional)

Create a simple HTTP endpoint that:
- `GET /flags` - List all flags with their config
- `POST /flags` - Create/update a flag
- `GET /flags/:name/evaluate?user=xxx&env=yyy` - Check if enabled

### 🔧 Stretch Challenge (Staff-Level)

Add **audit logging**:
- Log every flag evaluation to a channel
- Include: timestamp, flag name, user ID, environment, result
- Add a background goroutine that batches and writes to storage

---

## Lab 3: Simulate Canary Deployment

### 🎯 Goal
Build a simulation that demonstrates canary deployment with automated health checking and rollback.

### ⏱ Time: ~20 mins

### Step 1: Setup

```bash
cd .. && mkdir -p lab3_canary && cd lab3_canary
go mod init canary-sim
```

### Step 2: Implement Canary Controller

Create `canary.go`:

```go
package main

import (
	"context"
	"fmt"
	"math/rand"
	"time"
)

// CanaryDeployment simulates a canary release
type CanaryDeployment struct {
	StableVersion  string
	CanaryVersion string
	CanaryTraffic int // percentage 0-100

	// Metrics
	StableErrorRate float64
	CanaryErrorRate float64

	// Thresholds
	ErrorRateThreshold float64
	LatencyThresholdMs int
}

// NewCanaryDeployment creates a new canary deployment
func NewCanaryDeployment(stable, canary string) *CanaryDeployment {
	return &CanaryDeployment{
		StableVersion:    stable,
		CanaryVersion:    canary,
		CanaryTraffic:    1, // Start with 1%
		StableErrorRate:  0.1,
		CanaryErrorRate:  0.1,
		ErrorRateThreshold: 1.0, // 1% error rate
		LatencyThresholdMs: 100,
	}
}

// SimulateTraffic simulates traffic and returns metrics
func (c *CanaryDeployment) SimulateTraffic() (stableMetrics, canaryMetrics Metrics) {
	// Simulate stable version
	stableMetrics = Metrics{
		Version:     c.StableVersion,
		Requests:    1000 - c.CanaryTraffic*10,
		ErrorRate:  c.StableErrorRate + rand.Float64()*0.1,
		LatencyMs:  50 + rand.Intn(30),
	}

	// Simulate canary version
	canaryMetrics = Metrics{
		Version:     c.CanaryVersion,
		Requests:    c.CanaryTraffic * 10,
		ErrorRate:  c.CanaryErrorRate + rand.Float64()*0.5, // More variable
		LatencyMs:  45 + rand.Intn(60), // Slightly faster but more variable
	}

	return
}

// Metrics holds deployment metrics
type Metrics struct {
	Version    string
	Requests   int
	ErrorRate  float64
	LatencyMs  int
}

// EvaluateCanary determines if canary should be promoted, kept, or rolled back
func (c *CanaryDeployment) EvaluateCanary(stable, canary Metrics) string {
	// Check error rate
	if canary.ErrorRate > c.ErrorRateThreshold {
		return "ROLLBACK"
	}

	// Check latency
	if canary.LatencyMs > c.LatencyThresholdMs {
		return "PAUSE"
	}

	// If canary is better, promote
	if canary.ErrorRate < stable.ErrorRate && canary.LatencyMs < stable.LatencyMs {
		if c.CanaryTraffic < 50 {
			return "PROMOTE"
		}
	}

	// Otherwise maintain
	return "MAINTAIN"
}

func main() {
	rand.Seed(time.Now().UnixNano())

	canary := NewCanaryDeployment("v1.0", "v1.1")

	fmt.Println("=== Canary Deployment Simulation ===")
	fmt.Println()

	for round := 1; round <= 10; round++ {
		stable, canaryMetrics := canary.SimulateTraffic()

		decision := canary.EvaluateCanary(stable, canaryMetrics)

		fmt.Printf("Round %d - Traffic: %d%% | Canary Err: %.2f%% | Latency: %dms\n",
			round, canary.CanaryTraffic, canaryMetrics.ErrorRate*100, canaryMetrics.LatencyMs)
		fmt.Printf("  Decision: %s\n", decision)

		switch decision {
		case "PROMOTE":
			canary.CanaryTraffic = min(canary.CanaryTraffic*2, 100)
			fmt.Printf("  → Promoting to %d%%\n", canary.CanaryTraffic)
		case "ROLLBACK":
			fmt.Println("  → Rolling back canary!")
			break
		case "PAUSE":
			fmt.Println("  → Pausing, investigating...")
		case "MAINTAIN":
			fmt.Println("  → Maintaining current traffic")
		}

		time.Sleep(500 * time.Millisecond)
	}

	// Inject a fault to trigger rollback
	fmt.Println("\n--- Injecting fault at round 12 ---")
	canary.CanaryErrorRate = 5.0 // Spike error rate
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}
```

### Step 3: Run Simulation

```bash
go run canary.go
```

**Expected Output**:
```
=== Canary Deployment Simulation ===

Round 1 - Traffic: 1% | Canary Err: 0.32% | Latency: 72ms
  Decision: MAINTAIN
  → Maintaining current traffic
Round 2 - Traffic: 1% | Canary Err: 0.45% | Latency: 68ms
  Decision: MAINTAIN
  → Maintaining current traffic
...
Round 5 - Traffic: 2% | Canary Err: 0.28% | Latency: 55ms
  Decision: PROMOTE
  → Promoting to 4%
...
Round 12 - Traffic: 8% | Canary Err: 5.23% | Latency: 89ms
  Decision: ROLLBACK
  → Rolling back canary!
```

### 🔧 Stretch Challenge (Staff-Level)

Add **multi-metric analysis**:
- Add p50, p95, p99 latency tracking
- Add health check endpoint simulation
- Implement gradual latency degradation detection
- Add "golden metrics" comparison (error rate + latency + throughput)

---

## Lab 4: Visualize Deployment Trade-offs (Python)

### 🎯 Goal
Create visualizations comparing deployment strategies.

### ⏱ Time: ~15 mins

### Step 1: Run Existing Visualizations

```bash
cd ../visualizations
python visualizations.py
```

### Step 2: Extend the Visualization

Add a new chart showing **risk over time** for different deployment strategies:

```python
import matplotlib.pyplot as plt
import numpy as np

# Time points (deployment phases)
phases = ['Pre-Deploy', 'Deploy 25%', 'Deploy 50%', 'Deploy 75%', 'Deploy 100%']

# Risk levels for different strategies (0-10 scale, higher = riskier)
big_bang = [5, 10, 10, 10, 10]  # All risk at once
rolling = [5, 7, 8, 9, 10]     # Gradual increase
canary = [5, 3, 4, 6, 10]      # Starts lower due to testing
feature_flags = [2, 2, 3, 4, 10]  # Very low until full release

plt.figure(figsize=(10, 6))
plt.plot(phases, big_bang, marker='o', label='Big Bang', linewidth=2)
plt.plot(phases, rolling, marker='s', label='Rolling', linewidth=2)
plt.plot(phases, canary, marker='^', label='Canary', linewidth=2)
plt.plot(phases, feature_flags, marker='d', label='Feature Flags', linewidth=2)

plt.xlabel('Deployment Phase', fontweight='bold')
plt.ylabel('Risk Level (0-10)', fontweight='bold')
plt.title('Risk Profile During Deployment', fontsize=14, fontweight='bold')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('risk_over_time.png', dpi=150)
plt.show()
```

### 🔧 Stretch Challenge (Staff-Level)

Create a **cost-benefit analysis** chart:
- X-axis: Deployment frequency (deploys per month)
- Y-axis: Total cost (infrastructure + operational)
- Lines for each strategy
- Show the "sweet spot" where feature flags become cost-effective

---

## 🏆 Completion Criteria

| Lab | Core Requirement | Stretch Goal |
|-----|------------------|--------------|
| Lab 1 | Version router handles URL, header, query param | Content negotiation |
| Lab 2 | Feature flag with whitelist + percentage | Audit logging |
| Lab 3 | Canary with auto-promotion/rollback | Multi-metric analysis |
| Lab 4 | Run existing visualizations | Cost-benefit analysis |

---

## 📚 Further Reading

- **Release It!** (Chapter 12) — Nygard's original treatment
- **The DevOps Handbook** — CI/CD best practices
- **Site Reliability Engineering** — Google's SRE book, Chapter 8 (Release Management)
- **Google SRE Book**: https://sre.google/sre-book/release-management/

---

## 🔗 Connect to Next Chapter

Chapter 12's deployment strategies set the stage for **Chapter 13: Chaos Engineering**. Once you can deploy safely, the next question is: *how do you test your deployment in production?*

Key connection:
- Feature flags enable **chaos experiments** (canary is a simple form)
- Rollback mechanisms are essential for **controlled chaos**
- Versioning supports **gradual degradation testing**

*Next: Chapter 13 - Chaos Engineering →*
