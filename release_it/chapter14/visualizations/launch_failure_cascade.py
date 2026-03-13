"""
Launch Failure Cascade Visualization
Generates diagrams for Chapter 14 - The Trampled Product Launch
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# Set style
plt.style.use('seaborn-v0_8-whitegrid')

def create_launch_failure_cascade():
    """Create a diagram showing the cascade from organizational pressure to business impact"""

    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.set_aspect('equal')
    ax.axis('off')

    # Title
    ax.text(7, 9.5, "Launch Failure Cascade", fontsize=20, fontweight='bold',
            ha='center', va='top')
    ax.text(7, 9.0, "From Organizational Pressure to Business Impact", fontsize=12,
            ha='center', va='top', style='italic', color='gray')

    # Define box positions and sizes
    boxes = [
        # Organizational Pressure (top)
        {"pos": (2, 6.5), "size": (4, 2), "color": "#FF6B6B", "title": "ORGANIZATIONAL\nPRESSURE",
         "items": ["Unrealistic Timeline", "Feature Pressure", "Siloed Teams", "Success Theater"]},

        # Technical Shortcuts (middle)
        {"pos": (7, 6.5), "size": (4, 2), "color": "#FFE66D", "title": "TECHNICAL\nSHORTCUTS",
         "items": ["No Load Testing", "Skip Testing", "Deferred Maintenance", "No Circuit Breakers"]},

        # Business Impact (bottom right)
        {"pos": (12, 6.5), "size": (0.1, 0.1), "color": "#4ECDC4", "title": "", "items": []},  # Hidden anchor
    ]

    # Draw Organizational Pressure box
    org_box = mpatches.FancyBboxPatch((0, 4.5), 4, 4,
                                       boxstyle="round,pad=0.05,rounding_size=0.2",
                                       facecolor="#FF6B6B", edgecolor="black", linewidth=2, alpha=0.8)
    ax.add_patch(org_box)
    ax.text(2, 8.2, "ORGANIZATIONAL\nPRESSURE", fontsize=11, fontweight='bold',
            ha='center', va='center', color="white")
    ax.text(2, 6.5, "• Unrealistic Timeline\n• Feature Pressure\n• Siloed Teams\n• Success Theater",
            fontsize=9, ha='center', va='center', color="white")

    # Draw Technical Shortcuts box
    tech_box = mpatches.FancyBboxPatch((5, 4.5), 4, 4,
                                        boxstyle="round,pad=0.05,rounding_size=0.2",
                                        facecolor="#FFE66D", edgecolor="black", linewidth=2, alpha=0.8)
    ax.add_patch(tech_box)
    ax.text(7, 8.2, "TECHNICAL\nSHORTCUTS", fontsize=11, fontweight='bold',
            ha='center', va='center', color="black")
    ax.text(7, 6.5, "• No Load Testing\n• Skip Testing\n• Deferred Maint.\n• No Circuit Breakers",
            fontsize=9, ha='center', va='center', color="black")

    # Draw Business Impact box
    biz_box = mpatches.FancyBboxPatch((10, 4.5), 4, 4,
                                       boxstyle="round,pad=0.05,rounding_size=0.2",
                                       facecolor="#4ECDC4", edgecolor="black", linewidth=2, alpha=0.8)
    ax.add_patch(biz_box)
    ax.text(12, 8.2, "BUSINESS\nIMPACT", fontsize=11, fontweight='bold',
            ha='center', va='center', color="white")
    ax.text(12, 6.5, "• Reputation Damage\n• Press Coverage\n• User Frustration\n• Revenue Loss",
            fontsize=9, ha='center', va='center', color="white")

    # Draw arrows between boxes
    arrow_style = dict(arrowstyle='->', color='black', lw=2)

    # Arrow from Organizational to Technical
    ax.annotate('', xy=(5, 6.5), xytext=(4, 6.5), arrowprops=arrow_style)

    # Arrow from Technical to Business
    ax.annotate('', xy=(10, 6.5), xytext=(9, 6.5), arrowprops=arrow_style)

    # Add "Amplifies" labels
    ax.text(4.5, 7.2, "creates", fontsize=9, ha='center', va='center', style='italic')
    ax.text(9.5, 7.2, "causes", fontsize=9, ha='center', va='center', style='italic')

    # Add KEY INSIGHT box at bottom
    insight_box = mpatches.FancyBboxPatch((0.5, 1), 13, 2.5,
                                          boxstyle="round,pad=0.05,rounding_size=0.2",
                                          facecolor="#E8E8E8", edgecolor="#333", linewidth=2, alpha=0.9)
    ax.add_patch(insight_box)
    ax.text(7, 3, "KEY INSIGHT", fontsize=12, fontweight='bold', ha='center', va='center', color="#333")
    ax.text(7, 2.2, "Each layer amplifies the next: Organizational pressure → Technical shortcuts → System fragility\n"
             "System fragility + Launch traffic = Launch failure",
            fontsize=10, ha='center', va='center', color="#555", style='italic')

    plt.tight_layout()
    plt.savefig('launch_failure_cascade.png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print("Created: launch_failure_cascade.png")


def create_timeline_disaster():
    """Create a timeline visualization of a launch disaster"""

    fig, ax = plt.subplots(1, 1, figsize=(14, 8))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.axis('off')

    # Title
    ax.text(7, 9.5, "Timeline of a Launch Disaster", fontsize=18, fontweight='bold',
            ha='center', va='top')

    # Timeline phases
    phases = [
        {"name": "PRE-LAUNCH", "duration": "Months", "x": 2, "color": "#3498DB",
         "events": ["Features incomplete", "Testing shortcuts", "Pressure mounts"]},

        {"name": "LAUNCH", "duration": "Hour 0", "x": 7, "color": "#E74C3C",
         "events": ["Go live", "Traffic spikes", "Performance degrades"]},

        {"name": "POST-LAUNCH", "duration": "Days/Weeks", "x": 12, "color": "#9B59B6",
         "events": ["System crashes", "Users frustrated", "Reputation damaged"]},
    ]

    # Draw timeline line
    ax.plot([1, 13], [5, 5], 'k-', lw=3)

    # Draw phase boxes and markers
    for i, phase in enumerate(phases):
        x = phase["x"]

        # Phase marker
        circle = mpatches.Circle((x, 5), 0.5, facecolor=phase["color"], edgecolor="black", lw=2)
        ax.add_patch(circle)

        # Phase name above
        ax.text(x, 7.5, phase["name"], fontsize=11, fontweight='bold', ha='center', va='center')
        ax.text(x, 6.8, phase["duration"], fontsize=9, ha='center', va='center', style='italic', color='gray')

        # Events below
        events_text = "\n".join(phase["events"])
        ax.text(x, 3.2, events_text, fontsize=8, ha='center', va='top', linespacing=1.5)

        # Phase number
        ax.text(x, 5, str(i+1), fontsize=12, fontweight='bold', ha='center', va='center', color='white')

    # Add annotations for key moments
    ax.annotate('Launch Date\n(Fixed by marketing)', xy=(7, 5), xytext=(4, 2),
                fontsize=9, ha='center', va='center',
                arrowprops=dict(arrowstyle='->', color='#E74C3C', lw=1.5),
                bbox=dict(boxstyle='round', facecolor='#FFEEEE', edgecolor='#E74C3C'))

    ax.annotate('Peak Traffic\n(Beyond capacity)', xy=(7, 5), xytext=(10, 2),
                fontsize=9, ha='center', va='center',
                arrowprops=dict(arrowstyle='->', color='#E74C3C', lw=1.5),
                bbox=dict(boxstyle='round', facecolor='#FFEEEE', edgecolor='#E74C3C'))

    # Key insight at bottom
    ax.text(7, 1, "The problem isn't the launch day—it's everything that happened before it.",
            fontsize=11, ha='center', va='center', style='italic', color='#333',
            bbox=dict(boxstyle='round', facecolor='#F0F0F0', edgecolor='none'))

    plt.tight_layout()
    plt.savefig('timeline_disaster.png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print("Created: timeline_disaster.png")


def create_technical_debt_timeline():
    """Visualize how technical debt accumulates and comes due"""

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

    # Top plot: Debt accumulation over time
    time_months = np.arange(0, 12, 0.1)

    # Debt accumulation (accelerates over time)
    debt = 10 * np.exp(0.15 * time_months)
    debt = np.clip(debt, 0, 100)

    ax1.plot(time_months, debt, 'r-', lw=3, label='Technical Debt')
    ax1.axhline(y=50, color='orange', linestyle='--', lw=2, label='Warning Threshold')
    ax1.axhline(y=80, color='red', linestyle='--', lw=2, label='Critical Threshold')

    # Mark launch
    launch_idx = 6  # Launch at month 6
    ax1.axvline(x=launch_idx, color='green', linestyle='-', lw=3, alpha=0.7, label='Launch Date')
    ax1.scatter([launch_idx], [debt[int(launch_idx*10)]], s=200, c='green', zorder=5, marker='*')

    # Annotations
    ax1.annotate('Launch Date\n(Debt comes due)', xy=(launch_idx, debt[int(launch_idx*10)]),
                 xytext=(launch_idx+1.5, debt[int(launch_idx*10)]+15),
                 fontsize=10, ha='center',
                 arrowprops=dict(arrowstyle='->', color='green', lw=2))

    ax1.set_xlabel('Months of Development', fontsize=12)
    ax1.set_ylabel('Technical Debt Level', fontsize=12)
    ax1.set_title('Technical Debt Accumulation vs. Launch Date', fontsize=14, fontweight='bold')
    ax1.legend(loc='upper left')
    ax1.set_ylim(0, 110)
    ax1.set_xlim(0, 12)
    ax1.grid(True, alpha=0.3)

    # Bottom plot: System reliability
    # Reliability inversely proportional to debt
    reliability = 100 - debt * 0.8
    reliability = np.clip(reliability, 0, 100)

    ax2.plot(time_months, reliability, 'b-', lw=3, label='System Reliability')
    ax2.axhline(y=90, color='green', linestyle='--', lw=2, label='Target Reliability (90%)')
    ax2.axvline(x=launch_idx, color='red', linestyle='-', lw=3, alpha=0.7, label='Launch Date')

    # Shade the "danger zone"
    ax2.fill_between(time_months[launch_idx*10:], 0, reliability[launch_idx*10:],
                     alpha=0.3, color='red', label='Danger Zone')

    ax2.set_xlabel('Months of Development', fontsize=12)
    ax2.set_ylabel('System Reliability (%)', fontsize=12)
    ax2.set_title('System Reliability Degradation', fontsize=14, fontweight='bold')
    ax2.legend(loc='lower left')
    ax2.set_ylim(0, 110)
    ax2.set_xlim(0, 12)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('technical_debt_timeline.png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print("Created: technical_debt_timeline.png")


def create_comparison_table():
    """Create a comparison visualization of launch success vs failure factors"""

    fig, ax = plt.subplots(1, 1, figsize=(14, 8))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.axis('off')

    ax.text(7, 9.5, "Launch Success vs. Failure Factors", fontsize=18, fontweight='bold', ha='center')

    # Column headers
    ax.text(3.5, 8.5, "FAILURE FACTORS", fontsize=14, fontweight='bold', ha='center', color='#E74C3C')
    ax.text(10.5, 8.5, "SUCCESS FACTORS", fontsize=14, fontweight='bold', ha='center', color='#27AE60')

    # Factors lists
    failure_factors = [
        "Timeline set by marketing",
        "Testing skipped for speed",
        "No load testing performed",
        "Ops not involved in planning",
        "No rollback plan",
        "Monitoring added after launch",
        "Success theater over honesty",
        "Feature complete > stable",
    ]

    success_factors = [
        "Timeline based on technical readiness",
        "Comprehensive testing done",
        "Realistic load testing required",
        "Cross-functional team from day 1",
        "Rollback tested and ready",
        "Monitoring baseline established",
        "Honest assessment of risks",
        "Stable > feature complete",
    ]

    # Draw failure factors (left)
    for i, factor in enumerate(failure_factors):
        y = 7.8 - i * 0.8
        # Box
        box = mpatches.FancyBboxPatch((0.5, y-0.3), 6, 0.6,
                                       boxstyle="round,pad=0.02,rounding_size=0.1",
                                       facecolor="#FFEEEE", edgecolor="#E74C3C", linewidth=1)
        ax.add_patch(box)
        ax.text(3.5, y, f"❌ {factor}", fontsize=9, ha='center', va='center')

    # Draw success factors (right)
    for i, factor in enumerate(success_factors):
        y = 7.8 - i * 0.8
        # Box
        box = mpatches.FancyBboxPatch((7.5, y-0.3), 6, 0.6,
                                       boxstyle="round,pad=0.02,rounding_size=0.1",
                                       facecolor="#EEFFEE", edgecolor="#27AE60", linewidth=1)
        ax.add_patch(box)
        ax.text(10.5, y, f"✅ {factor}", fontsize=9, ha='center', va='center')

    # Arrow between columns
    ax.annotate('', xy=(7.3, 5), xytext=(6.7, 5),
                arrowprops=dict(arrowstyle='->', color='gray', lw=2))
    ax.text(7, 4.5, "The difference\nis process", fontsize=11, ha='center',
            va='center', style='italic', color='gray')

    plt.tight_layout()
    plt.savefig('success_vs_failure.png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print("Created: success_vs_failure.png")


if __name__ == "__main__":
    create_launch_failure_cascade()
    create_timeline_disaster()
    create_technical_debt_timeline()
    create_comparison_table()
    print("\nAll visualizations created successfully!")
