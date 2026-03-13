#!/usr/bin/env python3
"""
Chapter 8: Interconnect - Visualization Generator
Network boundary concepts and failure mode diagrams

Run: python 02_visualizations.py
Output: chapter8_*.png files
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# Set style
plt.style.use('seaborn-v0_8-whitegrid')


def create_network_boundary_diagram():
    """Create network boundary architecture diagram"""
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))

    colors = {
        'client': '#4ECDC4',
        'gateway': '#FF6B6B',
        'service': '#95E1D3',
        'database': '#F38181',
        'external': '#FCE38A',
        'fail': '#E74C3C',
        'success': '#2ECC71'
    }

    def draw_box(ax, x, y, w, h, color, label, fontsize=10):
        rect = mpatches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05",
                                        facecolor=color, edgecolor='black', linewidth=2)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h/2, label, ha='center', va='center',
                fontsize=fontsize, fontweight='bold', wrap=True)

    # Client tier
    draw_box(ax, 1, 7, 2, 1.2, colors['client'], 'Client\n(Application)')

    # API Gateway
    draw_box(ax, 4.5, 7, 2.5, 1.2, colors['gateway'], 'API Gateway\n(Load Balancer)')

    # DMZ Service
    draw_box(ax, 8, 7, 2, 1.2, colors['service'], 'DMZ Service\n(Public API)')

    # Internal services
    draw_box(ax, 4.5, 4.5, 2, 1.2, colors['service'], 'Service A')
    draw_box(ax, 7, 4.5, 2, 1.2, colors['service'], 'Service B')

    # Database
    draw_box(ax, 5.75, 2, 1.5, 1.2, colors['database'], 'Database')

    # External
    draw_box(ax, 11, 7, 2, 1.2, colors['external'], 'External\nAPI')

    # Draw arrows with labels
    arrow_style = dict(arrowstyle='->', lw=2, color='#34495E')

    # Client to Gateway
    ax.annotate('', xy=(4.5, 7.6), xytext=(3, 7.6), arrowprops=arrow_style)
    ax.text(3.75, 7.8, 'DNS Resolution', fontsize=9)

    # Gateway to DMZ
    ax.annotate('', xy=(8, 7.6), xytext=(7, 7.6), arrowprops=arrow_style)
    ax.text(7.25, 7.8, 'Route', fontsize=9)

    # DMZ to Service A
    ax.annotate('', xy=(6.5, 5.7), xytext=(8, 5.7), arrowprops=arrow_style)
    ax.text(7, 5.9, 'Internal API', fontsize=9)

    # Service A to Service B
    ax.annotate('', xy=(7, 5.2), xytext=(6.5, 5.2), arrowprops=arrow_style)
    ax.text(6.5, 5.35, 'mTLS', fontsize=9)

    # Service A to Database
    ax.annotate('', xy=(5.75, 3.3), xytext=(5.75, 4.5), arrowprops=arrow_style)
    ax.text(6, 4, 'Connection Pool', fontsize=9, rotation=90)

    # External API
    ax.annotate('', xy=(11, 7.6), xytext=(10, 7.6), arrowprops=arrow_style)
    ax.text(10.25, 7.8, '3rd Party', fontsize=9)

    # Add boundary boxes
    boundary1 = mpatches.FancyBboxPatch((0.5, 6.5), 13, 2, boxstyle="round,pad=0.1",
                                        facecolor='none', edgecolor='#E74C3C', linewidth=2, linestyle='--')
    ax.add_patch(boundary1)
    ax.text(0.7, 8.3, 'External Boundary', fontsize=9, color='#E74C3C')

    boundary2 = mpatches.FancyBboxPatch((4, 3.5), 5.5, 2.5, boxstyle="round,pad=0.1",
                                        facecolor='none', edgecolor='#2ECC71', linewidth=2, linestyle='--')
    ax.add_patch(boundary2)
    ax.text(4.2, 5.8, 'Internal', fontsize=9, color='#2ECC71')

    # Failure mode annotations
    ax.text(1, 5.5, 'FAILURE MODES:', fontsize=11, fontweight='bold')
    failures = [
        '1. DNS resolution fails',
        '2. LB health check misfires',
        '3. Connection pool exhaustion',
        '4. Firewall rule blocks',
        '5. External API timeout'
    ]
    for i, fail in enumerate(failures):
        ax.text(1, 5.2 - i*0.35, f'• {fail}', fontsize=9, color='#E74C3C')

    ax.set_xlim(0, 14)
    ax.set_ylim(1, 9)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('Network Boundary Architecture — Where Failures Occur', fontsize=14, fontweight='bold', pad=20)

    plt.tight_layout()
    plt.savefig('chapter8_network_boundaries.png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.show()
    print("Generated: chapter8_network_boundaries.png")


def create_circuit_breaker_state_diagram():
    """Create circuit breaker state machine diagram"""
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))

    states = {
        'CLOSED': (3, 5),
        'OPEN': (7, 5),
        'HALF-OPEN': (5, 2)
    }

    colors = {
        'CLOSED': '#2ECC71',
        'OPEN': '#E74C3C',
        'HALF-OPEN': '#F39C12'
    }

    # Draw states
    for state, (x, y) in states.items():
        circle = mpatches.Circle((x, y), 1, facecolor=colors[state],
                                  edgecolor='black', linewidth=2)
        ax.add_patch(circle)
        ax.text(x, y, state, ha='center', va='center',
                fontsize=14, fontweight='bold', color='white')

    # Draw transitions
    arrow_style = dict(arrowstyle='->', lw=2, color='#34495E')

    # CLOSED -> OPEN (failure threshold exceeded)
    ax.annotate('', xy=(6, 5), xytext=(4, 5), arrowprops=arrow_style)
    ax.text(5, 5.4, 'Failures >= threshold', fontsize=9)

    # OPEN -> HALF-OPEN (timeout)
    ax.annotate('', xy=(5.3, 3), xytext=(6.7, 3), arrowprops=arrow_style)
    ax.text(6, 2.7, 'Timeout expires', fontsize=9)

    # HALF-OPEN -> CLOSED (success threshold)
    ax.annotate('', xy=(3.3, 4), xytext=(4.7, 4), arrowprops=arrow_style)
    ax.text(4, 4.4, 'Successes >= threshold', fontsize=9)

    # HALF-OPEN -> OPEN (failure in half-open)
    ax.annotate('', xy=(7, 3), xytext=(7, 4), arrowprops=arrow_style)
    ax.text(7.3, 3.5, 'Failure', fontsize=9)

    # Add state descriptions
    descriptions = {
        'CLOSED': 'Normal operation\nRequests flow through',
        'OPEN': 'Failure mode\nRequests fail fast',
        'HALF-OPEN': 'Testing\nProbing for recovery'
    }

    for state, (x, y) in states.items():
        ax.text(x + 1.8, y, descriptions[state], fontsize=9,
                va='center', ha='left',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    ax.set_xlim(0, 12)
    ax.set_ylim(0, 7)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('Circuit Breaker State Machine', fontsize=14, fontweight='bold', pad=20)

    plt.tight_layout()
    plt.savefig('chapter8_circuit_breaker.png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.show()
    print("Generated: chapter8_circuit_breaker.png")


def create_dns_resolution_flow():
    """Create DNS resolution flow diagram"""
    fig, ax = plt.subplots(1, 1, figsize=(14, 8))

    # Components
    components = [
        (1, 6, 'Client', '#4ECDC4'),
        (3, 6, 'Local\nResolver', '#95E1D3'),
        (5, 8, 'Root\nServer', '#F39C12'),
        (7, 8, 'TLD\nServer', '#F39C12'),
        (9, 8, 'Authoritative\nServer', '#F39C12'),
        (11, 6, 'Target\nServer', '#F38181'),
    ]

    for x, y, label, color in components:
        rect = mpatches.FancyBboxPatch((x-0.7, y-0.6), 1.4, 1.2,
                                        boxstyle="round,pad=0.05",
                                        facecolor=color, edgecolor='black', linewidth=2)
        ax.add_patch(rect)
        ax.text(x, y, label, ha='center', va='center', fontsize=9, fontweight='bold')

    # Flow arrows
    arrows = [
        (1.7, 6, 2.3, 6, '1. Query'),
        (3.7, 6, 4.3, 6.8, '2. Refer'),
        (5, 7.3, 5, 7.6, ''),
        (5.7, 8, 6.3, 8, '3. Refer'),
        (7, 7.3, 7, 7.6, ''),
        (7.7, 8, 8.3, 8, '4. Refer'),
        (9, 7.3, 9, 7.6, ''),
        (10.3, 6, 9.7, 6, '5. IP Answer'),
        (2.3, 5.3, 1.7, 5.6, '6. Cache'),
    ]

    for x1, y1, x2, y2, label in arrows:
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='->', lw=1.5, color='#34495E'))
        if label:
            mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
            ax.text(mid_x, mid_y + 0.2, label, fontsize=8, ha='center')

    ax.set_xlim(0, 12)
    ax.set_ylim(4.5, 9.5)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('DNS Resolution Flow (Recursive Query)', fontsize=14, fontweight='bold', pad=20)

    plt.tight_layout()
    plt.savefig('chapter8_dns_flow.png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.show()
    print("Generated: chapter8_dns_flow.png")


def create_connection_pool_diagram():
    """Create connection pool behavior diagram"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Pool size vs performance
    pool_sizes = np.arange(1, 51)
    ideal_throughput = 100 * (1 - np.exp(-pool_sizes / 10))
    actual_throughput = 100 * (1 - np.exp(-pool_sizes / 10)) * (1 - 0.01 * pool_sizes)

    ax1.plot(pool_sizes, ideal_throughput, 'g--', label='Ideal (no contention)', linewidth=2)
    ax1.plot(pool_sizes, actual_throughput, 'b-', label='Actual (with contention)', linewidth=2)
    ax1.axvline(x=10, color='r', linestyle=':', label='Optimal pool size')
    ax1.set_xlabel('Pool Size (connections)', fontsize=11)
    ax1.set_ylabel('Throughput (req/s)', fontsize=11)
    ax1.set_title('Connection Pool: Size vs Throughput', fontsize=12, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Pool states
    states = ['Available', 'In Use', 'Waiting', 'Failed']
    colors = ['#2ECC71', '#3498DB', '#F39C12', '#E74C3C']

    # Simulate pool states over time
    np.random.seed(42)
    time_points = np.arange(0, 100)
    available = 5 + np.random.randn(100).cumsum()
    available = np.clip(available, 0, 10)
    in_use = 10 - available

    ax2.stackplot(time_points, available, in_use,
                  labels=['Available', 'In Use'],
                  colors=['#2ECC71', '#3498DB'], alpha=0.7)
    ax2.set_xlabel('Time (seconds)', fontsize=11)
    ax2.set_ylabel('Connections', fontsize=11)
    ax2.set_title('Connection Pool Utilization Over Time', fontsize=12, fontweight='bold')
    ax2.legend(loc='upper right')
    ax2.set_ylim(0, 10)

    plt.tight_layout()
    plt.savefig('chapter8_connection_pool.png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.show()
    print("Generated: chapter8_connection_pool.png")


def create_load_balancer_comparison():
    """Compare load balancing algorithms"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Request distribution
    n_requests = 100

    # Round Robin
    ax = axes[0, 0]
    servers = ['Server A', 'Server B', 'Server C']
    counts_rr = [34, 33, 33]
    colors = ['#4ECDC4', '#FF6B6B', '#95E1D3']
    ax.bar(servers, counts_rr, color=colors, edgecolor='black')
    ax.set_title('Round Robin', fontsize=12, fontweight='bold')
    ax.set_ylabel('Requests')
    ax.set_ylim(0, 50)

    # Least Connections (simulated)
    ax = axes[0, 1]
    counts_lc = [20, 40, 40]  # Server B has more existing connections
    ax.bar(servers, counts_lc, color=colors, edgecolor='black')
    ax.set_title('Least Connections', fontsize=12, fontweight='bold')
    ax.set_ylabel('Requests')
    ax.set_ylim(0, 50)

    # IP Hash (consistent hashing)
    ax = axes[1, 0]
    counts_hash = [50, 25, 25]  # Some IPs consistently map to Server A
    ax.bar(servers, counts_hash, color=colors, edgecolor='black')
    ax.set_title('IP Hash (Session Affinity)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Requests')
    ax.set_ylim(0, 60)

    # Weighted (capacity-based)
    ax = axes[1, 1]
    counts_weighted = [50, 30, 20]  # Server A has 50% capacity, B 30%, C 20%
    ax.bar(servers, counts_weighted, color=colors, edgecolor='black')
    ax.set_title('Weighted (by Capacity)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Requests')
    ax.set_ylim(0, 60)

    fig.suptitle('Load Balancing Algorithm Comparison', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig('chapter8_lb_algorithms.png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.show()
    print("Generated: chapter8_lb_algorithms.png")


if __name__ == '__main__':
    print("Generating Chapter 8 visualizations...")
    create_network_boundary_diagram()
    create_circuit_breaker_state_diagram()
    create_dns_resolution_flow()
    create_connection_pool_diagram()
    create_load_balancer_comparison()
    print("\nAll visualizations generated successfully!")
