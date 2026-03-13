"""
Chaos Engineering Engine - Python Implementation
================================================
A Chaos Mesh-style chaos orchestration engine for Kubernetes workloads.
Staff-level: Production-grade code with proper error handling and observability.
"""

import asyncio
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Callable
from datetime import datetime


class FailureType(Enum):
    """Types of chaos we can inject"""
    POD_KILL = "pod_kill"
    NETWORK_PARTITION = "network_partition"
    LATENCY = "latency"
    CPU_STRESS = "cpu_stress"
    MEMORY_STRESS = "memory_stress"
    IO_STRESS = "io_stress"
    PACKET_LOSS = "packet_loss"


class ExperimentStatus(Enum):
    """Lifecycle of a chaos experiment"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABORTED = "aborted"
    FAILED = "failed"


@dataclass
class SteadyState:
    """
    What 'normal' looks like for your system.
    Staff-level insight: Define these empirically, not arbitrarily.
    Run baseline measurements during low-traffic periods.
    """
    name: str
    metric: str
    operator: str  # "gt", "lt", "eq", "gte", "lte"
    value: float
    duration_seconds: int = 300  # How long to measure


@dataclass
class ChaosExperiment:
    """
    A structured chaos experiment following the Nygard framework.
    """
    name: str
    namespace: str
    target_kind: str  # "Deployment", "StatefulSet", "Pod"
    target_name: str
    failure_type: FailureType
    failure_params: Dict
    steady_states: List[SteadyState]
    hypothesis: str
    expected_outcome: str
    duration_seconds: int = 60
    status: ExperimentStatus = ExperimentStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    abort_conditions: List[Dict] = field(default_factory=list)
    callbacks: List[Callable] = field(default_factory=list)

    def validate(self) -> List[str]:
        """Validate experiment configuration"""
        errors = []

        if not self.name:
            errors.append("Experiment name is required")
        if not self.namespace:
            errors.append("Namespace is required")
        if not self.target_name:
            errors.append("Target is required")
        if self.duration_seconds <= 0:
            errors.append("Duration must be positive")
        if not self.steady_states:
            errors.append("At least one steady state is required")

        return errors


@dataclass
class ExperimentResult:
    """What happened during the experiment"""
    experiment_name: str
    started_at: datetime
    ended_at: datetime
    status: ExperimentStatus
    steady_state_passed: bool = True
    steady_state_violations: List[Dict] = field(default_factory=list)
    metrics_before: Dict[str, float] = field(default_factory=dict)
    metrics_during: List[Dict[str, float]] = field(default_factory=list)
    metrics_after: Dict[str, float] = field(default_factory=dict)
    abort_reason: Optional[str] = None
    observations: List[str] = field(default_factory=list)


class ChaosEngine:
    """
    A chaos engineering orchestration engine.
    In production, this would interface with Kubernetes API,
    Prometheus for metrics, and a chaos solution like Chaos Mesh.
    """

    def __init__(self, kube_config: Optional[str] = None):
        self.kube_config = kube_config
        self.experiments: List[ChaosExperiment] = []
        self.results: List[ExperimentResult] = []

    async def run_experiment(self, experiment: ChaosExperiment) -> ExperimentResult:
        """
        Execute a chaos experiment with full observability.
        This follows the scientific method: hypothesis, experiment, analysis.
        """
        print(f"\n{'='*60}")
        print(f"🔬 CHAOS EXPERIMENT: {experiment.name}")
        print(f"{'='*60}")

        # Validation
        errors = experiment.validate()
        if errors:
            print(f"❌ Validation failed: {errors}")
            experiment.status = ExperimentStatus.FAILED
            return self._create_failed_result(experiment, errors)

        experiment.status = ExperimentStatus.RUNNING
        experiment.start_time = datetime.now()

        # Phase 1: Measure steady state (baseline)
        print("\n📊 Phase 1: Measuring steady state...")
        before_metrics = await self._measure_steady_state(experiment)
        experiment.status = ExperimentStatus.RUNNING

        # Phase 2: Inject failure
        print(f"\n💥 Phase 2: Injecting {experiment.failure_type.value}...")
        print(f"   Target: {experiment.namespace}/{experiment.target_name}")
        print(f"   Duration: {experiment.duration_seconds}s")
        await self._inject_failure(experiment)

        # Phase 3: Monitor during experiment
        print("\n📈 Phase 3: Monitoring during experiment...")
        during_metrics = await self._monitor_during_experiment(experiment)

        # Phase 4: Stop injection and recover
        print("\n⬅️ Phase 4: Stopping injection and recovering...")
        await self._recover_from_failure(experiment)

        # Phase 5: Measure after state
        print("\n📊 Phase 5: Measuring post-experiment state...")
        after_metrics = await self._measure_steady_state(experiment)

        # Phase 6: Analyze results
        print("\n🔍 Phase 6: Analyzing results...")
        experiment.status = ExperimentStatus.COMPLETED
        experiment.end_time = datetime.now()

        result = self._analyze_results(
            experiment, before_metrics, during_metrics, after_metrics
        )

        self.results.append(result)
        self._print_result_summary(result)

        return result

    async def _measure_steady_state(self, exp: ChaosExperiment) -> Dict[str, float]:
        """
        Measure current system metrics.
        Staff-level insight: Use p99, not averages - averages hide outliers.
        """
        # In production: Query Prometheus, CloudWatch, DataDog
        # Staff-level insight: Use p99, not averages - averages hide outliers
        await asyncio.sleep(0.1)  # Simulate API call

        return {
            "p50_latency_ms": 45.2,
            "p95_latency_ms": 120.5,
            "p99_latency_ms": 250.0,
            "error_rate": 0.002,
            "success_rate": 99.8,
            "throughput_rps": 1500.0,
            "cpu_usage": 62.5,
            "memory_usage": 71.2,
        }

    async def _inject_failure(self, exp: ChaosExperiment):
        """Inject the chaos failure"""
        # In production: Use Kubernetes API, network policies, cgroups
        await asyncio.sleep(exp.duration_seconds / 1000.0)

    async def _monitor_during_experiment(self, exp: ChaosExperiment) -> List[Dict]:
        """Continuously monitor and check abort conditions"""
        metrics = []
        check_interval = 2  # seconds

        num_checks = exp.duration_seconds // check_interval

        for i in range(num_checks):
            current_metrics = await self._measure_steady_state(exp)
            metrics.append(current_metrics)

            # Check abort conditions
            for condition in exp.abort_conditions:
                metric = condition.get("metric")
                operator = condition.get("operator")
                threshold = condition.get("threshold")

                if metric in current_metrics:
                    value = current_metrics[metric]
                    should_abort = self._evaluate_condition(value, operator, threshold)

                    if should_abort:
                        print(f"\n⚠️  ABORT CONDITION TRIGGERED!")
                        print(f"   {metric} {operator} {threshold}")
                        print(f"   Current value: {value}")
                        exp.status = ExperimentStatus.ABORTED
                        return metrics

            await asyncio.sleep(check_interval)

        return metrics

    def _evaluate_condition(self, value: float, operator: str, threshold: float) -> bool:
        """Evaluate if abort condition is met"""
        ops = {
            ">": lambda v, t: v > t,
            "<": lambda v, t: v < t,
            ">=": lambda v, t: v >= t,
            "<=": lambda v, t: v <= t,
            "==": lambda v, t: v == t,
        }
        return ops.get(operator, lambda v, t: False)(value, threshold)

    async def _recover_from_failure(self, exp: ChaosExperiment):
        """Rollback the injected failure"""
        # In production: Delete chaos resources, restart pods, etc.
        await asyncio.sleep(0.1)
        print("   Recovery complete")

    def _analyze_results(
        self,
        exp: ChaosExperiment,
        before: Dict[str, float],
        during: List[Dict[str, float]],
        after: Dict[str, float]
    ) -> ExperimentResult:
        """Analyze experiment results against hypothesis"""

        violations = []

        # Check steady state deviations
        for ss in exp.steady_states:
            before_val = before.get(ss.metric, 0)
            after_val = after.get(ss.metric, 0)

            # Calculate deviation
            deviation = abs(after_val - before_val) / max(before_val, 0.001) * 100

            if deviation > ss.value:
                violations.append({
                    "metric": ss.metric,
                    "before": before_val,
                    "after": after_val,
                    "deviation_pct": deviation,
                    "threshold": ss.value
                })

        hypothesis_passed = len(violations) == 0

        result = ExperimentResult(
            experiment_name=exp.name,
            started_at=exp.start_time,
            ended_at=exp.end_time,
            status=exp.status,
            steady_state_passed=hypothesis_passed,
            steady_state_violations=violations,
            metrics_before=before,
            metrics_after=after,
            observations=[f"Hypothesis: {exp.hypothesis}"]
        )

        return result

    def _create_failed_result(self, exp: ChaosExperiment, errors: List[str]) -> ExperimentResult:
        """Create a failed result"""
        return ExperimentResult(
            experiment_name=exp.name,
            started_at=datetime.now(),
            ended_at=datetime.now(),
            status=ExperimentStatus.FAILED,
            observations=[f"Validation failed: {e}" for e in errors]
        )

    def _print_result_summary(self, result: ExperimentResult):
        """Print a human-readable result summary"""
        print(f"\n{'='*60}")
        print("📋 EXPERIMENT RESULTS")
        print(f"{'='*60}")
        print(f"Status: {result.status.value}")
        print(f"Duration: {result.ended_at - result.started_at}")

        if result.steady_state_passed:
            print("\n✅ STEADY STATE MAINTAINED")
            print(f"   System remained stable during {result.experiment_name}")
        else:
            print("\n⚠️  STEADY STATE VIOLATED")
            for v in result.steady_state_violations:
                print(f"   {v['metric']}: {v['before']:.2f} → {v['after']:.2f} "
                      f"({v['deviation_pct']:.1f}% deviation)")

        print(f"\n📊 Metrics Comparison:")
        print(f"   Before → After:")
        for key in result.metrics_before:
            before = result.metrics_before.get(key, 0)
            after = result.metrics_after.get(key, 0)
            diff = after - before
            sign = "+" if diff > 0 else ""
            print(f"   {key}: {before:.2f} → {after:.2f} ({sign}{diff:.2f})")


async def main():
    """Example chaos experiment execution"""

    engine = ChaosEngine()

    # Define what "normal" looks like
    latency_steady_state = SteadyState(
        name="p99_latency",
        metric="p99_latency_ms",
        operator="<=",
        value=500.0,  # Allow 500ms deviation (50% increase acceptable)
        duration_seconds=60
    )

    error_steady_state = SteadyState(
        name="error_rate",
        metric="error_rate",
        operator="<=",
        value=1.0,  # Error rate must stay under 1%
        duration_seconds=60
    )

    # Create the experiment
    experiment = ChaosExperiment(
        name="inventory-service-pod-kill",
        namespace="orders",
        target_kind="Deployment",
        target_name="inventory-service",
        failure_type=FailureType.POD_KILL,
        failure_params={
            "mode": "random",  # Kill random pod
            "percentage": 25,  # Kill 25% of pods
        },
        steady_states=[latency_steady_state, error_steady_state],
        hypothesis="Killing 25% of inventory-service pods will maintain 99% success rate",
        expected_outcome="System should failover to remaining pods within 30 seconds",
        duration_seconds=30,
        abort_conditions=[
            {"metric": "error_rate", "operator": ">", "threshold": 5.0},
            {"metric": "p99_latency_ms", "operator": ">", "threshold": 2000.0},
        ]
    )

    # Run it
    result = await engine.run_experiment(experiment)

    # Output:
    # 🔬 CHAOS EXPERIMENT: inventory-service-pod-kill
    # ...
    # 📋 EXPERIMENT RESULTS
    # Status: completed
    # ✅ STEADY STATE MAINTAINED


if __name__ == "__main__":
    asyncio.run(main())
