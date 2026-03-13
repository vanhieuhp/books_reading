package chaos

import (
	"context"
	"fmt"
	"math/rand"
	"time"
)

// ============================================================
// Naive Approach: Hardcoded failure injection
// Problem: No steady state, no measurement, no rollback
// ============================================================

func naiveChaosExperiment() {
	fmt.Println("Starting chaos...")
	// What could go wrong? Everything.

	// Simulate killing a service
	killRandomService()

	// No hypothesis
	// No steady state defined
	// No measurement
	// No rollback plan

	fmt.Println("Chaos complete. Hope nothing broke!")
}

// killRandomService simulates a naive "chaos" approach
func killRandomService() {
	// Just pick a random service and kill it
	services := []string{"order-service", "payment-service", "user-service"}
	service := services[rand.Intn(len(services))]
	fmt.Printf("Killing service: %s (no safety checks!)\n", service)
	time.Sleep(100 * time.Millisecond)
}

// ============================================================
// Production Approach: Structured Chaos Engineering
// Following Nygard's steady-state hypothesis framework
// ============================================================

// SteadyState represents the normal, measurable behavior of the system
type SteadyState struct {
	Metrics   []Metric
	Window    time.Duration
	Threshold float64
}

// Metric represents a measurable system behavior
type Metric struct {
	Name       string
	Aggregator func([]float64) float64
	Value      float64
}

// Hypothesis defines what we expect to happen during the experiment
type Hypothesis struct {
	Description   string
	SteadyState   SteadyState
	Expected      string
	AbortCondition func(results *ExperimentResults) bool
}

// ExperimentResults captures what actually happened
type ExperimentResults struct {
	Before       map[string]float64
	After        map[string]float64
	Deviation    map[string]float64
	Duration     time.Duration
	Aborted      bool
	Observations []string
}

// ChaosExperiment is the structured experiment
type ChaosExperiment struct {
	Name       string
	Hypothesis Hypothesis
	Injection  FailureInjection
	Monitor    MonitoringConfig
	Rollback   func() error
}

// FailureInjection defines what failure to inject
type FailureInjection struct {
	Type       string
	Target     string
	Parameters map[string]interface{}
	Duration   time.Duration
}

// MonitoringConfig defines how we observe the experiment
type MonitoringConfig struct {
	MetricsEndpoint string
	PollInterval   time.Duration
	StopConditions []StopCondition
}

// StopCondition defines when to abort the experiment
type StopCondition struct {
	Metric   string
	Operator string // ">", "<", ">=", "<="
	Value    float64
}

// RunExperiment executes a chaos experiment with full observability
func RunExperiment(ctx context.Context, exp ChaosExperiment) (*ExperimentResults, error) {
	fmt.Printf("🔬 Running Chaos Experiment: %s\n", exp.Name)
	fmt.Printf("   Hypothesis: %s\n", exp.Hypothesis.Description)

	// Step 1: Measure steady state BEFORE injection
	fmt.Println("\n📊 Step 1: Measuring steady state...")
	beforeMetrics := measureMetrics(ctx, exp.Monitor)
	printMetrics("Before", beforeMetrics)

	// Step 2: Inject the failure
	fmt.Printf("\n💥 Step 2: Injecting %s failure on %s...\n",
		exp.Injection.Type, exp.Injection.Target)

	injectFailure(exp.Injection)

	// Step 3: Monitor during injection
	fmt.Println("📈 Step 3: Monitoring during experiment...")
	results := monitorExperiment(ctx, exp)

	// Step 4: Stop injection and rollback
	fmt.Println("\n⬅️ Step 4: Rolling back...")
	if err := exp.Rollback(); err != nil {
		fmt.Printf("   Rollback warning: %v\n", err)
	}

	// Step 5: Measure after state
	fmt.Println("\n📊 Step 5: Measuring post-experiment state...")
	afterMetrics := measureMetrics(ctx, exp.Monitor)
	printMetrics("After", afterMetrics)

	// Step 6: Calculate deviation
	results.Before = beforeMetrics
	results.After = afterMetrics
	results.Deviation = calculateDeviation(beforeMetrics, afterMetrics)

	fmt.Printf("\n📋 Results: Deviation from steady state\n")
	for metric, dev := range results.Deviation {
		fmt.Printf("   %s: %.2f%%\n", metric, dev)
	}

	// Validate hypothesis
	validateHypothesis(results, exp.Hypothesis)

	return results, nil
}

