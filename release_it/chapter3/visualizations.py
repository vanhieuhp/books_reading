"""
Chapter 3 Visual Architecture - Stability Anti-Patterns
Generate concept maps and diagrams for understanding anti-pattern relationships
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import warnings
warnings.filterwarnings('ignore')

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def get_output_path(filename):
    """Get absolute path for output files"""
    return os.path.join(SCRIPT_DIR, filename)

# =============================================================================
# FIGURE 1: The Anti-Pattern Ecosystem - How They Connect
# =============================================================================

def create_anti_pattern_ecosystem():
    """Visualize how the 7 anti-patterns relate to each other"""

    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 12)
    ax.set_aspect('equal')
    ax.axis('off')

    # Define anti-pattern boxes
    patterns = [
        # (name, x, y, color)
        ("Integration\nPoints", 8, 10, '#FF6B6B'),
        ("Resource\nExhaustion", 4, 7, '#4ECDC4'),
        ("Cascading\nFailures", 12, 7, '#45B7D1'),
        ("Users as\nLoad Gen", 2, 4, '#96CEB4'),
        ("Unbalanced\nCapacities", 8, 4, '#FFEAA7'),
        ("Slow\nResponses", 14, 4, '#DDA0DD'),
        ("Self-Denial\nAttacks", 8, 1, '#F39C12'),
    ]

    # Draw boxes
    for name, x, y, color in patterns:
        box = FancyBboxPatch((x-1.5, y-0.6), 3, 1.2,
                            boxstyle="round,pad=0.05,rounding_size=0.2",
                            facecolor=color, edgecolor='black', linewidth=2, alpha=0.8)
        ax.add_patch(box)
        ax.text(x, y, name, ha='center', va='center', fontsize=11, fontweight='bold')

    # Draw arrows showing relationships
    arrows = [
        # Integration Points triggers everything
        ((8.5, 9.4), (4, 7.6), 'triggers'),
        ((8.5, 9.4), (12, 7.6), 'triggers'),
        ((8.5, 9.4), (14, 4.6), 'causes'),

        # Cascading flows down
        ((12, 6.4), (8, 4.6), 'causes'),
        ((12, 6.4), (14, 4.6), 'causes'),

        # Resource exhaustion causes cascading
        ((4, 6.4), (8, 1.6), 'feeds'),

        # Slow responses feed cascading
        ((14, 3.4), (12, 6.4), 'triggers'),

        # Self-denial attacks relate to everything
        ((8, 0.4), (4, 3.4), 'amplifies'),
        ((8, 0.4), (12, 3.4), 'amplifies'),
    ]

    for start, end, label in arrows:
        ax.annotate('', xy=end, xytext=start,
                   arrowprops=dict(arrowstyle='->', color='gray', lw=1.5))

    # Title and legend
    ax.text(8, 11.5, 'Stability Anti-Patterns Ecosystem',
            ha='center', va='center', fontsize=18, fontweight='bold')
    ax.text(8, 0.3, 'These anti-patterns form a failure network — understanding connections is key to prevention',
            ha='center', va='center', fontsize=10, style='italic', color='gray')

    plt.tight_layout()
    plt.savefig(get_output_path('fig1_anti_pattern_ecosystem.png'), dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print("Created fig1_anti_pattern_ecosystem.png")


# =============================================================================
# FIGURE 2: Cascading Failure Flow
# =============================================================================

def create_cascading_failure_diagram():
    """Visualize the cascading failure mechanism"""

    fig, ax = plt.subplots(1, 1, figsize=(14, 8))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.axis('off')

    # Service boxes
    services = [
        ('Load Balancer', 1, 8, '#3498DB'),
        ('Service A', 4, 8, '#E74C3C'),
        ('Service B', 7, 8, '#E74C3C'),
        ('Database', 10, 8, '#E74C3C'),
    ]

    for name, x, y, color in services:
        box = FancyBboxPatch((x-0.8, y-0.5), 1.6, 1,
                            boxstyle="round,pad=0.05,rounding_size=0.15",
                            facecolor=color, edgecolor='black', linewidth=2)
        ax.add_patch(box)
        ax.text(x, y, name, ha='center', va='center', fontsize=9, fontweight='bold', color='white')

    # Draw initial flow arrows
    for i in range(3):
        ax.annotate('', xy=(4.2, 8), xytext=(1.8, 8),
                   arrowprops=dict(arrowstyle='->', color='green', lw=2))
        ax.annotate('', xy=(7.2, 8), xytext=(4.2, 8),
                   arrowprops=dict(arrowstyle='->', color='green', lw=2))
        ax.annotate('', xy=(10.2, 8), xytext=(7.2, 8),
                   arrowprops=dict(arrowstyle='->', color='green', lw=2))

    # Failure cascade annotations
    # Step 1: DB slows
    ax.annotate('', xy=(9, 6.5), xytext=(10, 7.5),
               arrowprops=dict(arrowstyle='->', color='red', lw=2))
    ax.text(9.5, 6, '1. DB slows\n(500ms)', fontsize=9, color='red', ha='left')

    # Step 2: Service B queues
    ax.annotate('', xy=(6, 6.5), xytext=(7, 7.5),
               arrowprops=dict(arrowstyle='->', color='red', lw=2))
    ax.text(5.5, 6, '2. Service B\nwaits, queues', fontsize=9, color='red', ha='left')

    # Step 3: Service A threads block
    ax.annotate('', xy=(3, 6.5), xytext=(4, 7.5),
               arrowprops=dict(arrowstyle='->', color='red', lw=2))
    ax.text(2.5, 6, '3. Service A\nthread pool fills', fontsize=9, color='red', ha='left')

    # Step 4: Load balancer sees failure
    ax.annotate('', xy=(0, 6.5), xytext=(1, 7.5),
               arrowprops=dict(arrowstyle='->', color='red', lw=2))
    ax.text(0.2, 6, '4. LB sees\ntimeout/fail', fontsize=9, color='red', ha='left')

    # Resource exhaustion indicator
    box = FancyBboxPatch((0.5, 3), 5, 2.5,
                        boxstyle="round,pad=0.1,rounding_size=0.2",
                        facecolor='#FFF3CD', edgecolor='#856404', linewidth=2)
    ax.add_patch(box)
    ax.text(3, 4.25, '🔴 RESOURCE DEATH SPIRAL', ha='center', va='center',
            fontsize=11, fontweight='bold', color='#856404')
    ax.text(3, 3.6, '• Threads blocked waiting\n• Connection pool exhausted\n• New requests queue\n• Memory grows\n• System appears frozen',
            ha='center', va='center', fontsize=8, color='#856404')

    # Retry storm indicator
    box = FancyBboxPatch((7, 3), 5, 2.5,
                        boxstyle="round,pad=0.1,rounding_size=0.2",
                        facecolor='#F8D7DA', edgecolor='#721C24', linewidth=2)
    ax.add_patch(box)
    ax.text(9.5, 4.25, '🔴 RETRY STORM', ha='center', va='center',
            fontsize=11, fontweight='bold', color='#721C24')
    ax.text(9.5, 3.6, '• Clients retry immediately\n• 1000 req → 2000 req\n• Service overwhelmed\n• Cascading continues',
            ha='center', va='center', fontsize=8, color='#721C24')

    # Arrow from death spiral to retry storm
    ax.annotate('', xy=(7, 4.25), xytext=(5.5, 4.25),
               arrowprops=dict(arrowstyle='->', color='red', lw=2, linestyle='dashed'))

    ax.text(7, 0.5, 'Cascading Failure: A slow response in one component triggers resource exhaustion across the entire chain',
            ha='center', va='center', fontsize=10, style='italic', color='gray')

    ax.set_title('How Cascading Failures Propagate', fontsize=14, fontweight='bold', pad=20)
    plt.tight_layout()
    plt.savefig(get_output_path('fig2_cascading_failure.png'), dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print("Created fig2_cascading_failure.png")


# =============================================================================
# FIGURE 3: Resource Exhaustion Timeline
# =============================================================================

def create_resource_exhaustion_timeline():
    """Show the timeline of resource exhaustion"""

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), height_ratios=[1, 1])

    # Timeline
    time = np.linspace(0, 60, 100)  # 60 seconds

    # Scenario: Normal -> Slowdown -> Exhaustion -> Recovery
    # Connection pool utilization
    pool_util = np.zeros(100)
    for i, t in enumerate(time):
        if t < 10:
            pool_util[i] = 30 + np.random.randn() * 5  # Normal: 30%
        elif t < 20:
            pool_util[i] = 30 + (t-10)*3 + np.random.randn() * 3  # Growing: 30->60%
        elif t < 40:
            pool_util[i] = min(100, 60 + (t-20)*2 + np.random.randn() * 2)  # Exhausting
        else:
            pool_util[i] = max(95, 100 - (t-40)*0.5)  # Recovery attempt

    # Response time
    response_time = np.zeros(100)
    for i, t in enumerate(time):
        if t < 10:
            response_time[i] = 50 + np.random.randn() * 10  # 50ms normal
        elif t < 20:
            response_time[i] = 50 + (t-10)*50 + np.random.randn() * 20  # Growing
        elif t < 40:
            response_time[i] = min(5000, 500 + (t-20)*200 + np.random.randn() * 50)  # Spiking
        else:
            response_time[i] = max(200, 5000 - (t-40)*200)  # Recovery

    # Plot 1: Connection Pool
    ax1.fill_between(time, pool_util, alpha=0.3, color='#4ECDC4')
    ax1.plot(time, pool_util, color='#4ECDC4', linewidth=2, label='Connection Pool Utilization')
    ax1.axhline(y=80, color='orange', linestyle='--', label='Warning (80%)', linewidth=1.5)
    ax1.axhline(y=100, color='red', linestyle='--', label='Exhausted (100%)', linewidth=1.5)
    ax1.axvline(x=20, color='gray', linestyle=':', alpha=0.5)
    ax1.axvline(x=40, color='gray', linestyle=':', alpha=0.5)
    ax1.text(10, 105, 'Normal', ha='center', fontsize=10)
    ax1.text(30, 105, 'Exhaustion', ha='center', fontsize=10, color='red')
    ax1.text(50, 105, 'Recovery', ha='center', fontsize=10)
    ax1.set_ylabel('Pool Utilization (%)', fontsize=11)
    ax1.set_ylim(0, 120)
    ax1.set_xlim(0, 60)
    ax1.legend(loc='upper left')
    ax1.set_title('Resource Exhaustion Timeline', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3)

    # Plot 2: Response Time
    ax2.fill_between(time, response_time, alpha=0.3, color='#FF6B6B')
    ax2.plot(time, response_time, color='#FF6B6B', linewidth=2, label='Response Time (ms)')
    ax2.axhline(y=1000, color='orange', linestyle='--', label='Timeout Threshold', linewidth=1.5)
    ax2.axvline(x=20, color='gray', linestyle=':', alpha=0.5)
    ax2.axvline(x=40, color='gray', linestyle=':', alpha=0.5)
    ax2.set_xlabel('Time (seconds)', fontsize=11)
    ax2.set_ylabel('Response Time (ms)', fontsize=11)
    ax2.set_ylim(0, 5500)
    ax2.set_xlim(0, 60)
    ax2.legend(loc='upper left')
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(get_output_path('fig3_resource_exhaustion_timeline.png'), dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print("Created fig3_resource_exhaustion_timeline.png")


# =============================================================================
# FIGURE 4: Retry Storm Visualization
# =============================================================================

def create_retry_storm_chart():
    """Show how retries amplify failure"""

    fig, ax = plt.subplots(1, 1, figsize=(12, 6))

    # Time steps
    time = np.arange(0, 10)

    # Requests: Normal spike then retry storm
    original_requests = [1000, 1000, 800, 500, 1000, 1000, 1000, 1000, 1000, 1000]
    retry_requests = [0, 0, 200, 500, 800, 600, 300, 100, 50, 20]
    total_requests = [o + r for o, r in zip(original_requests, retry_requests)]

    x = np.arange(len(time))
    width = 0.35

    bars1 = ax.bar(x - width/2, original_requests, width, label='Original Requests',
                   color='#3498DB', alpha=0.8)
    bars2 = ax.bar(x + width/2, total_requests, width, label='Total (with Retries)',
                   color='#E74C3C', alpha=0.8)

    # Annotate the failure point
    ax.annotate('Service\nFailure', xy=(2, 800), xytext=(2, 2000),
               arrowprops=dict(arrowstyle='->', color='red', lw=2),
               ha='center', fontsize=10, color='red')

    ax.annotate('Retry Storm\nPeak', xy=(4, 1800), xytext=(5, 2500),
               arrowprops=dict(arrowstyle='->', color='red', lw=2),
               ha='center', fontsize=10, color='red')

    ax.set_xlabel('Time (seconds)', fontsize=11)
    ax.set_ylabel('Requests per Second', fontsize=11)
    ax.set_title('How Retries Amplify Failure: The Retry Storm Effect', fontsize=13, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([f'T+{t}s' for t in time])
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

    # Add insight box
    textstr = 'Without exponential backoff:\n• Every failed request generates immediate retry\n• 1000 failures → 2000 total requests\n• Service cannot recover under load'
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
    ax.text(0.98, 0.97, textstr, transform=ax.transAxes, fontsize=9,
            verticalalignment='top', horizontalalignment='right', bbox=props)

    plt.tight_layout()
    plt.savefig(get_output_path('fig4_retry_storm.png'), dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print("Created fig4_retry_storm.png")


# =============================================================================
# FIGURE 5: Bulkhead Pattern Concept
# =============================================================================

def create_bulkhead_diagram():
    """Show how bulkheads isolate failures"""

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # LEFT: No bulkheads - one failure takes all
    ax1.set_xlim(0, 10)
    ax1.set_ylim(0, 8)
    ax1.set_aspect('equal')
    ax1.axis('off')
    ax1.set_title('❌ No Bulkheads\nOne service failure = All services down',
                  fontsize=12, fontweight='bold', color='#E74C3C')

    # Single pool
    pool = FancyBboxPatch((3, 5), 4, 2,
                         boxstyle="round,pad=0.1,rounding_size=0.2",
                         facecolor='#3498DB', edgecolor='black', linewidth=2)
    ax1.add_patch(pool)
    ax1.text(5, 6, 'Shared Thread Pool\n(10 threads)', ha='center', va='center',
             fontsize=10, fontweight='bold', color='white')

    # Services connected to pool
    for i, name in enumerate(['Service A', 'Service B', 'Service C']):
        box = FancyBboxPatch((1+i*2.5, 1.5), 2, 1.5,
                            boxstyle="round,pad=0.05,rounding_size=0.15",
                            facecolor='#E74C3C', edgecolor='black', linewidth=2)
        ax1.add_patch(box)
        ax1.text(2+i*2.5, 2.25, name, ha='center', va='center', fontsize=9, fontweight='bold')
        ax1.annotate('', xy=(5, 5), xytext=(2+i*2.5, 3),
                   arrowprops=dict(arrowstyle='->', color='gray', lw=1.5))

    ax1.text(5, 0.5, 'If Service B is slow → Pool fills → A & C also fail',
             ha='center', fontsize=9, style='italic', color='gray')

    # RIGHT: Bulkheads - isolated pools
    ax2.set_xlim(0, 10)
    ax2.set_ylim(0, 8)
    ax2.set_aspect('equal')
    ax2.axis('off')
    ax2.set_title('✅ With Bulkheads\nFailure isolated to one service',
                  fontsize=12, fontweight='bold', color='#27AE60')

    # Three separate pools
    for i, name in enumerate(['Pool A\n(4)', 'Pool B\n(4)', 'Pool C\n(4)']):
        pool = FancyBboxPatch((1+i*2.8, 5), 2.2, 1.5,
                             boxstyle="round,pad=0.1,rounding_size=0.2",
                             facecolor='#27AE60', edgecolor='black', linewidth=2)
        ax2.add_patch(pool)
        ax2.text(2.1+i*2.8, 5.75, name, ha='center', va='center',
                fontsize=9, fontweight='bold', color='white')

    # Services connected to own pool
    for i, name in enumerate(['Service A', 'Service B', 'Service C']):
        box = FancyBboxPatch((1+i*2.8, 1.5), 2.2, 1.5,
                            boxstyle="round,pad=0.05,rounding_size=0.15",
                            facecolor='#27AE60', edgecolor='black', linewidth=2)
        ax2.add_patch(box)
        ax2.text(2.1+i*2.8, 2.25, name, ha='center', va='center', fontsize=9, fontweight='bold')
        ax2.annotate('', xy=(2.1+i*2.8, 5), xytext=(2.1+i*2.8, 3),
                   arrowprops=dict(arrowstyle='->', color='gray', lw=1.5))

    ax2.text(5, 0.5, 'If Service B is slow → Only Pool B fills → A & C continue working',
             ha='center', fontsize=9, style='italic', color='gray')

    plt.tight_layout()
    plt.savefig(get_output_path('fig5_bulkhead_pattern.png'), dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print("Created fig5_bulkhead_pattern.png")


# =============================================================================
# MAIN: Generate all figures
# =============================================================================

if __name__ == '__main__':
    print("Generating Chapter 3 Visualizations...")
    print("=" * 50)
    create_anti_pattern_ecosystem()
    create_cascading_failure_diagram()
    create_resource_exhaustion_timeline()
    create_retry_storm_chart()
    create_bulkhead_diagram()
    print("=" * 50)
    print("All visualizations generated successfully!")
    print("Files saved to: chapter3/")
