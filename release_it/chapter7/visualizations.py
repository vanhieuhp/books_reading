"""
Instance Room Visualizations
============================
This module generates visualizations for Chapter 7 - Instance Room concepts.
Run this script to generate all diagrams.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as path_effects
import numpy as np
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import warnings
warnings.filterwarnings('ignore')

# Color palette - professional, production-grade
COLORS = {
    'startup': '#3498DB',      # Blue
    'serving': '#27AE60',       # Green
    'shutdown': '#E67E22',     # Orange
    'failure': '#E74C3C',      # Red
    'pending': '#95A5A6',       # Gray
    'arrow': '#2C3E50',        # Dark gray
    'background': '#FAFAFA',   # Light gray
}


def create_lifecycle_state_machine():
    """
    Creates a state machine diagram showing instance lifecycle phases
    and transitions between them.
    """
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.set_facecolor(COLORS['background'])
    fig.patch.set_facecolor(COLORS['background'])

    # State positions
    states = {
        'STARTUP': (3, 7),
        'SERVING': (7, 7),
        'SHUTDOWN': (11, 7),
        'FAILURE': (7, 3),
    }

    # Draw states as rounded rectangles
    for state, (x, y) in states.items():
        color = COLORS[state.lower()]
        box = FancyBboxPatch((x - 1.3, y - 0.6), 2.6, 1.2,
                              boxstyle="round,pad=0.05,rounding_size=0.2",
                              facecolor=color, edgecolor='#2C3E50',
                              linewidth=2, alpha=0.9)
        ax.add_patch(box)
        ax.text(x, y, state, ha='center', va='center',
                fontsize=12, fontweight='bold', color='white')

    # Draw transitions as arrows with labels
    transitions = [
        ('STARTUP', 'SERVING', 'initialized\nready'),
        ('SERVING', 'SHUTDOWN', 'SIGTERM\ndrain'),
        ('SERVING', 'FAILURE', 'crash\nexception'),
        ('FAILURE', 'STARTUP', 'restart\nreplace'),
        ('STARTUP', 'FAILURE', 'init error'),
    ]

    for from_state, to_state, label in transitions:
        x1, y1 = states[from_state]
        x2, y2 = states[to_state]

        # Calculate arrow positions (from edge of boxes)
        if from_state == 'STARTUP' and to_state == 'SERVING':
            ax.annotate('', xy=(x2 - 1.4, y2), xytext=(x1 + 1.4, y1),
                       arrowprops=dict(arrowstyle='->', color=COLORS['arrow'], lw=2))
            ax.text((x1 + x2) / 2, y1 + 0.5, label, ha='center', va='center',
                   fontsize=9, style='italic', color='#2C3E50')
        elif from_state == 'SERVING' and to_state == 'SHUTDOWN':
            ax.annotate('', xy=(x2 - 1.4, y2), xytext=(x1 + 1.4, y1),
                       arrowprops=dict(arrowstyle='->', color=COLORS['arrow'], lw=2))
            ax.text((x1 + x2) / 2, y1 + 0.5, label, ha='center', va='center',
                   fontsize=9, style='italic', color='#2C3E50')
        elif from_state == 'SERVING' and to_state == 'FAILURE':
            ax.annotate('', xy=(x2, y2 + 0.6), xytext=(x1, y1 - 0.6),
                       arrowprops=dict(arrowstyle='->', color=COLORS['arrow'], lw=2,
                                      connectionstyle='arc3,rad=0.2'))
            ax.text(x1 + 0.8, y1 - 1.2, label, ha='center', va='center',
                   fontsize=9, style='italic', color='#2C3E50')
        elif from_state == 'FAILURE' and to_state == 'STARTUP':
            ax.annotate('', xy=(x2 - 1.3, y2 + 0.6), xytext=(x2, y2 - 0.6),
                       arrowprops=dict(arrowstyle='->', color=COLORS['arrow'], lw=2,
                                      connectionstyle='arc3,rad=-0.2'))
            ax.text(x2 - 1.5, y2 - 1.0, label, ha='center', va='center',
                   fontsize=9, style='italic', color='#2C3E50')
        elif from_state == 'STARTUP' and to_state == 'FAILURE':
            ax.annotate('', xy=(x2, y2 + 0.6), xytext=(x1, y1 - 0.6),
                       arrowprops=dict(arrowstyle='->', color=COLORS['arrow'], lw=2,
                                      connectionstyle='arc3,rad=-0.2'))
            ax.text(x1 + 0.3, y1 - 1.5, label, ha='center', va='center',
                   fontsize=9, style='italic', color='#2C3E50')

    # Add title and legend
    ax.set_title('Instance Lifecycle State Machine\n(From "Release It!" Chapter 7)',
                fontsize=16, fontweight='bold', pad=20)

    # Legend
    legend_elements = [
        mpatches.Patch(facecolor=COLORS['startup'], label='Startup - Initializing'),
        mpatches.Patch(facecolor=COLORS['serving'], label='Serving - Handling Traffic'),
        mpatches.Patch(facecolor=COLORS['shutdown'], label='Shutdown - Graceful Exit'),
        mpatches.Patch(facecolor=COLORS['failure'], label='Failure - Crashed/Restarting'),
    ]
    ax.legend(handles=legend_elements, loc='lower center', ncol=2, fontsize=10)

    ax.axis('off')
    plt.tight_layout()
    plt.savefig('instance_lifecycle_state_machine.png', dpi=150, bbox_inches='tight',
                facecolor=COLORS['background'])
    plt.close()
    print("Created: instance_lifecycle_state_machine.png")


def create_connection_storm_diagram():
    """
    Visualizes the connection storm problem and solution.
    Shows how simultaneous starts overwhelm the database.
    """
    fig, axes = plt.subplots(1, 2, figsize=(16, 8))

    # Problem: Connection Storm
    ax1 = axes[0]
    ax1.set_xlim(0, 10)
    ax1.set_ylim(0, 10)
    ax1.set_facecolor(COLORS['background'])
    ax1.set_title('PROBLEM: Connection Storm\n(All instances start simultaneously)',
                  fontsize=14, fontweight='bold', color='#E74C3C', pad=15)

    # Draw database
    db_box = FancyBboxPatch((3.5, 7), 3, 1.5,
                             boxstyle="round,pad=0.1",
                             facecolor='#9B59B6', edgecolor='#2C3E50', linewidth=2)
    ax1.add_patch(db_box)
    ax1.text(5, 7.75, 'DATABASE', ha='center', va='center',
             fontsize=11, fontweight='bold', color='white')

    # Draw instances (all starting at once)
    instance_positions = [(1, 4), (3, 4), (5, 4), (7, 4), (9, 4)]
    for i, (x, y) in enumerate(instance_positions):
        box = FancyBboxPatch((x - 0.6, y - 0.4), 1.2, 0.8,
                              boxstyle="round,pad=0.05",
                              facecolor=COLORS['startup'], edgecolor='#2C3E50', linewidth=2)
        ax1.add_patch(box)
        ax1.text(x, y, f'Instance {i+1}', ha='center', va='center',
                 fontsize=8, color='white', fontweight='bold')

    # Draw arrows - all pointing to DB at same time
    for x, y in instance_positions:
        ax1.annotate('', xy=(5, 7), xytext=(x, y + 0.4),
                    arrowprops=dict(arrowstyle='->', color='#E74C3C', lw=2.5))

    # Warning label
    ax1.text(5, 2, '⚠️ CONNECTION STORM\nDatabase overwhelmed!',
             ha='center', va='center', fontsize=12, fontweight='bold',
             color='#E74C3C',
             path_effects=[path_effects.withStroke(linewidth=3, foreground='white')])

    # Solution: Staggered Startup
    ax2 = axes[1]
    ax2.set_xlim(0, 10)
    ax2.set_ylim(0, 10)
    ax2.set_facecolor(COLORS['background'])
    ax2.set_title('SOLUTION: Staggered Startup\n(Instances start with delays)',
                 fontsize=14, fontweight='bold', color='#27AE60', pad=15)

    # Draw database
    db_box2 = FancyBboxPatch((3.5, 7), 3, 1.5,
                              boxstyle="round,pad=0.1",
                              facecolor='#9B59B6', edgecolor='#2C3E50', linewidth=2)
    ax2.add_patch(db_box2)
    ax2.text(5, 7.75, 'DATABASE', ha='center', va='center',
             fontsize=11, fontweight='bold', color='white')

    # Draw instances with staggered positions and different colors
    staggered_data = [
        ((1, 4), '#27AE60', '1'),  # Started, green (serving)
        ((3, 4), COLORS['startup'], '2'),  # Starting, blue
        ((5, 4), COLORS['pending'], '3'),  # Pending, gray
        ((7, 4), COLORS['pending'], '4'),  # Pending, gray
        ((9, 4), COLORS['pending'], '5'),  # Pending, gray
    ]
    for (x, y), color, label in staggered_data:
        box = FancyBboxPatch((x - 0.6, y - 0.4), 1.2, 0.8,
                              boxstyle="round,pad=0.05",
                              facecolor=color, edgecolor='#2C3E50', linewidth=2)
        ax2.add_patch(box)
        ax2.text(x, y, f'Instance {label}', ha='center', va='center',
                 fontsize=8, color='white', fontweight='bold')

    # Only first instance connected
    ax2.annotate('', xy=(5, 7), xytext=(1, 4.4),
                arrowprops=dict(arrowstyle='->', color='#27AE60', lw=2))

    # Label for stagger
    ax2.text(5, 2, '✅ STAGGERED START\nGradual traffic increase',
             ha='center', va='center', fontsize=12, fontweight='bold',
             color='#27AE60',
             path_effects=[path_effects.withStroke(linewidth=3, foreground='white')])

    # Time labels
    for i, ((x, y), _, _) in enumerate(staggered_data):
        ax2.text(x, 3, f't+{i*5}s', ha='center', va='center',
                fontsize=9, color='#2C3E50', style='italic')

    for ax in axes:
        ax.axis('off')

    plt.tight_layout()
    plt.savefig('connection_storm_problem_solution.png', dpi=150, bbox_inches='tight',
                facecolor=COLORS['background'])
    plt.close()
    print("Created: connection_storm_problem_solution.png")


def create_graceful_shutdown_timeline():
    """
    Visualizes the graceful shutdown sequence and timing.
    """
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.set_facecolor(COLORS['background'])

    # Title
    ax.text(7, 9.5, 'Graceful Shutdown Sequence', ha='center', va='center',
            fontsize=16, fontweight='bold')
    ax.text(7, 9, '(What happens when SIGTERM arrives)', ha='center', va='center',
            fontsize=11, style='italic', color='#7F8C8D')

    # Timeline phases
    phases = [
        (1, 3, 'SIGTERM\nReceived', '#E74C3C', 'Shutdown hook triggered'),
        (4, 3, 'Stop\nAccepting\nRequests', '#E67E22', 'Remove from load balancer'),
        (7, 3, 'Drain\nIn-Flight\nRequests', '#F39C12', 'Wait for completion (max 30s)'),
        (10, 3, 'Close\nConnections', '#9B59B6', 'DB, Redis, HTTP clients'),
        (13, 3, 'Process\nExit', '#2C3E50', 'Return 0 - clean exit'),
    ]

    for x, y, label, color, description in phases:
        # Phase box
        box = FancyBboxPatch((x - 0.8, y - 0.8), 1.6, 1.6,
                              boxstyle="round,pad=0.05",
                              facecolor=color, edgecolor='#2C3E50', linewidth=2)
        ax.add_patch(box)
        ax.text(x, y, label, ha='center', va='center',
                fontsize=9, fontweight='bold', color='white')

        # Description below
        ax.text(x, y - 1.5, description, ha='center', va='center',
                fontsize=8, color='#2C3E50', style='italic')

    # Draw arrows between phases
    for i in range(len(phases) - 1):
        x1 = phases[i][0] + 0.8
        x2 = phases[i + 1][0] - 0.8
        ax.annotate('', xy=(x2, phases[i+1][1]), xytext=(x1, phases[i][1]),
                   arrowprops=dict(arrowstyle='->', color=COLORS['arrow'], lw=2))

    # Add warning box for common pitfalls
    warning_box = FancyBboxPatch((1, 0.5), 12, 1.2,
                                   boxstyle="round,pad=0.1",
                                   facecolor='#FADBD8', edgecolor='#E74C3C', linewidth=2)
    ax.add_patch(warning_box)
    ax.text(7, 1.1, '⚠️ Common Pitfalls:',
            ha='center', va='center', fontsize=10, fontweight='bold', color='#E74C3C')
    ax.text(7, 0.6, 'No shutdown hook → Abrupt kill | Drain timeout too short → Truncated requests | Missing deregistration → Traffic to dead instances',
            ha='center', va='center', fontsize=8, color='#2C3E50')

    ax.axis('off')
    plt.tight_layout()
    plt.savefig('graceful_shutdown_timeline.png', dpi=150, bbox_inches='tight',
                facecolor=COLORS['background'])
    plt.close()
    print("Created: graceful_shutdown_timeline.png")


def create_health_check_comparison():
    """
    Compares readiness vs liveness checks with examples.
    """
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.set_facecolor(COLORS['background'])

    ax.set_title('Health Checks: Readiness vs Liveness', fontsize=16, fontweight='bold', pad=20)

    # Readiness check section
    ax.text(3.5, 9, 'READINESS PROBE', ha='center', va='center',
            fontsize=14, fontweight='bold', color=COLORS['serving'])
    ax.text(3.5, 8.5, '"Can I handle traffic?"', ha='center', va='center',
            fontsize=10, style='italic', color='#7F8C8D')

    readiness_items = [
        '✓ Database connection available',
        '✓ Cache warmed',
        '✓ Dependencies reachable',
        '✓ Initialization complete',
        '✓ Not overloaded',
    ]
    for i, item in enumerate(readiness_items):
        ax.text(3.5, 7.5 - i * 0.5, item, ha='center', va='center',
                fontsize=10, color='#2C3E50')

    readiness_box = FancyBboxPatch((0.5, 3), 6, 4.5,
                                    boxstyle="round,pad=0.1",
                                    facecolor='#E8F8F5', edgecolor='#27AE60', linewidth=2)
    ax.add_patch(readiness_box)
    ax.text(3.5, 4, 'Use for:\nLoad balancer\nrouting decisions', ha='center', va='center',
            fontsize=9, color='#27AE60', fontweight='bold')

    # Liveness check section
    ax.text(10.5, 9, 'LIVENESS PROBE', ha='center', va='center',
            fontsize=14, fontweight='bold', color=COLORS['failure'])
    ax.text(10.5, 8.5, '"Am I alive?"', ha='center', va='center',
            fontsize=10, style='italic', color='#7F8C8D')

    liveness_items = [
        '✓ Process running',
        '✓ Not deadlocked',
        '✓ Memory reasonable',
        '✓ Not in infinite loop',
        '✓ GC not stuck',
    ]
    for i, item in enumerate(liveness_items):
        ax.text(10.5, 7.5 - i * 0.5, item, ha='center', va='center',
                fontsize=10, color='#2C3E50')

    liveness_box = FancyBboxPatch((7.5, 3), 6, 4.5,
                                   boxstyle="round,pad=0.1",
                                   facecolor='#FADBD8', edgecolor='#E74C3C', linewidth=2)
    ax.add_patch(liveness_box)
    ax.text(10.5, 4, 'Use for:\nRestart decisions\n(Careful! Can cause\nrestart loops)', ha='center', va='center',
            fontsize=9, color='#E74C3C', fontweight='bold')

    # Warning at bottom
    ax.text(7, 1, '⚠️ WARNING: Liveness check too aggressive = Restart loops during brief issues',
            ha='center', va='center', fontsize=11, fontweight='bold', color='#E74C3C',
            path_effects=[path_effects.withStroke(linewidth=3, foreground='white')])

    ax.axis('off')
    plt.tight_layout()
    plt.savefig('health_checks_readiness_vs_liveness.png', dpi=150, bbox_inches='tight',
                facecolor=COLORS['background'])
    plt.close()
    print("Created: health_checks_readiness_vs_liveness.png")


def create_deployment_strategy_comparison():
    """
    Compares Blue-Green, Rolling, and Canary deployment strategies.
    """
    fig, axes = plt.subplots(1, 3, figsize=(18, 8))

    strategies = [
        ('Blue-Green\nDeployment', [
            (0, 'BLUE (v1.0)', '#3498DB'),
            (2, 'GREEN (v1.1)', '#27AE60'),
            (4, 'Switch Traffic', '#E74C3C'),
            (6, 'v1.1 serving', '#27AE60'),
        ], 'Zero downtime\nInstant rollback\nDouble resources'),
        ('Rolling\nDeployment', [
            (0, 'v1.0', '#3498DB'),
            (1, 'v1.0', '#3498DB'),
            (2, 'v1.1', '#27AE60'),
            (3, 'v1.0', '#3498DB'),
            (4, 'v1.1', '#27AE60'),
            (5, 'v1.1', '#27AE60'),
        ], 'No extra resources\nGradual rollout\nSlower rollback'),
        ('Canary\nDeployment', [
            (0, 'v1.0', '#3498DB'),
            (1, 'v1.0', '#3498DB'),
            (2, 'v1.0', '#3498DB'),
            (3, 'v1.0', '#3498DB'),
            (4, 'v1.1', '#27AE60'),
            (5, 'v1.1', '#27AE60'),
        ], 'Test with real traffic\nLow risk rollout\nRequires good metrics'),
    ]

    for idx, (title, instances, pros) in enumerate(strategies):
        ax = axes[idx]
        ax.set_xlim(-1, 7)
        ax.set_ylim(-1, 4)
        ax.set_facecolor(COLORS['background'])
        ax.set_title(title, fontsize=14, fontweight='bold', pad=15)

        # Draw instances
        for x, label, color in instances:
            box = FancyBboxPatch((x - 0.4, 1.5), 0.8, 0.8,
                                  boxstyle="round,pad=0.05",
                                  facecolor=color, edgecolor='#2C3E50', linewidth=2)
            ax.add_patch(box)
            ax.text(x, 1.9, label, ha='center', va='center',
                   fontsize=8, fontweight='bold', color='white')

        # Draw traffic arrow
        if title.startswith('Blue'):
            ax.annotate('', xy=(4, 2.5), xytext=(1, 2.5),
                       arrowprops=dict(arrowstyle='->', color='#E74C3C', lw=3))
            ax.text(2.5, 2.8, 'traffic', ha='center', fontsize=9, color='#E74C3C')

        # Pros box
        ax.text(3, 0, pros, ha='center', va='center',
               fontsize=9, color='#2C3E50', style='italic',
               bbox=dict(boxstyle='round', facecolor='white', edgecolor='#BDC3C7'))

        ax.axis('off')

    plt.suptitle('Deployment Strategies Comparison', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig('deployment_strategies.png', dpi=150, bbox_inches='tight',
                facecolor=COLORS['background'])
    plt.close()
    print("Created: deployment_strategies.png")


def create_instance_room_metaphor():
    """
    Visualizes the Instance Room hotel metaphor.
    """
    fig, ax = plt.subplots(figsize=(14, 10))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.set_facecolor(COLORS['background'])

    ax.set_title('Instance Room: The Hotel Metaphor', fontsize=16, fontweight='bold', pad=20)

    # Draw the hotel layout
    # Front desk (Load Balancer)
    desk = FancyBboxPatch((5.5, 8), 3, 1,
                          boxstyle="round,pad=0.1",
                          facecolor='#2C3E50', edgecolor='#34495E', linewidth=2)
    ax.add_patch(desk)
    ax.text(7, 8.5, 'LOAD BALANCER\n(Front Desk)', ha='center', va='center',
            fontsize=10, fontweight='bold', color='white')

    # Rooms (Instances)
    room_positions = [(1, 5), (3.5, 5), (6, 5), (8.5, 5), (11, 5),
                      (1, 3), (3.5, 3), (6, 3), (8.5, 3), (11, 3)]
    room_states = ['occupied', 'occupied', 'empty', 'occupied', 'maintenance',
                   'occupied', 'empty', 'occupied', 'occupied', 'empty']

    room_colors = {
        'occupied': COLORS['serving'],
        'empty': COLORS['pending'],
        'maintenance': '#9B59B6',
    }

    for (x, y), state in zip(room_positions, room_states):
        box = FancyBboxPatch((x - 0.7, y - 0.5), 1.4, 1,
                             boxstyle="round,pad=0.05",
                             facecolor=room_colors[state], edgecolor='#2C3E50', linewidth=2)
        ax.add_patch(box)
        state_text = '🛏️' if state == 'occupied' else '🧹' if state == 'maintenance' else '🔑'
        ax.text(x, y, f'{state_text}\nInstance', ha='center', va='center',
               fontsize=8, fontweight='bold', color='white')

    # Kitchen (Database)
    kitchen = FancyBboxPatch((5.5, 0.5), 3, 1.5,
                             boxstyle="round,pad=0.1",
                             facecolor='#9B59B6', edgecolor='#8E44AD', linewidth=2)
    ax.add_patch(kitchen)
    ax.text(7, 1.25, 'DATABASE\n(Kitchen)', ha='center', va='center',
            fontsize=10, fontweight='bold', color='white')

    # Arrows
    # LB to rooms
    for x, y in room_positions:
        ax.annotate('', xy=(x, y + 0.5), xytext=(7, 8),
                   arrowprops=dict(arrowstyle='->', color='#BDC3C7', lw=1, alpha=0.5))

    # Rooms to DB (for those serving)
    serving_rooms = [(1, 5), (3.5, 5), (8.5, 5), (1, 3), (6, 3), (8.5, 3)]
    for x, y in serving_rooms:
        ax.annotate('', xy=(7, 2), xytext=(x, y - 0.5),
                   arrowprops=dict(arrowstyle='->', color='#9B59B6', lw=1, alpha=0.5))

    # Legend
    legend_elements = [
        mpatches.Patch(facecolor=COLORS['serving'], label='Serving (Occupied)'),
        mpatches.Patch(facecolor=COLORS['pending'], label='Idle (Empty)'),
        mpatches.Patch(facecolor='#9B59B6', label='Maintenance'),
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=10)

    # Metaphor explanations
    explanations = [
        'Rooms = Instances',
        'Guests = Traffic/Requests',
        'Front Desk = Load Balancer',
        'Kitchen = Database/Backend',
    ]
    for i, exp in enumerate(explanations):
        ax.text(0.5, 7.5 - i * 0.4, exp, fontsize=10, color='#2C3E50', fontweight='bold')

    ax.axis('off')
    plt.tight_layout()
    plt.savefig('instance_room_metaphor.png', dpi=150, bbox_inches='tight',
                facecolor=COLORS['background'])
    plt.close()
    print("Created: instance_room_metaphor.png")


if __name__ == '__main__':
    print("Generating Instance Room Visualizations...")
    print("=" * 50)

    create_lifecycle_state_machine()
    create_connection_storm_diagram()
    create_graceful_shutdown_timeline()
    create_health_check_comparison()
    create_deployment_strategy_comparison()
    create_instance_room_metaphor()

    print("=" * 50)
    print("All visualizations generated successfully!")
    print("Output files:")
    print("  - instance_lifecycle_state_machine.png")
    print("  - connection_storm_problem_solution.png")
    print("  - graceful_shutdown_timeline.png")
    print("  - health_checks_readiness_vs_liveness.png")
    print("  - deployment_strategies.png")
    print("  - instance_room_metaphor.png")
