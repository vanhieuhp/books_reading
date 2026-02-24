"""
Exercise 2: Write Conflicts & Last Write Wins (LWW)

DDIA Reference: Chapter 5, "Multi-Leader Write Conflicts" (pp. 171)

This exercise demonstrates the fundamental flaw in Multi-Leader architecture:
Data divergence due to concurrent writes on the same record.

It implements the most common, simple, and dangerous conflict resolution 
strategy: Last Write Wins (LWW). LWW resolves conflicts by letting the 
write with the latest timestamp overwrite earlier ones, completely 
destroying the earlier data.

Run: python 02_write_conflicts.py
"""

import sys
import time
import uuid
from typing import Dict, List, Any, Tuple

# Fix Windows terminal encoding for Unicode output
sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# MULTI-LEADER INFRASTRUCTURE (With LWW support)
# =============================================================================

class LogEntry:
    def __init__(self, node_id: str, lsn: int, operation: str, 
                 table: str, data: Dict, timestamp: float):
        self.node_id = node_id
        self.lsn = lsn
        self.operation = operation
        self.table = table
        self.data = data
        self.timestamp = timestamp

    def __repr__(self):
        return f"[{self.node_id}-LSN{self.lsn}] {self.operation} {self.data.get('id')} at t={self.timestamp:.4f}"


class LeaderNodeLWW:
    """A Leader node that resolves conflicts using Last Write Wins (Timestamp)."""
    
    def __init__(self, datacenter: str):
        self.datacenter = datacenter
        
        # storage[table][row_id] = {"data": {...}, "timestamp": float}
        # We MUST store the timestamp of the last write for every row!
        self.storage: Dict[str, Dict[int, Dict]] = {}
        
        self.local_lsn = 0
        self.replication_log: List[LogEntry] = []
        self.processed_lsns: Dict[str, int] = {}

    def write_local(self, table: str, operation: str, data: Dict) -> LogEntry:
        """A client writes to this local leader directly."""
        write_time = time.time()
        
        if table not in self.storage:
            self.storage[table] = {}
            
        row_id = data.get("id")
        
        # Local writes ALWAYS succeed locally initially
        if operation == "INSERT" or operation == "UPDATE":
            if row_id not in self.storage[table]:
                self.storage[table][row_id] = {"data": {}, "timestamp": 0.0}
            
            # Update the data AND the timestamp
            self.storage[table][row_id]["data"].update(data)
            self.storage[table][row_id]["timestamp"] = write_time
        
        elif operation == "DELETE":
            # (In a real system you need tombstones with timestamps, keeping it simple here)
            self.storage[table].pop(row_id, None)

        self.local_lsn += 1
        entry = LogEntry(
            node_id=self.datacenter, lsn=self.local_lsn,
            operation=operation, table=table,
            data=data.copy(), timestamp=write_time
        )
        self.replication_log.append(entry)
        self.processed_lsns[self.datacenter] = self.local_lsn
        
        return entry

    def process_replicated_entry(self, entry: LogEntry) -> Tuple[bool, str]:
        """Receive a write from ANOTHER datacenter's leader. Applies LWW logic."""
        if entry.node_id == self.datacenter:
            return False, "Ignored: Own write"
            
        last_processed = self.processed_lsns.get(entry.node_id, 0)
        if entry.lsn <= last_processed:
            return False, "Ignored: Already processed"
            
        table = entry.table
        if table not in self.storage:
            self.storage[table] = {}
            
        row_id = entry.data.get("id")
        
        # Check if the row already exists to apply LWW
        current_record = self.storage[table].get(row_id)
        
        if entry.operation == "INSERT" or entry.operation == "UPDATE":
            if current_record is None:
                # No conflict! We don't have this row yet.
                self.storage[table][row_id] = {"data": entry.data.copy(), "timestamp": entry.timestamp}
                status = "✅ Applied (No conflict)"
            else:
                # CONFLICT CHECK: Is the incoming timestamp strictly GREATER than our local one?
                if entry.timestamp > current_record["timestamp"]:
                    # Remote write is newer. OVERWRITE our local data.
                    self.storage[table][row_id]["data"].update(entry.data)
                    self.storage[table][row_id]["timestamp"] = entry.timestamp
                    status = f"✅ Applied (Remote {entry.timestamp:.4f} > Local {current_record['timestamp']:.4f})"
                else:
                    # Remote write is OLDER. Ignore it! Keep our local data.
                    status = f"❌ Rejected (LWW: Remote {entry.timestamp:.4f} < Local {current_record['timestamp']:.4f})"
                    
        elif entry.operation == "DELETE":
            self.storage[table].pop(row_id, None)
            status = "✅ Applied (Delete)"

        self.processed_lsns[entry.node_id] = entry.lsn
        return True, status

    def read_all(self, table: str) -> Dict[int, Dict]:
        # Return only the data portion, hiding metadata for display
        return {k: v["data"] for k, v in self.storage.get(table, {}).items()}


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

