import matplotlib.pyplot as plt
import matplotlib.patches as patches

def draw_diagram():
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')

    # Draw Title
    ax.text(5, 5.5, "Distributed Job Scheduler (Overdrive) Architecture", 
            fontsize=12, fontweight='bold', ha='center', color='#0f111c')

    # Box styles
    box_blue = dict(boxstyle="round,pad=0.3", facecolor="#e0e7ff", edgecolor="#6366f1", lw=2)
    box_green = dict(boxstyle="round,pad=0.3", facecolor="#ecfdf5", edgecolor="#10b981", lw=2)
    box_orange = dict(boxstyle="round,pad=0.3", facecolor="#fffbeb", edgecolor="#f59e0b", lw=2)

    # Nodes
    ax.text(1.5, 3.5, "User Dashboard\n(HTML5 / CSS / JS)", ha='center', va='center', bbox=box_blue, fontsize=9)
    ax.text(4.5, 3.5, "FastAPI API Gateway\n(Web Server)", ha='center', va='center', bbox=box_blue, fontsize=9)
    ax.text(7.5, 3.5, "Relational SQLite DB\n(WAL Journal Mode)", ha='center', va='center', bbox=box_orange, fontsize=9)
    
    ax.text(4.5, 1.5, "Cron Scheduler\n(croniter daemon)", ha='center', va='center', bbox=box_green, fontsize=9)
    ax.text(7.5, 1.5, "Worker Fleet\n(Atomic Claims / Executor)", ha='center', va='center', bbox=box_green, fontsize=9)

    # Arrows
    # Dashboard <-> API Gateway
    ax.annotate('', xy=(3.2, 3.5), xytext=(2.8, 3.5), arrowprops=dict(arrowstyle="<->", lw=1.5, color="#6b7280"))
    
    # API Gateway <-> SQLite
    ax.annotate('', xy=(6.2, 3.5), xytext=(5.8, 3.5), arrowprops=dict(arrowstyle="<->", lw=1.5, color="#6b7280"))
    
    # Cron -> SQLite
    ax.annotate('', xy=(7.0, 1.5), xytext=(5.6, 1.5), arrowprops=dict(arrowstyle="->", lw=1.5, color="#6b7280"))
    ax.text(6.3, 1.7, "Enqueue", ha='center', fontsize=8, color="#4b5563")

    # Worker <-> SQLite
    ax.annotate('', xy=(7.5, 2.3), xytext=(7.5, 2.7), arrowprops=dict(arrowstyle="<->", lw=1.5, color="#6b7280"))
    ax.text(7.9, 2.5, "Atomic claim\n& Heartbeat", va='center', fontsize=8, color="#4b5563")

    # Cron -> API Gateway / DB relationship arrow
    ax.annotate('', xy=(4.5, 2.7), xytext=(4.5, 2.3), arrowprops=dict(arrowstyle="<-", lw=1.5, color="#6b7280"))

    # Save
    plt.tight_layout()
    plt.savefig("architecture_diagram.png", dpi=300, bbox_inches='tight')
    print("Architecture diagram successfully generated: architecture_diagram.png")

if __name__ == "__main__":
    draw_diagram()
