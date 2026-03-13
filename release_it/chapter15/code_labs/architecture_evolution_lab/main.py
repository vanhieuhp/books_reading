"""
Architecture Evolution Lab
==========================

This lab demonstrates how to make architectural evolution decisions
based on system metrics - a key skill for staff/principal engineers.

Staff-level insight: This is analogous to what architectural
decision records (ADRs) capture - the reasoning behind choices.

Run: python main.py
"""

import random
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from enum import Enum
import numpy as np
import matplotlib.pyplot as plt


class EvolutionStrategy(Enum):
    """Evolution strategies from Release It! Chapter 15"""
    MODULAR_MONOLITH = "modular_monolith"
    SERVICE_EXTRACTION = "service_extraction"
    STRANGLER = "strangler"
    BRANCH_BY_ABSTRACTION = "branch_by_abstraction"


@dataclass
class SystemMetrics:
    """What we're measuring to make evolution decisions"""
    # Team metrics
    team_size: int = 0
    deployment_frequency: str = "weekly"  # daily, weekly, monthly
    deployment_failure_rate: float = 0.0  # 0.0 to 1.0
    avg_deployment_time_minutes: float = 0.0

    # Development metrics
    code_conflicts_per_week: float = 0.0
    avg_build_time_minutes: float = 0.0

    # Performance metrics
    p99_latency_ms: float = 0.0

    # Database metrics
    database_cpu_percent: float = 0.0
    database_connections_used: int = 10
    database_max_connections: int = 100

    # Reliability
    incident_count_per_month: int = 0


@dataclass
class EvolutionRecommendation:
    strategy: EvolutionStrategy
    confidence: float  # 0.0 to 1.0
    reasoning: List[str]
    risk_level: str  # low, medium, high
    estimated_effort_months: int


