"""
Exercise 4: Failover — The Hardest Part

DDIA Reference: Chapter 5, "Handling Node Outages" (pp. 156-158)

This exercise simulates the most dangerous scenarios in single-leader replication:
  1. Detecting leader failure (heartbeat timeout)
  2. Choosing the best follower to promote
  3. Reconfiguring the cluster
  4. SPLIT-BRAIN: two leaders accepting conflicting writes
  5. Data loss during failover

Run: python 04_failover.py
"""

import sys
import time
import random
import threading
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum

# Fix Windows terminal encoding for Unicode output
sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# NODE ROLES AND STATES
# =============================================================================

class NodeRole(Enum):
    LEADER = "LEADER"
    FOLLOWER = "FOLLOWER"
    CANDIDATE = "CANDIDATE"  # During election


class NodeState(Enum):
    ALIVE = "ALIVE"
    DEAD = "DEAD"
    PARTITIONED = "PARTITIONED"  # Network partition — alive but unreachable


class ReplicationNode:
    """A node that can be a leader or follower, with failover support."""

    def __init__(self, name: str, role: NodeRole = NodeRole.FOLLOWER):
        self.name = name
        self.role = role
        self.state = NodeState.ALIVE
        self.storage: Dict[int, Dict] = {}
        self.replication_log: List[Dict] = []
        self.replication_position = 0  # LSN
        self.last_heartbeat_time = time.time()
        self.leader_term = 0  # Epoch/term number (for fencing)

    @property
    def is_leader(self) -> bool:
        return self.role == NodeRole.LEADER

    @property
    def is_alive(self) -> bool:
        return self.state == NodeState.ALIVE

    def write(self, data: Dict) -> Optional[Dict]:
        """Accept a write (only if leader and alive)."""
        if not self.is_leader:
            return None
        if not self.is_alive:
            return None

        self.replication_position += 1
        entry = {
            "lsn": self.replication_position,
            "data": data.copy(),
            "term": self.leader_term,
            "timestamp": time.time()
        }
        self.replication_log.append(entry)
        row_id = data.get("id", self.replication_position)
        self.storage[row_id] = data.copy()
        return entry

    def receive_replication(self, entry: Dict) -> bool:
        """Receive a replicated entry from the leader."""
        if not self.is_alive:
            return False

        self.replication_log.append(entry)
        row_id = entry["data"].get("id", entry["lsn"])
        self.storage[row_id] = entry["data"].copy()
        self.replication_position = entry["lsn"]
        return True

    def send_heartbeat(self):
        """Send heartbeat (leader only)."""
        self.last_heartbeat_time = time.time()

    def crash(self):
        """Simulate node crash."""
        self.state = NodeState.DEAD

    def recover(self):
        """Simulate node recovery."""
        self.state = NodeState.ALIVE

    def partition(self):
        """Simulate network partition (alive but unreachable)."""
        self.state = NodeState.PARTITIONED


class SingleLeaderCluster:
    """A single-leader cluster with failover support."""

    def __init__(self, num_nodes: int = 4, heartbeat_timeout_sec: float = 3.0):
        self.nodes: List[ReplicationNode] = []
        self.heartbeat_timeout = heartbeat_timeout_sec
        self.current_term = 0

        # Create leader + followers
        leader = ReplicationNode(f"NODE-1", NodeRole.LEADER)
        leader.leader_term = 1
        self.nodes.append(leader)

        for i in range(1, num_nodes):
            self.nodes.append(ReplicationNode(f"NODE-{i+1}", NodeRole.FOLLOWER))

    @property
    def leader(self) -> Optional[ReplicationNode]:
        leaders = [n for n in self.nodes if n.is_leader and n.is_alive]
        return leaders[0] if leaders else None

    @property
    def followers(self) -> List[ReplicationNode]:
        return [n for n in self.nodes if not n.is_leader]

    @property
    def alive_followers(self) -> List[ReplicationNode]:
        return [n for n in self.nodes if not n.is_leader and n.is_alive]

    def write(self, data: Dict) -> Optional[Dict]:
        """Write to the current leader, replicate to followers."""
        leader = self.leader
        if not leader:
            return None

        entry = leader.write(data)
        if not entry:
            return None

        # Replicate to alive followers with random delay
        for f in self.alive_followers:
            delay = random.uniform(0.001, 0.01)
            time.sleep(delay)
            # Sometimes a follower lags behind
            if random.random() > 0.1:  # 90% chance of receiving
                f.receive_replication(entry)

        return entry