def demo_write_conflict():
    print_header("🔥 DEMO: The Write Conflict")
    print("""
    Scenario: The company Wiki has a page for "Paris Office Details".
    User A in New York edits the page on the US Leader.
    Simultaneously, User B in Paris edits the page on the EU Leader.
    
    Because the network takes time to sync, BOTH leaders accept the 
    write locally. The data has now diverged.
    """)
    
    us = LeaderNodeLWW("US-EAST")
    eu = LeaderNodeLWW("EU-WEST")
    
    # Setup initial state
    us.write_local("wiki", "INSERT", {"id": 1, "title": "Paris Office", "info": "Located in France."})
    eu.process_replicated_entry(us.replication_log[0])
    
    print_section("INITIAL STATE")
    print(f"  [US-EAST] Wiki 1: {us.read_all('wiki')[1]['info']}")
    print(f"  [EU-WEST] Wiki 1: {eu.read_all('wiki')[1]['info']}")
    
    print_section("CONCURRENT WRITES (Data Diverges!)")
    
    # US saves at t=100
    us.write_local("wiki", "UPDATE", {"id": 1, "info": "Located near the Eiffel Tower. (By US)"})
    print(f"  ⏱️ US User clicks Save. US Leader accepts write.")
    
    time.sleep(0.1) # Simulate that the EU user hits save just 100ms later
    
    # EU saves at t=100.1
    eu.write_local("wiki", "UPDATE", {"id": 1, "info": "Located in the 7th arrondissement. (By EU)"})
    print(f"  ⏱️ EU User clicks Save. EU Leader accepts write.")
    
    print(f"\n  [US-EAST] Wiki 1: {us.read_all('wiki')[1]['info']}")
    print(f"  [EU-WEST] Wiki 1: {eu.read_all('wiki')[1]['info']}")
    print(f"  ⚠️ We have a conflict! The replicas disagree.")
    
    print_section("RESOLUTION via LAST WRITE WINS (LWW)")
    print("  ... Syncing US and EU ...\n")
    
    # US sends its log to EU
    _, status1 = eu.process_replicated_entry(us.replication_log[1])
    print(f"  EU Leader receives US write: {status1}")
    
    # EU sends its log to US
    _, status2 = us.process_replicated_entry(eu.replication_log[0])
    print(f"  US Leader receives EU write: {status2}")
    
    print(f"\n  [US-EAST] Wiki 1: {us.read_all('wiki')[1]['info']}")
    print(f"  [EU-WEST] Wiki 1: {eu.read_all('wiki')[1]['info']}")
    print("  ✅ Fully Synced! Both replicas agree again.")

    print("""
  💀 BUT LOOK CLOSER:
     The US User's edit ("Located near the Eiffel Tower") is completely GONE.
     It was silently dropped and overwritten by the EU user's edit, just because
     the EU user clicked save 100ms later.
     
     LWW resolved the replication conflict, but it caused DATA LOSS from the 
     user's perspective.
    """)



def main():
    print("=" * 80)
    print("  EXERCISE 2: WRITE CONFLICTS AND LAST-WRITE-WINS (LWW)")
    print("  DDIA Chapter 5: 'Multi-Leader Replication'")
    print("=" * 80)

    demo_write_conflict()

    print("\n" + "=" * 80)
    print("  EXERCISE 2 COMPLETE ✅")
    print("=" * 80)
    print("""
  LWW is the default in many NoSQL databases like Cassandra and Riak,
  because it guarantees convergence. Everyone eventually agrees on the 
  same data.

  But as DDIA points out: "LWW achieves the goal of eventual convergence, 
  but at the cost of durability."
  
  Next: Run 03_custom_resolution.py to see how to merge data intelligently
  instead of destroying it.
    """)

if __name__ == "__main__":
    main()
