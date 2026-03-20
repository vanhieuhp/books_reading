"""
Phase 3 Deep Dive — java.util.concurrent
Visualizations:
  1. ExecutorService + Thread Pool architecture
  2. Sync Utilities: CountDownLatch, Semaphore, CyclicBarrier
  3. Concurrent Collections comparison

Run: python phase3_vis.py
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

OUT = "e:/Workspaces/Myself/Projects/books_reading/java_concurrent/phase3/"

# ─────────────────────────────────────────────────────────────────────────────
# VISUAL 1 — ExecutorService / Thread Pool Architecture
# ─────────────────────────────────────────────────────────────────────────────

fig, ax = plt.subplots(figsize=(15, 9))
ax.set_xlim(0, 15); ax.set_ylim(0, 9)
ax.axis('off')
fig.patch.set_facecolor('#0D1117')
ax.set_facecolor('#0D1117')

ax.text(7.5, 8.5, "ExecutorService: Thread Pool Architecture",
        ha='center', va='center', fontsize=15, fontweight='bold', color='#F0F0F0')
ax.text(7.5, 8.0, "Instead of new Thread() per task — reuse a bounded pool of threads",
        ha='center', va='center', fontsize=9, color='#AAAAAA')

# Incoming tasks
tasks = [
    (0.5, 5.5, "Payment #1"),
    (0.5, 4.5, "Payment #2"),
    (0.5, 3.5, "Payment #3"),
    (0.5, 2.5, "Payment #N ..."),
]
for x, y, label in tasks:
    ax.add_patch(mpatches.FancyBboxPatch((x, y - 0.25), 2.0, 0.5,
        boxstyle="round,pad=0.05",
        facecolor='#3498DB', edgecolor='#1A5276', linewidth=1.5))
    ax.text(x + 1.0, y, label, ha='center', va='center',
            fontsize=7.5, fontweight='bold', color='white')

# Arrow to queue
for x, y, _ in tasks:
    ax.annotate('', xy=(3.5, 4.0), xytext=(x + 2.0, y),
        arrowprops=dict(arrowstyle='->', color='#3498DB', lw=1.5,
                        connectionstyle='arc3,rad=-0.2'))

# Task queue
ax.add_patch(mpatches.FancyBboxPatch((3.5, 2.2), 3.5, 3.8,
    boxstyle="round,pad=0.1",
    facecolor='#1C2833', edgecolor='#2980B9', linewidth=2))
ax.text(5.25, 5.6, "Task Queue", ha='center', va='center',
        fontsize=11, fontweight='bold', color='#3498DB')
ax.text(5.25, 5.15, "(LinkedBlockingQueue)", ha='center', va='center',
        fontsize=8, color='#AAAAAA')
ax.text(5.25, 4.65, "submit(Runnable/Callable)", ha='center', va='center',
        fontsize=7.5, color='#EEEEEE')
ax.text(5.25, 4.2, "No task limit — queue absorbs", ha='center', va='center',
        fontsize=7, color='#AAAAAA', style='italic')
ax.text(5.25, 3.7, "bursts; bounded pool reuses", ha='center', va='center',
        fontsize=7, color='#AAAAAA', style='italic')
ax.text(5.25, 3.2, "threads instead of creating", ha='center', va='center',
        fontsize=7, color='#AAAAAA', style='italic')
ax.text(5.25, 2.7, "new ones per task", ha='center', va='center',
        fontsize=7, color='#AAAAAA', style='italic')

# Thread pool (3 workers)
pool_label_y = 6.5
ax.add_patch(mpatches.FancyBboxPatch((8.0, 2.2), 5.5, 5.5,
    boxstyle="round,pad=0.1",
    facecolor='#1C2833', edgecolor='#27AE60', linewidth=2))
ax.text(10.75, 7.35, "Thread Pool (n = core size)", ha='center', va='center',
        fontsize=11, fontweight='bold', color='#27AE60')

thread_colors = ['#3498DB', '#E67E22', '#9B59B6']
thread_labels = ['Worker-1', 'Worker-2', 'Worker-3']
for i, (col, lbl) in enumerate(zip(thread_colors, thread_labels)):
    tx, ty = 8.3 + i * 1.75, 6.5
    ax.add_patch(mpatches.FancyBboxPatch((tx, ty - 0.25), 1.5, 0.5,
        boxstyle="round,pad=0.05",
        facecolor=col, edgecolor='white', linewidth=1.2))
    ax.text(tx + 0.75, ty, lbl, ha='center', va='center',
            fontsize=7.5, fontweight='bold', color='white')

# Run indicator
for i, (col, lbl) in enumerate(zip(thread_colors, thread_labels)):
    tx, ty = 8.3 + i * 1.75, 5.3
    ax.text(tx + 0.75, ty, "RUNNING", ha='center', va='center',
            fontsize=6.5, color='#2ECC71', fontweight='bold')

# Idle state
idle_y = 4.8
ax.add_patch(mpatches.FancyBboxPatch((8.3, idle_y - 0.25), 1.5, 0.5,
    boxstyle="round,pad=0.05",
    facecolor='#7F8C8D', edgecolor='white', linewidth=1.2))
ax.text(9.05, idle_y, "Worker-1", ha='center', va='center',
        fontsize=7.5, fontweight='bold', color='white')
ax.text(9.05, idle_y - 0.6, "IDLE (waiting)", ha='center', va='center',
        fontsize=6.5, color='#AAAAAA', style='italic')

# Arrow queue → pool
ax.annotate('', xy=(8.0, 4.0), xytext=(7.0, 4.0),
    arrowprops=dict(arrowstyle='->', color='#27AE60', lw=2.5))

# Results
ax.add_patch(mpatches.FancyBboxPatch((14.0, 3.5), 0.8, 1.5,
    boxstyle="round,pad=0.1",
    facecolor='#27AE60', edgecolor='white', linewidth=1.5))
ax.text(14.4, 4.25, "Future<V>\nor\nResult", ha='center', va='center',
        fontsize=7, color='white', fontweight='bold')

# Result arrow
ax.annotate('', xy=(14.0, 4.25), xytext=(13.5, 4.25),
    arrowprops=dict(arrowstyle='->', color='#2ECC71', lw=2))
ax.text(14.4, 2.5, "get()\nblocking\nread", ha='center', va='center',
        fontsize=6.5, color='#AAAAAA')

# Legend / key facts
facts = [
    ("FixedThreadPool", "n threads, unbounded queue — good for CPU-bound", '#2980B9'),
    ("CachedThreadPool", "0..Integer.MAX_VALUE threads — good for short I/O tasks", '#E67E22'),
    ("SingleThreaded", "1 thread, queue — FIFO with restart on exception", '#9B59B6'),
    ("ScheduledThreadPool", "delayed / periodic tasks", '#7F8C8D'),
]
fy = 1.9
for fname, fdesc, fc in facts:
    ax.add_patch(mpatches.FancyBboxPatch((0.5, fy - 0.2), 14.0, 0.35,
        boxstyle="round,pad=0.05",
        facecolor='#1C2833', edgecolor=fc, linewidth=1.5, alpha=0.9))
    ax.text(0.7, fy, fname, ha='left', va='center',
            fontsize=7.5, fontweight='bold', color=fc)
    ax.text(3.8, fy, fdesc, ha='left', va='center',
            fontsize=7, color='#AAAAAA')
    fy -= 0.45

plt.tight_layout(pad=1)
plt.savefig(OUT + "executor_service.png", dpi=160, bbox_inches='tight', facecolor='#0D1117')
plt.close()
print("[OK] executor_service.png saved")


# ─────────────────────────────────────────────────────────────────────────────
# VISUAL 2 — CountDownLatch, Semaphore, CyclicBarrier
# ─────────────────────────────────────────────────────────────────────────────

fig, axes = plt.subplots(1, 3, figsize=(16, 7))
fig.patch.set_facecolor('#FDF6E3')
for ax2 in axes:
    ax2.set_xlim(0, 12); ax2.set_ylim(0, 8)
    ax2.axis('off')
    ax2.set_facecolor('#FDF6E3')

# ─── Panel 1: CountDownLatch ───
ax = axes[0]
ax.text(6, 7.5, "CountDownLatch", ha='center', va='center',
        fontsize=13, fontweight='bold', color='#2980B9')
ax.text(6, 7.0, "(One-shot: countdown to 0)", ha='center', va='center',
        fontsize=9, color='#555555')

# Latch counter
ax.add_patch(mpatches.FancyBboxPatch((4.5, 5.2), 3.0, 1.0,
    boxstyle="round,pad=0.1",
    facecolor='#2980B9', edgecolor='#1A5276', linewidth=2))
ax.text(6.0, 5.7, "count = 3", ha='center', va='center',
        fontsize=11, fontweight='bold', color='white')

# Tasks
for i, lbl in enumerate(["Fraud Check", "Balance Check", "KYC Check"]):
    bx = 0.5 + i * 3.8
    ax.add_patch(mpatches.FancyBboxPatch((bx, 3.5), 3.0, 1.0,
        boxstyle="round,pad=0.1",
        facecolor='#27AE60', edgecolor='#1E8449', linewidth=1.5))
    ax.text(bx + 1.5, 4.0, lbl, ha='center', va='center',
            fontsize=8.5, fontweight='bold', color='white')
    ax.text(bx + 1.5, 3.7, "countDown()", ha='center', va='center',
            fontsize=7.5, color='#ABEB78', style='italic')
    ax.annotate('', xy=(6.0, 5.2), xytext=(bx + 1.5, 4.5),
        arrowprops=dict(arrowstyle='->', color='#27AE60', lw=1.5))

# Arrow down to main thread
ax.annotate('', xy=(6.0, 2.0), xytext=(6.0, 5.2),
    arrowprops=dict(arrowstyle='<->', color='#E67E22', lw=2))
ax.text(6.3, 3.6, "await()\n(blocks)", ha='center', va='center',
        fontsize=8, color='#E67E22', fontweight='bold')

# After all countDown
ax.add_patch(mpatches.FancyBboxPatch((4.5, 1.0), 3.0, 0.8,
    boxstyle="round,pad=0.1",
    facecolor='#E67E22', edgecolor='#B7770D', linewidth=2))
ax.text(6.0, 1.4, "UNBLOCKED!", ha='center', va='center',
        fontsize=10, fontweight='bold', color='white')

# Use case
ax.text(6, 0.3, "Payment: wait fraud+balance+KYC\nbefore authorization",
        ha='center', va='center', fontsize=7.5, color='#555555', style='italic')

# ─── Panel 2: Semaphore ───
ax = axes[1]
ax.text(6, 7.5, "Semaphore", ha='center', va='center',
        fontsize=13, fontweight='bold', color='#8E44AD')
ax.text(6, 7.0, "(Rate Limiting: permits = N)", ha='center', va='center',
        fontsize=9, color='#555555')

# Permits
ax.add_patch(mpatches.FancyBboxPatch((4.5, 5.2), 3.0, 1.0,
    boxstyle="round,pad=0.1",
    facecolor='#8E44AD', edgecolor='#6C3483', linewidth=2))
ax.text(6.0, 5.7, "permits = 3", ha='center', va='center',
        fontsize=11, fontweight='bold', color='white')

# API callers
for i, lbl in enumerate(["Payment API", "Ext. Processor", "Bank Gateway", "...more"]):
    bx = 0.5 + i * 2.8 if i < 3 else 6.5
    by = 4.5 if i < 3 else 3.5
    fc = '#27AE60' if i < 3 else '#E74C3C'
    ax.add_patch(mpatches.FancyBboxPatch((bx, by - 0.3), 2.4, 0.7,
        boxstyle="round,pad=0.05",
        facecolor=fc, edgecolor='white', linewidth=1.2))
    ax.text(bx + 1.2, by + 0.05, lbl, ha='center', va='center',
            fontsize=7.5, fontweight='bold', color='white')
    ax.annotate('', xy=(6.0, 5.2), xytext=(bx + 1.2, by + 0.4),
        arrowprops=dict(arrowstyle='->', color=fc, lw=1.5,
                        connectionstyle='arc3,rad=-0.1'))

# Acquired / Denied
ax.text(1.2, 2.5, "acquire() → permit granted\n→ call API\n→ release() → permit returned",
        ha='center', va='center', fontsize=7.5, color='#27AE60')
ax.add_patch(mpatches.FancyBboxPatch((5.0, 2.2), 3.5, 0.8,
    boxstyle="round,pad=0.1",
    facecolor='#E74C3C', edgecolor='#922B21', linewidth=1.5))
ax.text(6.75, 2.6, "Denied if 0 permits!", ha='center', va='center',
        fontsize=9, fontweight='bold', color='white')

ax.text(6, 0.3, "Max 3 concurrent calls to\npayment processor API",
        ha='center', va='center', fontsize=7.5, color='#555555', style='italic')

# ─── Panel 3: CyclicBarrier ───
ax = axes[2]
ax.text(6, 7.5, "CyclicBarrier", ha='center', va='center',
        fontsize=13, fontweight='bold', color='#C0392B')
ax.text(6, 7.0, "(Reusable: N threads wait, then all proceed)", ha='center', va='center',
        fontsize=9, color='#555555')

# Barrier counter
ax.add_patch(mpatches.FancyBboxPatch((4.5, 5.2), 3.0, 1.0,
    boxstyle="round,pad=0.1",
    facecolor='#C0392B', edgecolor='#922B21', linewidth=2))
ax.text(6.0, 5.7, "parties = 4", ha='center', va='center',
        fontsize=11, fontweight='bold', color='white')
ax.text(6.0, 5.3, "(countdown → 0 → reset)", ha='center', va='center',
        fontsize=7.5, color='#FADBD8', style='italic')

# Workers
for i in range(4):
    bx = 1.0 + i * 2.5
    ax.add_patch(mpatches.FancyBboxPatch((bx, 3.5), 2.0, 0.8,
        boxstyle="round,pad=0.05",
        facecolor='#3498DB', edgecolor='#1A5276', linewidth=1.5))
    ax.text(bx + 1.0, 3.9, f"Worker-{i+1}", ha='center', va='center',
            fontsize=8, fontweight='bold', color='white')
    ax.text(bx + 1.0, 3.65, "await()", ha='center', va='center',
            fontsize=7, color='#AED6F1', style='italic')
    ax.annotate('', xy=(6.0, 5.2), xytext=(bx + 1.0, 4.3),
        arrowprops=dict(arrowstyle='->', color='#3498DB', lw=1.5,
                        connectionstyle='arc3,rad=-0.1'))

# All proceed
ax.add_patch(mpatches.FancyBboxPatch((3.5, 1.8), 5.0, 0.8,
    boxstyle="round,pad=0.1",
    facecolor='#27AE60', edgecolor='#1E8449', linewidth=2))
ax.text(6.0, 2.2, "ALL PROCEED TOGETHER!", ha='center', va='center',
        fontsize=10, fontweight='bold', color='white')
ax.text(6.0, 2.5, "barrier.await()", ha='center', va='center',
        fontsize=7, color='#2ECC71')

ax.text(6, 0.3, "End-of-day settlement:\nall segments done → reconcile",
        ha='center', va='center', fontsize=7.5, color='#555555', style='italic')

plt.tight_layout(pad=1)
plt.savefig(OUT + "sync_utilities.png", dpi=160, bbox_inches='tight', facecolor='#FDF6E3')
plt.close()
print("[OK] sync_utilities.png saved")


# ─────────────────────────────────────────────────────────────────────────────
# VISUAL 3 — Concurrent Collections Comparison
# ─────────────────────────────────────────────────────────────────────────────

fig, ax = plt.subplots(figsize=(14, 9))
ax.set_xlim(0, 14); ax.set_ylim(0, 9)
ax.axis('off')
fig.patch.set_facecolor('#0D1117')
ax.set_facecolor('#0D1117')

ax.text(7, 8.5, "Concurrent Collections: Choosing the Right Tool",
        ha='center', va='center', fontsize=15, fontweight='bold', color='#F0F0F0')

cols = [
    ("ConcurrentHashMap", "#27AE60",
     ["High-throughput map", "Segment-level locking", "Read-heavy workloads",
      "No null keys/values!", "sessionCache, counters"]),
    ("CopyOnWriteArrayList", "#2980B9",
     ["Snapshot reads (iterates copy)", "Writes: copy entire list", "Read-heavy, rare writes",
      "No ConcurrentModificationEx", "config, subscribers"]),
    ("LinkedBlockingQueue", "#E67E22",
     ["Bounded producer-consumer", "FIFO, optional capacity", "Blocks on put/take",
      "Backpressure built-in", "transaction queues"]),
    ("ConcurrentLinkedQueue", "#8E44AD",
     ["Lock-free (CAS-based)", "Unbounded, no blocking", "Good for high concurrency",
      "No size() O(1) guarantee", "audit event queues"]),
    ("PriorityBlockingQueue", "#C0392B",
     ["Priority-ordered take()", "Unbounded by default", "Comparator determines priority",
      "High-priority txn first", "payment processing order"]),
]

header_y = 7.7
col_w = 2.7
for i, (name, color, items) in enumerate(cols):
    cx = 0.3 + i * col_w

    # Header
    ax.add_patch(mpatches.FancyBboxPatch((cx, header_y - 0.3), col_w - 0.15, 0.6,
        boxstyle="round,pad=0.05",
        facecolor=color, edgecolor='white', linewidth=1.8))
    ax.text(cx + (col_w - 0.15) / 2, header_y, name,
            ha='center', va='center', fontsize=8.5, fontweight='bold', color='white')

    # Body
    ax.add_patch(mpatches.FancyBboxPatch((cx, 1.2), col_w - 0.15, header_y - 1.6,
        boxstyle="round,pad=0.05",
        facecolor='#1C2833', edgecolor=color, linewidth=1.5, alpha=0.9))

    for j, item in enumerate(items):
        iy = header_y - 0.7 - j * 1.0
        bullet_x = cx + 0.15
        ax.text(bullet_x, iy, chr(9654), fontsize=7, color=color, va='center')
        ax.text(bullet_x + 0.25, iy, item, fontsize=7.5, color='#EEEEEE', va='center')

# Use case label
ax.add_patch(mpatches.FancyBboxPatch((0.3, 0.3), 13.4, 0.7,
    boxstyle="round,pad=0.1",
    facecolor='#1C2833', edgecolor='#F39C12', linewidth=2))
ax.text(7, 0.65,
        "Payment World: CHM for session tokens | COWAL for processor list | "
        "LBQ for transaction queue | CLQ for audit logs | PBQ for priority txn ordering",
        ha='center', va='center', fontsize=8, color='#F39C12')

plt.tight_layout(pad=1)
plt.savefig(OUT + "concurrent_collections.png", dpi=160, bbox_inches='tight', facecolor='#0D1117')
plt.close()
print("[OK] concurrent_collections.png saved")
