"""
Exercise 2: Replication Log Mechanisms

DDIA Reference: Chapter 5, "Implementation of Replication Logs" (pp. 158-161)

This exercise demonstrates the THREE ways data can be replicated:
  1. Statement-Based Replication — replay SQL statements (broken!)
  2. Write-Ahead Log (WAL) Shipping — replay raw bytes (coupled!)
  3. Logical (Row-Based) Replication — replay row changes (best!)

You'll see WHY statement-based replication breaks,
WHY WAL shipping is too tightly coupled,
and WHY logical replication is the modern standard.

Run: python 02_replication_logs.py
"""

import sys
import time
import random
import hashlib
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Fix Windows terminal encoding for Unicode output
sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# STATEMENT-BASED REPLICATION
# =============================================================================

class StatementBasedNode:
    """
    A node that uses statement-based replication.

    DDIA: "The leader logs every write request (statement) that it executes
    and sends that statement log to its followers."

    Problem: Non-deterministic functions (NOW(), RAND(), UUID()) produce
    different results on leader vs follower!
    """

    def __init__(self, name: str):
        self.name = name
        self.storage: Dict[str, List[Dict]] = {}
        self._auto_increment = {}

    def execute_statement(self, statement: str) -> Dict[str, Any]:
        """Execute a SQL-like statement locally."""
        result = {"statement": statement, "node": self.name}

        if statement.startswith("INSERT"):
            # Parse: INSERT INTO table VALUES (...)
            parts = statement.split("VALUES")
            table_part = parts[0].replace("INSERT INTO", "").strip()
            values_str = parts[1].strip().strip("()")

            if table_part not in self.storage:
                self.storage[table_part] = []
                self._auto_increment[table_part] = 1

            # Evaluate values — this is where non-determinism happens!
            row = {}
            for val in values_str.split(","):
                val = val.strip()
                key, value = val.split("=")
                key = key.strip()
                value = value.strip()

                # Evaluate non-deterministic functions
                if value == "NOW()":
                    value = datetime.now().isoformat()
                    time.sleep(0.01)  # Simulate time difference between nodes
                elif value == "RAND()":
                    value = str(random.random())
                elif value == "AUTO_INCREMENT":
                    value = str(self._auto_increment[table_part])
                    self._auto_increment[table_part] += 1
                else:
                    value = value.strip("'\"")

                row[key] = value

            self.storage[table_part].append(row)
            result["row"] = row

        return result


