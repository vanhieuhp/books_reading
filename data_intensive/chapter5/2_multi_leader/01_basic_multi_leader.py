"""
Exercise 1: Multi-Datacenter Setup & Local Writes

DDIA Reference: Chapter 5, "Multi-Leader Replication" (pp. 168)

This exercise demonstrates the basic architecture of a Multi-Leader system:
  1. Each datacenter has its own Leader.
  2. Local users write to their local Leader (ultra-fast latency!).
  3. Leaders asynchronously replicate their changes to each other.
  4. If the inter-datacenter network goes down, local writes STILL SUCCEED.
     (This is impossible in a Single-Leader architecture).

Run: python 01_basic_multi_leader.py
"""

import sys
import time
import random
import threading
from typing import Dict, List, Optional

# Fix Windows terminal encoding for Unicode output
sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# MULTI-LEADER INFRASTRUCTURE
# =============================================================================

class LogEntry:
    def __init__(self, node_id: str, lsn: int, operation: str, 
                 table: str, data: Dict, timestamp: float):
        self.node_id = node_id  # Originating node
        self.lsn = lsn          # Local Sequence Number at origin
        self.operation = operation
        self.table = table
        self.data = data
        self.timestamp = timestamp

    def __repr__(self):
        return f"[{self.node_id}-LSN{self.lsn}] {self.operation} {self.data.get('id')}"


class LeaderNode:
    """A Leader node in one datacenter."""
    
    def __init__(self, datacenter: str):
        self.datacenter = datacenter
        self.storage: Dict[str, Dict[int, Dict]] = {}
        
        # Local state
        self.local_lsn = 0
        self.replication_log: List[LogEntry] = []
        
        # Keep track of what we've received from other datacenters to avoid infinite loops!
        # DDIA: "Each node must remember which updates it has already processed."
        self.processed_lsns: Dict[str, int] = {}
        
        self.is_online = True

    def write_local(self, table: str, operation: str, data: Dict) -> LogEntry:
        """A client writes to this local leader directly."""
        if not self.is_online:
            raise Exception(f"{self.datacenter} is offline!")
            
        # 1. Update local storage immediately (Fast!)
        if table not in self.storage:
            self.storage[table] = {}
            
        row_id = data.get("id")
        if operation == "INSERT" or operation == "UPDATE":
            if row_id not in self.storage[table]:
                self.storage[table][row_id] = {}
            self.storage[table][row_id].update(data)
        elif operation == "DELETE":
            self.storage[table].pop(row_id, None)

        # 2. Append to local replication log
        self.local_lsn += 1
        entry = LogEntry(
            node_id=self.datacenter,
            lsn=self.local_lsn,
            operation=operation,
            table=table,
            data=data.copy(),
            timestamp=time.time()
        )
        self.replication_log.append(entry)
        
        # We process our own writes immediately
        self.processed_lsns[self.datacenter] = self.local_lsn
        
        return entry

    def process_replicated_entry(self, entry: LogEntry) -> bool:
        """Receive a write from ANOTHER datacenter's leader."""
        # Prevent infinite replication loops!
        # If I am US, and EU sends me a record, did EU originate it or was EU just passing it along?
        if entry.node_id == self.datacenter:
            return False  # I originated this! Ignore.
            
        last_processed = self.processed_lsns.get(entry.node_id, 0)
        if entry.lsn <= last_processed:
            return False  # Already processed this one.
            
        # Apply the remote change
        table = entry.table
        if table not in self.storage:
            self.storage[table] = {}
            
        row_id = entry.data.get("id")
        if entry.operation == "INSERT" or entry.operation == "UPDATE":
            if row_id not in self.storage[table]:
                self.storage[table][row_id] = {}
            self.storage[table][row_id].update(entry.data)
        elif entry.operation == "DELETE":
            self.storage[table].pop(row_id, None)

        # Record that we processed it
        self.processed_lsns[entry.node_id] = entry.lsn
        return True

    def read_all(self, table: str) -> Dict[int, Dict]:
        return self.storage.get(table, {})


class MultiDCNetwork:
    """Simulates the long-distance network between datacenters."""
    
    def __init__(self, leaders: List[LeaderNode]):
        self.leaders = {l.datacenter: l for l in leaders}
        self.network_partition = False

    def sync_background(self):
        """Simulate background multi-leader replication."""
        if self.network_partition:
            return 0
            
        synced = 0
        for name, sender in self.leaders.items():
            if not sender.is_online:
                continue
                
            for entry in sender.replication_log:
                # Send this entry to every OTHER leader
                for other_name, receiver in self.leaders.items():
                    if name != other_name and receiver.is_online:
                        if receiver.process_replicated_entry(entry):
                            synced += 1
        return synced


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


