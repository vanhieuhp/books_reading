"""
Exercise 5: Replication Lag — Consistency Anomalies

DDIA Reference: Chapter 5, "Problems with Replication Lag" (pp. 161-167)

This exercise demonstrates the THREE user-facing problems caused by
replication lag in async replication:

  1. Reading Your Own Writes — user updates profile, sees old data
  2. Monotonic Reads — data appears, disappears, reappears (time travel!)
  3. Consistent Prefix Reads — answer appears before question (causality broken!)

For each problem, you'll see THE BUG and then THE FIX.

Run: python 05_replication_lag.py
"""

import sys
import time
import random
import hashlib
from typing import Dict, List, Any, Optional, Tuple

# Fix Windows terminal encoding for Unicode output
sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# REPLICATION INFRASTRUCTURE
# =============================================================================

class ReplicaNode:
    """A database replica with configurable lag."""

    def __init__(self, name: str, lag_ms: float = 0):
        self.name = name
        self.base_lag_ms = lag_ms
        self.storage: Dict[str, Dict[int, Dict]] = {}
        self.replication_position = 0
        self._write_log: List[Dict] = []

    def apply_write(self, write: Dict, lag_multiplier: float = 1.0):
        """Apply a write with simulated lag."""
        actual_lag = self.base_lag_ms * lag_multiplier * random.uniform(0.8, 1.2)
        time.sleep(actual_lag / 1000.0)

        table = write.get("table", "default")
        if table not in self.storage:
            self.storage[table] = {}

        row_id = write["data"].get("id")

        if write["operation"] == "INSERT":
            self.storage[table][row_id] = write["data"].copy()
        elif write["operation"] == "UPDATE":
            if row_id in self.storage[table]:
                self.storage[table][row_id].update(write["data"])
            else:
                self.storage[table][row_id] = write["data"].copy()
        elif write["operation"] == "DELETE":
            self.storage[table].pop(row_id, None)

        self.replication_position = write.get("lsn", self.replication_position + 1)
        self._write_log.append(write)

    def read(self, table: str, row_id: int) -> Optional[Dict]:
        return self.storage.get(table, {}).get(row_id)

    def read_all(self, table: str) -> Dict[int, Dict]:
        return self.storage.get(table, {}).copy()


class ReplicatedDatabase:
    """A database with one leader and multiple followers."""

    def __init__(self, num_followers: int = 3, follower_lags: Optional[List[float]] = None):
        self.leader = ReplicaNode("LEADER", lag_ms=0)
        self.followers: List[ReplicaNode] = []
        self._lsn = 0

        if follower_lags is None:
            follower_lags = [random.uniform(50, 200) for _ in range(num_followers)]

        for i, lag in enumerate(follower_lags):
            self.followers.append(ReplicaNode(f"FOLLOWER-{i+1}", lag_ms=lag))

    def write(self, table: str, operation: str, data: Dict) -> Dict:
        """Write to leader, replicate to followers."""
        self._lsn += 1

        write_entry = {
            "lsn": self._lsn,
            "table": table,
            "operation": operation,
            "data": data,
            "timestamp": time.time()
        }

        # Apply to leader immediately
        self.leader.apply_write(write_entry)

        # Replicate to followers (async — with lag)
        for f in self.followers:
            f.apply_write(write_entry)

        return write_entry

    def read_from_leader(self, table: str, row_id: int) -> Optional[Dict]:
        return self.leader.read(table, row_id)

    def read_from_random_follower(self, table: str, row_id: int) -> Tuple[Optional[Dict], str]:
        follower = random.choice(self.followers)
        return follower.read(table, row_id), follower.name

    def read_from_specific_follower(self, follower_index: int,
                                     table: str, row_id: int) -> Tuple[Optional[Dict], str]:
        follower = self.followers[follower_index]
        return follower.read(table, row_id), follower.name


# =============================================================================
# ANOMALY 1: READING YOUR OWN WRITES
# =============================================================================

def print_header(title: str):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_section(title: str):
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")