def demo_statement_based():
    """
    Demonstrate why statement-based replication BREAKS.

    DDIA: "There are various edge cases... Any statement that calls a
    nondeterministic function, such as NOW() or RAND(), is likely to
    generate a different value on each replica."
    """
    print_section("1️⃣  STATEMENT-BASED REPLICATION")
    print("""
    The leader logs SQL statements and sends them to followers.
    Followers execute the SAME statements.

    Sounds simple... but watch what happens with NOW() and RAND():
    """)

    leader = StatementBasedNode("LEADER")
    follower = StatementBasedNode("FOLLOWER")

    # Case 1: Non-deterministic function NOW()
    print("  Case 1: INSERT with NOW()")
    print("  " + "─" * 50)

    statement = "INSERT INTO events VALUES (timestamp=NOW(), event=login)"
    leader_result = leader.execute_statement(statement)
    follower_result = follower.execute_statement(statement)

    print(f"  Statement: {statement}")
    print(f"  Leader   → timestamp = {leader_result['row']['timestamp']}")
    print(f"  Follower → timestamp = {follower_result['row']['timestamp']}")

    times_match = leader_result['row']['timestamp'] == follower_result['row']['timestamp']
    print(f"\n  Match? {'YES ✅' if times_match else 'NO ❌ — DIFFERENT timestamps!'}")

    # Case 2: Non-deterministic function RAND()
    print(f"\n  Case 2: INSERT with RAND()")
    print("  " + "─" * 50)

    statement = "INSERT INTO scores VALUES (user=alice, score=RAND())"
    leader_result = leader.execute_statement(statement)
    follower_result = follower.execute_statement(statement)

    print(f"  Statement: {statement}")
    print(f"  Leader   → score = {leader_result['row']['score']}")
    print(f"  Follower → score = {follower_result['row']['score']}")

    scores_match = leader_result['row']['score'] == follower_result['row']['score']
    print(f"\n  Match? {'YES ✅' if scores_match else 'NO ❌ — DIFFERENT random values!'}")

    # Case 3: Auto-increment with concurrent transactions
    print(f"\n  Case 3: AUTO_INCREMENT with different execution order")
    print("  " + "─" * 50)

    # On leader: Transaction A runs first
    leader.execute_statement("INSERT INTO users VALUES (id=AUTO_INCREMENT, name=Alice)")
    leader.execute_statement("INSERT INTO users VALUES (id=AUTO_INCREMENT, name=Bob)")

    # On follower: Transaction B runs first (different order!)
    follower.execute_statement("INSERT INTO users VALUES (id=AUTO_INCREMENT, name=Bob)")
    follower.execute_statement("INSERT INTO users VALUES (id=AUTO_INCREMENT, name=Alice)")

    print(f"  Leader:   Alice→id={leader.storage['users'][0]['id']}, Bob→id={leader.storage['users'][1]['id']}")
    print(f"  Follower: Bob→id={follower.storage['users'][0]['id']}, Alice→id={follower.storage['users'][1]['id']}")
    print(f"\n  ❌ Same users, DIFFERENT IDs! Data is INCONSISTENT!")

    print("""
  💡 VERDICT (DDIA):
     Statement-based replication is MOSTLY ABANDONED because:
     • NOW(), RAND(), UUID() produce different values
     • Auto-increment depends on execution order
     • Triggers, stored procedures, UDFs may have side effects

     MySQL used this before version 5.1. Now deprecated.
    """)


# =============================================================================
# WRITE-AHEAD LOG (WAL) SHIPPING
# =============================================================================

class WALEntry:
    """A low-level WAL entry — raw byte-level storage changes."""

    def __init__(self, page_id: int, offset: int, old_bytes: bytes, new_bytes: bytes,
                 storage_engine_version: str):
        self.page_id = page_id
        self.offset = offset
        self.old_bytes = old_bytes
        self.new_bytes = new_bytes
        self.storage_engine_version = storage_engine_version  # Tight coupling!

    def __repr__(self):
        return (f"WAL[page={self.page_id}, offset={self.offset}, "
                f"bytes={self.new_bytes.hex()[:16]}..., engine={self.storage_engine_version}]")


class WALBasedNode:
    """
    A node that uses WAL shipping for replication.

    DDIA: "The log describes changes at a very low level: which bytes
    were changed in which disk blocks."
    """

    def __init__(self, name: str, engine_version: str = "v15.4"):
        self.name = name
        self.engine_version = engine_version
        self.wal: List[WALEntry] = []
        self.pages: Dict[int, bytearray] = {}  # page_id -> raw bytes

    def write(self, data: Dict[str, Any]) -> WALEntry:
        """Write data and create a WAL entry (low-level byte changes)."""
        # Simulate storage engine writing bytes to a page
        data_bytes = json.dumps(data).encode('utf-8')
        page_id = len(self.pages)
        offset = 0

        # Create the page
        page = bytearray(4096)  # Standard 4KB page
        page[offset:offset + len(data_bytes)] = data_bytes
        self.pages[page_id] = page

        # Create WAL entry
        entry = WALEntry(
            page_id=page_id,
            offset=offset,
            old_bytes=bytes(4096),
            new_bytes=bytes(page),
            storage_engine_version=self.engine_version
        )
        self.wal.append(entry)
        return entry

    def apply_wal_entry(self, entry: WALEntry) -> Tuple[bool, str]:
        """
        Apply a WAL entry from the leader.
        FAILS if storage engine version doesn't match!
        """
        if entry.storage_engine_version != self.engine_version:
            return False, (
                f"Version mismatch! Entry={entry.storage_engine_version}, "
                f"Node={self.engine_version}"
            )

        self.pages[entry.page_id] = bytearray(entry.new_bytes)
        return True, "Applied successfully"