def demo_1_local_writes():
    """Demonstrate the incredibly fast local writes of Multi-Leader."""
    print_header("1️⃣  DEMO: Fast Local Writes across Continents")
    print("""
    In a Single-Leader system (Leader in US, Follower in EU):
    An EU user must send their WRITE across the Atlantic ocean to the US.
    Latency: ~150ms+. 🐢
    
    In a Multi-Leader system (Leader in US, Leader in EU):
    The EU user writes directly to the EU leader.
    Latency: ~2ms! 🚀  (Replication happens asynchronously via the network later).
    """)

    us_leader = LeaderNode("US-EAST")
    eu_leader = LeaderNode("EU-WEST")
    network = MultiDCNetwork([us_leader, eu_leader])

    print_section("WRITING DATA LOCALLY")
    
    # 1. US User writes to US Leader
    start = time.perf_counter()
    us_leader.write_local("users", "INSERT", {"id": 1, "name": "Alice (US)", "city": "New York"})
    us_time = (time.perf_counter() - start) * 1000
    print(f"  🗽 US User writes to US-EAST Leader:")
    print(f"     ✅ Success! Latency: {us_time:.3f} ms")

    # 2. EU User writes to EU Leader
    start = time.perf_counter()
    eu_leader.write_local("users", "INSERT", {"id": 2, "name": "Bob (EU)", "city": "Paris"})
    eu_time = (time.perf_counter() - start) * 1000
    print(f"\n  🗼 EU User writes to EU-WEST Leader:")
    print(f"     ✅ Success! Latency: {eu_time:.3f} ms")

    print_section("STATE BEFORE REPLICATION")
    print(f"  [US-EAST] Database: {us_leader.read_all('users')}")
    print(f"  [EU-WEST] Database: {eu_leader.read_all('users')}")
    print(f"  ⚠️  Notice they are completely DIFFERENT right now! They haven't synced.")

    print_section("BACKGROUND NETWORK SYNC")
    print("  ... Syncing US and EU across the transatlantic cable ...")
    time.sleep(1) # simulate network
    network.sync_background()

    print(f"\n  [US-EAST] Database: {us_leader.read_all('users')}")
    print(f"  [EU-WEST] Database: {eu_leader.read_all('users')}")
    print(f"  ✅ Fully Synced! Both sites have Alice and Bob.")


def demo_2_network_partition():
    """Demonstrate how Multi-Leader survives inter-datacenter network failures."""
    print_header("2️⃣  DEMO: Surviving Inter-Datacenter Partitions")
    print("""
    Single-Leader Problem: If the transatlantic cable gets cut, EU users CANNOT WRITE.
    They have no leader to talk to. ❌
    
    Multi-Leader Solution: If the cable is cut, US and EU keep accepting writes
    completely independently. When the cable is fixed, they catch up. ✅
    """)

    us_leader = LeaderNode("US-EAST")
    eu_leader = LeaderNode("EU-WEST")
    network = MultiDCNetwork([us_leader, eu_leader])
    
    # Pre-populate
    us_leader.write_local("users", "INSERT", {"id": 1, "name": "Alice (US)"})
    network.sync_background()

    print_section("💥 DISASTER: Transatlantic Cable Cut!")
    network.network_partition = True
    print("  Network partition is active. US and EU cannot communicate.")

    print("\n  🗽 US User tries to post a message:")
    try:
        us_leader.write_local("messages", "INSERT", {"id": 100, "text": "Hello from New York!"})
        print("     ✅ SUCCESS! US Leader accepted local write.")
    except Exception as e:
        print(f"     ❌ FAILED: {e}")

    print("\n  🗼 EU User tries to post a message:")
    try:
        eu_leader.write_local("messages", "INSERT", {"id": 200, "text": "Bonjour from Paris!"})
        print("     ✅ SUCCESS! EU Leader accepted local write.")
    except Exception as e:
        print(f"     ❌ FAILED: {e}")

    print_section("DIVERGENT STATE DURING OUTAGE")
    print(f"  [US-EAST] Messages: {us_leader.read_all('messages')}")
    print(f"  [EU-WEST] Messages: {eu_leader.read_all('messages')}")
    print(f"  ⚠️  Both leaders accepted writes, but neither knows about the other!")

    print_section("🔧 RECOVERY: Cable Fixed!")
    network.network_partition = False
    print("  Network partition healed. Running background sync...")
    
    synced = network.sync_background()
    print(f"  🔄 {synced} records synced bidirectionally.")

    print(f"\n  [US-EAST] Messages: {us_leader.read_all('messages')}")
    print(f"  [EU-WEST] Messages: {eu_leader.read_all('messages')}")
    print(f"  ✅ Fully Synced Again!")

    print("""
  💡 KEY INSIGHT (DDIA):
     In a single-leader setup, a network partition means followers behind the partition
     cannot write. 
     In a multi-leader setup, the partitioned datacenters continue operating independently.
     This provides MASSIVE availability improvements for global applications.
    """)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("  EXERCISE 1: MULTI-DATACENTER MULTI-LEADER SETUP")
    print("  DDIA Chapter 5: 'Multi-Leader Replication'")
    print("=" * 80)

    demo_1_local_writes()
    demo_2_network_partition()

    print("\n" + "=" * 80)
    print("  EXERCISE 1 COMPLETE ✅")
    print("=" * 80)
    print("""
  Next: Run 02_write_conflicts.py to see the FATAL FLAW of this architecture:
  What happens if the US user and the EU user edit the EXACT SAME RECORD
  while the network is disconnected?
    """)

if __name__ == "__main__":
    main()
