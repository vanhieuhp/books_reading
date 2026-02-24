"""
Exercise 3: Sloppy Quorums and Hinted Handoff

DDIA Reference: Chapter 5, "Sloppy Quorums and Hinted Handoff" (pp. 183-184)

This exercise demonstrates the extreme "write availability" of Leaderless DBs.
What happens if node A and B store the "users" table, but they both crash?
If w=2, a strict quorum would return an error to the user!

Solution: Sloppy Quorum.
The system temporarily borrows Nodes C and D (which normally don't store 
the "users" table) to hold the data securely.
When Nodes A and B come back online, C and D perform a "Hinted Handoff"
to give the data back to its rightful owners.

Run: python 03_sloppy_quorums.py
"""

import sys
import time
import random
from typing import Dict, List, Tuple, Optional

# Fix Windows terminal encoding for Unicode output
sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# LEADERLESS INFRASTRUCTURE
# =============================================================================

class NodeCluster:
    def __init__(self, all_nodes: List['Node']):
        self.all_nodes = all_nodes
        # Assume a ring/hash structure where certain nodes own certain keys.
        # For simplicity, we hardcode the owners of "user:123".
        self.home_nodes = ["Node A", "Node B", "Node C"]  # n=3 for this key
        
    def get_home_nodes(self) -> List['Node']:
        return [n for n in self.all_nodes if n.name in self.home_nodes]

    def get_borrowed_nodes(self) -> List['Node']:
        return [n for n in self.all_nodes if n.name not in self.home_nodes]


class Node:
    def __init__(self, name: str):
        self.name = name
        self.storage: Dict[str, Dict] = {}
        # Hinted Handoff Queue
        # Maps target_node_name -> list of (key, value, version)
        self.hints: Dict[str, List[Tuple[str, str, int]]] = {}
        self.is_online = True

    def write(self, key: str, value: str, version: int) -> bool:
        if not self.is_online:
            return False
            
        current_version = self.storage.get(key, {}).get("version", 0)
        if version > current_version:
            self.storage[key] = {"value": value, "version": version}
        return True

    def store_hint(self, target_node_name: str, key: str, value: str, version: int) -> bool:
        """Temporarily store data intended for a different, offline node."""
        if not self.is_online:
            return False
            
        if target_node_name not in self.hints:
            self.hints[target_node_name] = []
            
        self.hints[target_node_name].append((key, value, version))
        print(f"     📦 {self.name} accepted HINT for {target_node_name}")
        return True

    def flush_hints(self, cluster: NodeCluster) -> int:
        """Attempt to deliver hinted handoffs if the target node is back online."""
        if not self.is_online:
            return 0
            
        delivered = 0
        nodes_dict = {n.name: n for n in cluster.all_nodes}
        
        for target_name, hint_list in list(self.hints.items()):
            target_node = nodes_dict.get(target_name)
            
            if target_node and target_node.is_online:
                # Deliver all hints!
                while hint_list:
                    h_key, h_val, h_ver = hint_list.pop(0)
                    target_node.write(h_key, h_val, h_ver)
                    print(f"     ✅ {self.name} Handed off {h_key} to {target_name}!")
                    delivered += 1
                
                # Clear queue securely
                if not hint_list:
                    del self.hints[target_name]
                    
        return delivered


class SloppyClient:
    """A client that uses Sloppy Quorums and creates Hints."""
    
    def __init__(self, cluster: NodeCluster):
        self.cluster = cluster
        self.current_version = 0

    def write_sloppy(self, key: str, value: str, w_quorum: int) -> bool:
        self.current_version += 1
        print(f"\n  📝 Client SLOPPY WRITE (w={w_quorum}): {key} -> '{value}'")
        
        home_nodes = self.cluster.get_home_nodes()
        acks = 0
        dead_home_nodes = []
        
        # 1. Try to write to the rightful "Home" nodes first
        for node in home_nodes:
            if node.write(key, value, self.current_version):
                print(f"     ✅ {node.name} (Home) acknowledged")
                acks += 1
            else:
                print(f"     ❌ {node.name} (Home) is OFFLINE")
                dead_home_nodes.append(node)
                
        if acks >= w_quorum:
            print(f"  🏆 STRICT WRITE SUCCESS! Got {acks}/{len(home_nodes)} ACKs")
            return True

        # 2. Strict Quorum failed. Enter SLOPPY QUORUM mode.
        print(f"\n  ⚠️ Strict quorum failed. Entering SLOPPY QUORUM mode...")
        print(f"  Client looking for temporary 'borrowed' nodes to hold the data.")
        
        borrowed_nodes = self.cluster.get_borrowed_nodes()
        
        # For every dead home node, we ask a borrowed node to hold a "Hint"
        for dead_home in dead_home_nodes:
            for borrowed in borrowed_nodes:
                if borrowed.is_online:
                    # Borrowed node accepts the hint
                    if borrowed.store_hint(dead_home.name, key, value, self.current_version):
                        acks += 1
                        break # Got one
                
        # 3. Check if we met the write quorum with borrowed nodes!
        if acks >= w_quorum:
            print(f"  🏆 SLOPPY WRITE SUCCESS! Got {acks} total ACKs (Needed {w_quorum})")
            return True
        else:
            print(f"  💀 COMPLETE FAILURE. Network partition too extreme.")
            return False


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