# =============================================================================
# FAILOVER SCENARIOS
# =============================================================================

def print_header(title: str):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_section(title: str):
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")


def print_cluster_state(cluster: SingleLeaderCluster, label: str = ""):
    """Print the current state of all nodes."""
    if label:
        print(f"\n  📊 Cluster State: {label}")
    else:
        print(f"\n  📊 Cluster State:")

    print(f"  {'Node':<10} {'Role':<12} {'State':<14} {'LSN':<8} {'Rows':<8} {'Term'}")
    print(f"  {'─'*60}")
    for node in cluster.nodes:
        role_icon = "👑" if node.is_leader else "📖"
        state_icon = {"ALIVE": "✅", "DEAD": "💀", "PARTITIONED": "🔌"}.get(node.state.value, "?")
        print(f"  {node.name:<10} {role_icon} {node.role.value:<10} "
              f"{state_icon} {node.state.value:<12} "
              f"LSN={node.replication_position:<5} "
              f"{len(node.storage):<8} T={node.leader_term}")


def demo_1_detect_leader_failure():
    """
    Demo 1: How to detect that the leader is dead.

    DDIA: "There is no foolproof way of detecting what has gone wrong...
    Most systems simply use a timeout."
    """
    print_header("1️⃣  DETECTING LEADER FAILURE")
    print("""
    The HARDEST problem: How do you know the leader is dead?

    You CANNOT distinguish between:
    (A) Leader crashed → truly dead
    (B) Network is slow → alive but unreachable
    (C) Leader is overloaded → alive but slow to respond

    The only tool: HEARTBEAT TIMEOUT
    """)

    cluster = SingleLeaderCluster(num_nodes=4, heartbeat_timeout_sec=3.0)

    # Write some initial data
    for i in range(5):
        cluster.write({"id": i, "name": f"User_{i}"})

    print_cluster_state(cluster, "Before failure")

    # Simulate leader sending heartbeats
    print(f"\n  💓 Leader sends heartbeats every 1 second...")
    print(f"  ⏱️  Heartbeat timeout: {cluster.heartbeat_timeout}s")

    # Leader crashes
    print(f"\n  💀 LEADER CRASHES at T=0!")
    cluster.nodes[0].crash()

    # Simulate follower waiting for heartbeat
    timeouts = [2.5, 3.0, 3.5]  # Different followers detect at slightly different times
    for i, follower in enumerate(cluster.followers):
        timeout = timeouts[i] if i < len(timeouts) else 3.0
        print(f"  ⏱️  T={timeout}s: {follower.name} — no heartbeat for {timeout}s!")
        if timeout >= cluster.heartbeat_timeout:
            print(f"        → 🚨 {follower.name} declares: 'LEADER IS DEAD!'")
        else:
            print(f"        → ⏳ {follower.name}: 'Still waiting...'")

    print("""
  💡 KEY INSIGHT (DDIA):
     • Timeout too SHORT → false alarms, unnecessary failovers
     • Timeout too LONG → long downtime when leader truly dies
     • Production setting: typically 10-30 seconds

     You CANNOT know for sure if it's dead or just slow!
    """)


