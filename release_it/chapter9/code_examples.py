"""
Code Examples - Chapter 9: Control Plane
This file contains annotated code examples for the chapter.
"""

# ============================================================
# GO CODE EXAMPLE: Service Registry with Health Checks
# ============================================================

go_code = '''
package main

import (
	"context"
	"fmt"
	"sync"
	"time"
)

// ============================================================
// NAIVE APPROACH: What most developers do
// Simple in-memory registry without health checks
// ============================================================

type NaiveServiceRegistry struct {
	// staff-level: No thread safety, no health checks, no TTL
	services map[string][]string
}

func NewNaiveServiceRegistry() *NaiveServiceRegistry {
	return &NaiveServiceRegistry{
		services: make(map[string][]string),
	}
}

func (r *NaiveServiceRegistry) Register(serviceName, address string) {
	// Problem 1: No validation - empty addresses accepted
	// Problem 2: No deduplication - same instance registered twice
	// Problem 3: No thread safety - race conditions
	r.services[serviceName] = append(r.services[serviceName], address)
}

func (r *NaiveServiceRegistry) Discover(serviceName string) []string {
	// Problem: Returns ALL registered instances, healthy or not
	// A crashed instance will still receive traffic
	return r.services[serviceName]
}

// ============================================================
// PRODUCTION APPROACH: What this chapter teaches
// Thread-safe registry with health checks and TTL
// ============================================================

type ServiceInstance struct {
	ID        string
	Address  string
	Port     int
	Metadata map[string]string
	Status   InstanceStatus
	LastSeen time.Time
}

type InstanceStatus int

const (
	StatusUnknown InstanceStatus = iota
	StatusHealthy
	StatusUnhealthy
	StatusRemoved
)

type ServiceRegistry struct {
	mu        sync.RWMutex
	instances map[string]map[string]*ServiceInstance // serviceName -> instanceID -> instance

	// staff-level: Health check configuration
	healthCheckInterval time.Duration
	heartbeatTimeout   time.Duration
	// staff-level: Callbacks for lifecycle events
	onHealthy   func(*ServiceInstance)
	onUnhealthy func(*ServiceInstance)
	onRemoved   func(*ServiceInstance)
}

// NewServiceRegistry creates a production-grade registry
// Why: Provides thread safety, health checking, TTL, and lifecycle callbacks
func NewServiceRegistry(opts ...RegistryOption) *ServiceRegistry {
	registry := &ServiceRegistry{
		instances:           make(map[string]map[string]*ServiceInstance),
		healthCheckInterval: 10 * time.Second,
		heartbeatTimeout:    30 * time.Second,
	}

	for _, opt := range opts {
		opt(registry)
	}

	return registry
}

type RegistryOption func(*RegistryOption) error

func WithHealthCheckInterval(interval time.Duration) RegistryOption {
	return func(r *RegistryOption) error {
		return nil // Simplified for demo
	}
}

// Register adds a new service instance
// Why: Validates input, prevents duplicates, initializes with Unknown status
func (s *ServiceRegistry) Register(ctx context.Context, instance ServiceInstance) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	// Validation: Sanity check inputs
	if instance.ID == "" || instance.Address == "" || instance.Port == 0 {
		return fmt.Errorf("invalid instance: ID, Address, and Port are required")
	}

	// Initialize service map if needed
	if s.instances[instance.ID] == nil {
		s.instances[instance.ID] = make(map[string]*ServiceInstance)
	}

	// Check for duplicate registration
	if existing, ok := s.instances[instance.ID][instance.Address]; ok {
		// Update last seen for existing instance
		existing.LastSeen = time.Now()
		if existing.Status == StatusUnhealthy {
			existing.Status = StatusUnknown // Re-register resets health
			if s.onHealthy != nil {
				s.onHealthy(existing)
			}
		}
		return nil
	}

	// Register new instance
	instance.Status = StatusUnknown
	instance.LastSeen = time.Now()
	s.instances[instance.ID][instance.Address] = &instance

	return nil
}

// Discover returns only healthy instances for a service
// Why: Filters out unhealthy instances, preventing traffic to dead endpoints
func (s *ServiceRegistry) Discover(serviceName string) []*ServiceInstance {
	s.mu.RLock()
	defer s.mu.RUnlock()

	var healthy []*ServiceInstance

	serviceInstances, ok := s.instances[serviceName]
	if !ok {
		return healthy
	}

	for _, instance := range serviceInstances {
		if instance.Status == StatusHealthy {
			healthy = append(healthy, instance)
		}
	}

	return healthy
}

// Heartbeat updates the last seen time for an instance
// Why: Instances must heartbeat to prove they're alive
func (s *ServiceRegistry) Heartbeat(serviceName, address string) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	serviceInstances, ok := s.instances[serviceName]
	if !ok {
		return fmt.Errorf("service %s not found", serviceName)
	}

	instance, ok := serviceInstances[address]
	if !ok {
		return fmt.Errorf("instance %s not found for service %s", address, serviceName)
	}

	instance.LastSeen = time.Now()
	if instance.Status == StatusUnhealthy {
		instance.Status = StatusHealthy
		if s.onHealthy != nil {
			s.onHealthy(instance)
		}
	}

	return nil
}

// StartHealthChecker runs background health verification
// Why: Detects failed instances even if they don't heartbeat
func (s *ServiceRegistry) StartHealthChecker(ctx context.Context) {
	ticker := time.NewTicker(s.healthCheckInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			s.checkInstanceHealth()
		}
	}
}

func (s *ServiceRegistry) checkInstanceHealth() {
	s.mu.Lock()
	defer s.mu.Unlock()

	now := time.Now()
	for _, instances := range s.instances {
		for id, instance := range instances {
			// Check if instance has timed out
			if now.Sub(instance.LastSeen) > s.heartbeatTimeout {
				if instance.Status != StatusUnhealthy {
					instance.Status = StatusUnhealthy
					if s.onUnhealthy != nil {
						s.onUnhealthy(instance)
					}
				}
			}
		}
	}
}

// Deregister removes an instance from the registry
// Why: Clean shutdown is critical - instances must explicitly deregister
func (s *ServiceRegistry) Deregister(serviceName, address string) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	serviceInstances, ok := s.instances[serviceName]
	if !ok {
		return fmt.Errorf("service %s not found", serviceName)
	}

	instance, ok := serviceInstances[address]
	if !ok {
		return fmt.Errorf("instance %s not found", address)
	}

	instance.Status = StatusRemoved
	delete(serviceInstances, address)

	if s.onRemoved != nil {
		s.onRemoved(instance)
	}

	return nil
}

func main() {
	fmt.Println("=== Naive Registry ===")
	naive := NewNaiveServiceRegistry()
	naive.Register("user-service", "10.0.0.1:8080")
	naive.Register("user-service", "10.0.0.2:8080") // Won't receive traffic if crashed!
	instances := naive.Discover("user-service")
	fmt.Printf("Found %d instances (includes crashed ones!)\\n", len(instances))

	fmt.Println("\\n=== Production Registry ===")
	registry := NewServiceRegistry()

	// Register instances
	registry.Register(context.Background(), ServiceInstance{
		ID:       "user-service",
		Address:  "10.0.0.1",
		Port:     8080,
		Metadata: map[string]string{"version": "v1"},
	})

	registry.Register(context.Background(), ServiceInstance{
		ID:       "user-service",
		Address:  "10.0.0.2",
		Port:     8080,
		Metadata: map[string]string{"version": "v1"},
	})

	// Simulate heartbeat
	registry.Heartbeat("user-service", "10.0.0.1")

	// Discover only returns healthy instances
	healthy := registry.Discover("user-service")
	fmt.Printf("Healthy instances: %d\\n", len(healthy))
}
'''

