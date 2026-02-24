"""
Exercise 1: Multi-Leader Topologies

DDIA Reference: Chapter 5, "Multi-Leader Replication Topologies" (pp. 175-176)

In Multi-Leader replication, how do the leaders actually connect to each other?
1. Circular: A -> B -> C -> A
2. Star (Tree): A is the center, branching to B and C
3. All-to-All: Every leader connects to every other leader directly.

This script demonstrates two major flaws to watch out for:
1. Circular Topology is brittle: If one connection breaks (e.g., node crashes), 
   the entire replication chain halts!
2. All-to-All is resilient to a single crash... BUT, it introduces the 
   famous "Overtaking Messages" problem (messages taking different paths 
   arrive out of causal order).
"""

import sys
import time
from typing import Dict, List, Set, Any

# Fix Windows terminal encoding for Unicode output
sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# TOPOLOGY INFRASTRUCTURE
# =============================================================================

class LogEntry:
    def __init__(self, node_id: str, lsn: int, text: str):
        self.node_id = node_id   # Originating node
        self.lsn = lsn           # Sequence number at origin
        # The node_ids that have already forwarded/processed this message.
        # This prevents infinite loops!
        self.visited: Set[str] = {node_id}
        self.text = text

    @property
    def id(self):
        return f"{self.node_id}-{self.lsn}"


class Node:
    def __init__(self, name: str):
        self.name = name
        self.outbound_connections: List['Node'] = []
        self.storage: List[str] = []
        self.processed_ids: Set[str] = set()
        self.is_online = True
        self.local_count = 0

    def connect_to(self, other_node: 'Node'):
        """Create a directed network cable from this node to another."""
        self.outbound_connections.append(other_node)

    def write_local(self, text: str):
        if not self.is_online:
            print(f"  ❌ {self.name} is offline. Cannot write.")
            return

        self.local_count += 1
        entry = LogEntry(self.name, self.local_count, text)
        
        self.storage.append(text)
        self.processed_ids.add(entry.id)
        
        print(f"  📝 {self.name} local write: '{text}'")
        
        # Immediately attempt to broadcast over the network topology
        self._forward(entry)

    def receive_network_message(self, entry: LogEntry):
        if not self.is_online:
            return
            
        # Prevent infinite loops (e.g., Circular topology or All-to-All cycles)
        if entry.id in self.processed_ids:
            return
            
        # Accept the write locally!
        self.storage.append(entry.text)
        self.processed_ids.add(entry.id)
        
        # Important for topologies: we append ourselves to the visited list!
        entry.visited.add(self.name)
        
        # Forward it down the chain!
        self._forward(entry)

    def _forward(self, entry: LogEntry):
        for neighbor in self.outbound_connections:
            if neighbor.is_online and neighbor.name not in entry.visited:
                # The delay simulates network travel time
                # print(f"     ➔ {self.name} forwarding to {neighbor.name}...")
                neighbor.receive_network_message(entry)


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

def build_circular() -> List[Node]:
    """ A -> B -> C -> A """
    a, b, c = Node("Node A"), Node("Node B"), Node("Node C")
    a.connect_to(b)
    b.connect_to(c)
    c.connect_to(a)
    return [a, b, c]

def build_all_to_all() -> List[Node]:
    """ Every node connects to every other node in both directions """
    a, b, c = Node("Node A"), Node("Node B"), Node("Node C")
    a.connect_to(b); a.connect_to(c)
    b.connect_to(a); b.connect_to(c)
    c.connect_to(a); c.connect_to(b)
    return [a, b, c]


def demo_circular_brittleness():
    print_header("🎯 DEMO 1: Circular Topology & Single Point of Failure")
    print("""
    Topology: Node A ➔ Node B ➔ Node C ➔ (back to A)
    Advantage: Very simple to implement.
    Disadvantage: If ONE node goes down, the chain is broken.
    """)
    
    a, b, c = build_circular()
    
    # 1. Normal Operation
    a.write_local("Insert Row 1")
    print("\n  👀 Storage after A writes:")
    print(f"     [Node A] {a.storage}")
    print(f"     [Node B] {b.storage}")
    print(f"     [Node C] {c.storage}  <-- It traversed A->B->C seamlessly!")
    
    # 2. Disaster strikes the chain
    print_section("💥 DISASTER: Node B goes OFFLINE")
    b.is_online = False
    
    a.write_local("Insert Row 2")
    
    print("\n  👀 Storage after A writes while B is dead:")
    print(f"     [Node A] {a.storage}")
    print(f"     [Node B] {b.storage}  <-- DEAD")
    print(f"     [Node C] {c.storage}  <-- STALE! C never got Row 2 because B is the only bridge.")
    print("  💀 Node C is entirely cut off from Node A's updates!")


def demo_all_to_all_overtaking():
    print_header("🎯 DEMO 2: All-to-All Topology & Overtaking Messages")
    print("""
    Topology: Every node directly connects to every other node.
    Advantage: Node failures don't stop the spread of messages!
    Disadvantage: Network paths take different amounts of time.
                  Message 2 might overtake Message 1!
    """)
    
    a, b, c = build_all_to_all()
    
    print_section("The Overtaking Scenario")
    print("  Node A updates a record (v1).")
    print("  Node B receives the update, and modifies it further (v2).")
    print("  But the network link from A->C is super slow.")
    
    # Custom simulation logic to show overcoming messages
    
    # A writes locally, but we intercept the network broadcast to simulate delay
    entry_v1 = LogEntry(a.name, 1, "v1 (Created by A)")
    a.storage.append(entry_v1.text)
    a.processed_ids.add(entry_v1.id)
    
    # (FAST LINK) A forwards to B
    b.receive_network_message(entry_v1)
    
    # B modifies the record immediately
    print("  [Node B] sees v1, modifies it, and broadcasts v2 to A and C!")
    entry_v2 = LogEntry(b.name, 1, "v2 (Modified by B)")
    b.storage.append(entry_v2.text)
    b.processed_ids.add(entry_v2.id)
    
    # (FAST LINK) B forwards v2 to C
    c.receive_network_message(entry_v2)
    
    print("  [Node C] currently has:")
    print(f"     {c.storage}")
    
    # (SLOW LINK) A finally forwards its original v1 to C!
    print("  (5 seconds later) ... The slow link from A finally delivers v1 to C!")
    c.receive_network_message(entry_v1)
    
    print("\n  👀 Final corrupted state on Node C:")
    print(f"     [Node C] {c.storage}  <-- Causality VIOLATED!")
    print("  💀 Node C sees 'v2' ARRIVE FIRST, and 'v1' ARRIVE SECOND!")
    
    print("""
  💡 KEY INSIGHT (DDIA):
     To fix the Overtaking Message problem in All-to-All topologies,
     we cannot use timestamps. We must use `Version Vectors` to detect
     that v2 causally depends on v1. When node C receives v2 before v1,
     the Version Vector tells Node C: "Wait! Do not apply v2 yet! You
     are missing v1!"
    """)

def main():
    print("=" * 80)
    print("  EXERCISE 1: REPLICATION TOPOLOGIES")
    print("  DDIA Chapter 5: 'Multi-Leader Topologies'")
    print("=" * 80)

    demo_circular_brittleness()
    demo_all_to_all_overtaking()

    print("\n" + "=" * 80)
    print("  EXERCISE COMPLETE ✅")
    print("=" * 80)
    
if __name__ == "__main__":
    main()