def demo_wal_shipping():
    """
    Demonstrate WAL shipping — and its tight coupling problem.

    DDIA: "The main disadvantage is that the log describes the data on a
    very low level: a WAL contains details of which bytes were changed
    in which disk blocks. This makes replication closely coupled to the
    storage engine."
    """
    print_section("2️⃣  WRITE-AHEAD LOG (WAL) SHIPPING")
    print("""
    The leader ships its raw WAL (byte-level changes) to followers.
    Followers replay the exact same bytes.

    Advantage: Byte-for-byte identical, no ambiguity.
    Problem: Tightly coupled to storage engine version!
    """)

    # Case 1: Same version — works fine
    print("  Case 1: Same storage engine version")
    print("  " + "─" * 50)

    leader = WALBasedNode("LEADER", engine_version="PostgreSQL-15.4")
    follower = WALBasedNode("FOLLOWER", engine_version="PostgreSQL-15.4")

    entry = leader.write({"id": 1, "name": "Alice"})
    success, msg = follower.apply_wal_entry(entry)
    print(f"  Leader (PostgreSQL-15.4) writes: {{id: 1, name: 'Alice'}}")
    print(f"  Follower (PostgreSQL-15.4) applies: {msg} {'✅' if success else '❌'}")

    # Case 2: Different version — FAILS
    print(f"\n  Case 2: Different storage engine version (rolling upgrade)")
    print("  " + "─" * 50)

    new_follower = WALBasedNode("NEW-FOLLOWER", engine_version="PostgreSQL-16.1")
    entry = leader.write({"id": 2, "name": "Bob"})
    success, msg = new_follower.apply_wal_entry(entry)
    print(f"  Leader (PostgreSQL-15.4) writes: {{id: 2, name: 'Bob'}}")
    print(f"  Follower (PostgreSQL-16.1) applies: {msg} {'✅' if success else '❌'}")

    # Case 3: Cross-system replication — IMPOSSIBLE
    print(f"\n  Case 3: Replication to different database system")
    print("  " + "─" * 50)

    mysql_follower = WALBasedNode("MYSQL-REPLICA", engine_version="MySQL-8.0")
    success, msg = mysql_follower.apply_wal_entry(entry)
    print(f"  Leader (PostgreSQL-15.4) writes: {{id: 2, name: 'Bob'}}")
    print(f"  MySQL replica: {msg} {'✅' if success else '❌'}")

    print("""
  💡 VERDICT (DDIA):
     WAL shipping gives exact byte-for-byte replication but:
     • Can't run different DB versions (no rolling upgrades)
     • Can't replicate to different database systems
     • Storage engine format changes break replication

     Used by: PostgreSQL (streaming replication), Oracle
     Trade-off: Simplicity/exactness vs. flexibility
    """)


# =============================================================================
# LOGICAL (ROW-BASED) REPLICATION
# =============================================================================

class LogicalLogEntry:
    """
    A logical replication log entry — row-level changes.
    Decoupled from storage engine format.
    """

    def __init__(self, lsn: int, operation: str, table: str,
                 old_row: Optional[Dict] = None, new_row: Optional[Dict] = None):
        self.lsn = lsn
        self.operation = operation
        self.table = table
        self.old_row = old_row
        self.new_row = new_row
        self.timestamp = time.time()

    def to_json(self) -> str:
        """Serialize to JSON — can be sent over network, stored, etc."""
        return json.dumps({
            "lsn": self.lsn,
            "op": self.operation,
            "table": self.table,
            "old": self.old_row,
            "new": self.new_row,
            "ts": self.timestamp
        }, indent=2)

    def __repr__(self):
        if self.operation == "INSERT":
            return f"[LSN={self.lsn}] INSERT {self.table} → {self.new_row}"
        elif self.operation == "UPDATE":
            changed = {k: v for k, v in self.new_row.items()
                       if self.old_row.get(k) != v} if self.old_row and self.new_row else {}
            return f"[LSN={self.lsn}] UPDATE {self.table} key={self.new_row.get('id')} changed={changed}"
        elif self.operation == "DELETE":
            return f"[LSN={self.lsn}] DELETE {self.table} key={self.old_row.get('id')}"
        return f"[LSN={self.lsn}] {self.operation}"


