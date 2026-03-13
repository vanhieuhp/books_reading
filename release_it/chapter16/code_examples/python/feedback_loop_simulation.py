"""
Chapter 16: The Systemic View - Feedback Loop Simulation
Language: Python (simulation and visualization)

This script demonstrates:
1. Positive feedback loops - reinforcing cycles that can lead to exponential growth OR failure
2. Negative feedback loops - balancing cycles that maintain stability
3. The impact of delays in feedback systems

Run: python code_examples/python/feedback_loop_simulation.py
"""

import matplotlib.pyplot as plt
import numpy as np
from dataclasses import dataclass, field
from typing import List, Callable
import random


# ============================================================
# SECTION 1: Feedback Loop Models
# ============================================================

@dataclass
class SystemState:
    """Represents the state of a system at a point in time."""
    time: float
    value: float
    value_name: str = "system_value"


class FeedbackLoop:
    """
    Base class for feedback loop simulation.

    A feedback loop has:
    - A sensor: measures the current state
    - An effector: takes action based on the state
    - A delay: time between action and effect

    Staff insight: Delays are critical - they can cause oscillation
    or over-correction if not properly tuned.
    """

    def __init__(self, name: str, delay: float = 0.0):
        self.name = name
        self.delay = delay
        self.history: List[SystemState] = []
        self._delayed_values: List[tuple] = []  # (time, value)

    def sense(self, current_value: float) -> float:
        """SENSE PHASE: Measure the current state."""
        raise NotImplementedError

    def act(self, sensed_value: float) -> float:
        """ACT PHASE: Take action based on sensed value."""
        raise NotImplementedError

    def apply_delay(self, current_time: float, value: float) -> float:
        """Apply feedback delay - critical for realistic simulation."""
        if self.delay <= 0:
            return value

        # Add to delayed values
        self._delayed_values.append((current_time + self.delay, value))

        # Remove old values
        self._delayed_values = [
            (t, v) for t, v in self._delayed_values
            if t > current_time
        ]

        # Return most recent delayed value
        if self._delayed_values:
            return self._delayed_values[0][1]
        return value

    def step(self, current_value: float, time: float) -> float:
        """Execute one step of the feedback loop."""
        # Sense
        sensed = self.sense(current_value)

        # Apply delay (if any)
        delayed_sensed = self.apply_delay(time, sensed)

        # Act
        action = self.act(delayed_sensed)

        # Record history
        self.history.append(SystemState(time, current_value))

        return action


class PositiveFeedbackLoop(FeedbackLoop):
    """
    Positive (reinforcing) feedback loop.

    Example: Success breeds success
    - More users → more revenue → more investment → better product → more users

    Staff insight: Positive feedback is dangerous in production systems
    because it amplifies both good AND bad outcomes. Need balancing mechanisms.
    """

    def __init__(self, name: str, growth_rate: float, delay: float = 0.0):
        super().__init__(name, delay)
        self.growth_rate = growth_rate  # How fast it amplifies

    def sense(self, current_value: float) -> float:
        """Sense the current value - for positive feedback, we want MORE."""
        return current_value

    def act(self, sensed_value: float) -> float:
        """Act: amplify the value (reinforce the trend)."""
        return sensed_value * (1 + self.growth_rate)


class NegativeFeedbackLoop(FeedbackLoop):
    """
    Negative (balancing) feedback loop.

    Example: Thermostat
    - Temperature too high → AC turns on → temperature drops → AC turns off

    Staff insight: Negative feedback is essential for stability.
    The challenge is tuning the threshold and delay to avoid oscillation.
    """

    def __init__(self, name: str, target: float, correction_rate: float, delay: float = 0.0):
        super().__init__(name, delay)
        self.target = target  # The desired state
        self.correction_rate = correction_rate  # How fast we correct

    def sense(self, current_value: float) -> float:
        """Sense deviation from target."""
        return self.target - current_value

    def act(self, sensed_value: float) -> float:
        """Act: correct in the opposite direction (hence "negative")."""
        return sensed_value * self.correction_rate


# ============================================================
# SECTION 2: Production System Examples
# ============================================================

