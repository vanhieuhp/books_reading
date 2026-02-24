"""
Exercise 4b: Request Routing with ZooKeeper (Centralized Coordination)

DDIA Reference: Chapter 6, "ZooKeeper and Friends" (pp. 531-568)

This exercise simulates centralized routing coordination using ZooKeeper.

Key concepts:
  - ZooKeeper: A coordination service that tracks partition assignments
  - Nodes register their partition ownership in ZooKeeper
  - Routing tier subscribes to changes (watches)
  - When partitions move, ZooKeeper notifies all subscribers
  - Immediate consistency (vs. gossip's eventual consistency)

Run: python 02_zookeeper_coordination.py
"""

import sys
import time
import random
from typing import Dict, List, Optional, Set, Callable
from dataclasses import dataclass, field
from enum import Enum

# Fix Windows terminal encoding for Unicode output
sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# CORE COMPONENTS: ZooKeeper, Watch, PartitionRegistry
# =============================================================================

class WatchEvent(Enum):
    """Types of events that can trigger a watch."""
    PARTITION_ASSIGNED = "partition_assigned"
    PARTITION_MOVED = "partition_moved"
    NODE_JOINED = "node_joined"
    NODE_LEFT = "node_left"


@dataclass
class PartitionRegistration:
    """A node's registration of partition ownership in ZooKeeper."""
    node_id: str
    partition_id: int
    timestamp: float = field(default_factory=time.time)

    def __repr__(self):
        return f"{self.node_id}:Partition-{self.partition_id}"


class Watch:
    """
    A watch: a callback that fires when something changes in ZooKeeper.

    DDIA: "The routing tier subscribes to ZooKeeper for changes ('watches').
    When a partition moves from Node A to Node B, ZooKeeper notifies all
    subscribers instantly."
    """

    def __init__(self, watcher_id: str, callback: Callable):
        self.watcher_id = watcher_id
        self.callback = callback
        self.triggered_count = 0

    def trigger(self, event: WatchEvent, data: Dict):
        """Fire the watch callback."""
        self.triggered_count += 1
        self.callback(event, data)


class ZooKeeper:
    """
    A simplified ZooKeeper implementation.

    DDIA: "Many systems use a coordination service like ZooKeeper, etcd,
    or Consul to solve this: Each database node registers itself in
    ZooKeeper, announcing which partitions it owns."
    """

    def __init__(self):
        # Partition registrations: partition_id -> node_id
        self.registrations: Dict[int, str] = {}

        # Watches: who is watching for changes
        self.watches: Dict[str, List[Watch]] = {}

        # Version counter (for consistency)
        self.version = 0

    def register_partition(self, node_id: str, partition_id: int):
        """
        A node registers ownership of a partition.

        This is called when:
        - A node starts up and claims its partitions
        - A partition is rebalanced to this node
        """
        old_owner = self.registrations.get(partition_id)
        self.registrations[partition_id] = node_id
        self.version += 1

        # Notify all watchers
        if partition_id in self.watches:
            event = WatchEvent.PARTITION_MOVED if old_owner else WatchEvent.PARTITION_ASSIGNED
            for watch in self.watches[partition_id]:
                watch.trigger(event, {
                    "partition_id": partition_id,
                    "old_owner": old_owner,
                    "new_owner": node_id,
                    "version": self.version
                })

    def unregister_partition(self, node_id: str, partition_id: int):
        """A node releases ownership of a partition."""
        if self.registrations.get(partition_id) == node_id:
            del self.registrations[partition_id]
            self.version += 1

    def get_partition_owner(self, partition_id: int) -> Optional[str]:
        """Look up which node owns a partition."""
        return self.registrations.get(partition_id)

    def get_all_partitions(self) -> Dict[int, str]:
        """Get the complete partition map."""
        return self.registrations.copy()

    def watch_partition(self, partition_id: int, watcher_id: str, callback: Callable) -> Watch:
        """
        Subscribe to changes for a specific partition.

        DDIA: "The routing tier subscribes to ZooKeeper for changes."
        """
        if partition_id not in self.watches:
            self.watches[partition_id] = []

        watch = Watch(watcher_id, callback)
        self.watches[partition_id].append(watch)
        return watch

    def watch_all_partitions(self, watcher_id: str, callback: Callable) -> List[Watch]:
        """Subscribe to changes for all partitions."""
        watches = []
        for partition_id in range(12):  # Assume 12 partitions
            watch = self.watch_partition(partition_id, watcher_id, callback)
            watches.append(watch)
        return watches

    def __repr__(self):
        lines = [f"ZooKeeper (v{self.version}):"]
        for partition_id in sorted(self.registrations.keys()):
            node_id = self.registrations[partition_id]
            lines.append(f"  Partition {partition_id:2d} → {node_id}")
        return "\n".join(lines)