def demo_2_choose_and_promote():
    """
    Demo 2: Choosing the best follower to promote.

    DDIA: "The best candidate for leadership is usually the replica
    with the most up-to-date data changes from the old leader."
    """
    print_header("2️⃣  CHOOSING THE NEW LEADER")
    print("""
    When the leader dies, which follower should become the new leader?

    Answer: The one with the MOST UP-TO-DATE replication position.
    (This minimizes data loss from unreplicated writes.)
    """)

    cluster = SingleLeaderCluster(num_nodes=4)

    # Write data — followers will have different lag
    for i in range(10):
        cluster.write({"id": i, "name": f"User_{i}"})

    # Manually set different replication positions to simulate lag
    cluster.nodes[1].replication_position = 10  # Most up-to-date
    cluster.nodes[2].replication_position = 8   # 2 behind
    cluster.nodes[3].replication_position = 6   # 4 behind

    print_cluster_state(cluster, "Before failover")

    # Leader crashes with some unreplicated writes
    print(f"\n  💀 LEADER CRASHES!")
    print(f"     Leader had LSN=10, with 2 more writes pending (LSN=11, 12)")
    cluster.nodes[0].crash()

    # Election process
    print(f"\n  🗳️  ELECTION PROCESS:")
    print(f"  {'─'*50}")

    candidates = sorted(cluster.alive_followers,
                        key=lambda n: n.replication_position, reverse=True)

    for i, c in enumerate(candidates):
        if i == 0:
            print(f"  👑 {c.name}: LSN={c.replication_position} ← WINNER (most up-to-date)")
        else:
            gap = candidates[0].replication_position - c.replication_position
            print(f"     {c.name}: LSN={c.replication_position} ({gap} entries behind)")

    # Promote the best candidate
    new_leader = candidates[0]
    new_leader.role = NodeRole.LEADER
    new_leader.leader_term += 1

    print(f"\n  ✅ {new_leader.name} promoted to LEADER (term={new_leader.leader_term})")

    # Data loss assessment
    leader_lsn = 10
    new_leader_lsn = new_leader.replication_position
    lost_writes = leader_lsn - new_leader_lsn

    print(f"\n  📊 Data Loss Assessment:")
    print(f"     Old leader last LSN: {leader_lsn}")
    print(f"     New leader LSN:      {new_leader_lsn}")
    print(f"     Unreplicated writes: {lost_writes}")
    if lost_writes > 0:
        print(f"     ⚠️  {lost_writes} writes are PERMANENTLY LOST!")
        print(f"     These writes were acknowledged to clients but never reached followers.")
    else:
        print(f"     ✅ No data loss!")

    print_cluster_state(cluster, "After failover")

    print("""
  💡 KEY INSIGHT (DDIA):
     Data loss during failover is the fundamental price of async replication.
     The writes existed only on the dead leader.

     Real-world solutions:
     • Accept data loss (most common — simpler)
     • Use sync/semi-sync replication (prevents loss, adds latency)
     • Write to durable storage first (complicates architecture)
    """)


