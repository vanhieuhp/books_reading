"""
Exercise 1: Quorum Math (w + r > n)

DDIA Reference: Chapter 5, "Quorums for Reading and Writing" (pp. 179-183)

This exercise demonstrates how Leaderless systems (like Cassandra/DynamoDB)
guarantee consistency even when nodes are down or slow.

There is NO leader. A client sends its write to ALL replicas.
The write is considered "successful" once 'w' nodes acknowledge it.
To read, the client queries ALL replicas and waits for 'r' nodes to answer.

If w + r > n (where n is the total number of replicas), we are guaranteed
that an up-to-date value is in the read quorum!

Run: python 01_quorum_math.py
"""

import sys
import time
import random
from typing import Dict, List, Tuple, Optional, Any

# Fix Windows terminal encoding for Unicode output
sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# LEADERLESS INFRASTRUCTURE
# =============================================================================

class Node:
    """A storage replica in a leaderless system."""
    def __init__(self, name: str):
        self.name = name
        self.storage: Dict[str, Dict] = {}
        self.is_online = True
        self.latency_ms = random.uniform(5, 50)  # Random network latency

    def write(self, key: str, value: Any, version: int) -> bool:
        if not self.is_online:
            return False
            
        time.sleep(self.latency_ms / 1000.0)
        
        # In a real system, we'd check if the incoming version is newer.
        # For this demo, we just overwrite.
        self.storage[key] = {"value": value, "version": version}
        return True

    def read(self, key: str) -> Optional[Dict]:
        if not self.is_online:
            return None
            
        time.sleep(self.latency_ms / 1000.0)
        return self.storage.get(key)


class LeaderlessClient:
    """A client that coordinates quorum reads and writes."""
    
    def __init__(self, nodes: List[Node]):
        self.nodes = nodes
        self.n = len(nodes)
        self.current_version = 0

    def write_with_quorum(self, key: str, value: Any, w_quorum: int) -> bool:
        """
        Send write to ALL nodes, but only wait for 'w' acknowledgments.
        """
        self.current_version += 1
        print(f"\n  📝 Client attempting WRITE (w={w_quorum}): {key} -> '{value}' (v{self.current_version})")
        
        acks = 0
        failed_nodes = []
        
        # In a real system, this happens in parallel. We simulate it sequentially here.
        for node in self.nodes:
            success = node.write(key, value, self.current_version)
            if success:
                print(f"     ✅ {node.name} acknowledged write")
                acks += 1
            else:
                print(f"     ❌ {node.name} is OFFLINE")
                failed_nodes.append(node.name)
                
        if acks >= w_quorum:
            print(f"  🏆 WRITE SUCCESS! Got {acks}/{self.n} ACKs (Needed {w_quorum})")
            return True
        else:
            print(f"  💀 WRITE FAILED! Only got {acks}/{self.n} ACKs (Needed {w_quorum})")
            return False

    def read_with_quorum(self, key: str, r_quorum: int) -> Tuple[bool, Any]:
        """
        Send read to ALL nodes, wait for 'r' answers, and pick the newest version.
        """
        print(f"\n  📖 Client attempting READ (r={r_quorum}) for key: {key}")
        
        responses = []
        responses_count = 0
        
        for node in self.nodes:
            result = node.read(key)
            if result is not None:
                print(f"     ✅ {node.name} returned v{result['version']}: '{result['value']}'")
                responses.append(result)
                responses_count += 1
            else:
                print(f"     ❌ {node.name} is OFFLINE / unreachable")
                
        if responses_count >= r_quorum:
            # Pick the response with the highest version number
            newest = max(responses, key=lambda x: x["version"])
            print(f"  🏆 READ SUCCESS! Got {responses_count}/{self.n} replies (Needed {r_quorum})")
            print(f"  ✨ Client resolved newest value: '{newest['value']}' (v{newest['version']})")
            return True, newest['value']
        else:
            print(f"  💀 READ FAILED! Only got {responses_count}/{self.n} replies (Needed {r_quorum})")
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

