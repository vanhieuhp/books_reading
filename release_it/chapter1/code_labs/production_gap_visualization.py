"""
Production Gap Visualization
===========================
This script generates a conceptual diagram showing:
1. The Three Axes of Production (Time, Scale, Diversity)
2. The Test vs Production gap across each axis
3. How failures emerge from the intersection of these axes
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# Set up the figure with a dark theme for that "operations center" feel
plt.style.use('dark_background')
fig, ax = plt.subplots(1, 1, figsize=(16, 12))

# Remove axes
ax.set_xlim(0, 16)
ax.set_ylim(0, 12)
ax.axis('off')

# Color scheme
TEST_COLOR = '#3498DB'      # Blue - controlled
PROD_COLOR = '#E74C3C'      # Red - dangerous
AXIS_COLOR = '#F1C40F'      # Yellow - the three axes
GAP_COLOR = '#9B59B6'       # Purple - the gap between them

# Title
ax.text(8, 11.5, "THE PRODUCTION GAP", fontsize=24, fontweight='bold',
        ha='center', color='white', fontfamily='monospace')
ax.text(8, 10.9, "Three Axes Where Test Meets Reality", fontsize=14,
        ha='center', color='#AAAAAA', fontfamily='monospace')

# === AXIS 1: TIME (left side) ===
ax.text(3, 10.2, "AXIS 1: TIME", fontsize=12, fontweight='bold',
        ha='center', color=AXIS_COLOR, fontfamily='monospace')

# Test bubble - short duration
test_time = mpatches.FancyBboxPatch((0.5, 7), 5, 2.5, boxstyle="round,pad=0.1",
                                     facecolor=TEST_COLOR, alpha=0.7, edgecolor='white', linewidth=2)
ax.add_patch(test_time)
ax.text(3, 8.8, "TEST", fontsize=14, fontweight='bold', ha='center', color='white')
ax.text(3, 8.3, "Minutes", fontsize=11, ha='center', color='white', alpha=0.8)
ax.text(3, 7.8, "Fresh state", fontsize=10, ha='center', color='white', alpha=0.6)

# Arrow showing time expansion
ax.annotate('', xy=(3, 6.5), xytext=(3, 7),
            arrowprops=dict(arrowstyle='->', color='#FFFFFF', lw=2))

# Production bubble - long duration
prod_time = mpatches.FancyBboxPatch((0.5, 1), 5, 5, boxstyle="round,pad=0.1",
                                     facecolor=PROD_COLOR, alpha=0.7, edgecolor='white', linewidth=2)
ax.add_patch(prod_time)
ax.text(3, 5.5, "PRODUCTION", fontsize=14, fontweight='bold', ha='center', color='white')
ax.text(3, 4.8, "Months/Years", fontsize=11, ha='center', color='white', alpha=0.8)
ax.text(3, 4.3, "• Memory leaks accumulate", fontsize=9, ha='center', color='white', alpha=0.7)
ax.text(3, 3.8, "• SSL certs expire", fontsize=9, ha='center', color='white', alpha=0.7)
ax.text(3, 3.3, "• Data grows 1000x", fontsize=9, ha='center', color='white', alpha=0.7)
ax.text(3, 2.8, "• Schema drifts", fontsize=9, ha='center', color='white', alpha=0.7)
ax.text(3, 2.3, "• Clock drift", fontsize=9, ha='center', color='white', alpha=0.7)

# Gap indicator
ax.text(3, 6.2, "GAP", fontsize=10, fontweight='bold', ha='center', color=GAP_COLOR)

# === AXIS 2: SCALE (middle) ===
ax.text(8, 10.2, "AXIS 2: SCALE", fontsize=12, fontweight='bold',
        ha='center', color=AXIS_COLOR, fontfamily='monospace')

# Test bubble - low scale
test_scale = mpatches.FancyBboxPatch((5.5, 7), 5, 2.5, boxstyle="round,pad=0.1",
                                       facecolor=TEST_COLOR, alpha=0.7, edgecolor='white', linewidth=2)
ax.add_patch(test_scale)
ax.text(8, 8.8, "TEST", fontsize=14, fontweight='bold', ha='center', color='white')
ax.text(8, 8.3, "10 users", fontsize=11, ha='center', color='white', alpha=0.8)
ax.text(8, 7.8, "1 service", fontsize=10, ha='center', color='white', alpha=0.6)

# Arrow showing scale expansion
ax.annotate('', xy=(8, 6.5), xytext=(8, 7),
            arrowprops=dict(arrowstyle='->', color='#FFFFFF', lw=2))

# Production bubble - high scale
prod_scale = mpatches.FancyBboxPatch((5.5, 1), 5, 5, boxstyle="round,pad=0.1",
                                      facecolor=PROD_COLOR, alpha=0.7, edgecolor='white', linewidth=2)
ax.add_patch(prod_scale)
ax.text(8, 5.5, "PRODUCTION", fontsize=14, fontweight='bold', ha='center', color='white')
ax.text(8, 4.8, "100K+ concurrent", fontsize=11, ha='center', color='white', alpha=0.8)
ax.text(8, 4.3, "• Pool exhaustion", fontsize=9, ha='center', color='white', alpha=0.7)
ax.text(8, 3.8, "• Cache invalidation", fontsize=9, ha='center', color='white', alpha=0.7)
ax.text(8, 3.3, "• Thundering herd", fontsize=9, ha='center', color='white', alpha=0.7)
ax.text(8, 2.8, "• Network saturation", fontsize=9, ha='center', color='white', alpha=0.7)
ax.text(8, 2.3, "• Query timeouts", fontsize=9, ha='center', color='white', alpha=0.7)

# Gap indicator
ax.text(8, 6.2, "GAP", fontsize=10, fontweight='bold', ha='center', color=GAP_COLOR)

# === AXIS 3: DIVERSITY (right side) ===
ax.text(13, 10.2, "AXIS 3: DIVERSITY", fontsize=12, fontweight='bold',
        ha='center', color=AXIS_COLOR, fontfamily='monospace')

# Test bubble - low diversity
test_div = mpatches.FancyBboxPatch((10.5, 7), 5, 2.5, boxstyle="round,pad=0.1",
                                     facecolor=TEST_COLOR, alpha=0.7, edgecolor='white', linewidth=2)
ax.add_patch(test_div)
ax.text(13, 8.8, "TEST", fontsize=14, fontweight='bold', ha='center', color='white')
ax.text(13, 8.3, "1 browser", fontsize=11, ha='center', color='white', alpha=0.8)
ax.text(13, 7.8, "Clean data", fontsize=10, ha='center', color='white', alpha=0.6)

# Arrow showing diversity expansion
ax.annotate('', xy=(13, 6.5), xytext=(13, 7),
            arrowprops=dict(arrowstyle='->', color='#FFFFFF', lw=2))

# Production bubble - high diversity
prod_div = mpatches.FancyBboxPatch((10.5, 1), 5, 5, boxstyle="round,pad=0.1",
                                     facecolor=PROD_COLOR, alpha=0.7, edgecolor='white', linewidth=2)
ax.add_patch(prod_div)
ax.text(13, 5.5, "PRODUCTION", fontsize=14, fontweight='bold', ha='center', color='white')
ax.text(13, 4.8, "Millions of devices", fontsize=11, ha='center', color='white', alpha=0.8)
ax.text(13, 4.3, "• Input edge cases", fontsize=9, ha='center', color='white', alpha=0.7)
ax.text(13, 3.8, "• Network variability", fontsize=9, ha='center', color='white', alpha=0.7)
ax.text(13, 3.3, "• Geographic latency", fontsize=9, ha='center', color='white', alpha=0.7)
ax.text(13, 2.8, "• Device fragmentation", fontsize=9, ha='center', color='white', alpha=0.7)
ax.text(13, 2.3, "• Attack traffic", fontsize=9, ha='center', color='white', alpha=0.7)

# Gap indicator
ax.text(13, 6.2, "GAP", fontsize=10, fontweight='bold', ha='center', color=GAP_COLOR)

# === Bottom: THE CONVERGENCE ===
# Show how all three gaps converge to create the "unknown unknowns" zone
convergence = mpatches.FancyBboxPatch((3, -0.3), 10, 0.8, boxstyle="round,pad=0.05",
                                        facecolor=GAP_COLOR, alpha=0.9, edgecolor='white', linewidth=2)
ax.add_patch(convergence)
ax.text(8, 0.1, "THE CONVERGENCE → UNKNOWN UNKNOWNS", fontsize=11, fontweight='bold',
        ha='center', color='white', fontfamily='monospace')

# Add legend
legend_elements = [
    mpatches.Patch(facecolor=TEST_COLOR, alpha=0.7, label='Test Environment (known, controlled)'),
    mpatches.Patch(facecolor=PROD_COLOR, alpha=0.7, label='Production Reality (unknown, chaotic)'),
    mpatches.Patch(facecolor=GAP_COLOR, alpha=0.9, label='The Gap (where failures live)')
]
ax.legend(handles=legend_elements, loc='upper right', fontsize=10, framealpha=0.8)

plt.tight_layout()
plt.savefig("production_gap_concept.png", dpi=150, bbox_inches='tight', facecolor='#1a1a1a')
plt.show()

print("Visualization saved as 'production_gap_concept.png'")