def demo_3_split_brain():
    """
    Demo 3: SPLIT-BRAIN — the most dangerous scenario.

    DDIA: "In certain fault scenarios... it could happen that two nodes
    both believe that they are the leader. This situation is called
    split brain, and it is dangerous."
    """
    print_header("3️⃣  SPLIT-BRAIN DISASTER 🧠💥")
    print("""
    THE SCARIEST SCENARIO in distributed systems!

    A network partition makes followers THINK the leader is dead.
    They promote a new leader.
    But the old leader is STILL ALIVE on the other side of the partition.
    Now TWO leaders accept writes → CONFLICTING DATA.
    """)

    # Create cluster
    cluster = SingleLeaderCluster(num_nodes=4)

    # Write initial data
    for i in range(5):
        cluster.write({"id": i, "name": f"User_{i}"})

    print_cluster_state(cluster, "Before network partition")

    # Network partition!
    print(f"\n  🔌 NETWORK PARTITION!")
    print(f"""
  ╔═══════════════════════════════╦═══════════════════════════════╗
  ║  PARTITION A                  ║  PARTITION B                  ║
  ║                               ║                               ║
  ║  NODE-1 (OLD LEADER)          ║  NODE-2 (promoted to leader)  ║
  ║  Still thinks it's leader!    ║  NODE-3 (follower)            ║
  ║                               ║  NODE-4 (follower)            ║
  ║  Accepts writes from          ║  Accepts writes from          ║
  ║  Client A                     ║  Client B                     ║
  ╚═══════════════════════════════╩═══════════════════════════════╝
    """)

    # Simulate partition — old leader is alive but partitioned
    old_leader = cluster.nodes[0]
    old_leader.partition()  # Can't reach followers, but still accepts writes

    # Followers promote NODE-2 as new leader
    new_leader = cluster.nodes[1]
    new_leader.role = NodeRole.LEADER
    new_leader.leader_term = 2

    print(f"  👑 NODE-2 promoted to leader in Partition B (term=2)")
    print(f"  😈 NODE-1 still thinks it's leader in Partition A (term=1)")

    # BOTH leaders accept writes!
    print(f"\n  ✍️  CONFLICTING WRITES:")
    print(f"  {'─'*50}")

    # Old leader accepts writes
    old_leader.state = NodeState.ALIVE  # Temporarily allow writes
    old_leader_writes = [
        {"id": 100, "name": "Alice-from-PartitionA", "value": "ALICE_A"},
        {"id": 101, "name": "Bob-from-PartitionA", "value": "BOB_A"},
    ]
    for data in old_leader_writes:
        old_leader.write(data)
        print(f"  [OLD LEADER] Write: {data['name']}")

    # New leader accepts writes
    new_leader_writes = [
        {"id": 100, "name": "Alice-from-PartitionB", "value": "ALICE_B"},  # CONFLICT!
        {"id": 102, "name": "Charlie-from-PartitionB", "value": "CHARLIE_B"},
    ]
    for data in new_leader_writes:
        new_leader.write(data)
        print(f"  [NEW LEADER] Write: {data['name']}")

    # Show the conflict
    print(f"\n  ⚠️  CONFLICT DETECTED:")
    print(f"  {'─'*50}")
    print(f"  ID=100 on OLD leader: {old_leader.storage.get(100, {}).get('name', 'N/A')}")
    print(f"  ID=100 on NEW leader: {new_leader.storage.get(100, {}).get('name', 'N/A')}")
    print(f"\n  💥 SAME ID, DIFFERENT DATA! Which is correct?")
    print(f"     Neither — BOTH are 'correct' from each leader's perspective")
    print(f"     THIS IS DATA CORRUPTION!")

    # Network partition heals
    print(f"\n  🔧 PARTITION HEALS — now what?")
    print(f"  {'─'*50}")
    print(f"""
  When the partition heals, you must:
  1. Force one leader to step down (usually the old one)
  2. Decide what to do with conflicting writes
  3. Accept that some data may be lost or corrupted

  Node-1 (old leader) storage: {dict(list(old_leader.storage.items())[-3:])}
  Node-2 (new leader) storage: {dict(list(new_leader.storage.items())[-3:])}
    """)

    print("""
  💡 SOLUTIONS TO SPLIT-BRAIN (DDIA):

  1. STONITH (Shoot The Other Node In The Head):
     Forcibly power off the old leader before promoting a new one.
     Uses hardware (IPMI, cloud API) to guarantee old leader is truly dead.

  2. Fencing Tokens:
     Each leader gets an incrementing token (epoch/term number).
     Storage systems reject writes from old tokens.
     Old leader (term=1) → storage rejects writes.
     New leader (term=2) → storage accepts writes.

  3. Consensus Protocol (Raft, Paxos):
     Requires MAJORITY vote to become leader.
     In a 4-node cluster, need 3 votes.
     Partition A (1 node) → can't get majority → can't be leader!
     Partition B (3 nodes) → gets majority → legitimate leader!
    """)