def demo_sloppy_quorum():
    print_header("🎯 DEMO: Sloppy Quorum AND Hinted Handoff")
    print("""
    Scenario: A cluster of 5 nodes. 
    Nodes {A, B, C} own the key "user:123". (Home nodes)
    Nodes {D, E} do not own this key. (Borrowed nodes)
    
    A massive power outage takes down Nodes A and B!
    With a strict w=2 quorum, the database would reject all writes to "user:123".
    
    Let's see how Sloppy Quorum saves the day by temporarily storing
    the data on D and E, and how it hands the data back when A and B recover.
    """)
    
    # Setup cluster
    node_a = Node("Node A")
    node_b = Node("Node B")
    node_c = Node("Node C")
    node_d = Node("Node D")
    node_e = Node("Node E")
    cluster = NodeCluster([node_a, node_b, node_c, node_d, node_e])
    
    client = SloppyClient(cluster)
    
    print_section("💥 DISASTER: Home Nodes A and B go OFFLINE")
    node_a.is_online = False
    node_b.is_online = False
    
    # 1. Sloppy Write
    print("""
  The client attempts to write. It needs w=2 ACKs from {A, B, C}.
    But A and B are dead! It will fail over to Slack Quorum and ask
    {D, E} to hold the data securely.
    """)
    client.write_sloppy("user:123", "Alice", w_quorum=2)
    
    print_section("👀 Look at the raw storage")
    print(f"  [Node A] is DEAD")
    print(f"  [Node B] is DEAD")
    print(f"  [Node C] Storage: {node_c.storage.get('user:123')}")
    print(f"  [Node D] Hint Queue: {node_d.hints}")
    print(f"  [Node E] Hint Queue: {node_e.hints}")
    
    # 2. Recovery and Hinted Handoff
    print_section("🔧 RECOVERY: Home Nodes come back ONLINE")
    node_a.is_online = True
    node_b.is_online = True
    print("  Node A and Node B rebooted. But they don't have the data yet.")
    
    print("""
  🔄 HINTED HANDOFF IN BACKGROUND
    Nodes D and E periodically check if the targets of their
    hints are back online. Let's trigger that background process.
    """)
    
    for borrowed_node in [node_d, node_e]:
        borrowed_node.flush_hints(cluster)
        
    print_section("✅ Verify Final State")
    print(f"  [Node A] Storage: {node_a.storage.get('user:123')}  <-- Handoff successful!")
    print(f"  [Node B] Storage: {node_b.storage.get('user:123')}  <-- Handoff successful!")
    print(f"  [Node C] Storage: {node_c.storage.get('user:123')}")
    print(f"  [Node D] Hint Queue: {node_d.hints}  <-- Emptied safely!")
    print(f"  [Node E] Hint Queue: {node_e.hints}  <-- Emptied safely!")

    print("""
  💡 KEY INSIGHT (DDIA):
     Sloppy Quorums optimize for **WRITE AVAILABILITY**.
     Even if the primary replicas are all dead, the database will accept writes
     as long as *any* nodes in the cluster are alive.
     
     But there is a catch: until the Hinted Handoff completes, you cannot be
     sure that a Read (r) will find the data! A Sloppy Quorum write is NOT
     a strict quorum, so `w + r > n` math briefly breaks down. In Cassandra,
     you can turn Sloppy Quorums on or off depending on your needs.
    """)


def main():
    print("=" * 80)
    print("  EXERCISE 3: SLOPPY QUORUMS AND HINTED HANDOFF")
    print("  DDIA Chapter 5: 'Leaderless Replication'")
    print("=" * 80)

    demo_sloppy_quorum()

    print("\n" + "=" * 80)
    print("  EXERCISE 3 COMPLETE ✅")
    print("=" * 80)
    print("""
  🎉 CONGRATULATIONS! You have completed ALL of Chapter 5 Replication!
  
  You now deeply understand:
  1. Single-Leader (The standard: MySQL, Postgres)
  2. Multi-Leader (The local-first model)
  3. Leaderless (The extreme scale model: Cassandra, DynamoDB)
    """)

if __name__ == "__main__":
    main()