// measureMetrics scrapes metrics from the monitoring system
// Staff-level insight: Use histogram_quantile for latency, not averages
func measureMetrics(ctx context.Context, mc MonitoringConfig) map[string]float64 {
	// In production: scrape Prometheus, CloudWatch, DataDog, etc.
	// Staff-level insight: Use histogram_quantile for latency, not averages
	time.Sleep(100 * time.Millisecond) // Simulate measurement
	return map[string]float64{
		"p50_latency_ms":    45.0,
		"p99_latency_ms":    180.0,
		"error_rate":        0.001,
		"throughput_rps":    1250.0,
		"cpu_usage":         65.0,
	}
}

func injectFailure(inj FailureInjection) {
	// In production: use Kubernetes client, network policies, etc.
	fmt.Printf("   Injecting: %s for %v\n", inj.Type, inj.Duration)
	time.Sleep(50 * time.Millisecond)
}

func monitorExperiment(ctx context.Context, exp ChaosExperiment) *ExperimentResults {
	results := &ExperimentResults{
		Duration:    exp.Injection.Duration,
		Observations: []string{},
	}

	// Simulate observation loop
	ticker := time.NewTicker(exp.Monitor.PollInterval)
	defer ticker.Stop()

	obsCount := 0
	for {
		select {
		case <-ctx.Done():
			results.Aborted = true
			results.Observations = append(results.Observations, "Experiment aborted: context cancelled")
			return results
		case <-ticker.C:
			obsCount++
			// Check stop conditions
			for _, stop := range exp.Monitor.StopConditions {
				if shouldStop(stop) {
					results.Aborted = true
					results.Observations = append(results.Observations,
						fmt.Sprintf("Stopped due to: %s %s %.2f",
							stop.Metric, stop.Operator, stop.Value))
					return results
				}
			}
			if obsCount >= 5 {
				return results
			}
		}
	}
}

func shouldStop(stop StopCondition) bool {
	// Simplified: in production, compare actual metrics
	return false
}

func calculateDeviation(before, after map[string]float64) map[string]float64 {
	deviation := make(map[string]float64)
	for key, bVal := range before {
		if aVal, ok := after[key]; ok && bVal != 0 {
			deviation[key] = ((aVal - bVal) / bVal) * 100
		}
	}
	return deviation
}

func validateHypothesis(results *ExperimentResults, hyp Hypothesis) {
	fmt.Println("\n🎯 Hypothesis Validation:")
	fmt.Printf("   Expected: %s\n", hyp.Expected)

	// Staff-level insight: p99 matters more than averages for user impact
	// A 1% p99 increase affects 1 in 100 users = significant UX impact

	if results.Aborted {
		fmt.Println("   ❌ Experiment was aborted - safety mechanisms worked!")
		return
	}

	fmt.Println("   Results:")
	for metric, dev := range results.Deviation {
		status := "✅"
		if dev > 10 {
			status = "⚠️"
		}
		if dev > 50 {
			status = "❌"
		}
		fmt.Printf("   %s %s: %.2f%% deviation\n", status, metric, dev)
	}
}

func printMetrics(phase string, metrics map[string]float64) {
	fmt.Printf("   %s metrics:\n", phase)
	for key, val := range metrics {
		fmt.Printf("      %s: %.2f\n", key, val)
	}
}

// ExampleLatencyExperiment demonstrates running a latency injection experiment
func ExampleLatencyExperiment() {
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	experiment := ChaosExperiment{
		Name: "Payment Service Latency Injection",
		Hypothesis: Hypothesis{
			Description: "Adding 500ms latency to payment service will not exceed 2s p99",
			SteadyState: SteadyState{
				Window:    5 * time.Minute,
				Threshold: 500.0, // ms
			},
			Expected: "p99 latency stays under 2000ms",
			AbortCondition: func(r *ExperimentResults) bool {
				// Abort if error rate exceeds 5%
				return r.Deviation["error_rate"] > 5.0
			},
		},
		Injection: FailureInjection{
			Type:       "latency",
			Target:     "payment-service",
			Parameters: map[string]interface{}{"latency_ms": 500},
			Duration:   10 * time.Second,
		},
		Monitor: MonitoringConfig{
			MetricsEndpoint: "http://prometheus:9090/api/v1/query",
			PollInterval:    2 * time.Second,
			StopConditions: []StopCondition{
				{Metric: "error_rate", Operator: ">", Value: 5.0},
				{Metric: "p99_latency_ms", Operator: ">", Value: 5000.0},
			},
		},
		Rollback: func() error {
			// In production: remove injected fault, restart pods, etc.
			fmt.Println("   Rollback: Removing latency injection...")
			return nil
		},
	}

	results, err := RunExperiment(ctx, experiment)
	if err != nil {
		fmt.Printf("Experiment error: %v\n", err)
	}

	_ = results
}