def demo_4_fencing_tokens():
    """
    Demo 4: Fencing tokens — preventing split-brain writes.

    DDIA: "A system that uses epoch numbers can ensure that writes
    from an old leader are rejected."
    """
    print_header("4️⃣  FENCING TOKENS: Preventing Split-Brain Writes")
    print("""
    Each leader gets an incrementing TERM/EPOCH number.
    Storage rejects writes from leaders with old terms.
    """)

    # Simulate fencing token mechanism
    class FencedStorage:
        """Storage that rejects writes from old leaders (using fencing tokens)."""

        def __init__(self):
            self.data: Dict[int, Dict] = {}
            self.current_term = 0

        def write(self, term: int, row_id: int, data: Dict) -> Tuple[bool, str]:
            if term < self.current_term:
                return False, f"REJECTED: term {term} < current term {self.current_term}"
            self.current_term = max(self.current_term, term)
            self.data[row_id] = data.copy()
            return True, f"ACCEPTED (term={term})"

    storage = FencedStorage()

    print("  Scenario: Split-brain with fencing tokens\n")

    # Old leader (term=1) writes successfully at first
    success, msg = storage.write(1, 100, {"name": "Alice-v1"})
    print(f"  Old leader (term=1) writes id=100: {msg} {'✅' if success else '❌'}")

    # New leader (term=2) is elected
    print(f"\n  🗳️  New leader elected with term=2")

    success, msg = storage.write(2, 100, {"name": "Alice-v2"})
    print(f"  New leader (term=2) writes id=100: {msg} {'✅' if success else '❌'}")

    # Old leader tries to write with old term — REJECTED!
    success, msg = storage.write(1, 101, {"name": "Bob-from-old-leader"})
    print(f"  Old leader (term=1) writes id=101: {msg} {'✅' if success else '❌'}")

    print(f"\n  Storage state: {storage.data}")
    print(f"  Current term: {storage.current_term}")

    print("""
  💡 KEY INSIGHT:
     Fencing tokens ensure that even if split-brain occurs,
     the old leader's writes are REJECTED by storage.

     The storage acts as the ultimate arbiter of who is the "real" leader.
     No conflicting data can be written!

     Real-world implementations:
     • ZooKeeper: session IDs as fencing tokens
     • etcd: revision numbers
     • Raft: term numbers
    """)