# ============================================================
# PYTHON CODE EXAMPLE: Feature Flags
# ============================================================

python_code = '''
"""
Feature Flag System - Production Implementation
"""

import time
import random
import hashlib
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import threading


class FlagState(Enum):
    """Possible states for a feature flag"""
    OFF = "off"
    ON = "on"
    CONDITIONAL = "conditional"
    ROLLOUT = "rollout"


@dataclass
class FeatureFlag:
    """
    Production-grade feature flag with percentage rollout support.

    staff-level: Why this matters:
    - Enables kill switches for instant rollback
    - Supports gradual rollouts to catch issues early
    - A/B testing support
    - Audit trail for compliance
    """
    name: str
    state: FlagState
    rollout_percentage: float = 0.0  # 0.0 to 100.0
    conditions: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Metrics
    evaluation_count: int = 0
    enabled_count: int = 0

    def should_enable(self, user_id: Optional[str] = None,
                      attributes: Optional[Dict[str, Any]] = None) -> bool:
        """
        Determine if feature should be enabled for a given user/context.

        Why: Deterministic based on user_id ensures consistent experience.
        Using hash ensures same user always gets same treatment.
        """
        self.evaluation_count += 1

        # Check hard states first
        if self.state == FlagState.OFF:
            return False
        if self.state == FlagState.ON:
            self.enabled_count += 1
            return True

        # Check conditions (if any)
        if self.conditions and attributes:
            for key, expected in self.conditions.items():
                if attributes.get(key) != expected:
                    return False

        # Handle rollout percentage
        if self.state == FlagState.ROLLOUT and self.rollout_percentage > 0:
            if user_id is None:
                # No user_id, use random (for anonymous traffic)
                enabled = random.random() * 100 < self.rollout_percentage
            else:
                # Deterministic: hash user_id to get consistent assignment
                hash_value = int(hashlib.md5(
                    f"{self.name}:{user_id}".encode()
                ).hexdigest(), 16)
                enabled = (hash_value % 100) < self.rollout_percentage

            if enabled:
                self.enabled_count += 1
            return enabled

        return False


class FeatureFlagSystem:
    """
    Thread-safe feature flag management system.

    staff-level: Design decisions:
    - In-memory for speed, but can be backed by external store
    - Thread-safe for concurrent evaluation
    - Supports dynamic updates without restart
    - Emits metrics for observability
    """

    def __init__(self):
        self._flags: Dict[str, FeatureFlag] = {}
        self._lock = threading.RLock()
        self._subscribers: list[Callable[[str, bool], None]] = []

    def create_flag(self, name: str, state: FlagState = FlagState.OFF,
                   rollout_percentage: float = 0.0,
                   conditions: Optional[Dict[str, Any]] = None) -> FeatureFlag:
        """Create a new feature flag"""
        with self._lock:
            flag = FeatureFlag(
                name=name,
                state=state,
                rollout_percentage=rollout_percentage,
                conditions=conditions or {}
            )
            self._flags[name] = flag
            return flag

    def get_flag(self, name: str) -> Optional[FeatureFlag]:
        """Get a flag by name"""
        with self._lock:
            return self._flags.get(name)

    def update_flag(self, name: str, **updates) -> bool:
        """Update a flag dynamically - supports kill switches"""
        with self._lock:
            flag = self._flags.get(name)
            if not flag:
                return False

            for key, value in updates.items():
                if hasattr(flag, key):
                    setattr(flag, key, value)

            flag.updated_at = datetime.now()
            return True

    def evaluate(self, flag_name: str,
                 user_id: Optional[str] = None,
                 attributes: Optional[Dict[str, Any]] = None) -> bool:
        """
        Evaluate a feature flag.

        Why: This is the hot path - called on every request for gated features.
        Must be fast (< 1ms) and thread-safe.
        """
        with self._lock:
            flag = self._flags.get(flag_name)
            if not flag:
                return False  # Default to off for unknown flags

        result = flag.should_enable(user_id, attributes)

        # Notify subscribers (for metrics, logging)
        for subscriber in self._subscribers:
            try:
                subscriber(flag_name, result)
            except Exception:
                pass  # Don't let subscriber errors affect flag evaluation

        return result

    def subscribe(self, callback: Callable[[str, bool], None]):
        """Subscribe to flag evaluation events"""
        self._subscribers.append(callback)

    def get_metrics(self, name: str) -> Optional[Dict[str, Any]]:
        """Get flag metrics for monitoring"""
        with self._lock:
            flag = self._flags.get(name)
            if not flag:
                return None

            return {
                "name": flag.name,
                "state": flag.state.value,
                "rollout_percentage": flag.rollout_percentage,
                "evaluation_count": flag.evaluation_count,
                "enabled_count": flag.enabled_count,
                "enable_rate": (flag.enabled_count / flag.evaluation_count * 100)
                              if flag.evaluation_count > 0 else 0
            }


# ============================================================
# NAIVE APPROACH: What most developers do
# Hard-coded feature toggles
# ============================================================

# Problem: Requires code changes to toggle features
# Problem: No gradual rollout capability
# Problem: No metrics on feature usage
# Problem: No kill switch for emergencies

NAIVE_FEATURE_ENABLED = False  # Need to redeploy to change!

def naive_payment_flow(amount: float):
    if NAIVE_FEATURE_ENABLED:
        # New payment flow
        process_payment_v2(amount)
    else:
        # Old payment flow
        process_payment_v1(amount)


# ============================================================
# PRODUCTION APPROACH: What this chapter teaches
# Dynamic feature flags with rollout
# ============================================================

# Initialize feature flags
flags = FeatureFlagSystem()

# Kill switch flag - can be toggled instantly
flags.create_flag(
    name="new-payment-flow",
    state=FlagState.ON  # Enabled for everyone
)

# Gradual rollout flag - starts at 1%, increases as confidence grows
flags.create_flag(
    name="recommendation-algo-v2",
    state=FlagState.ROLLOUT,
    rollout_percentage=10.0  # 10% of users
)

# Conditional flag - based on user attributes
flags.create_flag(
    name="premium-checkout",
    state=FlagState.CONDITIONAL,
    conditions={"plan": "premium"}  # Only for premium users
)


def production_payment_flow(amount: float, user_id: str, user_attributes: dict):
    """
    Production payment flow with feature flags.

    Why this matters:
    - Can disable instantly (kill switch) without deployment
    - Gradual rollout catches issues before 100% of users
    - Metrics show exactly how many users are affected
    """

    # Kill switch: can disable immediately without deployment
    if not flags.evaluate("new-payment-flow", user_id, user_attributes):
        process_payment_v1(amount)
        return

    # New payment flow
    process_payment_v2(amount)


def process_payment_v1(amount: float):
    """Legacy payment processing"""
    print(f"Processing ${amount} via v1 (legacy)")


def process_payment_v2(amount: float):
    """New payment processing with improvements"""
    print(f"Processing ${amount} via v2 (new!)")


# Example usage
if __name__ == "__main__":
    print("=== Naive Approach ===")
    naive_payment_flow(100.0)

    print("\\n=== Production Feature Flags ===")

    # Regular user
    regular_user = {"user_id": "user-123", "attributes": {"plan": "free"}}
    result = flags.evaluate("premium-checkout", **regular_user)
    print(f"Premium checkout for free user: {result}")

    # Premium user
    premium_user = {"user_id": "user-456", "attributes": {"plan": "premium"}}
    result = flags.evaluate("premium-checkout", **premium_user)
    print(f"Premium checkout for premium user: {result}")

    # Gradual rollout - test multiple users
    print("\\n=== Gradual Rollout Test (10%) ===")
    for i in range(20):
        user_id = f"user-{i:03d}"
        enabled = flags.evaluate("recommendation-algo-v2", user_id=user_id)
        print(f"User {user_id}: {'✓ enabled' if enabled else '✗ disabled'}")

    # Get metrics
    print("\\n=== Flag Metrics ===")
    metrics = flags.get_metrics("recommendation-algo-v2")
    print(f"Metrics: {metrics}")

    # Kill switch demo - instant disable
    print("\\n=== Kill Switch Demo ===")
    flags.update_flag("new-payment-flow", state=FlagState.OFF)
    print("Flag disabled via kill switch (no deployment needed!)")
'''

if __name__ == "__main__":
    print("=== Go Code (Service Registry) ===")
    print(go_code)
    print("\n" + "="*60 + "\n")
    print("=== Python Code (Feature Flags) ===")
    print(python_code)
