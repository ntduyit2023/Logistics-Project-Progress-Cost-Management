"""
Pareto Frontier Visualization Script
=====================================
Script đọc kết quả JSON từ GLPO Pipeline Runner và vẽ biểu đồ
Pareto Frontier chất lượng cao để đưa vào báo cáo khoa học.

Cách chạy:
    python plot_pareto.py --input pareto_output.json --output pareto_frontier.png
"""

import argparse
import json
import os
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize

# Dùng non-interactive backend để lưu file mà không cần display
matplotlib.use("Agg")


def load_pareto_data(json_path: str):
    """Đọc file JSON đầu ra từ pipeline runner."""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    options = data.get("pareto_options", [])
    if not options:
        raise ValueError("Không tìm thấy 'pareto_options' trong file JSON!")
    return options, data.get("project_id", "Unknown")


def plot_pareto_2d(options, project_id: str, output_path: str):
    """
    Vẽ biểu đồ 2D Scatter: Makespan (giờ) vs Total Cost ($)
    - Màu sắc mỗi điểm thể hiện Risk (risk_pct %)
    - Kích thước điểm tương ứng với số lượng crashed tasks
    """
    makespans = [o["makespan_hours"] for o in options]
    costs     = [o["total_cost"] for o in options]
    risks     = [o.get("risk_pct", 0.0) for o in options]
    labels    = [o.get("option_name", f"Opt {i+1}") for i, o in enumerate(options)]
    crashed   = [len(o.get("crashed_tasks", [])) for o in options]

    # Kích thước điểm tỉ lệ với crashed tasks (min 120, max 400)
    sizes = [120 + 60 * c for c in crashed]

    fig, ax = plt.subplots(figsize=(12, 7))
    fig.patch.set_facecolor("#0f1117")
    ax.set_facecolor("#1a1d2e")

    # Vẽ đường nối Pareto frontier (sắp xếp theo makespan)
    sorted_pts = sorted(zip(makespans, costs, risks), key=lambda x: x[0])
    px = [p[0] for p in sorted_pts]
    py = [p[1] for p in sorted_pts]
    ax.plot(px, py, color="#4a9eff", lw=1.5, ls="--", alpha=0.5, zorder=1, label="Pareto Frontier")

    # Colormap theo Risk %
    norm = Normalize(vmin=min(risks), vmax=max(risks))
    cmap = plt.cm.RdYlGn_r  # Xanh = ít rủi ro, Đỏ = nhiều rủi ro

    sc = ax.scatter(
        makespans, costs,
        c=risks, cmap=cmap, norm=norm,
        s=sizes, zorder=3,
        edgecolors="white", linewidths=0.8, alpha=0.92
    )

    # Nhãn từng điểm
    for i, (x, y, lbl) in enumerate(zip(makespans, costs, labels)):
        ax.annotate(
            lbl,
            xy=(x, y),
            xytext=(6, 6),
            textcoords="offset points",
            fontsize=8.5,
            color="white",
            alpha=0.85
        )

    # Colorbar cho Risk
    cbar = plt.colorbar(sc, ax=ax, pad=0.02)
    cbar.set_label("Risk (Delay Probability %)", color="white", fontsize=11)
    cbar.ax.yaxis.set_tick_params(color="white")
    plt.setp(plt.getp(cbar.ax.axes, "yticklabels"), color="white")

    # Legend kích thước crashed tasks
    legend_sizes = [0, 1, 2, 3]
    legend_handles = [
        plt.scatter([], [], s=120 + 60 * c, c="gray", edgecolors="white", lw=0.6,
                    label=f"{c} task(s) crashed")
        for c in legend_sizes
    ]
    ax.legend(handles=legend_handles, title="Crashed Tasks",
              title_fontsize=9, fontsize=8,
              facecolor="#1a1d2e", edgecolor="#4a9eff",
              labelcolor="white", loc="upper right")

    # Styling
    ax.set_xlabel("Makespan (Hours)", color="white", fontsize=13, labelpad=10)
    ax.set_ylabel("Total Cost (USD)", color="white", fontsize=13, labelpad=10)
    ax.set_title(
        f"Pareto Frontier — Project: {project_id}\n"
        f"Trade-off: Makespan vs Cost  |  Color = Delay Risk %",
        color="white", fontsize=14, pad=16, fontweight="bold"
    )
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_edgecolor("#4a9eff")
        spine.set_linewidth(0.7)
    ax.grid(True, color="#2a2d3e", lw=0.8, alpha=0.7)

    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches="tight", facecolor=fig.get_facecolor())
    print(f"[OK] Da luu bieu do Pareto tai: {output_path}")
    plt.close()


def main():
    parser = argparse.ArgumentParser(description="GLPO Pareto Frontier Visualizer")
    parser.add_argument("--input",  type=str, required=True, help="Duong dan file JSON dau ra tu pipeline")
    parser.add_argument("--output", type=str, default="pareto_frontier.png", help="Duong dan anh PNG dau ra")
    args = parser.parse_args()

    options, project_id = load_pareto_data(args.input)
    print(f"[INFO] Tai thanh cong {len(options)} phuong an Pareto cua du an: {project_id}")
    plot_pareto_2d(options, project_id, args.output)


if __name__ == "__main__":
    main()