def demo_5_full_failover():
    """Demo 5: Complete failover simulation end-to-end."""
    print_header("5️⃣  COMPLETE FAILOVER SIMULATION")
    print("""
    Watch a complete failover unfold step by step:
    Leader crash → Detection → Election → Promotion → Recovery
    """)

    cluster = SingleLeaderCluster(num_nodes=4, heartbeat_timeout_sec=3.0)

    # Phase 1: Normal operation
    print_section("Phase 1: Normal Operation")
    for i in range(8):
        cluster.write({"id": i, "name": f"User_{i}", "status": "active"})
    print(f"  ✅ 8 writes completed successfully")
    print_cluster_state(cluster, "Normal operation")

    # Phase 2: Leader starts struggling
    print_section("Phase 2: Leader Struggles")
    print("  ⚠️  Leader is under heavy load...")
    print("  ⚠️  Replication to followers slowing down...")

    # Simulate followers lagging
    cluster.nodes[1].replication_position = 8  # Up to date
    cluster.nodes[2].replication_position = 7  # 1 behind
    cluster.nodes[3].replication_position = 5  # 3 behind
    print_cluster_state(cluster, "Followers lagging")

    # Phase 3: Leader crashes
    print_section("Phase 3: 💀 LEADER CRASHES!")
    old_leader = cluster.nodes[0]

    # Leader had 2 more unreplicated writes
    old_leader.write({"id": 8, "name": "UNREPLICATED_1"})
    old_leader.write({"id": 9, "name": "UNREPLICATED_2"})
    print(f"  Leader had 2 unreplicated writes (LSN=9, 10)")
    print(f"  Leader LSN: {old_leader.replication_position}")

    old_leader.crash()
    print(f"  💀 Leader is DEAD!")
    print_cluster_state(cluster, "After crash")

    # Phase 4: Detection
    print_section("Phase 4: ⏱️ Detecting Failure")
    print(f"  Heartbeat timeout: {cluster.heartbeat_timeout}s")
    print(f"  T=0.0s: Last heartbeat received")
    print(f"  T=1.0s: No heartbeat... waiting")
    print(f"  T=2.0s: No heartbeat... still waiting")
    print(f"  T=3.0s: TIMEOUT! Followers declare leader dead")

    # Phase 5: Election
    print_section("Phase 5: 🗳️ Leader Election")
    candidates = sorted(
        [n for n in cluster.nodes if n.is_alive and not n.is_leader],
        key=lambda n: n.replication_position,
        reverse=True
    )

    print(f"  Candidates (sorted by replication position):")
    for i, c in enumerate(candidates):
        marker = " ← WINNER" if i == 0 else ""
        print(f"    {c.name}: LSN={c.replication_position}{marker}")

    # Phase 6: Promotion
    print_section("Phase 6: 👑 Promotion")
    new_leader = candidates[0]
    new_leader.role = NodeRole.LEADER
    new_leader.leader_term = 2

    # Reconfigure other followers
    for f in candidates[1:]:
        print(f"  {f.name}: Reconfigured to follow {new_leader.name}")

    print(f"\n  ✅ {new_leader.name} is the NEW LEADER (term=2)")

    # Phase 7: Data loss assessment
    print_section("Phase 7: 📊 Data Loss Assessment")
    lost = old_leader.replication_position - new_leader.replication_position
    print(f"  Old leader LSN: {old_leader.replication_position}")
    print(f"  New leader LSN: {new_leader.replication_position}")
    if lost > 0:
        print(f"  ⚠️  LOST WRITES: {lost} entries")
        print(f"  These writes were ACKed to clients but never replicated!")
    else:
        print(f"  ✅ No data loss")

    # Phase 8: Old leader comes back
    print_section("Phase 8: 🔄 Old Leader Recovers")
    old_leader.recover()
    old_leader.role = NodeRole.FOLLOWER  # Demoted!
    print(f"  {old_leader.name} comes back online")
    print(f"  {old_leader.name} demoted to FOLLOWER")
    print(f"  {old_leader.name} must discard unreplicated writes and catch up")
    print(f"  {old_leader.name} syncs from {new_leader.name}")

    print_cluster_state(cluster, "After recovery")

    print("""
  💡 COMPLETE FAILOVER TIMELINE:
     T=0.0s: Leader crashes
     T=3.0s: Followers detect failure (heartbeat timeout)
     T=3.1s: Election starts
     T=3.2s: Best follower promoted
     T=3.5s: Other followers reconfigured
     T=???:  Old leader recovers, demoted to follower

     Total downtime: ~3-5 seconds (automated)
     vs. manual failover: minutes to hours!

     Real-world tools:
     • PostgreSQL: Patroni (uses etcd for consensus)
     • MySQL: MySQL Group Replication, Orchestrator
     • MongoDB: Built-in replica set elections
     • Redis: Sentinel
    """)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("  EXERCISE 4: FAILOVER — THE HARDEST PART")
    print("  DDIA Chapter 5: 'Handling Node Outages'")
    print("=" * 80)
    print("""
  This is where single-leader replication gets SCARY.
  What happens when the leader dies? Split-brain? Data loss?
    """)

    demo_1_detect_leader_failure()
    demo_2_choose_and_promote()
    demo_3_split_brain()
    demo_4_fencing_tokens()
    demo_5_full_failover()

    print("\n" + "=" * 80)
    print("  EXERCISE 4 COMPLETE ✅")
    print("=" * 80)
    print("""
  Key Takeaways:

  1. ⏱️  Detection: Heartbeat timeout is imperfect (can't tell dead vs slow)
  2. 🗳️  Election: Promote follower with most recent data (minimize loss)
  3. 🧠 Split-brain: TWO leaders = DATA CORRUPTION (the worst scenario)
  4. 🔒 Fencing tokens: Reject writes from old leaders
  5. 💀 Data loss: Unreplicated async writes are PERMANENTLY LOST

  This is why DDIA says failover is "fraught with things that can go wrong"!

  Next: Run 05_replication_lag.py to see the user-facing consistency problems
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
