"""
Visualization Script for Chapter 4: Stability Patterns
Run this script to generate concept diagrams.

Requirements:
    pip install matplotlib networkx

Usage:
    python visualizations.py
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import networkx as nx
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle
import warnings
warnings.filterwarnings('ignore')

# Set style
plt.style.use('default')
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['axes.facecolor'] = 'white'
plt.rcParams['font.family'] = 'sans-serif'


def create_circuit_breaker_state_machine():
    """Generate Circuit Breaker state machine diagram."""
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))

    # State nodes with positions
    states = {
        'CLOSED': (0.2, 0.5),
        'OPEN': (0.8, 0.8),
        'HALF_OPEN': (0.8, 0.2)
    }

    # Draw state boxes
    for state, (x, y) in states.items():
        color = '#4CAF50' if state == 'CLOSED' else ('#F44336' if state == 'OPEN' else '#FF9800')
        rect = FancyBboxPatch((x-0.12, y-0.08), 0.24, 0.16,
                              boxstyle="round,pad=0.02,rounding_size=0.03",
                              facecolor=color, edgecolor='black', linewidth=2, alpha=0.8)
        ax.add_patch(rect)
        ax.text(x, y, state, ha='center', va='center', fontsize=14, fontweight='bold', color='white')

    # Draw transitions with arrows
    # CLOSED -> OPEN (failure threshold exceeded)
    ax.annotate('', xy=(0.68, 0.74), xytext=(0.32, 0.58),
                arrowprops=dict(arrowstyle='->', color='#D32F2F', lw=2))
    ax.text(0.5, 0.7, 'Failure threshold\nexceeded', fontsize=10, ha='center',
            color='#D32F2F', style='italic')

    # OPEN -> HALF_OPEN (timeout elapsed)
    ax.annotate('', xy=(0.8, 0.36), xytext=(0.8, 0.64),
                arrowprops=dict(arrowstyle='->', color='#FF9800', lw=2))
    ax.text(0.92, 0.5, 'Timeout\nelapsed', fontsize=10, ha='left',
            color='#FF9800', style='italic')

    # HALF_OPEN -> CLOSED (test success)
    ax.annotate('', xy=(0.32, 0.5), xytext=(0.68, 0.28),
                arrowprops=dict(arrowstyle='->', color='#4CAF50', lw=2))
    ax.text(0.4, 0.35, 'Test request\nsucceeds', fontsize=10, ha='center',
            color='#4CAF50', style='italic')

    # HALF_OPEN -> OPEN (test failure)
    ax.annotate('', xy=(0.8, 0.52), xytext=(0.92, 0.28),
                arrowprops=dict(arrowstyle='->', color='#D32F2F', lw=2))
    ax.text(0.9, 0.4, 'Test fails', fontsize=9, ha='left',
            color='#D32F2F', style='italic')

    # Self loop on CLOSED (success)
    theta = np.linspace(0, np.pi, 100)
    x_loop = 0.2 + 0.08 * np.cos(theta)
    y_loop = 0.58 + 0.08 * np.sin(theta)
    ax.plot(x_loop, y_loop, 'g-', lw=2)
    ax.text(0.08, 0.7, 'Success', fontsize=9, ha='center', color='#4CAF50')

    # Self loop on OPEN (request fails fast)
    theta = np.linspace(0, np.pi, 100)
    x_loop = 0.8 + 0.06 * np.cos(theta + np.pi/2)
    y_loop = 0.86 + 0.06 * np.sin(theta + np.pi/2)
    ax.plot(x_loop, y_loop, 'r-', lw=2)
    ax.text(0.72, 0.95, 'Fail fast', fontsize=9, ha='center', color='#D32F2F')

    # Title and formatting
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('Circuit Breaker State Machine', fontsize=16, fontweight='bold', pad=20)

    # Legend
    legend_elements = [
        mpatches.Patch(facecolor='#4CAF50', edgecolor='black', label='Normal operation'),
        mpatches.Patch(facecolor='#F44336', edgecolor='black', label='Blocking requests'),
        mpatches.Patch(facecolor='#FF9800', edgecolor='black', label='Testing recovery')
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=9)

    plt.tight_layout()
    plt.savefig('circuit_breaker_state_machine.png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print("✓ Created circuit_breaker_state_machine.png")


def create_bulkhead_isolation():
    """Generate Bulkhead isolation diagram showing multiple levels."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 6))

    # Application Level
    ax1 = axes[0]
    ax1.set_xlim(0, 10)
    ax1.set_ylim(0, 10)
    ax1.set_title('Application Level\n(Thread Pools)', fontsize=12, fontweight='bold')

    pools = [(2, 7, 'Pool A\n(10 threads)', '#2196F3'),
             (5, 7, 'Pool B\n(10 threads)', '#4CAF50'),
             (8, 7, 'Pool C\n(10 threads)', '#FF9800')]

    for x, y, label, color in pools:
        circle = Circle((x, y), 1.5, facecolor=color, edgecolor='black', linewidth=2, alpha=0.7)
        ax1.add_patch(circle)
        ax1.text(x, y, label, ha='center', va='center', fontsize=10, fontweight='bold', color='white')

    # Services
    for x in [2, 5, 8]:
        ax1.arrow(x, 5.3, 0, 1.2, head_width=0.3, head_length=0.3, fc='gray', ec='gray')
        ax1.text(x, 4.5, 'Service', ha='center', fontsize=9)

    ax1.text(5, 1, 'Failure in Pool A\ndoes not affect\nPools B or C',
             ha='center', fontsize=10, style='italic', color='#D32F2F')
    ax1.axis('off')

    # Process Level
    ax2 = axes[1]
    ax2.set_xlim(0, 10)
    ax2.set_ylim(0, 10)
    ax2.set_title('Process Level\n(Container Isolation)', fontsize=12, fontweight='bold')

    processes = [(2.5, 6, 'Process A\n(Container)', '#E91E63'),
                 (7.5, 6, 'Process B\n(Container)', '#9C27B0')]

    for x, y, label, color in processes:
        rect = FancyBboxPatch((x-1.5, y-1), 3, 2,
                              boxstyle="round,pad=0.1,rounding_size=0.3",
                              facecolor=color, edgecolor='black', linewidth=2, alpha=0.7)
        ax2.add_patch(rect)
        ax2.text(x, y, label, ha='center', va='center', fontsize=10, fontweight='bold', color='white')

    # Shared nothing
    ax2.annotate('', xy=(2, 4), xytext=(2, 5),
                arrowprops=dict(arrowstyle='->', color='gray', lw=1, ls='--'))
    ax2.annotate('', xy=(8, 4), xytext=(8, 5),
                arrowprops=dict(arrowstyle='->', color='gray', lw=1, ls='--'))

    ax2.text(5, 3, 'Memory isolated\nvia containerization', ha='center', fontsize=10, style='italic')
    ax2.text(5, 1.5, 'Crash in Process A\ndoes not crash\nProcess B',
             ha='center', fontsize=10, style='italic', color='#D32F2F')
    ax2.axis('off')

    # Infrastructure Level
    ax3 = axes[2]
    ax3.set_xlim(0, 10)
    ax3.set_ylim(0, 10)
    ax3.set_title('Infrastructure Level\n(Multi-DB Architecture)', fontsize=12, fontweight='bold')

    # Database boxes
    db1 = FancyBboxPatch((0.5, 6), 4, 2,
                         boxstyle="round,pad=0.1,rounding_size=0.2",
                         facecolor='#3F51B5', edgecolor='black', linewidth=2)
    db2 = FancyBboxPatch((5.5, 6), 4, 2,
                         boxstyle="round,pad=0.1,rounding_size=0.2",
                         facecolor='#009688', edgecolor='black', linewidth=2)
    ax3.add_patch(db1)
    ax3.add_patch(db2)
    ax3.text(2.5, 7, 'Database A\n(Users)', ha='center', va='center', fontsize=11, fontweight='bold', color='white')
    ax3.text(7.5, 7, 'Database B\n(Orders)', ha='center', va='center', fontsize=11, fontweight='bold', color='white')

    # Network isolation
    ax3.annotate('', xy=(4.8, 7), xytext=(5.2, 7),
                arrowprops=dict(arrowstyle='->', color='red', lw=2))
    ax3.text(5, 7.5, 'Network\nsegment', ha='center', fontsize=9, color='red')

    ax3.text(5, 4, 'Database A failure\ndoes not affect\nDatabase B',
             ha='center', fontsize=10, style='italic', color='#D32F2F')
    ax3.text(5, 1.5, 'Scaling independent\nSecurity isolated',
             ha='center', fontsize=10, style='italic')
    ax3.axis('off')

    plt.tight_layout()
    plt.savefig('bulkhead_isolation_levels.png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print("✓ Created bulkhead_isolation_levels.png")


def create_failure_comparison():
    """Compare system behavior with and without stability patterns."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Without patterns - cascading failure
    ax1.set_xlim(0, 10)
    ax1.set_ylim(0, 10)
    ax1.set_title('WITHOUT Stability Patterns\n(Cascading Failure)', fontsize=12, fontweight='bold', color='#D32F2F')

    # Components
    components = [
        (2, 8, 'API\nGateway', '#2196F3'),
        (5, 8, 'Service\nA', '#4CAF50'),
        (8, 8, 'External\nAPI', '#FF9800'),
        (2, 5, 'Thread\nPool', '#9C27B0'),
        (5, 5, 'DB\nPool', '#E91E63'),
        (8, 5, 'Memory', '#00BCD4'),
    ]

    for x, y, label, color in components:
        rect = FancyBboxPatch((x-0.8, y-0.6), 1.6, 1.2,
                              boxstyle="round,pad=0.05,rounding_size=0.1",
                              facecolor=color, edgecolor='black', linewidth=1.5, alpha=0.8)
        ax1.add_patch(rect)
        ax1.text(x, y, label, ha='center', va='center', fontsize=8, fontweight='bold', color='white')

    # Failure cascade arrows
    arrows_style = dict(arrowstyle='->', color='red', lw=2)
    # API Gateway -> Service A (timeout)
    ax1.annotate('', xy=(4.2, 8), xytext=(3.4, 8), arrowprops={**arrows_style, 'color': 'red'})
    # Service A -> External API (timeout)
    ax1.annotate('', xy=(7.2, 8), xytext=(6.4, 8), arrowprops={**arrows_style, 'color': 'red'})
    # Service A -> Thread Pool (exhaustion)
    ax1.annotate('', xy=(3.4, 6.2), xytext=(2.6, 6.8), arrowprops={**arrows_style, 'color': 'orange'})
    # Thread Pool -> DB Pool (starvation)
    ax1.annotate('', xy=(4.2, 5), xytext=(3.4, 5), arrowprops={**arrows_style, 'color': 'orange'})
    # Thread Pool -> Memory (leak)
    ax1.annotate('', xy=(7.2, 5.8), xytext=(7.8, 5.2), arrowprops={**arrows_style, 'color': 'purple'})

    ax1.text(5, 1, 'Timeout → Resource Exhaustion\n→ Memory Leak → Crash',
             ha='center', fontsize=10, color='#D32F2F', fontweight='bold')
    ax1.axis('off')

    # With patterns - contained failure
    ax2.set_xlim(0, 10)
    ax2.set_ylim(0, 10)
    ax2.set_title('WITH Stability Patterns\n(Contained Failure)', fontsize=12, fontweight='bold', color='#4CAF50')

    # Components with protections
    components_protected = [
        (2, 8, 'API\nGateway', '#2196F3'),
        (5, 8, 'Service\nA\n(CB)', '#4CAF50'),
        (8, 8, 'External\nAPI', '#FF9800'),
        (2, 5, 'Thread\nPool\n(Bulkhead)', '#9C27B0'),
        (5, 5, 'DB\nPool', '#E91E63'),
        (8, 5, 'Cache', '#00BCD4'),
    ]

    for x, y, label, color in components_protected:
        rect = FancyBboxPatch((x-0.8, y-0.6), 1.6, 1.2,
                              boxstyle="round,pad=0.05,rounding_size=0.1",
                              facecolor=color, edgecolor='black', linewidth=1.5, alpha=0.8)
        ax2.add_patch(rect)
        ax2.text(x, y, label, ha='center', va='center', fontsize=8, fontweight='bold', color='white')

    # Protected arrows
    ax2.annotate('', xy=(4.2, 8), xytext=(3.4, 8), arrowprops=dict(arrowstyle='->', color='green', lw=2))
    ax2.annotate('', xy=(7.2, 8), xytext=(6.4, 8), arrowprops=dict(arrowstyle='->', color='gray', lw=1.5, ls='--'))

    # Circuit breaker "stop" symbol
    ax2.text(7.5, 8.3, 'CB trips\n(fail fast)', ha='center', fontsize=7, color='red', fontweight='bold')

    # Bulkhead protection
    ax2.annotate('', xy=(3.4, 6.2), xytext=(2.6, 6.8), arrowprops=dict(arrowstyle='->', color='green', lw=2))
    ax2.annotate('', xy=(7.2, 5.8), xytext=(7.8, 5.2), arrowprops=dict(arrowstyle='->', color='gray', lw=1.5, ls='--'))

    # Cache fallback
    ax2.annotate('', xy=(7.2, 6.2), xytext=(7.8, 6.8), arrowprops=dict(arrowstyle='->', color='blue', lw=1.5))

    ax2.text(5, 1, 'Circuit Breaker → Fail Fast\nBulkhead → Isolated Resources\nCache → Graceful Degradation',
             ha='center', fontsize=10, color='#4CAF50', fontweight='bold')
    ax2.axis('off')

    plt.tight_layout()
    plt.savefig('failure_comparison.png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print("✓ Created failure_comparison.png")


def create_timeout_strategy_diagram():
    """Show timeout strategy across different operation types."""
    fig, ax = plt.subplots(1, 1, figsize=(12, 6))

    operations = [
        ('Cache Lookup', 0.1, 0.5, '#4CAF50'),
        ('Internal Service', 1, 3, '#2196F3'),
        ('Database Query', 1, 5, '#FF9800'),
        ('External API', 5, 30, '#E91E63'),
        ('User-Facing Request', 30, 60, '#9C27B0'),
    ]

    y_positions = np.linspace(0.9, 0.1, len(operations))

    for i, (op, min_t, max_t, color) in enumerate(operations):
        y = y_positions[i]

        # Draw timeout range as bar
        bar = FancyBboxPatch((0.1, y-0.05), 0.8, 0.1,
                            boxstyle="round,pad=0.01",
                            facecolor=color, edgecolor='black', linewidth=1)
        ax.add_patch(bar)
        ax.text(0.5, y, op, ha='center', va='center', fontsize=10, fontweight='bold', color='white')

        # Draw timeout markers
        ax.scatter([min_t], [y], s=100, c=color, marker='|', linewidths=3)
        ax.scatter([max_t], [y], s=100, c=color, marker='|', linewidths=3)

        # Range line
        ax.plot([min_t, max_t], [y, y], color=color, linewidth=2)
        ax.text(max_t + 1, y, f'{min_t}s - {max_t}s', ha='left', va='center', fontsize=9, color=color)

    ax.set_xlim(0, 70)
    ax.set_ylim(0, 1)
    ax.set_xlabel('Timeout (seconds)', fontsize=12)
    ax.set_title('Timeout Strategy by Operation Type\n(Proportional to operation risk and user expectation)', fontsize=14, fontweight='bold')
    ax.grid(True, axis='x', alpha=0.3)
    ax.set_yticks([])

    plt.tight_layout()
    plt.savefig('timeout_strategy.png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print("✓ Created timeout_strategy.png")


def create_handshake_flow():
    """Show handshake pattern flow between client and server."""
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))

    # Client and Server boxes
    client = FancyBboxPatch((1, 3), 3, 2,
                           boxstyle="round,pad=0.1,rounding_size=0.3",
                           facecolor='#2196F3', edgecolor='black', linewidth=2)
    server = FancyBboxPatch((8, 3), 3, 2,
                           boxstyle="round,pad=0.1,rounding_size=0.3",
                           facecolor='#4CAF50', edgecolor='black', linewidth=2)
    ax.add_patch(client)
    ax.add_patch(server)
    ax.text(2.5, 4, 'Client', ha='center', va='center', fontsize=14, fontweight='bold', color='white')
    ax.text(9.5, 4, 'Server', ha='center', va='center', fontsize=14, fontweight='bold', color='white')

    # Queue/capacity visualization on server
    server_queue = FancyBboxPatch((8.5, 1), 2.5, 1.5,
                                  boxstyle="round,pad=0.05,rounding_size=0.1",
                                  facecolor='#E8F5E9', edgecolor='#4CAF50', linewidth=2)
    ax.add_patch(server_queue)
    ax.text(9.75, 1.75, 'Capacity: 50\nAvailable: 12', ha='center', va='center', fontsize=9)

    # Flow steps
    steps = [
        (4.5, 6.5, '1. Client: "Can I send work?"', '#2196F3'),
        (7.5, 6.5, '2. Server: "Yes, capacity available"', '#4CAF50'),
        (4.5, 5.5, '3. Client: Sends request within limits', '#2196F3'),
        (7.5, 4.5, '4. Server: Accepts (or rejects if full)', '#4CAF50'),
    ]

    for x, y, text, color in steps:
        ax.text(x, y, text, fontsize=10, ha='center', va='center',
               bbox=dict(boxstyle='round', facecolor='white', edgecolor=color, alpha=0.9))

    # Arrows for main flow
    ax.annotate('', xy=(7.5, 6.2), xytext=(5, 6.2),
               arrowprops=dict(arrowstyle='->', color='#2196F3', lw=2))
    ax.annotate('', xy=(4.5, 5.8), xytext=(7, 5.8),
               arrowprops=dict(arrowstyle='->', color='#4CAF50', lw=2))
    ax.annotate('', xy=(7, 5.2), xytext=(4.5, 5.2),
               arrowprops=dict(arrowstyle='->', color='#2196F3', lw=2))

    # Rejection case
    ax.annotate('', xy=(4.5, 3.8), xytext=(7, 3.8),
               arrowprops=dict(arrowstyle='->', color='#F44336', lw=2, ls='--'))
    ax.text(5.75, 3.5, '429 Too Many Requests', fontsize=9, ha='center',
           color='#F44336', fontweight='bold', style='italic')

    ax.set_xlim(0, 13)
    ax.set_ylim(0, 8)
    ax.set_title('Handshake Pattern: Client-Server Capacity Negotiation', fontsize=14, fontweight='bold')
    ax.axis('off')

    plt.tight_layout()
    plt.savefig('handshake_flow.png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print("✓ Created handshake_flow.png")


def create_stable_topology():
    """Show stable topology patterns (hub-and-spoke, mesh, tiered)."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    # Hub and Spoke
    ax1 = axes[0]
    ax1.set_xlim(0, 10)
    ax1.set_ylim(0, 10)

    # Hub
    hub = Circle((5, 5), 1.2, facecolor='#E91E63', edgecolor='black', linewidth=2)
    ax1.add_patch(hub)
    ax1.text(5, 5, 'Hub', ha='center', va='center', fontsize=11, fontweight='bold', color='white')

    # Spokes
    spoke_positions = [(5, 8), (7.5, 6.5), (7.5, 3.5), (5, 2), (2.5, 3.5), (2.5, 6.5)]
    for x, y in spoke_positions:
        circle = Circle((x, y), 0.8, facecolor='#2196F3', edgecolor='black', linewidth=1.5)
        ax1.add_patch(circle)
        ax1.text(x, y, 'Service', ha='center', va='center', fontsize=8, color='white')
        ax1.plot([5, x], [5, y], 'gray', linewidth=1, linestyle='--')

    ax1.set_title('Hub and Spoke\n(Central hub, isolated spokes)', fontsize=11, fontweight='bold')
    ax1.axis('off')

    # Mesh
    ax2 = axes[1]
    ax2.set_xlim(0, 10)
    ax2.set_ylim(0, 10)

    # Services in a mesh
    mesh_positions = [(3, 7), (7, 7), (5, 5), (3, 3), (7, 3)]
    for x, y in mesh_positions:
        circle = Circle((x, y), 0.9, facecolor='#4CAF50', edgecolor='black', linewidth=1.5)
        ax2.add_patch(circle)
        ax2.text(x, y, 'Service', ha='center', va='center', fontsize=8, color='white')

    # Interconnections (sparse mesh)
    connections = [(3, 7, 7, 7), (7, 7, 5, 5), (5, 5, 3, 3), (3, 3, 7, 3), (7, 3, 5, 5), (3, 7, 3, 3)]
    for x1, y1, x2, y2 in connections:
        ax2.plot([x1, x2], [y1, y2], 'gray', linewidth=1)

    ax2.set_title('Mesh\n(Interconnected but isolated)', fontsize=11, fontweight='bold')
    ax2.axis('off')

    # Tiered
    ax3 = axes[2]
    ax3.set_xlim(0, 10)
    ax3.set_ylim(0, 10)

    # Tiers
    tiers = [
        (5, 8.5, 'Tier 1: Gateway', '#FF9800', 3),
        (5, 5.5, 'Tier 2: Services', '#4CAF50', 3),
        (5, 2.5, 'Tier 3: Data', '#2196F3', 3),
    ]

    for x, y, label, color, width in tiers:
        rect = FancyBboxPatch((x-width/2, y-0.6), width, 1.2,
                             boxstyle="round,pad=0.05,rounding_size=0.1",
                             facecolor=color, edgecolor='black', linewidth=2)
        ax3.add_patch(rect)
        ax3.text(x, y, label, ha='center', va='center', fontsize=10, fontweight='bold', color='white')

    # Arrows between tiers
    for y in [7.2, 4.2]:
        ax3.annotate('', xy=(5, y), xytext=(5, y+0.6),
                   arrowprops=dict(arrowstyle='->', color='gray', lw=2))

    ax3.set_title('Tiered\n(Layers with clear boundaries)', fontsize=11, fontweight='bold')
    ax3.axis('off')

    plt.tight_layout()
    plt.savefig('stable_topology.png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print("✓ Created stable_topology.png")


def create_pattern_relationship_map():
    """Create a network diagram showing how patterns relate to each other."""
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))

    G = nx.Graph()

    # Add nodes with positions manually
    pos = {
        'Circuit\nBreaker': (0.3, 0.8),
        'Timeout': (0.5, 0.9),
        'Bulkhead': (0.7, 0.8),
        'Handshake': (0.9, 0.65),
        'Fail Fast': (0.2, 0.5),
        'Middleware': (0.5, 0.5),
        'Let It\nCrash': (0.8, 0.35),
        'Stable\nTopology': (0.35, 0.2),
    }

    # Add edges (relationships)
    edges = [
        ('Timeout', 'Circuit\nBreaker', 3),
        ('Circuit\nBreaker', 'Bulkhead', 2),
        ('Bulkhead', 'Handshake', 2),
        ('Fail Fast', 'Circuit\nBreaker', 2),
        ('Fail Fast', 'Timeout', 2),
        ('Middleware', 'Circuit\nBreaker', 1),
        ('Middleware', 'Handshake', 2),
        ('Let It\nCrash', 'Bulkhead', 1),
        ('Stable\nTopology', 'Bulkhead', 2),
        ('Stable\nTopology', 'Middleware', 1),
    ]

    for n1, n2, w in edges:
        G.add_edge(n1, n2, weight=w)

    # Draw nodes
    node_colors = ['#4CAF50', '#2196F3', '#FF9800', '#9C27B0', '#E91E63', '#00BCD4', '#795548', '#607D8B']
    for i, (node, (x, y)) in enumerate(pos.items()):
        circle = Circle((x, y), 0.08, facecolor=node_colors[i], edgecolor='black', linewidth=2)
        ax.add_patch(circle)
        ax.text(x, y, node, ha='center', va='center', fontsize=9, fontweight='bold', color='white')

    # Draw edges
    for (n1, n2), (x1, y1), (x2, y2) in [
        (('Timeout', 'Circuit\nBreaker'), pos['Timeout'], pos['Circuit\nBreaker']),
        (('Circuit\nBreaker', 'Bulkhead'), pos['Circuit\nBreaker'], pos['Bulkhead']),
        (('Bulkhead', 'Handshake'), pos['Bulkhead'], pos['Handshake']),
        (('Fail Fast', 'Circuit\nBreaker'), pos['Fail Fast'], pos['Circuit\nBreaker']),
        (('Fail Fast', 'Timeout'), pos['Fail Fast'], pos['Timeout']),
        (('Middleware', 'Circuit\nBreaker'), pos['Middleware'], pos['Circuit\nBreaker']),
        (('Middleware', 'Handshake'), pos['Middleware'], pos['Handshake']),
        (('Let It\nCrash', 'Bulkhead'), pos['Let It\nCrash'], pos['Bulkhead']),
        (('Stable\nTopology', 'Bulkhead'), pos['Stable\nTopology'], pos['Bulkhead']),
        (('Stable\nTopology', 'Middleware'), pos['Stable\nTopology'], pos['Middleware']),
    ]:
        ax.plot([x1, x2], [y1, y2], 'gray', linewidth=2, alpha=0.7)

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_title('Stability Patterns Relationship Map\n(How patterns work together)', fontsize=14, fontweight='bold')
    ax.axis('off')

    plt.tight_layout()
    plt.savefig('pattern_relationships.png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print("✓ Created pattern_relationships.png")


if __name__ == '__main__':
    print("Generating visualizations for Chapter 4: Stability Patterns...")
    print("-" * 50)

    create_circuit_breaker_state_machine()
    create_bulkhead_isolation()
    create_failure_comparison()
    create_timeout_strategy_diagram()
    create_handshake_flow()
    create_stable_topology()
    create_pattern_relationship_map()

    print("-" * 50)
    print("All visualizations created successfully!")
    print("Files generated:")
    print("  - circuit_breaker_state_machine.png")
    print("  - bulkhead_isolation_levels.png")
    print("  - failure_comparison.png")
    print("  - timeout_strategy.png")
    print("  - handshake_flow.png")
    print("  - stable_topology.png")
    print("  - pattern_relationships.png")