def demo_1_read_your_writes():
    """
    ANOMALY 1: Reading Your Own Writes

    DDIA: "With asynchronous replication, if the user views the data
    shortly after making a write, the new data may not yet have reached
    the replica."

    Scenario: User updates their profile, refreshes page → sees old data!
    """
    print_header("1️⃣  ANOMALY: Reading Your Own Writes")
    print("""
    Scenario: User updates their profile, then immediately reads it.
    If the read hits a LAGGING follower, they see their OLD data!

    This is confusing: "I just changed my name, why does it show the old one?"
    """)

    # Setup: leader + followers with varying lag
    db = ReplicatedDatabase(num_followers=3, follower_lags=[0, 100, 300])

    # Initial data
    db.write("profiles", "INSERT", {"id": 42, "name": "Alice", "bio": "Hello world"})

    print_section("THE BUG")

    # User updates their profile
    print("\n  📝 Alice updates her bio...")
    db.write("profiles", "UPDATE", {"id": 42, "name": "Alice", "bio": "I love distributed systems!"})

    # User refreshes → hits different followers
    print("  📖 Alice refreshes her profile page...\n")

    print(f"  {'Attempt':<10} {'Read From':<15} {'Bio':<35} {'Status'}")
    print(f"  {'─'*75}")

    for attempt in range(6):
        data, source = db.read_from_random_follower("profiles", 42)
        bio = data.get("bio", "N/A") if data else "N/A"
        is_stale = bio != "I love distributed systems!"
        status = "😡 STALE! Old data!" if is_stale else "✅ Correct"
        bio_display = bio[:30] + "..." if len(bio) > 30 else bio
        print(f"  {attempt+1:<10} {source:<15} {bio_display:<35} {status}")

    print("""
  🐛 Alice sees her OLD bio sometimes because she hit a lagging follower.
     She thinks the update didn't work and tries again. Frustrating!
    """)

    # THE FIX
    print_section("THE FIX: Read-Your-Writes Consistency")

    print("""
  Three strategies to fix this:
    """)

    # Fix 1: Read from leader after user's own writes
    print("  Fix 1: Route user's reads to LEADER after they write")
    print("  " + "─" * 50)

    class ReadYourWritesRouter:
        """Route reads to leader for a short time after user writes."""

        def __init__(self, db: ReplicatedDatabase, sticky_duration_sec: float = 5.0):
            self.db = db
            self.sticky_duration = sticky_duration_sec
            self.user_write_times: Dict[int, float] = {}

        def record_write(self, user_id: int):
            self.user_write_times[user_id] = time.time()

        def read(self, user_id: int, table: str, row_id: int) -> Tuple[Any, str, str]:
            last_write = self.user_write_times.get(user_id, 0)
            elapsed = time.time() - last_write

            if elapsed < self.sticky_duration:
                # Recent write → read from leader
                data = self.db.read_from_leader(table, row_id)
                return data, "LEADER", "read-your-writes"
            else:
                # No recent write → read from any follower
                data, source = self.db.read_from_random_follower(table, row_id)
                return data, source, "follower"

    router = ReadYourWritesRouter(db, sticky_duration_sec=5.0)
    router.record_write(user_id=42)  # Alice just wrote

    print(f"\n  {'Attempt':<10} {'Read From':<15} {'Strategy':<20} {'Bio':<30}")
    print(f"  {'─'*75}")

    for attempt in range(4):
        data, source, strategy = router.read(42, "profiles", 42)
        bio = data.get("bio", "N/A") if data else "N/A"
        bio_display = bio[:25] + "..." if len(bio) > 25 else bio
        print(f"  {attempt+1:<10} {source:<15} {strategy:<20} {bio_display}")

    # Fix 2: Session stickiness
    print(f"\n  Fix 2: Session stickiness (hash user to same replica)")
    print("  " + "─" * 50)

    def sticky_follower(user_id: int, num_followers: int) -> int:
        """Deterministic mapping: same user always reads from same follower."""
        return hash(user_id) % num_followers

    follower_idx = sticky_follower(42, len(db.followers))
    print(f"  User 42 → always reads from FOLLOWER-{follower_idx + 1}")
    print(f"  User 43 → always reads from FOLLOWER-{sticky_follower(43, len(db.followers)) + 1}")
    print(f"  User 44 → always reads from FOLLOWER-{sticky_follower(44, len(db.followers)) + 1}")

    # Fix 3: Track replication position
    print(f"\n  Fix 3: Track replication position (LSN-based)")
    print("  " + "─" * 50)
    print(f"  After write, client remembers: last_write_lsn = {db._lsn}")
    print(f"  On read, only use followers where replication_position >= {db._lsn}")
    print(f"  If no follower is caught up → fall back to leader")

    print("""
  💡 KEY INSIGHT (DDIA):
     "Read-your-writes consistency" means:
     After a user makes a write, if they read the same data,
     they will see the value they wrote (or a later value).

     This is a per-USER guarantee, not a global guarantee!
     Other users may still see old data until followers catch up.
    """)


