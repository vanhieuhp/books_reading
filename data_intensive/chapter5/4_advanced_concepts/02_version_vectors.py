"""
Exercise 2: Version Vectors & The Happens-Before Relationship

DDIA Reference: Chapter 5, "Detecting Concurrent Writes" (pp. 184-189)

Physical clocks are terrible for distributed systems (Clock Skew).
If you use Last-Write-Wins (LWW) with physical timestamps, a node with
a fast clock will incorrectly overwrite data from a node with a slow clock.

The Solution: Version Vectors (e.g., Dynamo's Vector Clocks).
A Version Vector is a dictionary of {node_id: counter}. Every time a node
modifies a record, it increments its own counter in the dictionary.

Because nodes send these dictionaries back and forth, they can mathematically
prove if Write A "happened-before" Write B, or if they happened CONCURRENTLY
(meaning the users are in a genuine conflict that must be merged).

Run: python 02_version_vectors.py
"""

import sys
from typing import Dict, List, Set, Tuple

# Fix Windows terminal encoding for Unicode output
sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# VERSION VECTOR INFRASTRUCTURE
# =============================================================================

class VersionVector:
    def __init__(self, vector: Dict[str, int] = None):
        if vector is None:
            self.vector = {}
        else:
            # We must copy to avoid mutating references
            self.vector = dict(vector)

    def increment(self, node_id: str):
        """A node increments its personal counter when modifying data."""
        current = self.vector.get(node_id, 0)
        self.vector[node_id] = current + 1

    def merge(self, other: 'VersionVector') -> 'VersionVector':
        """When receiving data, we take the pointwise MAX of the vectors."""
        merged = dict(self.vector)
        for node, count in other.vector.items():
            merged[node] = max(merged.get(node, 0), count)
        return VersionVector(merged)

    def compare(self, other: 'VersionVector') -> str:
        """
        The core logic of Dynamo's conflict detection!
        Returns: 'EQUAL', 'BEFORE', 'AFTER', or 'CONCURRENT'
        """
        # Collect all unique node IDs from both vectors
        all_nodes = set(self.vector.keys()).union(other.vector.keys())

        i_am_greater_or_equal = True
        they_are_greater_or_equal = True

        for node in all_nodes:
            my_v = self.vector.get(node, 0)
            their_v = other.vector.get(node, 0)

            if my_v < their_v:
                i_am_greater_or_equal = False
            if their_v < my_v:
                they_are_greater_or_equal = False

        if i_am_greater_or_equal and they_are_greater_or_equal:
            return 'EQUAL'
        elif i_am_greater_or_equal and not they_are_greater_or_equal:
            return 'AFTER'
        elif not i_am_greater_or_equal and they_are_greater_or_equal:
            return 'BEFORE'
        else:
            # Neither is strictly greater than the other!
            # Example: A={US:1, EU:0}, B={US:0, EU:1}
            return 'CONCURRENT'
            
    def __repr__(self):
        return str(self.vector)

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


def demo_version_vectors():
    print_header("🎯 DEMO: Mathematical Proof of Causality")
    print("""
    Scenario: A shopping cart synced between a phone (Client A) and laptop (Client B).
    
    Version Vectors prove if an edit should overwrite an old one,
    or if the edits happened CONCURRENTLY and must be treated as a conflict.
    """)
    
    # 1. Initial State
    print_section("1. The First Write")
    cart_v1 = {"items": ["Milk"]}
    vv_v1 = VersionVector({"Server1": 1})
    print(f"  [Server1] Client A adds Milk.")
    print(f"  Version Vector: {vv_v1}")
    
    # 2. Causality (Happens-Before)
    print_section("2. A Causal Update (Happens-Before)")
    print(f"  Client B reads the cart, sees 'Milk', and adds 'Eggs'.")
    print(f"  Because Client B specifically read vv_v1 before editing,")
    print(f"  Server1 knows the 'Eggs' edit DEPENDS ON the 'Milk' edit.")
    
    cart_v2 = {"items": ["Milk", "Eggs"]}
    vv_v2 = VersionVector(vv_v1.vector) # Client sends back the vector they read
    vv_v2.increment("Server1")          # Server increments for this new write
    
    print(f"  Version Vector: {vv_v2}")
    
    comparison = vv_v2.compare(vv_v1)
    print(f"\n  🧮 MATH CHECK: Is v2 strictly AFTER v1?")
    print(f"  vv_v2: {vv_v2}")
    print(f"  vv_v1: {vv_v1}")
    print(f"  Result: {comparison}")
    print(f"  ✅ Correct! The database can safely delete v1 and keep v2.")


def demo_concurrent_conflicts():
    print_header("🔥 DEMO: Detecting Concurrent Conflicts")
    print("""
    Scenario: While offline, Client A (Phone) and Client B (Laptop) BOTH
    start editing from Version 2 at the exact same time.
    """)
    
    # The starting point exactly as before (Milk + Eggs)
    base_vv = VersionVector({"Server1": 2})
    
    # Client A acts on Server 1
    print("  [Server 1] Client A removes Milk (Offline on Phone).")
    cart_a = {"items": ["Eggs"]}
    vv_a = VersionVector(base_vv.vector)
    vv_a.increment("Server1")
    print(f"  Write A Vector: {vv_a}")
    
    # Client B acts on Server 2
    print("\n  [Server 2] Client B adds Bacon (Offline on Laptop).")
    cart_b = {"items": ["Milk", "Eggs", "Bacon"]}
    vv_b = VersionVector(base_vv.vector)
    vv_b.increment("Server2")
    print(f"  Write B Vector: {vv_b}")
    
    print_section("THE MERGE ATTEMPT")
    print("  The network comes back online! The servers talk to each other.")
    print("  Should Write A overwrite B? Should B overwrite A?")
    
    comparison = vv_a.compare(vv_b)
    print(f"\n  🧮 MATH CHECK:")
    print(f"  vv_a: {vv_a}")
    print(f"  vv_b: {vv_b}")
    print(f"  Result: 💥 {comparison} 💥")
    
    print("""
  💡 KEY INSIGHT (DDIA):
     The vectors {Server1: 3} and {Server1: 2, Server2: 1} are INCOMPARABLE.
     Neither is strictly greater than the other!
     
     This mathematically proves they happened concurrently (they knew nothing 
     about each other). The database CANNOT blindly overwrite one with the other 
     (like LWW would do based on clock time).
     
     The database MUST return BOTH versions to the application and force
     the application (or user) to resolve the conflict!
    """)
    
    print_section("RESOLVING THE CONFLICT")
    print("  The application merges the carts: {'Eggs', 'Bacon'}")
    
    final_vv = vv_a.merge(vv_b)
    final_vv.increment("Server1") # Server increments to record the resolution
    print(f"  Final Resolved Vector: {final_vv}")
    

def main():
    print("=" * 80)
    print("  EXERCISE 2: VERSION VECTORS & HAPPENS-BEFORE")
    print("  DDIA Chapter 5: 'Detecting Concurrent Writes'")
    print("=" * 80)

    demo_version_vectors()
    demo_concurrent_conflicts()

    print("\n" + "=" * 80)
    print("  EXERCISE COMPLETE ✅")
    print("=" * 80)
    print("""
  This concept is effectively what powers:
  - Amazon Dynamo (Vector Clocks)
  - Riak (Dotted Version Vectors)
  - Git (Commit Hashes and Ancestry)
  
  You now have a true "Mastery" level understanding of Chapter 5!
    """)

if __name__ == "__main__":
    main()