class RoutingTier:
    """
    A routing tier that uses ZooKeeper for partition discovery.

    DDIA: "A dedicated routing layer sits between clients and the database.
    It maintains a complete mapping of partitions to nodes."
    """

    def __init__(self, tier_id: str, zookeeper: ZooKeeper):
        self.tier_id = tier_id
        self.zookeeper = zookeeper

        # Local cache of partition map
        self.partition_map: Dict[int, str] = {}

        # Watches for all partitions
        self.watches: List[Watch] = []

        # Statistics
        self.requests_routed = 0
        self.updates_received = 0

    def initialize(self):
        """
        Initialize the routing tier by:
        1. Loading the current partition map from ZooKeeper
        2. Subscribing to all changes
        """
        # Load current state
        self.partition_map = self.zookeeper.get_all_partitions()

        # Subscribe to changes
        def on_partition_change(event: WatchEvent, data: Dict):
            self.updates_received += 1
            partition_id = data["partition_id"]
            new_owner = data["new_owner"]
            self.partition_map[partition_id] = new_owner

        self.watches = self.zookeeper.watch_all_partitions(self.tier_id, on_partition_change)

    def route_request(self, partition_id: int) -> Optional[str]:
        """
        Route a request to the correct node.

        DDIA: "Clients talk only to the router; the router forwards to
        the correct node."
        """
        self.requests_routed += 1
        return self.partition_map.get(partition_id)

    def __repr__(self):
        return f"RoutingTier({self.tier_id}, routed={self.requests_routed}, updates={self.updates_received})"


class DatabaseNode:
    """
    A database node that registers with ZooKeeper.

    DDIA: "Each database node registers itself in ZooKeeper, announcing
    which partitions it owns."
    """

    def __init__(self, node_id: str, zookeeper: ZooKeeper):
        self.node_id = node_id
        self.zookeeper = zookeeper
        self.owned_partitions: Set[int] = set()

    def claim_partition(self, partition_id: int):
        """Claim ownership of a partition."""
        self.owned_partitions.add(partition_id)
        self.zookeeper.register_partition(self.node_id, partition_id)

    def release_partition(self, partition_id: int):
        """Release ownership of a partition."""
        self.owned_partitions.discard(partition_id)
        self.zookeeper.unregister_partition(self.node_id, partition_id)

    def __repr__(self):
        return f"Node({self.node_id}, owns={sorted(self.owned_partitions)})"


# =============================================================================
# DEMONSTRATION SCENARIOS
# =============================================================================

def print_header(title: str):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_section(title: str):
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")


def demo_1_zookeeper_basics():
    """
    Demo 1: Basic ZooKeeper operations.

    DDIA concept: "Each database node registers itself in ZooKeeper,
    announcing which partitions it owns."
    """
    print_header("DEMO 1: ZooKeeper Basics")
    print("""
    ZooKeeper is a coordination service. Database nodes register their
    partition ownership, and routing tiers subscribe to changes.
    """)

    zk = ZooKeeper()

    # Nodes register their partitions
    print("  📝 Nodes register partitions with ZooKeeper:\n")

    nodes = [DatabaseNode(f"Node-{i}", zk) for i in range(1, 4)]

    for i, node in enumerate(nodes):
        partitions = list(range(i * 4, (i + 1) * 4))
        for p in partitions:
            node.claim_partition(p)
        print(f"    {node.node_id} claims partitions {partitions}")

    print(f"\n  ✅ ZooKeeper state:")
    print(f"    {zk}")

    # Query the state
    print(f"\n  🔍 Routing queries:")
    for partition_id in [0, 5, 11]:
        owner = zk.get_partition_owner(partition_id)
        print(f"    Partition {partition_id} → {owner}")