class ArchitectureEvolutionSimulator:
    """
    Simulates architecture evolution decision-making.
    """

    def __init__(self):
        self.metrics_history: List[SystemMetrics] = []

    def add_metrics(self, metrics: SystemMetrics):
        """Add metrics snapshot to history"""
        self.metrics_history.append(metrics)

    def calculate_trouble_score(self, metrics: SystemMetrics) -> float:
        """
        Calculate composite trouble score (0-100).
        Higher = more pain = evolution needed.
        """
        score = 0.0

        # Deployment pain (max 30 points)
        freq_map = {"daily": 5, "weekly": 15, "monthly": 25}
        score += freq_map.get(metrics.deployment_frequency, 15)
        score += min(5, metrics.deployment_failure_rate * 25)

        # Development pain (max 30 points)
        score += min(20, metrics.code_conflicts_per_week * 1.5)
        score += min(10, metrics.avg_build_time_minutes / 3)

        # Performance pain (max 20 points)
        if metrics.p99_latency_ms > 2000:
            score += 20
        elif metrics.p99_latency_ms > 1000:
            score += 12
        elif metrics.p99_latency_ms > 500:
            score += 5

        # Database pain (max 15 points)
        if metrics.database_cpu_percent > 80:
            score += 10
        elif metrics.database_cpu_percent > 60:
            score += 5

        db_util = metrics.database_connections_used / metrics.database_max_connections
        if db_util > 0.8:
            score += 5

        # Reliability (max 5 points)
        score += min(5, metrics.incident_count_per_month)

        return min(100, score)

    def analyze_signs_of_trouble(self) -> Dict[str, bool]:
        """Analyze current metrics for signs that evolution is needed"""
        if not self.metrics_history:
            return {}

        current = self.metrics_history[-1]
        trouble = self.calculate_trouble_score(current)

        return {
            # Technical signs
            "deployment_pain": (
                current.deployment_frequency in ["monthly"] or
                current.deployment_failure_rate > 0.2
            ),
            "performance_issues": current.p99_latency_ms > 1000,
            "development_slowdown": current.code_conflicts_per_week > 10,
            "reliability_issues": current.incident_count_per_month > 4,
            "database_bottleneck": current.database_cpu_percent > 80,

            # Composite
            "high_trouble": trouble > 50,
        }

    def recommend_strategy(self) -> EvolutionRecommendation:
        """
        Core decision logic - this is what staff engineers do.
        Based on Release It! Chapter 15 framework.
        """
        if not self.metrics_history:
            return EvolutionRecommendation(
                strategy=EvolutionStrategy.MODULAR_MONOLITH,
                confidence=0.5,
                reasoning=["No metrics available, recommending safe start"],
                risk_level="low",
                estimated_effort_months=1
            )

        current = self.metrics_history[-1]
        trouble = self.calculate_trouble_score(current)
        signs = self.analyze_signs_of_trouble()

        # Decision tree based on Nygard's framework

        # 1. Small team (< 10) - stay monolith, optimize first
        if current.team_size < 10:
            if signs.get("high_trouble"):
                return EvolutionRecommendation(
                    strategy=EvolutionStrategy.MODULAR_MONOLITH,
                    confidence=0.85,
                    reasoning=[
                        f"Team size ({current.team_size}) is small",
                        "Focus on modular boundaries within monolith first",
                        "Service extraction adds unnecessary complexity"
                    ],
                    risk_level="low",
                    estimated_effort_months=2
                )
            else:
                return EvolutionRecommendation(
                    strategy=EvolutionStrategy.MODULAR_MONOLITH,
                    confidence=0.95,
                    reasoning=[
                        "Team small enough to coordinate effectively",
                        "Monolith provides simplest deployment model"
                    ],
                    risk_level="low",
                    estimated_effort_months=0
                )

        # 2. Medium team (10-25) - consider extraction
        if 10 <= current.team_size <= 25:
            if signs.get("development_slowdown") or trouble > 40:
                return EvolutionRecommendation(
                    strategy=EvolutionStrategy.SERVICE_EXTRACTION,
                    confidence=0.75,
                    reasoning=[
                        f"Team size ({current.team_size}) creating coordination overhead",
                        f"Trouble score {trouble:.0f} indicates stress",
                        "Extract independent modules to services"
                    ],
                    risk_level="medium",
                    estimated_effort_months=4
                )
            else:
                return EvolutionRecommendation(
                    strategy=EvolutionStrategy.MODULAR_MONOLITH,
                    confidence=0.7,
                    reasoning=[
                        f"Team size ({current.team_size}) manageable with structure",
                        "Add modular boundaries, defer extraction"
                    ],
                    risk_level="low",
                    estimated_effort_months=2
                )

        # 3. Large team (25+) or specific triggers
        if current.team_size > 25:
            if signs.get("database_bottleneck"):
                return EvolutionRecommendation(
                    strategy=EvolutionStrategy.STRANGLER,
                    confidence=0.7,
                    reasoning=[
                        "Database limits reached - may need new data layer",
                        "Strangler allows incremental migration with zero downtime",
                        "Can rollback at any percentage if issues arise"
                    ],
                    risk_level="medium",
                    estimated_effort_months=8
                )
            else:
                return EvolutionRecommendation(
                    strategy=EvolutionStrategy.SERVICE_EXTRACTION,
                    confidence=0.8,
                    reasoning=[
                        f"Team at {current.team_size} developers needs autonomy",
                        "Conway's Law: communication overhead scales quadratically",
                        "Services enable independent team operation"
                    ],
                    risk_level="medium",
                    estimated_effort_months=6
                )

        # Default: stay modular, evolve as needed
        return EvolutionRecommendation(
            strategy=EvolutionStrategy.MODULAR_MONOLITH,
            confidence=0.6,
            reasoning=["No clear trigger for evolution detected"],
            risk_level="low",
            estimated_effort_months=1
        )

    def simulate_scale_growth(self, months: int = 12) -> Dict[str, List[float]]:
        """Simulate metrics growth over time"""
        team_sizes = []
        complexity_scores = []

        team = 5
        for month in range(months):
            team_sizes.append(team)
            # Conway's Law: complexity grows with team communication
            # O(n^2) communication overhead approximation
            complexity = (team * (team - 1)) / 2 / 10
            complexity_scores.append(complexity)

            # Growth with some randomness
            team += random.choices([0, 1, 2, 3], weights=[0.3, 0.4, 0.2, 0.1])[0]

        return {"team_size": team_sizes, "complexity": complexity_scores}


def run_scenario(name: str, metrics: SystemMetrics):
    """Run a single scenario and print results"""
    print("=" * 60)
    print(f"Scenario: {name}")
    print("=" * 60)

    simulator = ArchitectureEvolutionSimulator()
    simulator.add_metrics(metrics)

    trouble = simulator.calculate_trouble_score(metrics)
    print(f"Trouble Score: {trouble:.1f}/100")

    signs = simulator.analyze_signs_of_trouble()
    print("\nSigns of Trouble:")
    for sign, is_present in signs.items():
        status = "YES" if is_present else "no"
        print(f"  - {sign}: {status}")

    rec = simulator.recommend_strategy()
    print(f"\nRecommended Strategy: {rec.strategy.value}")
    print(f"Confidence: {rec.confidence * 100:.0f}%")
    print(f"Risk Level: {rec.risk_level}")
    print(f"Estimated Effort: {rec.estimated_effort_months} months")
    print("\nReasoning:")
    for r in rec.reasoning:
        print(f"  - {r}")
    print()