# =============================================================================
# ANOMALY 2: MONOTONIC READS
# =============================================================================

def demo_2_monotonic_reads():
    """
    ANOMALY 2: Monotonic Reads (Non-Monotonic Reads = Time Travel!)

    DDIA: "If a user makes several reads in sequence, they may see
    a value moving backward in time."

    Scenario: User sees a comment, refreshes → comment DISAPPEARS
    (then reappears on next refresh!)
    """
    print_header("2️⃣  ANOMALY: Non-Monotonic Reads (Time Travel)")
    print("""
    Scenario: User sees a comment from their friend. They refresh the page.
    The comment DISAPPEARS! They refresh again — it comes back.

    This happens because each read may hit a DIFFERENT follower,
    and some followers are MORE BEHIND than others.
    """)

    print_section("THE BUG")

    # Setup followers with VERY different lag
    leader = ReplicaNode("LEADER", lag_ms=0)
    follower_a = ReplicaNode("FOLLOWER-A", lag_ms=0)   # Fast — has the comment
    follower_b = ReplicaNode("FOLLOWER-B", lag_ms=0)   # Slow — doesn't have it yet

    # Write a comment — both leader and follower-A have it
    comment = {
        "lsn": 1, "table": "comments", "operation": "INSERT",
        "data": {"id": 1, "author": "Bob", "text": "Great article!", "time": "10:00:00"}
    }

    leader.apply_write(comment)
    follower_a.apply_write(comment)
    # follower_b is BEHIND — hasn't received the comment yet!

    followers = [follower_a, follower_b]

    print("\n  Bob posts: 'Great article!' at 10:00:00\n")
    print(f"  {'Read #':<8} {'Hits':<15} {'Sees Comment?':<20} {'User Experience'}")
    print(f"  {'─'*65}")

    # Simulate user reading from random followers
    experiences = [
        (follower_a, True, "🙂 Sees Bob's comment"),
        (follower_b, False, "😕 Comment GONE! 'Where did it go?'"),
        (follower_a, True, "😳 Comment is BACK! 'Am I going crazy?'"),
        (follower_b, False, "😡 Gone AGAIN! 'This site is broken!'"),
        (follower_a, True, "🤯 It's back... time travel!"),
    ]

    for i, (follower, sees_it, experience) in enumerate(experiences):
        comment_data = follower.read("comments", 1)
        has_comment = comment_data is not None
        print(f"  {i+1:<8} {follower.name:<15} "
              f"{'YES ✅' if has_comment else 'NO ❌':<20} "
              f"{experience}")

    print("""
  🐛 The user sees data going BACKWARD in time!
     Comment exists → disappears → reappears → disappears

     Root cause: Each request hits a DIFFERENT follower.
     Follower-A is caught up, Follower-B is still behind.
    """)

    # THE FIX
    print_section("THE FIX: Monotonic Reads (Session Stickiness)")

    print("""
  Solution: Each user ALWAYS reads from the SAME follower.
  (Hash user_id to a specific follower)
    """)

    def get_sticky_follower(user_id: str, followers: List[ReplicaNode]) -> ReplicaNode:
        index = int(hashlib.md5(user_id.encode()).hexdigest(), 16) % len(followers)
        return followers[index]

    user_follower = get_sticky_follower("user_123", followers)
    print(f"  user_123 → always reads from {user_follower.name}\n")

    print(f"  {'Read #':<8} {'Hits':<15} {'Sees Comment?':<20} {'User Experience'}")
    print(f"  {'─'*65}")

    for i in range(5):
        comment_data = user_follower.read("comments", 1)
        has_comment = comment_data is not None
        experience = "🙂 Consistent view" if has_comment else "😐 Not yet (but consistent)"
        print(f"  {i+1:<8} {user_follower.name:<15} "
              f"{'YES ✅' if has_comment else 'NO ❌':<20} "
              f"{experience}")

    print("""
  ✅ Now the user always hits the same follower.
     Even if that follower is behind, the user never sees time go backward.

  💡 KEY INSIGHT (DDIA):
     "Monotonic reads" means:
     If a user has seen a value at time T, they won't see an OLDER value later.
     Time only moves FORWARD from the user's perspective.

     Implementation: hash(user_id) % num_replicas → same replica every time
    """)


