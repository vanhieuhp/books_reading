"""
Exercise 4: Conflict-Free Replicated Data Types (CRDTs)

DDIA Reference: Chapter 5, "Automatic Conflict Resolution" (pp. 174)

This exercise demonstrates the magic of CRDTs. A CRDT is a data structure
designed specifically for Multi-Leader architectures. It is mathematically
proven to always converge to the same state across all replicas, regardless
of the order in which messages are delivered, duplicated, or delayed!

We will implement a G-Counter (Grow-Only Counter) which tracks things
like "Page Views" or "Upvotes" across multiple data centers.

Run: python 04_crdts.py
"""

import sys
import time
from typing import Dict, List, Any, Tuple

sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# CRDT INFRASTRUCTURE (G-COUNTER)
# =============================================================================

class GCounter:
    """
    GROW-ONLY COUNTER (CRDT)
    
    Instead of holding a single integer (which would cause write conflicts),
    it holds a map of node_id -> local_count.
    
    To get the total value: sum all the local_counts.
    To merge two counters: take the pointwise MAX of each node's count.
    """
    
    def __init__(self, node_id: str):
        self.node_id = node_id
        # State: Map of node_id -> integer
        self.state: Dict[str, int] = {}
        
    def increment(self, amount: int = 1):
        """A local write: only increment our OWN bucket!"""
        if amount < 0:
            raise ValueError("Grow-Only Counters cannot be decremented!")
            
        current = self.state.get(self.node_id, 0)
        self.state[self.node_id] = current + amount
        
    def value(self) -> int:
        """Read the value: sum all buckets!"""
        return sum(self.state.values())
        
    def merge(self, other_state: Dict[str, int]):
        """
        Merge remote state into our state.
        CRDT Rule for G-Counter: Pointwise Maximum.
        """
        for node, other_count in other_state.items():
            current_count = self.state.get(node, 0)
            # ‼️ THE MAGIC LIES HERE ‼️
            self.state[node] = max(current_count, other_count)
            
    def __repr__(self):
        return f"{self.value()} (Internal State: {self.state})"


# =============================================================================
# EXERCISES
# =============================================================================

def print_header(title: str):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def print_section(title: str):
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")

def demo_crdt_gcounter():
    print_header("🎯 DEMO: The Magic of the G-Counter CRDT")
    print("""
    Scenario: A viral video is being upvoted globally.
    US users upvote on the US Server.
    EU users upvote on the EU Server.
    
    If both servers tracked `upvotes = 5` and then simultaneously
    received an upvote (`upvotes = 6`), LWW would merge 6 and 6
    and result in `upvotes = 6` (Losing an upvote!).
    
    Let's see how a CRDT G-Counter handles thousands of concurrent upvotes.
    """)
    
    us_counter = GCounter("US-EAST")
    eu_counter = GCounter("EU-WEST")
    
    print_section("CONCURRENT WRITES (Data Diverges!)")
    
    # 1. Simulate 50 upvotes hitting the US server
    us_counter.increment(50)
    print(f"  ⬆️ US Server receives 50 upvotes.")
    
    # 2. Simulate 30 upvotes hitting the EU server concurrently
    eu_counter.increment(30)
    print(f"  ⬆️ EU Server receives 30 upvotes.")
    
    print(f"\n  [US-EAST] Reads: {us_counter}")
    print(f"  [EU-WEST] Reads: {eu_counter}")
    print(f"  ⚠️ They disagree on the total! 50 vs 30.")
    print(f"  (True total globally should be 80)")
    
    print_section("THE MAGIC MERGE")
    print("  ... Syncing internal states across the Atlantic ...\n")
    
    # US sends its internal state `{ "US-EAST": 50 }` to EU
    eu_counter.merge(us_counter.state)
    print(f"  EU Server merges US state  -> Uses MAX logic")
    
    # EU sends its internal state `{ "EU-WEST": 30 }` to US
    us_counter.merge(eu_counter.state)
    print(f"  US Server merges EU state  -> Uses MAX logic")
    
    print(f"\n  [US-EAST] Reads: {us_counter}")
    print(f"  [EU-WEST] Reads: {eu_counter}")
    print("  ✅ Fully Synced! NO DATA WAS LOST.")
    
    print_section("WHY IT IS BULLETPROOF")
    print("""
    What if the EU server accidentally re-sends its message tomorrow?
    """)
    
    # Re-sending the exact same message
    us_counter.merge({'EU-WEST': 30})
    print(f"  US Server processes duplicate message `EU-WEST: 30`")
    print(f"  [US-EAST] Reads: {us_counter}")
    
    print("""
  💡 KEY INSIGHT (DDIA):
     Because `max(50, 30)` is idempotent (calling it twice doesn't change
     the answer), duplicate messages are safely ignored.
     
     Because of mathematics, no matter how chaotic the network is,
     these datacenters will always converge to exactly 80.
     CRDTs are the future of Multi-Leader applications!
    """)

def main():
    print("=" * 80)
    print("  EXERCISE 4: CONFLICT-FREE REPLICATED DATA TYPES")
    print("  DDIA Chapter 5: 'Multi-Leader Replication'")
    print("=" * 80)

    demo_crdt_gcounter()

    print("\n" + "=" * 80)
    print("  EXERCISE 4 COMPLETE ✅")
    print("=" * 80)
    print("""
  Riak 2.0 and Redis (via RedisEnterprise) have native support for CRDTs.
  You can just tell the database "this field is a CRDT Counter" and it
  quietly handles all the Multi-Leader conflict merging in the background
  without your app ever having to worry about it.

  🎉 CONGRATULATIONS! You have completed the Multi-Leader exercises.
  Next up: Leaderless Replication!
    """)

if __name__ == "__main__":
    main()