def demo_quorum_math():
    print_header("🎯 DEMO 1: Strict Quorum (w=2, r=2, n=3)")
    print("""
    The Magic Formula: w + r > n
    
    If n=3 (total nodes), and we want to tolerate 1 dead node, we configure:
    w = 2 (write to at least 2 nodes)
    r = 2 (read from at least 2 nodes)
    
    2 + 2 > 3. Therefore, the read and write sets MUST OVERLAP!
    """)
    
    node_a = Node("Node A")
    node_b = Node("Node B")
    node_c = Node("Node C")
    client = LeaderlessClient([node_a, node_b, node_c])
    
    # 1. Initial State
    client.write_with_quorum("greeting", "Hello", w_quorum=2)
    
    print_section("💥 DISASTER: Node C goes OFFLINE")
    node_c.is_online = False
    
    # 2. Write while Node C is offline
    print("""
    The client updates the greeting. Because w=2, it only needs 2 ACKs.
    Node C is dead, but A and B are alive. The write should SUCCEED.
    """)
    client.write_with_quorum("greeting", "Hola", w_quorum=2)
    
    # 3. Read while Node C is offline
    print("""
  📖 The client tries to read. Because r=2, it only needs 2 replies.
    Node C is dead, but A and B answer. The read should SUCCEED,
    and we are GUARANTEED to see "Hola" because A and B have the newest data.
    """)
    client.read_with_quorum("greeting", r_quorum=2)
    
    
    print_header("⚠️ DEMO 2: Stale Reads (w=1, r=1, n=3)")
    print("""
    What if we care more about speed than consistency?
    We set w=1 (fast writes) and r=1 (fast reads).
    
    1 + 1 is NOT greater than 3. The sets don't overlap. We might read stale data!
    """)
    
    # Bring C back online, but now C is stale (it missed the "Hola" update)
    print_section("🔧 RECOVERY: Node C comes back ONLINE (but is stale)")
    node_c.is_online = True
    print(f"  Node A has: {node_a.storage['greeting']['value']} (v2)")
    print(f"  Node B has: {node_b.storage['greeting']['value']} (v2)")
    print(f"  Node C has: {node_c.storage['greeting']['value']} (v1) <-- STALE!")
    
    print("""
  📖 The client attempts a fast read (r=1).
    Since it only needs ONE reply, if Node C happens to answer fastest,
    the client will see the OLD data!
    """)
    
    # Simulate C answering fastest
    node_c.latency_ms = 1
    node_a.latency_ms = 100
    node_b.latency_ms = 100
    
    print(f"\n  📖 Client attempting READ (r=1) for key: greeting")
    print(f"     ✅ Node C answered fastest: v1: 'Hello'")
    print(f"  🏆 READ SUCCESS! Got 1/3 replies (Needed 1)")
    print(f"  💀 THE CLIENT JUST READ STALE DATA ('Hello' instead of 'Hola')!")
    
    print("""
  💡 KEY INSIGHT (DDIA):
     Quorums are a trade-off. 
     • High (w=2, r=2): Stronger consistency, tolerates 1 failure. Slower.
     • Low (w=1, r=1): High performance, extremely available. But you might read old data.
     
     Cassandra lets you choose `w` and `r` on a PER-QUERY basis!
    """)

def main():
    print("=" * 80)
    print("  EXERCISE 1: QUORUM MATH AND LEADERLESS REPLICATION")
    print("  DDIA Chapter 5: 'Leaderless Replication'")
    print("=" * 80)

    demo_quorum_math()

    print("\n" + "=" * 80)
    print("  EXERCISE 1 COMPLETE ✅")
    print("=" * 80)
    print("""
  Next: What happens to that stale Node C? How does it ever get the new data if 
  there's no "Leader" to send it to them?
  
  Run 02_read_repair.py to see how the CLIENT heals the database!
    """)

if __name__ == "__main__":
    main()
