import matplotlib.pyplot as plt

def draw_diagram():
    fig, ax = plt.subplots(figsize=(8.5, 5))
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
    ax.text(1.5, 3.8, "User Dashboard\n(HTML5 / CSS / JS)", ha='center', va='center', bbox=box_blue, fontsize=9)
    ax.text(4.8, 3.8, "FastAPI API Gateway\n(Web Server)", ha='center', va='center', bbox=box_blue, fontsize=9)
    ax.text(8.2, 3.8, "Relational SQLite DB\n(WAL Journal Mode)", ha='center', va='center', bbox=box_orange, fontsize=9)
    
    ax.text(4.8, 1.6, "Cron Scheduler\n(croniter daemon)", ha='center', va='center', bbox=box_green, fontsize=9)
    ax.text(8.2, 1.6, "Worker Fleet\n(Atomic Claims / Executor)", ha='center', va='center', bbox=box_green, fontsize=9)

    # Arrows
    # Dashboard <-> API Gateway
    ax.annotate('', xy=(3.5, 3.8), xytext=(2.8, 3.8), arrowprops=dict(arrowstyle="<->", lw=1.5, color="#6b7280"))
    
    # API Gateway <-> SQLite
    ax.annotate('', xy=(6.8, 3.8), xytext=(6.1, 3.8), arrowprops=dict(arrowstyle="<->", lw=1.5, color="#6b7280"))
    
    # Cron -> API Gateway (Pointing UP)
    ax.annotate('', xy=(4.8, 3.1), xytext=(4.8, 2.2), arrowprops=dict(arrowstyle="->", lw=1.5, color="#6b7280"))
    ax.text(4.2, 2.6, "Schedules Job", ha='center', va='center', fontsize=8, color="#4b5563")

    # Worker <-> SQLite (Pointing UP)
    ax.annotate('', xy=(8.2, 3.1), xytext=(8.2, 2.2), arrowprops=dict(arrowstyle="<->", lw=1.5, color="#6b7280"))
    ax.text(8.9, 2.6, "Claims Job &\nHeartbeats", ha='left', va='center', fontsize=8, color="#4b5563")

    # Save
    plt.tight_layout()
    plt.savefig("architecture_diagram.png", dpi=300, bbox_inches='tight')
    print("Architecture diagram successfully generated: architecture_diagram.png")

if __name__ == "__main__":
    draw_diagram()