# =============================================================================
# ANOMALY 3: CONSISTENT PREFIX READS
# =============================================================================

def demo_3_consistent_prefix():
    """
    ANOMALY 3: Consistent Prefix Reads (Causality Violation)

    DDIA: "If a sequence of writes happens in a certain order, then
    anyone reading those writes will see them appear in the same order."

    Scenario: Person A asks a question, Person B answers.
    A third observer sees the ANSWER before the QUESTION!
    """
    print_header("3️⃣  ANOMALY: Consistent Prefix Reads (Causality Violation)")
    print("""
    Scenario: In a chat app with partitioned data...

    Person A asks: "What's the capital of France?"
    Person B answers: "It's Paris!"

    But an observer sees: "It's Paris!" FIRST, then "What's the capital?"
    The ANSWER appears BEFORE the QUESTION!
    """)

    print_section("THE BUG")

    # In a partitioned system, different messages go to different partitions
    partition_1 = ReplicaNode("PARTITION-1", lag_ms=0)   # Slow — has question
    partition_2 = ReplicaNode("PARTITION-2", lag_ms=0)   # Fast — has answer

    # Person A's question goes to partition 1
    question = {
        "lsn": 1, "table": "messages", "operation": "INSERT",
        "data": {"id": 1, "author": "Alice", "text": "What's the capital of France?",
                 "time": "10:00:00", "seq": 1}
    }

    # Person B's answer goes to partition 2
    answer = {
        "lsn": 2, "table": "messages", "operation": "INSERT",
        "data": {"id": 2, "author": "Bob", "text": "It's Paris!",
                 "time": "10:00:05", "seq": 2}
    }

    # Answer arrives BEFORE question due to partition lag!
    partition_2.apply_write(answer)   # Answer arrives first
    # partition_1 is slow — question hasn't arrived yet

    print("""
  Timeline of what actually happens:

    10:00:00 — Alice asks: "What's the capital of France?"  → Partition 1
    10:00:05 — Bob answers: "It's Paris!"                    → Partition 2

  What an observer sees (reading from both partitions):
    """)

    print(f"  {'Time':<12} {'Source':<15} {'Message':<45} {'Status'}")
    print(f"  {'─'*75}")

    # Observer reads partition 2 first (it's faster)
    answer_data = partition_2.read("messages", 2)
    question_data = partition_1.read("messages", 1)

    msg_bob = 'Bob: "It\'s Paris!"'
    print(f"  {'10:00:06':<12} {'PARTITION-2':<15} {msg_bob:<45} \u2705 Arrived")

    print(f"  {'10:00:07':<12} {'PARTITION-1':<15} "
          f"{'(still waiting...)':<45} ⏳ Hasn't arrived yet!")

    # Now question arrives
    partition_1.apply_write(question)

    msg_alice = 'Alice: "What\'s the capital?"'
    print(f"  {'10:00:10':<12} {'PARTITION-1':<15} {msg_alice:<45} \u2705 Finally arrived")

    print("""
  🐛 The observer sees:
     1. "It's Paris!"                    ← ANSWER first!?
     2. "What's the capital of France?"  ← QUESTION second!?

     Causality is BROKEN! The answer appeared before the question.
     This makes NO SENSE to the observer.
    """)

    # THE FIX
    print_section("THE FIX: Write Causally Related Data to Same Partition")

    print("""
  Solution: Ensure causally related writes go to the SAME partition.
  Use conversation_id or thread_id as the partition key.
    """)

    # All messages in same conversation → same partition
    same_partition = ReplicaNode("SINGLE-PARTITION", lag_ms=0)

    # Both messages go to the same partition → preserved order!
    same_partition.apply_write(question)
    same_partition.apply_write(answer)

    print(f"  Using partition key = conversation_id\n")
    print(f"  {'Order':<8} {'Message':<50} {'Causal Order'}")
    print(f"  {'─'*65}")

    q = same_partition.read("messages", 1)
    a = same_partition.read("messages", 2)

    if q and a:
        print(f"  {'1':<8} {q['author'] + ': ' + q['text']:<50} {'✅ Question first'}")
        print(f"  {'2':<8} {a['author'] + ': ' + a['text']:<50} {'✅ Answer second'}")

    print("""
  ✅ By writing to the same partition:
     • All reads from that partition see writes in the correct order
     • Causality is preserved!

  💡 KEY INSIGHT (DDIA):
     "Consistent prefix reads" means:
     If writes happen in order A → B, no reader should see B before A.

     This is particularly tricky in PARTITIONED databases where
     there is no global ordering of writes across partitions.

     Solutions:
     • Partition by causal group (conversation, thread, user)
     • Use logical timestamps or vector clocks
     • Use a total-order broadcast mechanism
    """)


