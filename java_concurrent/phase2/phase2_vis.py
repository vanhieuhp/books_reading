"""
Phase 2 Deep Dive — Synchronization
Visualizations:
  1. Happens-Before Guarantees (synchronization ordering)
  2. Deadlock vs. Consistent Lock Ordering
  3. Producer-Consumer with wait/notify

Run: python phase2_vis.py
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch
import numpy as np

OUT = "e:/Workspaces/Myself/Projects/books_reading/java_concurrent/"

# ─────────────────────────────────────────────────────────────────────────────
# VISUAL 1 — Happens-Before Guarantees (JMM ordering)
# ─────────────────────────────────────────────────────────────────────────────

fig, ax = plt.subplots(figsize=(15, 9))
ax.set_xlim(0, 15); ax.set_ylim(0, 9)
ax.axis('off')
fig.patch.set_facecolor('#0D1117')
ax.set_facecolor('#0D1117')

ax.text(7.5, 8.5, "Java Memory Model: Happens-Before Guarantees",
        ha='center', va='center', fontsize=15, fontweight='bold', color='#F0F0F0')
ax.text(7.5, 8.05, "If action A happens-before B, A's writes are guaranteed visible to B's reads",
        ha='center', va='center', fontsize=9, color='#AAAAAA')

# ---- Rule boxes ----
rules = [
    ("Thread.start()", 1.5, 6.0,
     "All actions in thread T\nhappen-before any action in T\nafter thread.start()",
     "#27AE60"),
    ("Monitor Lock\n(unlock → lock)", 1.5, 3.5,
     "Unlock of monitor M\nhappens-before subsequent\nlock on same monitor M",
     "#2980B9"),
    ("volatile Write\n→ Read", 7.5, 6.0,
     "Write to volatile v\nhappens-before every subsequent\nread of volatile v",
     "#E67E22"),
    ("Thread.join()", 7.5, 3.5,
     "All actions in thread T\nhappen-before any thread\nafter T.join() returns",
     "#8E44AD"),
    ("CountDownLatch", 13.5, 6.0,
     "countDown() HB await()\n(used in payment: wait for\nfraud + balance + KYC)",
     "#C0392B"),
    ("Compound Actions", 13.5, 3.5,
     "volatile is NOT enough\nfor ++ or check-then-act\n→ Use AtomicInteger",
     "#7F8C8D"),
]

for label, x, y, text, color in rules:
    box = mpatches.FancyBboxPatch((x - 1.4, y - 1.1), 2.8, 2.2,
        boxstyle="round,pad=0.1",
        facecolor=color, edgecolor='white', linewidth=1.5, alpha=0.9)
    ax.add_patch(box)
    ax.text(x, y + 0.6, label, ha='center', va='center',
            fontsize=9.5, fontweight='bold', color='white')
    ax.text(x, y - 0.2, text, ha='center', va='center',
            fontsize=7, color='#EEEEEE', style='italic')

# Arrows between related rules
arrow_cfg = dict(arrowstyle='<->', color='#F39C12', lw=1.5)
# start → volatile write
ax.annotate('', xy=(3.0, 6.0), xytext=(1.5, 6.0),
            arrowprops=arrow_cfg)
ax.text(2.25, 6.35, "HB", fontsize=7, color='#F39C12', ha='center')
# start → monitor unlock
ax.annotate('', xy=(2.85, 3.5), xytext=(2.85, 5.0),
            arrowprops=dict(arrowstyle='->', color='#AAAAAA', lw=1.2))
ax.text(2.3, 4.3, "implied\nHB chain", fontsize=7, color='#AAAAAA', ha='center')
# volatile → join (through program order)
ax.annotate('', xy=(7.5, 5.1), xytext=(7.5, 4.5),
            arrowprops=dict(arrowstyle='->', color='#AAAAAA', lw=1.2))
# join → latch
ax.annotate('', xy=(12.1, 5.7), xytext=(10.3, 6.0),
            arrowprops=arrow_cfg)
ax.text(11.2, 6.3, "HB", fontsize=7, color='#F39C12', ha='center')

# Key insight box
ax.add_patch(mpatches.FancyBboxPatch((3.5, 1.2), 8.0, 1.3,
    boxstyle="round,pad=0.15",
    facecolor='#1C2833', edgecolor='#E67E22', linewidth=2))
ax.text(7.5, 2.0,
        "Key: Without a happens-before link, the JVM/CPU may reorder operations freely.\n"
        "A write in Thread A may never be visible to Thread B — even if A finishes first.",
        ha='center', va='center', fontsize=8.5, color='#EEEEEE')

plt.tight_layout(pad=1)
plt.savefig(OUT + "happens_before.png", dpi=160, bbox_inches='tight', facecolor='#0D1117')
plt.close()
print("[OK] happens_before.png saved")


# ─────────────────────────────────────────────────────────────────────────────
# VISUAL 2 — Deadlock vs. Consistent Lock Ordering
# ─────────────────────────────────────────────────────────────────────────────

fig, axes = plt.subplots(1, 2, figsize=(16, 7))
fig.patch.set_facecolor('#FDF6E3')
for ax2 in axes:
    ax2.set_xlim(0, 14); ax2.set_ylim(0, 8)
    ax2.axis('off')
    ax2.set_facecolor('#FDF6E3')

# --- LEFT: Deadlock ---
ax = axes[0]
ax.text(7, 7.4, "DEADLOCK — Lock in Different Orders",
        ha='center', va='center', fontsize=12, fontweight='bold', color='#C0392B')

# Thread A box
ax.add_patch(mpatches.FancyBboxPatch((0.5, 3.0), 4.0, 3.5,
    boxstyle="round,pad=0.1", facecolor='#3498DB', edgecolor='#1A5276', linewidth=1.5))
ax.text(2.5, 6.1, "Thread A\ntransfer(A→B)",
        ha='center', va='center', fontsize=10, fontweight='bold', color='white')

# Thread B box
ax.add_patch(mpatches.FancyBboxPatch((9.5, 3.0), 4.0, 3.5,
    boxstyle="round,pad=0.1", facecolor='#E74C3C', edgecolor='#922B21', linewidth=1.5))
ax.text(11.5, 6.1, "Thread B\ntransfer(B→A)",
        ha='center', va='center', fontsize=10, fontweight='bold', color='white')

# Account A and B
ax.add_patch(mpatches.FancyBboxPatch((5.5, 5.0), 3.0, 1.5,
    boxstyle="round,pad=0.1", facecolor='#27AE60', edgecolor='#1A5276', linewidth=2))
ax.text(7, 5.75, "Account A", ha='center', va='center', fontsize=9, fontweight='bold', color='white')
ax.text(7, 5.4, "Lock: Acquired", ha='center', va='center', fontsize=8, color='#ABEB78')

ax.add_patch(mpatches.FancyBboxPatch((5.5, 2.0), 3.0, 1.5,
    boxstyle="round,pad=0.1", facecolor='#27AE60', edgecolor='#1A5276', linewidth=2))
ax.text(7, 2.75, "Account B", ha='center', va='center', fontsize=9, fontweight='bold', color='white')
ax.text(7, 2.4, "Lock: Acquired", ha='center', va='center', fontsize=8, color='#ABEB78')

# A → holds A lock, waits for B
ax.annotate('', xy=(5.5, 5.75), xytext=(4.5, 5.75),
    arrowprops=dict(arrowstyle='->', color='#2ECC71', lw=2.5))
ax.text(3.5, 6.0, "A: lock(A) OK", ha='center', va='center', fontsize=8, color='#27AE60')
ax.annotate('', xy=(8.5, 2.75), xytext=(8.5, 5.0),
    arrowprops=dict(arrowstyle='->', color='#E74C3C', lw=2.0,
                    connectionstyle='arc3,rad=-0.3'))
ax.text(9.5, 3.7, "A: try lock(B)\nBLOCKED!", ha='center', va='center',
        fontsize=8, color='#E74C3C', fontweight='bold')

# B → holds B lock, waits for A
ax.annotate('', xy=(8.5, 2.75), xytext=(9.5, 2.75),
    arrowprops=dict(arrowstyle='->', color='#2ECC71', lw=2.5))
ax.text(10.2, 2.95, "B: lock(B) OK", ha='center', va='center', fontsize=8, color='#27AE60')
ax.annotate('', xy=(5.5, 5.75), xytext=(5.5, 3.5),
    arrowprops=dict(arrowstyle='->', color='#E74C3C', lw=2.0,
                    connectionstyle='arc3,rad=-0.3'))
ax.text(4.0, 3.7, "B: try lock(A)\nBLOCKED!", ha='center', va='center',
        fontsize=8, color='#E74C3C', fontweight='bold')

# Cycle annotation
ax.annotate('', xy=(7.8, 1.5), xytext=(7.8, 7.2),
    arrowprops=dict(arrowstyle='->', color='#E74C3C', lw=1.5,
                    connectionstyle='arc3,rad=0.0'))
ax.text(7.9, 4.3, "CYCLE:\nA waits B\nB waits A",
        ha='left', va='center', fontsize=8, color='#C0392B', fontweight='bold')

# --- RIGHT: Fixed ---
ax = axes[1]
ax.text(7, 7.4, "FIXED — Consistent Lock Ordering (Low-ID First)",
        ha='center', va='center', fontsize=12, fontweight='bold', color='#27AE60')

ax.add_patch(mpatches.FancyBboxPatch((0.5, 3.0), 4.0, 3.5,
    boxstyle="round,pad=0.1", facecolor='#3498DB', edgecolor='#1A5276', linewidth=1.5))
ax.text(2.5, 6.1, "Thread A\ntransfer(A→B)",
        ha='center', va='center', fontsize=10, fontweight='bold', color='white')

ax.add_patch(mpatches.FancyBboxPatch((9.5, 3.0), 4.0, 3.5,
    boxstyle="round,pad=0.1", facecolor='#E74C3C', edgecolor='#922B21', linewidth=1.5))
ax.text(11.5, 6.1, "Thread B\ntransfer(B→A)",
        ha='center', va='center', fontsize=10, fontweight='bold', color='white')

ax.add_patch(mpatches.FancyBboxPatch((5.5, 5.0), 3.0, 1.5,
    boxstyle="round,pad=0.1", facecolor='#27AE60', edgecolor='#1A5276', linewidth=2))
ax.text(7, 5.75, "Account A (ID=1)", ha='center', va='center', fontsize=9, fontweight='bold', color='white')
ax.text(7, 5.4, "Lock: Acquired 1st", ha='center', va='center', fontsize=8, color='#ABEB78')

ax.add_patch(mpatches.FancyBboxPatch((5.5, 2.0), 3.0, 1.5,
    boxstyle="round,pad=0.1", facecolor='#27AE60', edgecolor='#1A5276', linewidth=2))
ax.text(7, 2.75, "Account B (ID=2)", ha='center', va='center', fontsize=9, fontweight='bold', color='white')
ax.text(7, 2.4, "Lock: Acquired 2nd", ha='center', va='center', fontsize=8, color='#ABEB78')

# Both threads lock A first
ax.annotate('', xy=(5.5, 5.75), xytext=(4.5, 5.75),
    arrowprops=dict(arrowstyle='->', color='#2ECC71', lw=2.5))
ax.text(3.2, 6.0, "A: lock(A) 1st", ha='center', va='center', fontsize=8, color='#27AE60')

ax.annotate('', xy=(8.5, 2.75), xytext=(9.5, 2.75),
    arrowprops=dict(arrowstyle='->', color='#2ECC71', lw=2.5))
ax.text(10.2, 2.95, "B: lock(A) 1st", ha='center', va='center', fontsize=8, color='#27AE60')

# B must wait for A to release A before it can proceed
ax.annotate('', xy=(8.5, 5.75), xytext=(8.5, 3.5),
    arrowprops=dict(arrowstyle='->', color='#F39C12', lw=2.0))
ax.text(9.5, 4.4, "B waits here\nfor A to\nrelease A lock", ha='center', va='center',
        fontsize=8, color='#E67E22', fontweight='bold')

# B then proceeds to lock B
ax.annotate('', xy=(8.5, 2.75), xytext=(8.5, 5.0),
    arrowprops=dict(arrowstyle='->', color='#2ECC71', lw=2.0,
                    connectionstyle='arc3,rad=-0.3'))
ax.text(9.5, 4.0, "A: lock(B) 2nd", ha='center', va='center',
        fontsize=8, color='#27AE60')
ax.text(9.5, 3.65, "(done, unlocks)", ha='center', va='center',
        fontsize=7, color='#888888')

ax.text(4.0, 1.2,
        "Both threads acquire lock(A) first → B serializes behind A\n→ No cycle → No deadlock",
        ha='center', va='center', fontsize=9, color='#27AE60', fontweight='bold')

plt.tight_layout(pad=1)
plt.savefig(OUT + "deadlock_vs_fix.png", dpi=160, bbox_inches='tight', facecolor='#FDF6E3')
plt.close()
print("[OK] deadlock_vs_fix.png saved")


# ─────────────────────────────────────────────────────────────────────────────
# VISUAL 3 — Producer-Consumer with wait/notify
# ─────────────────────────────────────────────────────────────────────────────

fig, ax = plt.subplots(figsize=(15, 8))
ax.set_xlim(0, 15); ax.set_ylim(0, 8)
ax.axis('off')
fig.patch.set_facecolor('#0D1117')
ax.set_facecolor('#0D1117')

ax.text(7.5, 7.5, "Producer-Consumer: wait()/notifyAll() State Machine",
        ha='center', va='center', fontsize=14, fontweight='bold', color='#F0F0F0')

# Queue box
ax.add_patch(mpatches.FancyBboxPatch((5.5, 2.8), 4.0, 2.2,
    boxstyle="round,pad=0.1",
    facecolor='#1C2833', edgecolor='#2980B9', linewidth=2.5))
ax.text(7.5, 4.5, "TransactionQueue (capacity=5)",
        ha='center', va='center', fontsize=9.5, fontweight='bold', color='#3498DB')
ax.text(7.5, 4.0, "size = N  (0 ≤ N ≤ 5)",
        ha='center', va='center', fontsize=8, color='#AAAAAA')
ax.text(7.5, 3.5, "enqueue() / dequeue()",
        ha='center', va='center', fontsize=8, color='#AAAAAA')

# Producer
ax.add_patch(mpatches.FancyBboxPatch((0.5, 3.2), 4.0, 3.0,
    boxstyle="round,pad=0.1",
    facecolor='#27AE60', edgecolor='#1E8449', linewidth=1.5, alpha=0.9))
ax.text(2.5, 5.8, "PRODUCER", ha='center', va='center',
        fontsize=10, fontweight='bold', color='white')
ax.text(2.5, 5.3, "(Payment Intake)", ha='center', va='center',
        fontsize=8, color='#ABEB78', style='italic')

prod_steps = [
    (0.7, 4.7, "enqueue(txn):"),
    (0.7, 4.2, "  while(size == capacity)"),
    (0.7, 3.8, "    wait(); // sleep"),
    (0.7, 3.3, "  queue.add(txn)"),
    (0.7, 2.85, "  notifyAll()"),
]
for x, y, txt in prod_steps:
    ax.text(x, y, txt, fontsize=7.5, color='#F0F0F0', fontfamily='monospace')

# Consumer
ax.add_patch(mpatches.FancyBboxPatch((10.5, 3.2), 4.0, 3.0,
    boxstyle="round,pad=0.1",
    facecolor='#E67E22', edgecolor='#B7770D', linewidth=1.5, alpha=0.9))
ax.text(12.5, 5.8, "CONSUMER", ha='center', va='center',
        fontsize=10, fontweight='bold', color='white')
ax.text(12.5, 5.3, "(Processor)", ha='center', va='center',
        fontsize=8, color='#FDEBD0', style='italic')

cons_steps = [
    (10.7, 4.7, "dequeue():"),
    (10.7, 4.2, "  while(size == 0)"),
    (10.7, 3.8, "    wait(); // sleep"),
    (10.7, 3.3, "  notifyAll()"),
    (10.7, 2.85, "  return queue.poll()"),
]
for x, y, txt in cons_steps:
    ax.text(x, y, txt, fontsize=7.5, color='#F0F0F0', fontfamily='monospace')

# Arrows
ax.annotate('', xy=(5.5, 4.0), xytext=(4.5, 4.0),
    arrowprops=dict(arrowstyle='->', color='#27AE60', lw=2))
ax.text(5.0, 4.3, "enqueue()", fontsize=8, color='#27AE60', ha='center')

ax.annotate('', xy=(10.5, 3.5), xytext=(9.5, 3.5),
    arrowprops=dict(arrowstyle='<-', color='#E67E22', lw=2))
ax.text(10.0, 3.2, "dequeue()", fontsize=8, color='#E67E22', ha='center')

# notifyAll arrows
ax.annotate('', xy=(7.5, 5.0), xytext=(4.5, 5.5),
    arrowprops=dict(arrowstyle='->', color='#F39C12', lw=1.5,
                    connectionstyle='arc3,rad=0.2'))
ax.text(5.5, 5.7, "notifyAll()", fontsize=7, color='#F39C12', ha='center')

ax.annotate('', xy=(7.5, 5.0), xytext=(9.5, 5.5),
    arrowprops=dict(arrowstyle='->', color='#F39C12', lw=1.5,
                    connectionstyle='arc3,rad=-0.2'))
ax.text(9.0, 5.7, "notifyAll()", fontsize=7, color='#F39C12', ha='center')

# Key rule box
ax.add_patch(mpatches.FancyBboxPatch((2.5, 0.4), 10.0, 1.4,
    boxstyle="round,pad=0.15",
    facecolor='#1C2833', edgecolor='#E67E22', linewidth=2))
ax.text(7.5, 1.4,
        "RULE: Always use while(size == LIMIT), never if()!\n"
        "Reason: Spurious wakeups — thread may wake without being notified.\n"
        "        while() re-checks; if() would act on stale state.",
        ha='center', va='center', fontsize=8.5, color='#EEEEEE')

plt.tight_layout(pad=1)
plt.savefig(OUT + "producer_consumer.png", dpi=160, bbox_inches='tight', facecolor='#0D1117')
plt.close()
print("[OK] producer_consumer.png saved")
