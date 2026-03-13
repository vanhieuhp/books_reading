"""
Observability Architecture Visualization
Chapter 11: Transparency - Concept Map
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# Create figure with two subplots
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

# ============== LEFT: Observability Stack ==============
ax1.set_xlim(0, 10)
ax1.set_ylim(0, 10)
ax1.set_title("The Observability Stack", fontsize=14, fontweight='bold')
ax1.axis('off')

# Application box
app_box = mpatches.FancyBboxPatch((0.5, 7), 3.5, 2,
                                   boxstyle="round,pad=0.1",
                                   facecolor='#E3F2FD', edgecolor='#1976D2', linewidth=2)
ax1.add_patch(app_box)
ax1.text(2.25, 8.5, "Application\n(Your Code)", ha='center', va='center', fontsize=10, fontweight='bold')
ax1.text(2.25, 7.8, "- Structured Logs\n- Metrics\n- Traces\n- Health Checks",
         ha='center', va='center', fontsize=8)

# Collectors
collectors = mpatches.FancyBboxPatch((4.5, 7), 2, 2,
                                      boxstyle="round,pad=0.1",
                                      facecolor='#FFF3E0', edgecolor='#F57C00', linewidth=2)
ax1.add_patch(collectors)
ax1.text(5.5, 8.5, "Collectors", ha='center', va='center', fontsize=10, fontweight='bold')
ax1.text(5.5, 7.8, "- Filebeat/Fluentd\n- Prometheus\n- OpenTelemetry",
         ha='center', va='center', fontsize=8)

# Storage layer
storage = mpatches.FancyBboxPatch((0.5, 4), 3.5, 2,
                                   boxstyle="round,pad=0.1",
                                   facecolor='#E8F5E9', edgecolor='#388E3C', linewidth=2)
ax1.add_patch(storage)
ax1.text(2.25, 5.5, "Storage Layer", ha='center', va='center', fontsize=10, fontweight='bold')
ax1.text(2.25, 4.8, "- Elasticsearch\n- Prometheus TSDB\n- Jaeger",
         ha='center', va='center', fontsize=8)

# Query/Visualization
viz = mpatches.FancyBboxPatch((4.5, 4), 3.5, 2,
                               boxstyle="round,pad=0.1",
                               facecolor='#FCE4EC', edgecolor='#C2185B', linewidth=2)
ax1.add_patch(viz)
ax1.text(6.25, 5.5, "Query & Viz", ha='center', va='center', fontsize=10, fontweight='bold')
ax1.text(6.25, 4.8, "- Kibana\n- Grafana\n- Jaeger UI",
         ha='center', va='center', fontsize=8)

# Alerting
alerting = mpatches.FancyBboxPatch((2.5, 1.5), 3, 1.5,
                                    boxstyle="round,pad=0.1",
                                    facecolor='#FFEBEE', edgecolor='#D32F2F', linewidth=2)
ax1.add_patch(alerting)
ax1.text(4, 2.7, "Alerting & Automation", ha='center', va='center', fontsize=10, fontweight='bold')
ax1.text(4, 2.2, "- Alertmanager\n- PagerDuty\n- Runbooks",
         ha='center', va='center', fontsize=8)

# Arrows
ax1.annotate('', xy=(4.3, 8), xytext=(1.5, 8),
            arrowprops=dict(arrowstyle='->', color='#1976D2', lw=2))
ax1.annotate('', xy=(4.5, 7), xytext=(4.5, 7.8),
            arrowprops=dict(arrowstyle='->', color='#F57C00', lw=2))
ax1.annotate('', xy=(2.5, 6), xytext=(2.5, 6.8),
            arrowprops=dict(arrowstyle='->', color='#388E3C', lw=2))
ax1.annotate('', xy=(4.5, 5.5), xytext=(4.5, 6),
            arrowprops=dict(arrowstyle='->', color='#C2185B', lw=2))
ax1.annotate('', xy=(4, 1.5), xytext=(4, 4),
            arrowprops=dict(arrowstyle='->', color='#D32F2F', lw=2))

# ============== RIGHT: Metrics Flow ==============
ax2.set_xlim(0, 10)
ax2.set_ylim(0, 10)
ax2.set_title("Metrics Collection: Pull vs Push", fontsize=14, fontweight='bold')
ax2.axis('off')

# Push Model (left side)
push_box = mpatches.FancyBboxPatch((0.5, 6), 4, 3,
                                    boxstyle="round,pad=0.1",
                                    facecolor='#E1F5FE', edgecolor='#0288D1', linewidth=2)
ax2.add_patch(push_box)
ax2.text(2.5, 8.5, "PUSH Model", ha='center', va='center', fontsize=12, fontweight='bold')
ax2.text(2.5, 7.8, "App -> Agent -> Aggregator", ha='center', va='center', fontsize=9, style='italic')
ax2.text(2.5, 7.2, "- Lower latency\n- Real-time\n- StatsD, DataDog", ha='center', va='center', fontsize=9)

# Pull Model (right side)
pull_box = mpatches.FancyBboxPatch((5.5, 6), 4, 3,
                                    boxstyle="round,pad=0.1",
                                    facecolor='#E8EAF6', edgecolor='#3F51B5', linewidth=2)
ax2.add_patch(pull_box)
ax2.text(7.5, 8.5, "PULL Model", ha='center', va='center', fontsize=12, fontweight='bold')
ax2.text(7.5, 7.8, "Scrape -> /metrics Endpoint", ha='center', va='center', fontsize=9, style='italic')
ax2.text(7.5, 7.2, "- Single endpoint\n- Easy to secure\n- Prometheus", ha='center', va='center', fontsize=9)

# RED Method box
red_box = mpatches.FancyBboxPatch((0.5, 2.5), 4, 2.5,
                                   boxstyle="round,pad=0.1",
                                   facecolor='#FFF8E1', edgecolor='#FFA000', linewidth=2)
ax2.add_patch(red_box)
ax2.text(2.5, 4.3, "RED Method (Per Service)", ha='center', va='center', fontsize=11, fontweight='bold')
ax2.text(2.5, 3.7, "Rate: requests/sec\nErrors: error rate\nDuration: p50/p95/p99", ha='center', va='center', fontsize=9)

# USE Method box
use_box = mpatches.FancyBboxPatch((5.5, 2.5), 4, 2.5,
                                   boxstyle="round,pad=0.1",
                                   facecolor='#F3E5F5', edgecolor='#7B1FA2', linewidth=2)
ax2.add_patch(use_box)
ax2.text(7.5, 4.3, "USE Method (Per Resource)", ha='center', va='center', fontsize=11, fontweight='bold')
ax2.text(7.5, 3.7, "Utilization: % capacity\nSaturation: overload amount\nErrors: error count", ha='center', va='center', fontsize=9)

plt.tight_layout()
plt.savefig('observability_architecture.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.show()
print("Generated: observability_architecture.png")
