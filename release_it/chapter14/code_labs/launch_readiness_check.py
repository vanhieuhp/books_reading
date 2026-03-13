"""
Launch Readiness Assessment Tool
Chapter 14: The Trampled Product Launch
Validates that a system is ready for production traffic
"""

import asyncio
import json
import time
from dataclasses import dataclass, field
from typing import List, Dict, Callable, Any
from enum import Enum
from datetime import datetime


class ReadinessStatus(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"
    NOT_TESTED = "NOT_TESTED"


@dataclass
class ReadinessCheck:
    """Represents a single readiness check"""
    name: str
    category: str
    check_fn: Callable
    status: ReadinessStatus = ReadinessStatus.NOT_TESTED
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


# ============================================================
# INFRASTRUCTURE CHECKS
# ============================================================

async def check_connection_pool_size() -> ReadinessCheck:
    """
    Verify connection pool is sized for production load
    staff-level: This is one of the most common launch failures
    Rule of thumb: pool size should handle burst + have headroom
    """
    # Simulated check - in real code, query your database/infrastructure
    await asyncio.sleep(0.1)  # Simulate check

    # Example: PostgreSQL default is 100 connections
    # At 1000 req/sec with 10ms per query, you need ~10 connections
    # But bursts can be 5-10x, so pool of 25-50 is reasonable
    pool_size = 100  # This would be queried from config
    expected_peak = 500  # Expected concurrent requests

    if pool_size < expected_peak / 10:  # Less than 10% of peak
        return ReadinessCheck(
            name="Connection Pool Size",
            category="Infrastructure",
            check_fn=check_connection_pool_size,
            status=ReadinessStatus.FAIL,
            message=f"Pool size {pool_size} too small for {expected_peak} peak requests",
            details={"pool_size": pool_size, "expected_peak": expected_peak}
        )

    return ReadinessCheck(
        name="Connection Pool Size",
        category="Infrastructure",
        check_fn=check_connection_pool_size,
        status=ReadinessStatus.PASS,
        message=f"Pool size {pool_size} adequate for {expected_peak} peak",
        details={"pool_size": pool_size, "expected_peak": expected_peak}
    )


async def check_circuit_breakers() -> ReadinessCheck:
    """
    Verify circuit breakers are configured for all external dependencies
    staff-level: No external call should be without circuit protection
    """
    # Simulated - check your service configuration
    await asyncio.sleep(0.1)

    configured_dependencies = ["payment-api", "user-api", "notification-service"]
    # These would be discovered from your actual service config

    # If any major dependency lacks circuit breaker, fail
    missing = [d for d in configured_dependencies if d not in ["payment-api"]]  # Simplified

    if missing:
        return ReadinessCheck(
            name="Circuit Breakers Configured",
            category="Infrastructure",
            check_fn=check_circuit_breakers,
            status=ReadinessStatus.WARNING,
            message=f"Circuit breakers may be missing for: {missing}",
            details={"dependencies": configured_dependencies}
        )

    return ReadinessCheck(
        name="Circuit Breakers Configured",
        category="Infrastructure",
        check_fn=check_circuit_breakers,
        status=ReadinessStatus.PASS,
        message="Circuit breakers configured for all dependencies",
        details={"dependencies": configured_dependencies}
    )


async def check_timeouts() -> ReadinessCheck:
    """Verify all external calls have explicit timeouts"""
    await asyncio.sleep(0.1)

    # Check that timeouts are set (not using default infinite wait)
    timeout_configs = {
        "database": 5000,  # 5 seconds in ms
        "external_api": 10000,
        "cache": 2000,
    }

    # Validate all have timeouts
    missing_timeout = [k for k, v in timeout_configs.items() if v is None]

    if missing_timeout:
        return ReadinessCheck(
            name="Explicit Timeouts",
            category="Infrastructure",
            check_fn=check_timeouts,
            status=ReadinessStatus.FAIL,
            message=f"Missing timeouts for: {missing_timeout}",
            details={"timeout_configs": timeout_configs}
        )

    return ReadinessCheck(
        name="Explicit Timeouts",
        category="Infrastructure",
        check_fn=check_timeouts,
        status=ReadinessStatus.PASS,
        message="All external calls have explicit timeouts",
        details={"timeout_configs": timeout_configs}
    )


async def check_database_indexes() -> ReadinessCheck:
    """Verify database indexes exist for common query patterns"""
    await asyncio.sleep(0.1)

    # Check for missing indexes
    # In real code, query your database for missing index recommendations
    missing_indexes = ["user_email_idx", "order_status_idx"]

    if missing_indexes:
        return ReadinessCheck(
            name="Database Indexes",
            category="Infrastructure",
            check_fn=check_database_indexes,
            status=ReadinessStatus.WARNING,
            message=f"Missing indexes may cause slow queries: {missing_indexes}",
            details={"missing_indexes": missing_indexes}
        )

    return ReadinessCheck(
        name="Database Indexes",
        category="Infrastructure",
        check_fn=check_database_indexes,
        status=ReadinessStatus.PASS,
        message="All critical indexes exist",
        details={"indexes_checked": True}
    )


# ============================================================
# MONITORING CHECKS
# ============================================================

async def check_monitoring_coverage() -> ReadinessCheck:
    """Verify critical metrics are being collected"""
    await asyncio.sleep(0.1)

    critical_metrics = [
        "request_latency_p50",
        "request_latency_p99",
        "error_rate",
        "cpu_usage",
        "memory_usage",
        "database_connections",
        "cache_hit_rate",
    ]

    # In real code, query your monitoring system
    # This simulates checking if metrics exist
    collected_metrics = critical_metrics[:-1]  # Missing cache_hit_rate

    missing = set(critical_metrics) - set(collected_metrics)

    if missing:
        return ReadinessCheck(
            name="Monitoring Coverage",
            category="Observability",
            check_fn=check_monitoring_coverage,
            status=ReadinessStatus.FAIL,
            message=f"Missing monitoring for: {missing}",
            details={"collected": collected_metrics, "missing": list(missing)}
        )

    return ReadinessCheck(
        name="Monitoring Coverage",
        category="Observability",
        check_fn=check_monitoring_coverage,
        status=ReadinessStatus.PASS,
        message="All critical metrics are being collected",
        details={"metrics": collected_metrics}
    )


async def check_alert_thresholds() -> ReadinessCheck:
    """Verify alerts are configured with appropriate thresholds"""
    await asyncio.sleep(0.1)

    # Check if alert thresholds are set appropriately for launch
    # Too sensitive = alert fatigue; too lenient = missed incidents
    alerts_configured = {
        "high_error_rate": {"threshold": 5, "period": "5m"},  # 5% error rate
        "high_latency_p99": {"threshold": 2000, "period": "5m"},  # 2s
        "database_connection_pool": {"threshold": 80, "period": "2m"},  # 80% utilized
    }

    return ReadinessCheck(
        name="Alert Thresholds",
        category="Observability",
        check_fn=check_alert_thresholds,
        status=ReadinessStatus.PASS,
        message="Alert thresholds configured for launch traffic",
        details={"alerts": alerts_configured}
    )


async def check_logging_coverage() -> ReadinessCheck:
    """Verify logging is configured appropriately for production"""
    await asyncio.sleep(0.1)

    # Check logging levels and output
    logging_config = {
        "level": "INFO",
        "structured": True,
        "sampling": False,
        "integrations": ["datadog", "cloudwatch"],
    }

    # Validate critical integrations
    if len(logging_config["integrations"]) == 0:
        return ReadinessCheck(
            name="Logging Coverage",
            category="Observability",
            check_fn=check_logging_coverage,
            status=ReadinessStatus.FAIL,
            message="No logging integrations configured",
            details=logging_config
        )

    return ReadinessCheck(
        name="Logging Coverage",
        category="Observability",
        check_fn=check_logging_coverage,
        status=ReadinessStatus.PASS,
        message="Logging properly configured with integrations",
        details=logging_config
    )


# ============================================================
# PROCESS CHECKS
# ============================================================

async def check_rollback_procedure() -> ReadinessCheck:
    """Verify rollback procedure is documented and tested"""
    await asyncio.sleep(0.1)

    # Check if rollback is documented and can be executed
    rollback_checks = {
        "documented": True,
        "tested": True,
        "automated": True,
        "estimated_time_minutes": 5,
    }

    if not rollback_checks["tested"]:
        return ReadinessCheck(
            name="Rollback Procedure",
            category="Process",
            check_fn=check_rollback_procedure,
            status=ReadinessStatus.FAIL,
            message="Rollback procedure has NOT been tested",
            details=rollback_checks
        )

    if rollback_checks["estimated_time_minutes"] > 15:
        return ReadinessCheck(
            name="Rollback Procedure",
            category="Process",
            check_fn=check_rollback_procedure,
            status=ReadinessStatus.WARNING,
            message=f"Rollback takes {rollback_checks['estimated_time_minutes']} minutes - consider automation",
            details=rollback_checks
        )

    return ReadinessCheck(
        name="Rollback Procedure",
        category="Process",
        check_fn=check_rollback_procedure,
        status=ReadinessStatus.PASS,
        message="Rollback procedure tested and ready",
        details=rollback_checks
    )


async def check_load_test_results() -> ReadinessCheck:
    """Verify load testing has been performed and results analyzed"""
    await asyncio.sleep(0.1)

    # Load test should have been performed with realistic traffic
    load_test_results = {
        "performed": True,
        "peak_rps_tested": 1000,
        "peak_rps_achieved": 1000,
        "p99_latency_ms": 150,
        "error_rate_percent": 0.1,
        "bottlenecks_found": ["database_connection_pool"],
    }

    if not load_test_results["performed"]:
        return ReadinessCheck(
            name="Load Testing",
            category="Process",
            check_fn=check_load_test_results,
            status=ReadinessStatus.FAIL,
            message="No load testing has been performed!",
            details=load_test_results
        )

    if load_test_results["p99_latency_ms"] > 500:
        return ReadinessCheck(
            name="Load Testing",
            category="Process",
            check_fn=check_load_test_results,
            status=ReadinessStatus.WARNING,
            message=f"High P99 latency ({load_test_results['p99_latency_ms']}ms) under load",
            details=load_test_results
        )

    return ReadinessCheck(
        name="Load Testing",
        category="Process",
        check_fn=check_load_test_results,
        status=ReadinessStatus.PASS,
        message="Load testing passed with acceptable metrics",
        details=load_test_results
    )


async def check_incident_response_plan() -> ReadinessCheck:
    """Verify incident response plan is documented"""
    await asyncio.sleep(0.1)

    incident_plan = {
        "escalation_contacts": True,
        "communication_template": True,
        "runbooks_available": True,
        "war_room_protocol": True,
    }

    missing = [k for k, v in incident_plan.items() if not v]

    if missing:
        return ReadinessCheck(
            name="Incident Response Plan",
            category="Process",
            check_fn=check_incident_response_plan,
            status=ReadinessStatus.WARNING,
            message=f"Missing incident response components: {missing}",
            details=incident_plan
        )

    return ReadinessCheck(
        name="Incident Response Plan",
        category="Process",
        check_fn=check_incident_response_plan,
        status=ReadinessStatus.PASS,
        message="Incident response plan fully documented",
        details=incident_plan
    )


# ============================================================
# SECURITY CHECKS
# ============================================================

async def check_security_scan_results() -> ReadinessCheck:
    """Verify security scanning has been performed"""
    await asyncio.sleep(0.1)

    security_results = {
        "dependency_scan": "passed",
        "static_analysis": "passed",
        "dynamic_scan": "warnings",
        "pen_test": "not_completed",
    }

    if security_results["pen_test"] == "not_completed":
        return ReadinessCheck(
            name="Security Scanning",
            category="Security",
            check_fn=check_security_scan_results,
            status=ReadinessStatus.WARNING,
            message="Penetration testing not completed",
            details=security_results
        )

    return ReadinessCheck(
        name="Security Scanning",
        category="Security",
        check_fn=check_security_scan_results,
        status=ReadinessStatus.PASS,
        message="Security scans completed",
        details=security_results
    )


# ============================================================
# RUN ALL CHECKS
# ============================================================

async def run_all_checks() -> List[ReadinessCheck]:
    """Run all launch readiness checks"""

    checks = [
        # Infrastructure
        check_connection_pool_size(),
        check_circuit_breakers(),
        check_timeouts(),
        check_database_indexes(),
        # Observability
        check_monitoring_coverage(),
        check_alert_thresholds(),
        check_logging_coverage(),
        # Process
        check_rollback_procedure(),
        check_load_test_results(),
        check_incident_response_plan(),
        # Security
        check_security_scan_results(),
    ]

    results = await asyncio.gather(*checks)
    return results


def print_results(checks: List[ReadinessCheck]):
    """Print formatted results"""

    print("\n" + "=" * 60)
    print("LAUNCH READINESS ASSESSMENT")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 60 + "\n")

    # Group by category
    by_category = {}
    for check in checks:
        if check.category not in by_category:
            by_category[check.category] = []
        by_category[check.category].append(check)

    for category, category_checks in by_category.items():
        print(f"\n## {category}")
        print("-" * 40)

        for check in category_checks:
            status_icon = {
                ReadinessStatus.PASS: "[PASS]",
                ReadinessStatus.FAIL: "[FAIL]",
                ReadinessStatus.WARNING: "[WARN]",
                ReadinessStatus.NOT_TESTED: "[N/A]",
            }[check.status]

            print(f"  {status_icon} {check.name}: {check.message}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    status_counts = {}
    for check in checks:
        status_counts[check.status] = status_counts.get(check.status, 0) + 1

    for status, count in sorted(status_counts.items(), key=lambda x: x[0].value):
        print(f"  {status.value}: {count}")

    # Launch decision
    failed = status_counts.get(ReadinessStatus.FAIL, 0)
    warnings = status_counts.get(ReadinessStatus.WARNING, 0)

    print("\n" + "-" * 40)
    if failed > 0:
        print(f"[FAIL] LAUNCH NOT READY: {failed} critical issues must be resolved")
    elif warnings > 0:
        print(f"[WARN] LAUNCH WITH CAUTION: {warnings} warnings to address")
    else:
        print("[PASS] LAUNCH READY: All checks passed")


def export_json(checks: List[ReadinessCheck], filename: str = "launch_readiness.json"):
    """Export results to JSON for CI/CD integration"""

    results = {
        "timestamp": datetime.now().isoformat(),
        "checks": [
            {
                "name": c.name,
                "category": c.category,
                "status": c.status.value,
                "message": c.message,
                "details": c.details,
            }
            for c in checks
        ],
        "summary": {
            "total": len(checks),
            "passed": sum(1 for c in checks if c.status == ReadinessStatus.PASS),
            "failed": sum(1 for c in checks if c.status == ReadinessStatus.FAIL),
            "warnings": sum(1 for c in checks if c.status == ReadinessStatus.WARNING),
        }
    }

    with open(filename, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n[JSON] Results exported to {filename}")


async def main():
    """Main entry point"""
    print("Starting Launch Readiness Assessment...")
    start_time = time.time()

    results = await run_all_checks()
    print_results(results)

    # Export to JSON
    export_json(results)

    elapsed = time.time() - start_time
    print(f"\n[TIME] Assessment completed in {elapsed:.2f}s")


if __name__ == "__main__":
    asyncio.run(main())
