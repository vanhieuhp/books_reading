"""
Phase 1 Deep Dive — Thread Foundations
Visualization: Thread Lifecycle State Machine + Race Condition

Generates:
  1. Thread lifecycle state machine (state_transitions.png)
  2. Race condition in action (race_condition.png)
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch
import numpy as np

# ─────────────────────────────────────────────────────────────────────────────
# VISUALIZATION 1 — Thread Lifecycle State Machine
# ─────────────────────────────────────────────────────────────────────────────

fig, ax = plt.subplots(figsize=(14, 10))
ax.set_xlim(0, 14)
ax.set_ylim(0, 10)
ax.axis('off')
fig.patch.set_facecolor('#0D1117')
ax.set_facecolor('#0D1117')

# State box definitions: (label, x, y, color, description)
states = [
    ("NEW",          2,  7.5, "#27AE60", "Thread object created\nNot yet started"),
    ("RUNNABLE",     7,  7.5, "#2980B9", "Running or ready to run\non CPU / scheduler"),
    ("BLOCKED",      7,  5.0, "#E67E22", "Waiting to acquire\nan intrinsic lock"),
    ("WAITING",      11, 5.0, "#8E44AD", "Indefinite wait:\nwait()/join()/park()"),
    ("TIMED_WAITING",11, 7.5, "#C0392B", "Bounded wait:\nsleep()/wait(n)/join(n)"),
    ("TERMINATED",   7,  2.5, "#7F8C8D", "run() completed\nor uncaught exception"),
]

state_colors = {s[0]: s[3] for s in states}

# Draw state boxes
for label, x, y, color, desc in states:
    box = mpatches.FancyBboxPatch(
        (x - 1.1, y - 0.65), 2.2, 1.3,
        boxstyle="round,pad=0.1",
        facecolor=color, edgecolor='white', linewidth=1.8, alpha=0.9
    )
    ax.add_patch(box)
    ax.text(x, y + 0.2, label, ha='center', va='center',
            fontsize=11, fontweight='bold', color='white')
    ax.text(x, y - 0.35, desc, ha='center', va='center',
            fontsize=7, color='#EEEEEE', style='italic')

# Arrow helper
def arrow(ax, x1, y1, x2, y2, label='', color='#AAAAAA', lw=2):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(arrowstyle='->', color=color, lw=lw))
    mx, my = (x1 + x2) / 2 + 0.1, (y1 + y2) / 2
    if label:
        ax.text(mx, my, label, fontsize=7.5, color='#F39C12',
                ha='center', va='center',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='#1C1C1C', edgecolor='none', alpha=0.7))

# Transitions
# NEW → RUNNABLE
arrow(ax, 2.3, 7.5, 5.9, 7.5, "start()", '#AAAAAA')

# RUNNABLE → BLOCKED
arrow(ax, 7.6, 7.0, 7.6, 5.65, "lock wait", '#AAAAAA')

# RUNNABLE → TIMED_WAITING
arrow(ax, 7.7, 7.5, 10.6, 7.7, "sleep(n)", '#AAAAAA')

# RUNNABLE → TERMINATED
arrow(ax, 7.0, 6.85, 7.0, 3.15, "run() returns", '#AAAAAA')

# BLOCKED → RUNNABLE
arrow(ax, 6.4, 5.0, 5.4, 6.5, "lock acquired", '#AAAAAA')
arrow(ax, 6.4, 5.0, 5.4, 7.5, "", '#AAAAAA')

# WAITING → RUNNABLE
arrow(ax, 10.1, 5.0, 8.0, 6.5, "notify()/interrupt()", '#AAAAAA')

# TIMED_WAITING → RUNNABLE
arrow(ax, 10.1, 7.5, 8.0, 7.5, "timeout expires", '#AAAAAA')

# WAITING → TIMED_WAITING
arrow(ax, 11.0, 5.65, 11.0, 6.85, "wait(n)", '#AAAAAA')

# Title
ax.text(7, 9.6, "Thread Lifecycle State Machine",
        ha='center', va='center', fontsize=16, fontweight='bold', color='#F5F5F5')
ax.text(7, 9.15, "JVM-defined thread states — from java.lang.Thread.State",
        ha='center', va='center', fontsize=9, color='#AAAAAA')

# Legend
legend_items = [
    mpatches.Patch(color='#2980B9', label='RUNNABLE: CPU-active or queued'),
    mpatches.Patch(color='#E67E22', label='BLOCKED: lock contention'),
    mpatches.Patch(color='#8E44AD', label='WAITING: indefinite wait'),
    mpatches.Patch(color='#C0392B', label='TIMED_WAITING: bounded wait'),
]
ax.legend(handles=legend_items, loc='lower left', fontsize=8,
          facecolor='#1C1C1C', edgecolor='#333', labelcolor='white')

plt.tight_layout(pad=1)
plt.savefig("e:/Workspaces/Myself/Projects/books_reading/java_concurrent/state_transitions.png",
            dpi=160, bbox_inches='tight', facecolor='#0D1117')
plt.close()
print("[OK] state_transitions.png saved")

# ─────────────────────────────────────────────────────────────────────────────
# VISUALIZATION 2 — Race Condition (Two threads interleaving reads/writes)
# ─────────────────────────────────────────────────────────────────────────────

fig, ax = plt.subplots(figsize=(14, 7))
ax.set_xlim(0, 14)
ax.set_ylim(0, 8)
ax.axis('off')
fig.patch.set_facecolor('#FDF6E3')
ax.set_facecolor('#FDF6E3')

# Title
ax.text(7, 7.5, "Race Condition: Two Threads Debiting the Same Account",
        ha='center', va='center', fontsize=14, fontweight='bold', color='#222')

# Shared state box
shared = mpatches.FancyBboxPatch((5.5, 3.0), 3.0, 1.5,
    boxstyle="round,pad=0.1",
    facecolor='#27AE60', edgecolor='#1A5276', linewidth=2)
ax.add_patch(shared)
ax.text(7, 3.85, "balance = 1000", ha='center', va='center',
        fontsize=11, fontweight='bold', color='white')
ax.text(7, 3.45, "(Shared Heap Memory)", ha='center', va='center',
        fontsize=8, color='white')

# Thread A
ax.add_patch(mpatches.FancyBboxPatch((1, 1), 3.5, 4,
    boxstyle="round,pad=0.1",
    facecolor='#3498DB', edgecolor='#1A5276', linewidth=1.5, alpha=0.85))
ax.text(2.75, 4.7, "Thread A (debit 500)", ha='center', va='center',
        fontsize=10, fontweight='bold', color='white')

# Timeline rows for Thread A
a_steps = [
    (1.1, 3.8, "T1: read balance  → 1000"),
    (1.1, 3.1, "T2: check ≥ 500   → true"),
    (1.1, 2.4, "T3: write 1000-500"),
]
for x, y, label in a_steps:
    ax.text(x, y, label, fontsize=7.5, color='white', fontfamily='monospace')

# Thread B
ax.add_patch(mpatches.FancyBboxPatch((9.5, 1), 3.5, 4,
    boxstyle="round,pad=0.1",
    facecolor='#E74C3C', edgecolor='#922B21', linewidth=1.5, alpha=0.85))
ax.text(11.25, 4.7, "Thread B (debit 500)", ha='center', va='center',
        fontsize=10, fontweight='bold', color='white')

b_steps = [
    (9.6, 3.8, "T1: read balance  → 1000"),
    (9.6, 3.1, "T2: check ≥ 500   → true"),
    (9.6, 2.4, "T3: write 1000-500"),
]
for x, y, label in b_steps:
    ax.text(x, y, label, fontsize=7.5, color='white', fontfamily='monospace')

# Arrow A→shared
ax.annotate('', xy=(5.5, 3.75), xytext=(4.5, 3.75),
    arrowprops=dict(arrowstyle='<->', color='#3498DB', lw=2))

# Arrow B→shared
ax.annotate('', xy=(8.5, 3.75), xytext=(9.5, 3.75),
    arrowprops=dict(arrowstyle='<->', color='#E74C3C', lw=2))

# Problem annotation
ax.add_patch(mpatches.FancyBboxPatch((4.2, 5.3), 5.6, 1.2,
    boxstyle="round,pad=0.15",
    facecolor='#FFF3CD', edgecolor='#E67E22', linewidth=2))
ax.text(7, 5.9, "Both threads read 1000 at the same time!", ha='center', va='center',
        fontsize=10, fontweight='bold', color='#922B21')
ax.text(7, 5.5, "Both pass the balance check. Both write back 500.\nFinal balance = 500  (should be 0!)",
        ha='center', va='center', fontsize=8.5, color='#333')

# Result box
ax.add_patch(mpatches.FancyBboxPatch((10.8, 5.3), 2.5, 1.2,
    boxstyle="round,pad=0.1",
    facecolor='#E74C3C', edgecolor='#922B21', linewidth=2))
ax.text(12.05, 6.1, "LOST", ha='center', va='center',
        fontsize=13, fontweight='bold', color='white')
ax.text(12.05, 5.7, "U$500", ha='center', va='center',
        fontsize=10, color='white')

plt.tight_layout(pad=1)
plt.savefig("e:/Workspaces/Myself/Projects/books_reading/java_concurrent/race_condition.png",
            dpi=160, bbox_inches='tight', facecolor='#FDF6E3')
plt.close()
print("[OK] race_condition.png saved")
