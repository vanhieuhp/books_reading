"""
Exercise 2: Read Repair (Anti-Entropy)

DDIA Reference: Chapter 5, "Read Repair and Anti-Entropy" (pp. 178-179)

This exercise demonstrates the self-healing nature of Leaderless databases.
When a node is offline, it misses writes. When it comes back online, its
data is stale. Because there is no leader to push the updates to it, how
does it ever catch up?

Solution 1: Read Repair.
When a client reads from multiple nodes to satisfy the 'r' quorum, it might 
notice that some nodes returned stale data compared to others. The client 
will immediately send the newest data back to the stale nodes to fix them!

Run: python 02_read_repair.py
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

class Node:
    def __init__(self, name: str):
        self.name = name
        self.storage: Dict[str, Dict] = {}
        self.is_online = True
        self.latency_ms = random.uniform(5, 50)

    def write(self, key: str, value: str, version: int) -> bool:
        if not self.is_online:
            return False
        
        # In a real system, you only overwrite if the incoming version is NEWER.
        current_version = self.storage.get(key, {}).get("version", 0)
        if version > current_version:
            self.storage[key] = {"value": value, "version": version}
            
        return True

    def read(self, key: str) -> Optional[Dict]:
        if not self.is_online:
            return None
        return self.storage.get(key)


class LeaderlessClientWithRepair:
    """A client that performs Read Repair."""
    
    def __init__(self, nodes: List[Node]):
        self.nodes = nodes
        self.n = len(nodes)
        self.current_version = 0

    def write_with_quorum(self, key: str, value: str, w_quorum: int) -> bool:
        self.current_version += 1
        print(f"\n  📝 Client attempting WRITE (w={w_quorum}): {key} -> '{value}' (v{self.current_version})")
        
        acks = 0
        for node in self.nodes:
            if node.write(key, value, self.current_version):
                print(f"     ✅ {node.name} acknowledged write")
                acks += 1
            else:
                print(f"     ❌ {node.name} is OFFLINE")
                
        if acks >= w_quorum:
            print(f"  🏆 WRITE SUCCESS! Got {acks}/{self.n} ACKs (Needed {w_quorum})")
            return True
        return False

    def read_with_repair(self, key: str, r_quorum: int) -> Tuple[bool, Optional[str]]:
        """
        Sends read to ALL nodes, waits for 'r' answers.
        If it detects stale answers, it issues a background repair write!
        """
        print(f"\n  📖 Client attempting READ with REPAIR (r={r_quorum}) for key: {key}")
        
        responses = []
        for node in self.nodes:
            result = node.read(key)
            if result is not None:
                print(f"     ✅ {node.name} returned v{result['version']}: '{result['value']}'")
                responses.append({"node": node, "data": result})
            else:
                print(f"     ❌ {node.name} is OFFLINE")
                
        if len(responses) >= r_quorum:
            # 1. Find the newest version
            newest_response = max(responses, key=lambda x: x["data"]["version"])
            newest_version = newest_response["data"]["version"]
            newest_value = newest_response["data"]["value"]
            
            print(f"  ✨ Resolved newest value: '{newest_value}' (v{newest_version})")
            
            # 2. READ REPAIR: Find any nodes that returned stale data
            stale_nodes = [r["node"] for r in responses if r["data"]["version"] < newest_version]
            
            if stale_nodes:
                print(f"\n  🛠️ READ REPAIR TRIGGERED 🛠️")
                print(f"     Stale nodes detected: {[n.name for n in stale_nodes]}")
                print(f"     Client is writing v{newest_version} back to them...")
                
                for stale_node in stale_nodes:
                    # Fix the stale node!
                    stale_node.write(key, newest_value, newest_version)
                    print(f"     ✅ {stale_node.name} has been REPAIRED!")
            else:
                print(f"\n  ✅ All responding nodes were up-to-date. No repair needed.")
                
            return True, newest_value
        else:
            print(f"  💀 READ FAILED! Only got {len(responses)} replies (Needed {r_quorum})")
            return False, None


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

def demo_read_repair():
    print_header("🎯 DEMO: Read Repair in Action")
    print("""
    Scenario: A cluster of 3 nodes (w=2, r=2).
    A node goes offline, misses an update, and then comes back online.
    When a client reads data, it will notice the node is stale and FIX IT.
    """)
    
    node_a = Node("Node A")
    node_b = Node("Node B")
    node_c = Node("Node C")
    client = LeaderlessClientWithRepair([node_a, node_b, node_c])
    
    # 1. Initial State (All nodes get v1)
    client.write_with_quorum("status", "System Online", w_quorum=2)
    
    print_section("💥 DISASTER: Node C goes OFFLINE")
    node_c.is_online = False
    
    # 2. Update while C is offline (A and B get v2)
    client.write_with_quorum("status", "System Maintenance", w_quorum=2)
    
    print_section("🔧 RECOVERY: Node C comes back ONLINE (Stale!)")
    node_c.is_online = True
    
    print("  Let's look at the raw storage (what the nodes actually have):")
    print(f"  [Node A] {node_a.storage['status']}")
    print(f"  [Node B] {node_b.storage['status']}")
    print(f"  [Node C] {node_c.storage['status']}  <-- Missing the latest update!")
    
    # 3. Read Repair
    print_section("📖 The Client Reads the Data")
    print("  Watch what happens when the client reads from all 3 nodes...")
    
    # Client reads from all 3 nodes. 
    # It gets v2 from A and B, and v1 from C.
    # It realizes C is stale and issues a write to C!
    client.read_with_repair("status", r_quorum=2)
    
    # 4. Verify Repair
    print_section("✅ Verify Repair")
    print("  Let's look at the raw storage again:")
    print(f"  [Node A] {node_a.storage['status']}")
    print(f"  [Node B] {node_b.storage['status']}")
    print(f"  [Node C] {node_c.storage['status']}  <-- FIXED by the client!")

    print("""
  💡 KEY INSIGHT (DDIA):
     In leaderless systems, the CLIENT does a lot of the heavy lifting.
     When a node misses a write, the database relies heavily on "Read Repair"
     to heal the missing data. 
     
     If a piece of data is NEVER read by a client, it might stay stale forever!
     (This is why Cassandra also runs a background "Anti-Entropy" process 
     that slowly scrubs and repairs data behind the scenes to catch things
     that are rarely read).
    """)


def main():
    print("=" * 80)
    print("  EXERCISE 2: READ REPAIR (ANTI-ENTROPY)")
    print("  DDIA Chapter 5: 'Leaderless Replication'")
    print("=" * 80)

    demo_read_repair()

    print("\n" + "=" * 80)
    print("  EXERCISE 2 COMPLETE ✅")
    print("=" * 80)
    print("""
  Next: What happens if so many nodes are dead that you can't even get
  'w' acknowledgments? Does the database just crash and reject all writes?
  
  Run 03_sloppy_quorums.py to see how Hinted Handoff saves the day.
    """)

if __name__ == "__main__":
    main()
