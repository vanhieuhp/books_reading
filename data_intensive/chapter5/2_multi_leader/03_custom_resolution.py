"""
Exercise 3: Custom Conflict Resolution (Application-Level Merging)

DDIA Reference: Chapter 5, "Custom Conflict Resolution Logic" (pp. 173)

This exercise demonstrates a better way to handle conflicts than throwing
data away with LWW. When two datacenters receive conflicting updates 
for the same record, they invoke Application-Level Merge Logic.

Scenario: A Shopping Cart stringing across both US and EU servers. 
US user adds "Laptop" to Cart 1. 
EU user adds "Mouse" to Cart 1. 
Both leaders merge by unioning the Sets together!

Run: python 03_custom_resolution.py
"""

import sys
import time
from typing import Dict, List, Set, Any, Tuple

sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# MULTI-LEADER INFRASTRUCTURE (With Custom Merge Logic)
# =============================================================================

class LogEntry:
    def __init__(self, node_id: str, lsn: int, operation: str, 
                 table: str, data: Dict):
        self.node_id = node_id
        self.lsn = lsn
        self.operation = operation
        self.table = table
        self.data = data
        self.timestamp = time.time()


class LeaderNodeMerge:
    """A Leader node that resolves conflicts using custom merge logic."""
    
    def __init__(self, datacenter: str):
        self.datacenter = datacenter
        
        # storage[table][row_id] = {"items": set(), "last_editor": str}
        self.storage: Dict[str, Dict[int, Dict]] = {}
        
        self.local_lsn = 0
        self.replication_log: List[LogEntry] = []
        self.processed_lsns: Dict[str, int] = {}

    def write_local(self, table: str, row_id: int, item: str) -> LogEntry:
        """A client writes to this local leader directly."""
        
        if table not in self.storage:
            self.storage[table] = {}
            
        if row_id not in self.storage[table]:
            self.storage[table][row_id] = {"items": set(), "last_editor": ""}
            
        # Add the item to the cart
        self.storage[table][row_id]["items"].add(item)
        self.storage[table][row_id]["last_editor"] = self.datacenter

        self.local_lsn += 1
        entry = LogEntry(
            node_id=self.datacenter, lsn=self.local_lsn,
            operation="ADD_ITEM", table=table,
            data={"id": row_id, "item": item, "full_cart": self.storage[table][row_id]["items"].copy()}
        )
        self.replication_log.append(entry)
        self.processed_lsns[self.datacenter] = self.local_lsn
        
        return entry

    def process_replicated_entry(self, entry: LogEntry) -> Tuple[bool, str]:
        """Receive a write from ANOTHER datacenter. Applies CUSTOM MERGE LOGIC."""
        if entry.node_id == self.datacenter:
            return False, "Ignored: Own write"
            
        last_processed = self.processed_lsns.get(entry.node_id, 0)
        if entry.lsn <= last_processed:
            return False, "Ignored: Already processed"
            
        table = entry.table
        if table not in self.storage:
            self.storage[table] = {}
            
        row_id = entry.data.get("id")
        
        # The Custom Application Logic
        current_record = self.storage[table].get(row_id)
        
        if current_record is None:
            # We don't have it, just accept it
            self.storage[table][row_id] = {
                "items": entry.data["full_cart"].copy(), 
                "last_editor": entry.node_id
            }
            status = f"✅ Applied (New record)"
        else:
            # ‼️ CONFLICT DETECTED ‼️
            # LWW would delete our local items. Instead, we union the sets!
            
            local_items = self.storage[table][row_id]["items"]
            remote_items = entry.data["full_cart"]
            
            # The Merge Logic
            merged_items = local_items.union(remote_items)
            
            self.storage[table][row_id]["items"] = merged_items
            self.storage[table][row_id]["last_editor"] = f"{self.datacenter} & {entry.node_id}"
            
            status = f"✅ Merged! (Combined {len(local_items)} local and {len(remote_items)} remote items)"

        self.processed_lsns[entry.node_id] = entry.lsn
        return True, status

    def read_cart(self, row_id: int) -> set:
        return self.storage.get("carts", {}).get(row_id, {}).get("items", set())


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

def demo_custom_merge():
    print_header("🛒 DEMO: Shopping Cart Union Merging")
    print("""
    Scenario: User logs into an e-commerce site on her laptop (routed to US).
    She also logs in on her phone (routed to EU).
    
    10:00:00 - On Laptop: adds "MacBook Pro" to Cart 42.
    10:00:01 - On Phone:  adds "AirPods" to Cart 42.
    
    With LWW, she would lose one of these items.
    With Custom Conflict Resolution, the application unions them.
    """)
    
    us = LeaderNodeMerge("US-EAST")
    eu = LeaderNodeMerge("EU-WEST")
    
    print_section("CONCURRENT WRITES (Data Diverges!)")
    
    us.write_local("carts", 42, "💻 MacBook Pro")
    print(f"  ⏱️ Laptop User clicks Add to Cart. US Leader accepts write.")
    
    eu.write_local("carts", 42, "🎧 AirPods")
    print(f"  ⏱️ Phone User clicks Add to Cart. EU Leader accepts write.")
    
    print(f"\n  [US-EAST] Cart 42: {us.read_cart(42)}")
    print(f"  [EU-WEST] Cart 42: {eu.read_cart(42)}")
    print(f"  ⚠️ We have a conflict! The servers disagree on what's in Cart 42.")
    
    print_section("RESOLUTION via CUSTOM LOGIC (Union)")
    print("  ... Syncing US and EU ...\n")
    
    # US sends its log to EU
    _, status1 = eu.process_replicated_entry(us.replication_log[0])
    print(f"  EU Server receives US write: {status1}")
    
    # EU sends its log to US
    _, status2 = us.process_replicated_entry(eu.replication_log[0])
    print(f"  US Server receives EU write: {status2}")
    
    print(f"\n  [US-EAST] Cart 42: {us.read_cart(42)}")
    print(f"  [EU-WEST] Cart 42: {eu.read_cart(42)}")
    print("  ✅ Fully Synced! NO DATA WAS LOST.")

    print("""
  💡 KEY INSIGHT (DDIA):
     This custom merge logic guarantees that writes are never silently 
     dropped. Whatever order the updates arrive in, US and EU will eventually
     arrive at the exact same answer (because Set Union is mathematically
     commutative: A U B == B U A).
    """)

def main():
    print("=" * 80)
    print("  EXERCISE 3: CUSTOM CONFLICT RESOLUTION (MERGING)")
    print("  DDIA Chapter 5: 'Multi-Leader Replication'")
    print("=" * 80)

    demo_custom_merge()

    print("\n" + "=" * 80)
    print("  EXERCISE 3 COMPLETE ✅")
    print("=" * 80)
    print("""
  Writing custom merge logic in Python is easy for a simple Set.
  But for complex documents (like a Google Doc or a complex JSON tree),
  writing bug-free merge code is incredibly difficult.
  
  What if we had a data structure that did this automatically for us?
  
  Next: Run 04_crdts.py to see the magic of Conflict-Free Replicated Data Types (CRDTs).
    """)

if __name__ == "__main__":
    main()