# =============================================================================
# SUMMARY
# =============================================================================

def demo_summary():
    """Print summary of all three anomalies and their fixes."""
    print_header("📊 SUMMARY: Three Consistency Anomalies")

    print("""
  ┌────────────────────────┬────────────────────────┬───────────────────────────┐
  │ Anomaly                │ User Experience        │ Fix                       │
  ├────────────────────────┼────────────────────────┼───────────────────────────┤
  │ Read-Your-Writes       │ "My update didn't      │ Route user's reads to     │
  │                        │  save!"                │ leader for N sec after    │
  │                        │                        │ write, or track LSN       │
  ├────────────────────────┼────────────────────────┼───────────────────────────┤
  │ Non-Monotonic Reads    │ "Comment appeared,     │ Session stickiness:       │
  │ (Time Travel)          │  disappeared, then     │ hash(user_id) → same     │
  │                        │  reappeared!"          │ follower always           │
  ├────────────────────────┼────────────────────────┼───────────────────────────┤
  │ Consistent Prefix      │ "Answer appeared       │ Causally related writes   │
  │ (Causality)            │  before the question!" │ → same partition          │
  └────────────────────────┴────────────────────────┴───────────────────────────┘

  These anomalies ONLY occur with:
  • Asynchronous replication (replication lag)
  • Multi-follower setups (different followers at different positions)
  • Partitioned databases (no global write ordering)

  With SYNCHRONOUS replication, none of these happen — but you pay
  with latency and availability (as we saw in Exercise 3).
    """)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("  EXERCISE 5: REPLICATION LAG — CONSISTENCY ANOMALIES")
    print("  DDIA Chapter 5: 'Problems with Replication Lag'")
    print("=" * 80)
    print("""
  Asynchronous replication is fast, but the lag creates THREE
  specific user-facing problems. You'll see each bug AND its fix.
    """)

    demo_1_read_your_writes()
    demo_2_monotonic_reads()
    demo_3_consistent_prefix()
    demo_summary()

    print("\n" + "=" * 80)
    print("  EXERCISE 5 COMPLETE ✅")
    print("=" * 80)
    print("""
  Key Takeaways:

  1. 👤 Read-Your-Writes: Route user's reads to leader after they write
  2. ⏱️  Monotonic Reads: Stick each user to the same follower (hash)
  3. 🔗 Consistent Prefix: Write causally related data to same partition

  These three guarantees form the foundation of consistency models
  that you'll encounter in real systems:

  • PostgreSQL: synchronous_commit for read-your-writes
  • MongoDB: readConcern + readPreference for all three
  • Cassandra: LOCAL_QUORUM for strong reads

  ═══════════════════════════════════════════════════════════════

  🎉 CONGRATULATIONS! You've completed ALL 5 exercises for
     Single-Leader Replication (Section 1 of Chapter 5)!

  You now understand:
  ✅ How leader-follower replication works
  ✅ Three types of replication logs
  ✅ Sync vs async trade-offs
  ✅ Failover mechanics and split-brain
  ✅ Consistency anomalies and their solutions

  Next: Multi-Leader Replication (Section 2) — where conflicts get REAL!

  ═══════════════════════════════════════════════════════════════
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