class AutoScalingFeedback(FeedbackLoop):
    """
    Real-world example: Auto-scaling in cloud infrastructure.

    This is a negative feedback loop:
    - Load increases → scale out → load decreases → scale in

    Staff insight: Delays in auto-scaling cause oscillation.
    - Scale-up delay: by the time instances are ready, load may have peaked
    - Scale-down delay: by the time we scale down, load may have bottomed out

    This is why "hysteresis" (delayed scaling) is critical.
    """

    def __init__(self, target_utilization: float = 0.7,
                 instance_capacity: int = 100,
                 scale_up_threshold: float = 0.8,
                 scale_down_threshold: float = 0.5,
                 delay: float = 1.0):
        super().__init__("auto-scaling", delay)
        self.target_utilization = target_utilization
        self.instance_capacity = instance_capacity
        self.scale_up_threshold = scale_up_threshold
        self.scale_down_threshold = scale_down_threshold
        self.instances = 1

    def sense(self, current_load: float) -> float:
        """Calculate current utilization."""
        return current_load / (self.instances * self.instance_capacity)

    def act(self, utilization: float) -> float:
        """Scale instances based on utilization."""
        if utilization > self.scale_up_threshold:
            # Need more instances
            new_instances = max(1, int(utilization * self.instances / self.target_utilization))
            added = new_instances - self.instances
            self.instances = new_instances
            return added
        elif utilization < self.scale_down_threshold:
            # Can reduce instances
            new_instances = max(1, int(utilization * self.instances / self.target_utilization))
            removed = self.instances - new_instances
            self.instances = new_instances
            return -removed
        return 0


class CircuitBreakerFeedback(FeedbackLoop):
    """
    Real-world example: Circuit Breaker pattern.

    This is a negative feedback loop that prevents cascade failures:
    - Failures detected → open circuit → reject requests → service recovers

    Staff insight: The failure threshold and recovery timeout are critical.
    Too sensitive: circuit opens too often, degrading UX
    Too lenient: cascade failures occur before circuit opens
    """

    def __init__(self, failure_threshold: int = 5,
                 recovery_timeout: float = 10.0,
                 half_open_successes_needed: int = 3):
        super().__init__("circuit-breaker", delay=0)
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_successes_needed = half_open_successes_needed

        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None

    def sense(self, request_success: bool) -> float:
        """Sense whether the last request succeeded."""
        return 1.0 if request_success else 0.0

    def act(self, success_indicator: float) -> float:
        """Update circuit state based on success/failure."""
        current_time = self.history[-1].time if self.history else 0

        if self.state == "CLOSED":
            if success_indicator < 0.5:
                self.failure_count += 1
                self.last_failure_time = current_time
                if self.failure_count >= self.failure_threshold:
                    self.state = "OPEN"
                    self.failure_count = 0
                    return -1  # Circuit opening

        elif self.state == "OPEN":
            if self.last_failure_time:
                if current_time - self.last_failure_time > self.recovery_timeout:
                    self.state = "HALF_OPEN"
                    self.success_count = 0
                    return 0.5  # Testing recovery

        elif self.state == "HALF_OPEN":
            if success_indicator >= 0.5:
                self.success_count += 1
                if self.success_count >= self.half_open_successes_needed:
                    self.state = "CLOSED"
                    self.failure_count = 0
                    return 1  # Circuit closed
            else:
                self.state = "OPEN"
                self.last_failure_time = current_time
                return -1  # Circuit reopened

        return 0  # No state change


# ============================================================
# SECTION 3: Simulation and Visualization
# ============================================================

def simulate_feedback_loop(loop: FeedbackLoop,
                          initial_value: float,
                          steps: int,
                          external_force: Callable[[int], float] = None) -> List[SystemState]:
    """Simulate a feedback loop over time."""

    current_value = initial_value

    for t in range(steps):
        # Apply external force (e.g., varying load)
        if external_force:
            current_value += external_force(t)

        # Apply feedback loop
        change = loop.step(current_value, float(t))
        current_value += change

        # Clamp to reasonable bounds
        current_value = max(0, current_value)

    return loop.history