def demo_2_watch_mechanism():
    """
    Demo 2: Show how watches notify subscribers of changes.

    DDIA concept: "The routing tier subscribes to ZooKeeper for changes
    ('watches'). When a partition moves, ZooKeeper notifies all subscribers."
    """
    print_header("DEMO 2: Watch Mechanism")
    print("""
    A routing tier subscribes to partition changes via watches.
    When a partition is rebalanced, ZooKeeper notifies the routing tier.
    """)

    zk = ZooKeeper()
    nodes = [DatabaseNode(f"Node-{i}", zk) for i in range(1, 4)]

    # Initial setup
    for i, node in enumerate(nodes):
        for p in range(i * 4, (i + 1) * 4):
            node.claim_partition(p)

    # Create routing tier
    routing_tier = RoutingTier("Router-1", zk)
    routing_tier.initialize()

    print(f"  ✅ Routing tier initialized")
    print(f"    Partition map: {routing_tier.partition_map}")

    # Simulate a rebalancing: Partition 0 moves from Node-1 to Node-2
    print(f"\n  🔄 Rebalancing: Partition 0 moves from Node-1 to Node-2")

    nodes[0].release_partition(0)
    nodes[1].claim_partition(0)

    print(f"\n  ✅ Watch triggered! Routing tier updated:")
    print(f"    Partition map: {routing_tier.partition_map}")
    print(f"    Updates received: {routing_tier.updates_received}")


def demo_3_multiple_routing_tiers():
    """
    Demo 3: Multiple routing tiers all stay in sync via ZooKeeper.

    DDIA concept: "Multiple routing tiers can subscribe to the same
    partition changes and stay in sync."
    """
    print_header("DEMO 3: Multiple Routing Tiers")
    print("""
    In a real system, there are multiple routing tiers for redundancy.
    All of them subscribe to ZooKeeper and stay in sync.
    """)

    zk = ZooKeeper()
    nodes = [DatabaseNode(f"Node-{i}", zk) for i in range(1, 4)]

    # Initial setup
    for i, node in enumerate(nodes):
        for p in range(i * 4, (i + 1) * 4):
            node.claim_partition(p)

    # Create multiple routing tiers
    routing_tiers = [RoutingTier(f"Router-{i}", zk) for i in range(1, 4)]
    for tier in routing_tiers:
        tier.initialize()

    print(f"  ✅ {len(routing_tiers)} routing tiers initialized")

    # Simulate rebalancing
    print(f"\n  🔄 Rebalancing: Partition 0 moves from Node-1 to Node-2")
    nodes[0].release_partition(0)
    nodes[1].claim_partition(0)

    print(f"\n  ✅ All routing tiers updated:")
    for tier in routing_tiers:
        owner = tier.partition_map.get(0)
        print(f"    {tier.tier_id}: Partition 0 → {owner}")


def demo_4_client_routing_with_zookeeper():
    """
    Demo 4: Show how clients route requests through the routing tier.

    DDIA concept: "Clients talk only to the router; the router forwards
    to the correct node."
    """
    print_header("DEMO 4: Client Routing with ZooKeeper")
    print("""
    Clients connect to a routing tier, which uses ZooKeeper to find
    the correct node for each partition.
    """)

    zk = ZooKeeper()
    nodes = [DatabaseNode(f"Node-{i}", zk) for i in range(1, 4)]

    # Initial setup
    for i, node in enumerate(nodes):
        for p in range(i * 4, (i + 1) * 4):
            node.claim_partition(p)

    # Create routing tier
    routing_tier = RoutingTier("Router-1", zk)
    routing_tier.initialize()

    # Simulate client requests
    keys = ["user_42", "user_100", "user_7", "post_999", "comment_5"]

    print(f"\n  🔑 Client requests routed through Router-1:")
    for key in keys:
        partition_id = hash(key) % 12
        node_id = routing_tier.route_request(partition_id)
        print(f"    Key '{key}' → Partition {partition_id} → {node_id}")

    print(f"\n  📊 Routing tier stats:")
    print(f"    Requests routed: {routing_tier.requests_routed}")
    print(f"    Updates received: {routing_tier.updates_received}")