class LogicalReplicationNode:
    """
    A node using logical (row-based) replication.

    DDIA: "A logical log for a relational database is usually a sequence
    of records describing writes to database tables at the granularity
    of a row."
    """

    def __init__(self, name: str, db_system: str = "MySQL-8.0"):
        self.name = name
        self.db_system = db_system
        self.storage: Dict[str, Dict[int, Dict]] = {}
        self.log: List[LogicalLogEntry] = []
        self._next_lsn = 1

    def write(self, operation: str, table: str, data: Dict[str, Any]) -> LogicalLogEntry:
        """Write data and create a logical log entry."""
        if table not in self.storage:
            self.storage[table] = {}

        old_row = None
        new_row = None
        row_id = data.get("id")

        if operation == "INSERT":
            new_row = data.copy()
            self.storage[table][row_id] = data.copy()
        elif operation == "UPDATE":
            old_row = self.storage[table].get(row_id, {}).copy()
            self.storage[table][row_id].update(data)
            new_row = self.storage[table][row_id].copy()
        elif operation == "DELETE":
            old_row = self.storage[table].pop(row_id, {}).copy()

        entry = LogicalLogEntry(self._next_lsn, operation, table, old_row, new_row)
        self.log.append(entry)
        self._next_lsn += 1
        return entry

    def apply_logical_entry(self, entry: LogicalLogEntry) -> Tuple[bool, str]:
        """
        Apply a logical log entry — works regardless of storage engine!
        This is the key advantage of logical replication.
        """
        table = entry.table
        if table not in self.storage:
            self.storage[table] = {}

        if entry.operation == "INSERT":
            row_id = entry.new_row["id"]
            self.storage[table][row_id] = entry.new_row.copy()
        elif entry.operation == "UPDATE":
            row_id = entry.new_row["id"]
            if row_id in self.storage[table]:
                self.storage[table][row_id].update(entry.new_row)
            else:
                self.storage[table][row_id] = entry.new_row.copy()
        elif entry.operation == "DELETE":
            row_id = entry.old_row["id"]
            self.storage[table].pop(row_id, None)

        return True, f"Applied on {self.db_system}"


def demo_logical_replication():
    """
    Demonstrate logical (row-based) replication — the modern standard.

    DDIA: "Since a logical log is decoupled from the storage engine internals,
    it can more easily be kept backward compatible."
    """
    print_section("3️⃣  LOGICAL (ROW-BASED) REPLICATION ⭐")
    print("""
    The leader logs ROW-LEVEL changes (not SQL, not bytes).
    This is decoupled from the storage engine format.

    Advantages:
    • Deterministic (no NOW()/RAND() problems)
    • Works across database versions
    • Works across different database systems!
    • Enables Change Data Capture (CDC)
    """)

    # Create leader
    leader = LogicalReplicationNode("LEADER", "MySQL-8.0")

    # Write data — notice how NOW() is resolved by the leader
    print("  Writing data on leader (MySQL 8.0):")
    print("  " + "─" * 50)

    e1 = leader.write("INSERT", "users", {"id": 1, "name": "Alice", "email": "alice@example.com"})
    print(f"  {e1}")

    e2 = leader.write("INSERT", "users", {"id": 2, "name": "Bob", "email": "bob@example.com"})
    print(f"  {e2}")

    e3 = leader.write("UPDATE", "users", {"id": 1, "name": "Alice", "email": "alice@newdomain.com"})
    print(f"  {e3}")

    e4 = leader.write("DELETE", "users", {"id": 2})
    print(f"  {e4}")

    # Show the log format
    print(f"\n  Logical log entry (JSON format):")
    print("  " + "─" * 50)
    for line in e1.to_json().split("\n"):
        print(f"  {line}")

    # Replicate to different systems — ALL WORK!
    print(f"\n  Replicating to different database systems:")
    print("  " + "─" * 50)

    replicas = [
        LogicalReplicationNode("REPLICA-1", "MySQL-8.0"),      # Same DB
        LogicalReplicationNode("REPLICA-2", "MySQL-5.7"),      # Older version
        LogicalReplicationNode("REPLICA-3", "PostgreSQL-16"),   # Different DB!
        LogicalReplicationNode("REPLICA-4", "Elasticsearch-8"), # Search engine!
    ]

    for entry in leader.log:
        for replica in replicas:
            success, msg = replica.apply_logical_entry(entry)

    for replica in replicas:
        data = replica.storage.get("users", {})
        data_summary = {k: v.get("name", "?") for k, v in data.items()}
        print(f"  [{replica.db_system:>18}] Rows: {len(data)}  Data: {data_summary}  ✅")

    # Verify all consistent
    leader_data = leader.storage.get("users", {})
    all_match = all(r.storage.get("users", {}) == leader_data for r in replicas)
    print(f"\n  All replicas consistent with leader: {'YES ✅' if all_match else 'NO ❌'}")

    print("""
  💡 VERDICT (DDIA):
     Logical replication is the BEST approach because:
     • Row-level changes are deterministic (leader resolves NOW(), RAND())
     • Decoupled from storage engine → rolling upgrades work
     • Cross-system replication → sync MySQL to Elasticsearch
     • Enables CDC (Change Data Capture) → stream changes to Kafka, etc.

     Used by: MySQL (binlog row format, default since 5.7),
              MongoDB (change streams), PostgreSQL (logical decoding)
    """)