def plot_feedback_comparison():
    """Plot comparison of positive vs negative feedback loops."""

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # --- Plot 1: Positive Feedback (Growth) ---
    ax = axes[0, 0]
    loop = PositiveFeedbackLoop("growth", growth_rate=0.1, delay=0)
    history = simulate_feedback_loop(loop, initial_value=10, steps=50)

    times = [s.time for s in history]
    values = [s.value for s in history]
    ax.plot(times, values, 'b-', linewidth=2, label='System Value')
    ax.axhline(y=100, color='r', linestyle='--', alpha=0.5, label='Capacity Limit')
    ax.set_title('Positive Feedback: Exponential Growth', fontweight='bold')
    ax.set_xlabel('Time')
    ax.set_ylabel('Value')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # --- Plot 2: Positive Feedback (Failure Cascade) ---
    ax = axes[0, 1]
    # Simulate failure cascade: one component fails, triggers others
    cascade_values = [100]
    for t in range(1, 50):
        # Each step, lose 10% of remaining + some randomness
        loss = cascade_values[-1] * 0.1 + random.uniform(-5, 5)
        new_value = max(0, cascade_values[-1] - loss)
        cascade_values.append(new_value)

    ax.plot(range(50), cascade_values, 'r-', linewidth=2)
    ax.fill_between(range(50), cascade_values, alpha=0.3, color='red')
    ax.set_title('Positive Feedback: Failure Cascade', fontweight='bold')
    ax.set_xlabel('Time')
    ax.set_ylabel('System Health %')
    ax.grid(True, alpha=0.3)

    # --- Plot 3: Negative Feedback (Stable) ---
    ax = axes[1, 0]
    loop = NegativeFeedbackLoop("thermostat", target=70, correction_rate=0.3, delay=0)

    # Simulate with varying external temperature
    def external_temp(t: int) -> float:
        return 10 * np.sin(t / 5)  # Oscillating external temperature

    history = simulate_feedback_loop(loop, initial_value=50, steps=50,
                                      external_force=external_temp)

    times = [s.time for s in history]
    values = [s.value for s in history]
    ax.plot(times, values, 'g-', linewidth=2, label='System Value')
    ax.axhline(y=70, color='r', linestyle='--', alpha=0.5, label='Target')
    ax.set_title('Negative Feedback: Stable Equilibrium', fontweight='bold')
    ax.set_xlabel('Time')
    ax.set_ylabel('Value')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # --- Plot 4: Negative Feedback with Delay (Oscillation) ---
    ax = axes[1, 1]
    loop_with_delay = NegativeFeedbackLoop("thermostat_delayed", target=70,
                                           correction_rate=0.5, delay=3)

    history = simulate_feedback_loop(loop_with_delay, initial_value=50, steps=50,
                                     external_force=external_temp)

    times = [s.time for s in history]
    values = [s.value for s in history]
    ax.plot(times, values, 'purple', linewidth=2, label='With Delay')
    ax.axhline(y=70, color='r', linestyle='--', alpha=0.5, label='Target')
    ax.set_title('Negative Feedback + Delay: Oscillation', fontweight='bold')
    ax.set_xlabel('Time')
    ax.set_ylabel('Value')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.suptitle('Feedback Loops: The Good, The Bad, and The Oscillating',
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('feedback_loop_comparison.png', dpi=150, bbox_inches='tight')
    print("[OK] Saved: feedback_loop_comparison.png")
    plt.close()


def plot_autoscaling_simulation():
    """Simulate auto-scaling behavior with feedback loops."""

    fig, ax = plt.subplots(1, 1, figsize=(12, 6))

    # Simulate varying load pattern
    np.random.seed(42)
    time_steps = 100

    # Create load pattern: gradual increase, peak, gradual decrease
    load_pattern = []
    for t in range(time_steps):
        base = 50 + 100 * np.sin(t / 20)  # Oscillating base load
        noise = np.random.normal(0, 20)  # Random variation
        load = max(10, base + noise)
        load_pattern.append(load)

    # Simulate auto-scaling
    scaler = AutoScalingFeedback(
        target_utilization=0.7,
        instance_capacity=100,
        scale_up_threshold=0.8,
        scale_down_threshold=0.5,
        delay=2.0  # 2-step delay in scaling
    )

    instances_history = [scaler.instances]
    utilization_history = []

    for t, load in enumerate(load_pattern):
        # Calculate current utilization
        util = load / (scaler.instances * scaler.instance_capacity)
        utilization_history.append(util)

        # Scale decision
        scaler.step(load, float(t))
        instances_history.append(scaler.instances)

    # Plot
    ax2 = ax.twinx()
    ax.plot(range(time_steps), load_pattern, 'b-', linewidth=2, label='Load')
    ax2.plot(range(time_steps), utilization_history, 'orange', linewidth=2,
             linestyle='--', label='Utilization')
    ax2.plot(range(len(instances_history)), [i * 100 for i in instances_history],
             'g-', linewidth=2, alpha=0.7, label='Capacity (load units)')

    ax.axhline(y=70, color='gray', linestyle=':', alpha=0.5)
    ax2.axhline(y=0.7, color='orange', linestyle=':', alpha=0.5)

    ax.set_title('Auto-Scaling Feedback Loop Simulation', fontweight='bold', fontsize=14)
    ax.set_xlabel('Time')
    ax.set_ylabel('Load (requests)', color='blue')
    ax2.set_ylabel('Utilization / Capacity', color='orange')

    # Combined legend
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('autoscaling_simulation.png', dpi=150, bbox_inches='tight')
    print("[OK] Saved: autoscaling_simulation.png")
    plt.close()


# ============================================================
# DEMO: Running the Simulations
# ============================================================

if __name__ == "__main__":
    print("=== Chapter 16: Feedback Loop Simulation ===\n")

    print("1. Running feedback loop comparison...")
    plot_feedback_comparison()

    print("\n2. Running auto-scaling simulation...")
    plot_autoscaling_simulation()

    print("\n3. Key Insights from Simulation:")
    print("""
    • Positive feedback amplifies changes (both good and bad)
      → Need balancing mechanisms in production systems

    • Negative feedback maintains stability
      → Too aggressive correction causes oscillation

    • Delays are critical
      → Auto-scaling delay causes "flapping"
      → Circuit breaker timeout must balance recovery vs. protection

    • The "sweet spot" depends on system characteristics
      → Need to tune thresholds and delays empirically
    """)