def demo_5_zookeeper_vs_gossip():
    """
    Demo 5: Compare ZooKeeper (centralized) vs. Gossip (decentralized).

    DDIA concept: "Cassandra and Riak use gossip protocol (decentralized).
    HBase and MongoDB use ZooKeeper (centralized)."
    """
    print_header("DEMO 5: ZooKeeper vs. Gossip Protocol")
    print("""
    DDIA describes two approaches to keeping routing tables in sync:
    """)

    print("""
    ┌─────────────────────────────────────────────────────────────────┐
    │ ZOOKEEPER (Centralized Coordination)                            │
    ├─────────────────────────────────────────────────────────────────┤
    │                                                                  │
    │  Architecture:                                                   │
    │    Nodes → ZooKeeper ← Routing Tier / Client                    │
    │                                                                  │
    │  How it works:                                                   │
    │    1. Nodes register partition ownership in ZooKeeper           │
    │    2. Routing tier subscribes to changes (watches)              │
    │    3. When partition moves, ZooKeeper notifies subscribers      │
    │    4. Routing tier updates immediately                          │
    │                                                                  │
    │  Consistency:                                                    │
    │    ✅ Strong consistency (all subscribers see change instantly) │
    │                                                                  │
    │  Pros:                                                           │
    │    • Immediate consistency (no stale routing)                    │
    │    • Simple to reason about                                      │
    │    • Centralized source of truth                                 │
    │                                                                  │
    │  Cons:                                                           │
    │    • ZooKeeper is a single point of failure (needs replication) │
    │    • Routing tier is a bottleneck                                │
    │    • Extra network hop through routing tier                      │
    │                                                                  │
    │  Used by: HBase, Kafka, MongoDB (config servers), SolrCloud     │
    └─────────────────────────────────────────────────────────────────┘
    """)

    print("""
    ┌─────────────────────────────────────────────────────────────────┐
    │ GOSSIP PROTOCOL (Decentralized)                                 │
    ├─────────────────────────────────────────────────────────────────┤
    │                                                                  │
    │  Architecture:                                                   │
    │    Node-A ←→ Node-B ←→ Node-C ←→ ... (peer-to-peer)            │
    │                                                                  │
    │  How it works:                                                   │
    │    1. Nodes periodically exchange routing info with peers       │
    │    2. Each node maintains a local routing table                 │
    │    3. Changes propagate gradually through the network           │
    │    4. Eventually all nodes converge on same routing table       │
    │                                                                  │
    │  Consistency:                                                    │
    │    ⏳ Eventual consistency (takes time to propagate)             │
    │                                                                  │
    │  Pros:                                                           │
    │    • Fully decentralized (no single point of failure)            │
    │    • No routing tier bottleneck                                  │
    │    • Scales well (peer-to-peer communication)                    │
    │                                                                  │
    │  Cons:                                                           │
    │    • Eventual consistency (routing may be stale)                 │
    │    • Harder to reason about (distributed state)                  │
    │    • Takes time for changes to propagate                         │
    │                                                                  │
    │  Used by: Cassandra, Riak                                        │
    └─────────────────────────────────────────────────────────────────┘
    """)

    print("""
    ┌─────────────────────────────────────────────────────────────────┐
    │ COMPARISON TABLE                                                │
    ├──────────────────────┬──────────────┬──────────────────────────┤
    │ Aspect               │ ZooKeeper    │ Gossip                   │
    ├──────────────────────┼──────────────┼──────────────────────────┤
    │ Consistency          │ Strong       │ Eventual                 │
    │ Latency              │ Immediate    │ Gradual (O(log N) rounds)│
    │ Centralization       │ Centralized  │ Decentralized            │
    │ Single Point Failure │ Yes (ZK)     │ No                       │
    │ Bottleneck Risk      │ Routing tier │ None                     │
    │ Complexity           │ Moderate     │ High                     │
    │ Scalability          │ Limited      │ Excellent                │
    └──────────────────────┴──────────────┴──────────────────────────┘
    """)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("  EXERCISE 4b: REQUEST ROUTING WITH ZOOKEEPER")
    print("  DDIA Chapter 6: 'ZooKeeper and Friends'")
    print("=" * 80)
    print("""
  This exercise simulates centralized routing coordination using ZooKeeper.

  We'll explore how ZooKeeper keeps routing tables in sync across
  multiple routing tiers and database nodes.
    """)

    demo_1_zookeeper_basics()
    demo_2_watch_mechanism()
    demo_3_multiple_routing_tiers()
    demo_4_client_routing_with_zookeeper()
    demo_5_zookeeper_vs_gossip()

    print("\n" + "=" * 80)
    print("  EXERCISE 4b COMPLETE ✅")
    print("=" * 80)
    print("""
  Key Takeaways:

  1. 🗂️  ZooKeeper: Centralized coordination service for partition tracking
  2. 📝 Registration: Nodes register partition ownership in ZooKeeper
  3. 👁️  Watches: Routing tiers subscribe to changes
  4. ⚡ Immediate Consistency: Changes propagate instantly to all subscribers
  5. 🔄 Comparison:
     • ZooKeeper (centralized) → strong consistency, bottleneck risk
     • Gossip (decentralized) → eventual consistency, no bottleneck
  6. 🏢 Real-world usage:
     • HBase, Kafka, MongoDB use ZooKeeper-like coordination
     • Cassandra, Riak use gossip protocol

  Summary: Chapter 6 covers how distributed databases partition data
  and route requests to the correct node. The choice between centralized
  (ZooKeeper) and decentralized (gossip) routing is a fundamental
  architectural decision with major trade-offs.
    """)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