# =============================================================================
# COMPARISON SUMMARY
# =============================================================================

def demo_comparison():
    """Print a side-by-side comparison of all three methods."""
    print_section("📊 COMPARISON: All Three Methods")

    print("""
  ┌──────────────────────┬──────────────┬──────────────┬──────────────────┐
  │ Aspect               │ Statement    │ WAL Shipping │ Logical (Row)    │
  ├──────────────────────┼──────────────┼──────────────┼──────────────────┤
  │ What's shipped       │ SQL text     │ Raw bytes    │ Row changes      │
  │ Deterministic?       │ ❌ No        │ ✅ Yes       │ ✅ Yes           │
  │ Cross-version?       │ ✅ Yes       │ ❌ No        │ ✅ Yes           │
  │ Cross-system?        │ ⚠️  Partial  │ ❌ No        │ ✅ Yes           │
  │ CDC support?         │ ❌ No        │ ❌ No        │ ✅ Yes           │
  │ Storage overhead     │ Low          │ High         │ Medium           │
  │ Rolling upgrades?    │ ✅ Yes       │ ❌ No        │ ✅ Yes           │
  │ Status               │ ❌ Abandoned │ ⚠️  Limited  │ ✅ Standard      │
  ├──────────────────────┼──────────────┼──────────────┼──────────────────┤
  │ Used by              │ MySQL <5.1   │ PostgreSQL   │ MySQL >=5.7      │
  │                      │              │ Oracle       │ MongoDB          │
  │                      │              │              │ Most modern DBs  │
  └──────────────────────┴──────────────┴──────────────┴──────────────────┘
    """)


# =============================================================================
# UTILITIES
# =============================================================================

def print_section(title: str):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("  EXERCISE 2: REPLICATION LOG MECHANISMS")
    print("  DDIA Chapter 5: 'Implementation of Replication Logs'")
    print("=" * 80)
    print("""
  This exercise demonstrates the THREE ways data moves between nodes.
  You'll see why two methods are broken/limited,
  and why logical replication is the modern standard.
    """)

    demo_statement_based()
    demo_wal_shipping()
    demo_logical_replication()
    demo_comparison()

    print("\n" + "=" * 80)
    print("  EXERCISE 2 COMPLETE ✅")
    print("=" * 80)
    print("""
  Key Takeaways:

  1. ❌ Statement-based: Breaks with NOW(), RAND(), auto-increment order
  2. ⚠️  WAL shipping: Exact bytes, but can't upgrade or cross-replicate
  3. ✅ Logical (row-based): Deterministic, cross-version, cross-system, CDC

  The evolution: Statement → WAL → Logical (industry moved forward)

  Next: Run 03_sync_vs_async.py to learn about the sync/async trade-off
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
