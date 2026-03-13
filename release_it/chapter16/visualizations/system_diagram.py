"""
Chapter 16: The Systemic View - System Components & Feedback Loops Visualization

This script generates a concept map showing:
1. Three core components: Software, Hardware, Humans
2. Interconnections between components
3. Feedback loops (positive and negative)
4. System boundaries

Run: python visualizations/system_diagram.py
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle
import numpy as np

def draw_system_diagram():
    """Draw the three-component system with interconnections and feedback loops."""

    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 12)
    ax.set_aspect('equal')
    ax.axis('off')

    # Colors
    colors = {
        'software': '#3498DB',   # Blue
        'hardware': '#E74C3C',  # Red
        'humans': '#27AE60',     # Green
        'positive': '#F39C12',   # Orange
        'negative': '#9B59B6',   # Purple
        'delay': '#95A5A6',      # Gray
        'boundary': '#2C3E50'    # Dark blue
    }

    # Draw system boundary
    boundary = FancyBboxPatch((0.5, 0.5), 15, 11, boxstyle="round,pad=0.1,rounding_size=0.5",
                              facecolor='none', edgecolor=colors['boundary'], linewidth=3, linestyle='--')
    ax.add_patch(boundary)
    ax.text(8, 11.3, "THE SYSTEM", ha='center', fontsize=14, fontweight='bold', color=colors['boundary'])

    # ===== COMPONENTS =====

    # Software component (top-left)
    sw_box = FancyBboxPatch((1.5, 7.5), 4, 3, boxstyle="round,pad=0.1,rounding_size=0.3",
                             facecolor=colors['software'], edgecolor='#2980B9', linewidth=2)
    ax.add_patch(sw_box)
    ax.text(3.5, 9.8, "SOFTWARE", ha='center', va='center', fontsize=12, fontweight='bold', color='white')
    ax.text(3.5, 9.0, "• Business logic", ha='center', va='center', fontsize=9, color='white')
    ax.text(3.5, 8.5, "• Data processing", ha='center', va='center', fontsize=9, color='white')
    ax.text(3.5, 8.0, "• API responses", ha='center', va='center', fontsize=9, color='white')

    # Hardware component (top-right)
    hw_box = FancyBboxPatch((10.5, 7.5), 4, 3, boxstyle="round,pad=0.1,rounding_size=0.3",
                             facecolor=colors['hardware'], edgecolor='#C0392B', linewidth=2)
    ax.add_patch(hw_box)
    ax.text(12.5, 9.8, "HARDWARE", ha='center', va='center', fontsize=12, fontweight='bold', color='white')
    ax.text(12.5, 9.0, "• Compute (CPU)", ha='center', va='center', fontsize=9, color='white')
    ax.text(12.5, 8.5, "• Storage (Disk)", ha='center', va='center', fontsize=9, color='white')
    ax.text(12.5, 8.0, "• Network", ha='center', va='center', fontsize=9, color='white')

    # Humans component (bottom-center)
    hu_box = FancyBboxPatch((5.5, 2), 5, 3, boxstyle="round,pad=0.1,rounding_size=0.3",
                             facecolor=colors['humans'], edgecolor='#1E8449', linewidth=2)
    ax.add_patch(hu_box)
    ax.text(8, 4.3, "HUMANS", ha='center', va='center', fontsize=12, fontweight='bold', color='white')
    ax.text(8, 3.5, "• Developers", ha='center', va='center', fontsize=9, color='white')
    ax.text(8, 3.0, "• Operators", ha='center', va='center', fontsize=9, color='white')
    ax.text(8, 2.5, "• Users", ha='center', va='center', fontsize=9, color='white')

    # ===== INTERCONNECTIONS =====

    # Software → Hardware arrow
    ax.annotate('', xy=(10.3, 8.5), xytext=(5.7, 8.5),
                arrowprops=dict(arrowstyle='->', color='#34495E', lw=2))
    ax.text(8, 8.8, "depends on", ha='center', fontsize=8, color='#34495E')

    # Hardware → Software arrow
    ax.annotate('', xy=(5.3, 8.5), xytext=(9.9, 8.5),
                arrowprops=dict(arrowstyle='->', color='#34495E', lw=2))
    ax.text(8, 8.2, "affects", ha='center', fontsize=8, color='#34495E')

    # Software → Humans arrow
    ax.annotate('', xy=(7, 5.3), xytext=(5.5, 7.2),
                arrowprops=dict(arrowstyle='->', color='#34495E', lw=2))
    ax.text(5, 6, "affects", ha='center', fontsize=8, color='#34495E')

    # Humans → Software arrow
    ax.annotate('', xy=(3.8, 7.8), xytext=(6.5, 5.3),
                arrowprops=dict(arrowstyle='->', color='#34495E', lw=2))
    ax.text(6.5, 6.8, "builds", ha='center', fontsize=8, color='#34495E')

    # Hardware → Humans arrow
    ax.annotate('', xy=(7.5, 5.3), xytext=(10.5, 7.2),
                arrowprops=dict(arrowstyle='->', color='#34495E', lw=2))
    ax.text(10.5, 6, "affects", ha='center', fontsize=8, color='#34495E')

    # Humans → Hardware arrow
    ax.annotate('', xy=(10.3, 8), xytext=(8, 5.3),
                arrowprops=dict(arrowstyle='->', color='#34495E', lw=2))
    ax.text(9.5, 6.8, "manages", ha='center', fontsize=8, color='#34495E')

    # ===== FEEDBACK LOOPS =====

    # Positive feedback loop (reinforcing) - outer circle
    circle_pos = plt.Circle((3.5, 5.5), 1.8, fill=False, edgecolor=colors['positive'], linewidth=2, linestyle='--')
    ax.add_patch(circle_pos)
    ax.text(1.5, 5.5, "+", ha='center', va='center', fontsize=14, fontweight='bold', color=colors['positive'])
    ax.text(1.5, 4.7, "Positive\nFeedback", ha='center', va='center', fontsize=7, color=colors['positive'])

    # Negative feedback loop (balancing) - inner circle
    circle_neg = plt.Circle((12.5, 5.5), 1.8, fill=False, edgecolor=colors['negative'], linewidth=2, linestyle='--')
    ax.add_patch(circle_neg)
    ax.text(14.3, 5.5, "-", ha='center', va='center', fontsize=14, fontweight='bold', color=colors['negative'])
    ax.text(14.3, 4.7, "Negative\nFeedback", ha='center', va='center', fontsize=7, color=colors['negative'])

    # Delay indicator
    ax.text(8, 1.2, "DELAYS: Effects lag causes -- monitoring & patience required",
            ha='center', fontsize=10, style='italic', color=colors['delay'])

    # Title
    plt.title("The Systemic View: Three Components & Their Interconnections", fontsize=16, fontweight='bold', pad=20)

    # Legend
    legend_elements = [
        mpatches.Patch(facecolor=colors['software'], label='Software'),
        mpatches.Patch(facecolor=colors['hardware'], label='Hardware'),
        mpatches.Patch(facecolor=colors['humans'], label='Humans'),
        mpatches.Patch(facecolor='none', edgecolor=colors['positive'], linestyle='--', label='Positive Feedback (Reinforcing)'),
        mpatches.Patch(facecolor='none', edgecolor=colors['negative'], linestyle='--', label='Negative Feedback (Balancing)'),
    ]
    ax.legend(handles=legend_elements, loc='lower right', fontsize=9)

    plt.tight_layout()
    plt.savefig('system_diagram.png', dpi=150, bbox_inches='tight', facecolor='white')
    print("[OK] Saved: system_diagram.png")

    plt.close()


def draw_feedback_loop_types():
    """Draw detailed feedback loop types - positive vs negative."""

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Left: Positive Feedback (Reinforcing)
    ax = axes[0]
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')
    ax.set_title("Positive Feedback (Reinforcing)", fontsize=14, fontweight='bold', color='#F39C12')

    # Arrow cycle for positive feedback
    arrows_pos = [
        ((2, 8), (8, 8), "Good Performance\n→ More Users"),
        ((8, 8), (8, 2), "More Users\n→ More Revenue"),
        ((8, 2), (2, 2), "More Revenue\n→ More Investment"),
        ((2, 2), (2, 8), "More Investment\n→ Better Performance"),
    ]

    for start, end, label in arrows_pos:
        ax.annotate('', xy=end, xytext=start,
                    arrowprops=dict(arrowstyle='->', color='#F39C12', lw=2))
        mid = ((start[0] + end[0])/2, (start[1] + end[1])/2)
        ax.text(mid[0], mid[1] + 0.5, label, ha='center', fontsize=9, color='#F39C12')

    ax.text(5, 5, "+", ha='center', va='center', fontsize=24, fontweight='bold',
            color='#F39C12', alpha=0.3)

    # Right: Negative Feedback (Balancing)
    ax = axes[1]
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')
    ax.set_title("Negative Feedback (Balancing)", fontsize=14, fontweight='bold', color='#9B59B6')

    # Arrow cycle for negative feedback
    arrows_neg = [
        ((2, 8), (8, 8), "Load Increases\n→ Add Instances"),
        ((8, 8), (8, 2), "More Instances\n→ Load Decreases"),
        ((8, 2), (2, 2), "Load Decreases\n→ Remove Instances"),
        ((2, 2), (2, 8), "Remove Instances\n→ Load Increases"),
    ]

    for start, end, label in arrows_neg:
        ax.annotate('', xy=end, xytext=start,
                    arrowprops=dict(arrowstyle='->', color='#9B59B6', lw=2))
        mid = ((start[0] + end[0])/2, (start[1] + end[1])/2)
        ax.text(mid[0], mid[1] + 0.5, label, ha='center', fontsize=9, color='#9B59B6')

    ax.text(5, 5, "-", ha='center', va='center', fontsize=24, fontweight='bold',
            color='#9B59B6', alpha=0.3)

    # Key insight box
    fig.text(0.5, 0.02,
             "Key Insight: Positive feedback amplifies (growth or failure) | Negative feedback stabilizes (homeostasis)",
             ha='center', fontsize=11, style='italic', color='#2C3E50')

    plt.tight_layout(rect=[0, 0.05, 1, 1])
    plt.savefig('feedback_loops.png', dpi=150, bbox_inches='tight', facecolor='white')
    print("[OK] Saved: feedback_loops.png")

    plt.close()


def draw_organizational_antipatterns():
    """Draw organizational anti-patterns that affect system reliability."""

    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.axis('off')
    ax.set_title("Organizational Anti-Patterns: The Hidden System Failures", fontsize=14, fontweight='bold', pad=20)

    colors = {
        'silos': '#E74C3C',
        'hero': '#F39C12',
        'blame': '#9B59B6',
        'healthy': '#27AE60'
    }

    # Silos
    silo_box1 = FancyBboxPatch((1, 7), 3, 2, boxstyle="round,pad=0.1,rounding_size=0.2",
                               facecolor=colors['silos'], edgecolor='#C0392B', linewidth=2)
    ax.add_patch(silo_box1)
    ax.text(2.5, 8.3, "SILOS", ha='center', va='center', fontsize=11, fontweight='bold', color='white')
    ax.text(2.5, 7.7, "Teams isolated\nKnowledge trapped\nNo visibility", ha='center', va='center', fontsize=8, color='white')

    silo_box2 = FancyBboxPatch((5.5, 7), 3, 2, boxstyle="round,pad=0.1,rounding_size=0.2",
                               facecolor=colors['silos'], edgecolor='#C0392B', linewidth=2)
    ax.add_patch(silo_box2)
    ax.text(7, 8.3, "SILOS", ha='center', va='center', fontsize=11, fontweight='bold', color='white')
    ax.text(7, 7.7, "Optimize locally\nSystem suffers\nHandoffs break", ha='center', va='center', fontsize=8, color='white')

    silo_box3 = FancyBboxPatch((10, 7), 3, 2, boxstyle="round,pad=0.1,rounding_size=0.2",
                               facecolor=colors['silos'], edgecolor='#C0392B', linewidth=2)
    ax.add_patch(silo_box3)
    ax.text(11.5, 8.3, "SILOS", ha='center', va='center', fontsize=11, fontweight='bold', color='white')
    ax.text(11.5, 7.7, "Communication\nbroken\nConfusion", ha='center', va='center', fontsize=8, color='white')

    # Arrow between silos
    ax.annotate('', xy=(5.3, 8), xytext=(3.2, 8), arrowprops=dict(arrowstyle='->', color=colors['silos'], lw=1))
    ax.annotate('', xy=(9.8, 8), xytext=(7.7, 8), arrowprops=dict(arrowstyle='->', color=colors['silos'], lw=1))

    # Hero culture
    hero_box = FancyBboxPatch((1.5, 4), 4.5, 2, boxstyle="round,pad=0.1,rounding_size=0.2",
                               facecolor=colors['hero'], edgecolor='#D68910', linewidth=2)
    ax.add_patch(hero_box)
    ax.text(3.75, 5.3, "HERO CULTURE", ha='center', va='center', fontsize=11, fontweight='bold', color='white')
    ax.text(3.75, 4.7, "Individual heroes\nKnowledge not shared\nBurnout & fragility", ha='center', va='center', fontsize=8, color='white')

    # Blame culture
    blame_box = FancyBboxPatch((8, 4), 4.5, 2, boxstyle="round,pad=0.1,rounding_size=0.2",
                               facecolor=colors['blame'], edgecolor='#7D3C98', linewidth=2)
    ax.add_patch(blame_box)
    ax.text(10.25, 5.3, "BLAME CULTURE", ha='center', va='center', fontsize=11, fontweight='bold', color='white')
    ax.text(10.25, 4.7, "Fear of reporting\nHidden problems\nNo learning", ha='center', va='center', fontsize=8, color='white')

    # Healthy alternatives (bottom)
    ax.text(7, 2.8, "→ HEALTHY ALTERNATIVES ←", ha='center', fontsize=12, fontweight='bold', color=colors['healthy'])

    alt_box = FancyBboxPatch((2, 1), 10, 1.5, boxstyle="round,pad=0.1,rounding_size=0.2",
                              facecolor=colors['healthy'], edgecolor='#1E8449', linewidth=2)
    ax.add_patch(alt_box)
    ax.text(7, 1.9, "Cross-functional teams | Blameless post-mortems | Psychological safety | Learning organization",
            ha='center', va='center', fontsize=9, color='white')

    plt.tight_layout()
    plt.savefig('org_antipatterns.png', dpi=150, bbox_inches='tight', facecolor='white')
    print("[OK] Saved: org_antipatterns.png")

    plt.close()


if __name__ == "__main__":
    import os
    os.makedirs('visualizations', exist_ok=True)

    print("Generating Chapter 16 visualizations...")
    draw_system_diagram()
    draw_feedback_loop_types()
    draw_organizational_antipatterns()
    print("\n[OK] All visualizations generated successfully!")