def demo_scenarios():
    """Demonstrate different scenarios"""

    # Scenario 1: Small team, healthy system
    run_scenario("Small Team, Healthy System", SystemMetrics(
        team_size=6,
        deployment_frequency="daily",
        deployment_failure_rate=0.05,
        code_conflicts_per_week=2,
        p99_latency_ms=100,
        database_cpu_percent=25,
        incident_count_per_month=1
    ))

    # Scenario 2: Growing team, conflicts increasing
    run_scenario("Growing Team, High Conflicts", SystemMetrics(
        team_size=22,
        deployment_frequency="weekly",
        deployment_failure_rate=0.15,
        code_conflicts_per_week=15,
        avg_build_time_minutes=25,
        p99_latency_ms=350,
        database_cpu_percent=55,
        incident_count_per_month=5
    ))

    # Scenario 3: Scale issues - database bottleneck
    run_scenario("Scale Issues - Database Bottleneck", SystemMetrics(
        team_size=40,
        deployment_frequency="daily",
        deployment_failure_rate=0.08,
        code_conflicts_per_week=8,
        p99_latency_ms=2500,
        database_cpu_percent=95,
        incident_count_per_month=8
    ))

    # Scenario 4: Large team, needs extraction
    run_scenario("Large Team, Multiple Issues", SystemMetrics(
        team_size=60,
        deployment_frequency="weekly",
        deployment_failure_rate=0.20,
        code_conflicts_per_week=25,
        avg_build_time_minutes=40,
        p99_latency_ms=800,
        database_cpu_percent=70,
        incident_count_per_month=6
    ))


def visualize_complexity_growth():
    """Visualize Conway's Law effect"""
    simulator = ArchitectureEvolutionSimulator()
    data = simulator.simulate_scale_growth(24)

    plt.figure(figsize=(10, 5))
    plt.plot(data["team_size"], data["complexity"], 'b-o', linewidth=2, markersize=6)
    plt.axhline(y=10, color='r', linestyle='--', label='Complexity threshold (action needed)')
    plt.xlabel('Team Size')
    plt.ylabel('Communication Complexity (normalized)')
    plt.title("Conway's Law: Team Size vs Communication Complexity")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig('complexity_growth.png', dpi=150)
    print("\nVisualization saved to: complexity_growth.png")
    plt.close()


def visualize_decision_space():
    """Visualize the evolution decision space"""
    fig, ax = plt.subplots(figsize=(12, 6))

    sizes = [5, 10, 15, 25, 50, 75, 100]
    troubles = [20, 50, 80]

    colors = {
        EvolutionStrategy.MODULAR_MONOLITH: "#27AE60",
        EvolutionStrategy.SERVICE_EXTRACTION: "#3498DB",
        EvolutionStrategy.STRANGLER: "#9B59B6",
    }

    for size in sizes:
        for trouble in troubles:
            metrics = SystemMetrics(
                team_size=size,
                deployment_failure_rate=trouble / 100,
                code_conflicts_per_week=trouble / 5,
                database_cpu_percent=trouble
            )
            sim = ArchitectureEvolutionSimulator()
            sim.add_metrics(metrics)
            rec = sim.recommend_strategy()

            color = colors.get(rec.strategy, "#666")
            ax.scatter(size, trouble, c=color, s=300, edgecolors='black', linewidth=2)
            ax.annotate(
                rec.strategy.value.replace("_", "\n")[:20],
                (size, trouble),
                textcoords="offset points",
                xytext=(0, 18),
                ha='center',
                fontsize=7,
                fontweight='bold'
            )

    ax.set_xlabel("Team Size", fontsize=12)
    ax.set_ylabel("System Trouble Score", fontsize=12)
    ax.set_title("Architecture Evolution Decision Space", fontsize=14, fontweight='bold')
    ax.set_xlim(0, 110)
    ax.set_ylim(0, 100)
    ax.grid(True, alpha=0.3)

    # Legend
    for strategy, color in colors.items():
        ax.scatter([], [], c=color, s=150, label=strategy.value.replace("_", " ").title(),
                  edgecolors='black')
    ax.legend(loc='upper left', fontsize=9)

    plt.tight_layout()
    plt.savefig('evolution_decision_space.png', dpi=150)
    print("Visualization saved to: evolution_decision_space.png")
    plt.close()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("ARCHITECTURE EVOLUTION LAB")
    print("Release It! - Chapter 15")
    print("=" * 60 + "\n")

    # Run all scenarios
    demo_scenarios()

    # Generate visualizations
    print("\nGenerating visualizations...")
    visualize_complexity_growth()
    visualize_decision_space()

    print("\n" + "=" * 60)
    print("LAB COMPLETE")
    print("=" * 60)
    print("\nKey Takeaway:")
    print("  - Small team + healthy = Stay monolith")
    print("  - Growing team + conflicts = Extract services")
    print("  - Scale issues = Consider strangler")
    print("  - Team size > 25 = Services help with autonomy")
