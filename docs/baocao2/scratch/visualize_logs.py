import os
import json
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import matplotlib.ticker as ticker

# Set professional plotting style
sns.set_theme(style="whitegrid")
plt.rcParams.update({
    "font.size": 11,
    "axes.labelsize": 12,
    "axes.titlesize": 13,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "figure.titlesize": 14,
    "font.family": "serif",
    "text.usetex": False
})

# Paths
checkpoints_dir = r"E:\University\Year 3 - 3\DA3\ai_pipeline\models\moi\checkpoints"
image_dir = r"E:\University\Year 3 - 3\DA3\docs\baocao2\image"
os.makedirs(image_dir, exist_ok=True)

# Colors
COLOR_TRAIN = "#1e3a8a" # Dark blue
COLOR_VAL = "#b91c1c"   # Dark red
COLOR_PARETO = "#059669" # Emerald green
COLOR_ACCENT = "#d97706" # Amber

# ==========================================================
# 1. VISUALIZE PRETRAINING HISTORY (pretrain_loss.png)
# ==========================================================
pretrain_path = os.path.join(checkpoints_dir, "pretrain_history.json")
if os.path.exists(pretrain_path):
    with open(pretrain_path, "r", encoding="utf-8") as f:
        pretrain_data = json.load(f)
    
    epochs = [x["epoch"] for x in pretrain_data]
    train_loss = [x["train_loss"] for x in pretrain_data]
    val_loss = [x["val_loss"] for x in pretrain_data]
    val_mae = [x["val_mae"] for x in pretrain_data]
    val_rmse = [x["val_rmse"] for x in pretrain_data]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), dpi=300)
    
    ax1.plot(epochs, train_loss, label="Huấn luyện (Train Loss)", color=COLOR_TRAIN, linewidth=2)
    ax1.plot(epochs, val_loss, label="Kiểm thử (Val Loss)", color=COLOR_VAL, linewidth=2, linestyle="--")
    ax1.set_xlabel("Epoch")
    ax1.set_ylabel("Hàm mất mát (NLL Loss)")
    ax1.set_title("Quá trình hội tụ NLL Loss của HGT MAE")
    ax1.legend()
    ax1.grid(True, linestyle=":", alpha=0.6)
    
    ax2.plot(epochs, val_mae, label="MAE Kiểm thử", color=COLOR_ACCENT, linewidth=2)
    ax2.plot(epochs, val_rmse, label="RMSE Kiểm thử", color="#7c3aed", linewidth=2, linestyle="-.")
    ax2.set_xlabel("Epoch")
    ax2.set_ylabel("Chỉ số Sai số (Hệ số Thời lượng)")
    ax2.set_title("Sai số MAE và RMSE trong Pre-training")
    ax2.legend()
    ax2.grid(True, linestyle=":", alpha=0.6)
    
    plt.tight_layout()
    pretrain_out = os.path.join(image_dir, "pretrain_loss.png")
    plt.savefig(pretrain_out, bbox_inches="tight", dpi=300)
    plt.close()
    print(f"Generated: {pretrain_out}")

# ==========================================================
# 2. VISUALIZE 5-FOLD FINE-TUNING CONVERGENCE (epoch.jpg)
# ==========================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), dpi=300)
fold_colors = ["#3b82f6", "#ef4444", "#10b981", "#f59e0b", "#6366f1"]

for fold in range(1, 6):
    ft_path = os.path.join(checkpoints_dir, f"finetune_history_fold_{fold}.json")
    if os.path.exists(ft_path):
        with open(ft_path, "r", encoding="utf-8") as f:
            ft_data = json.load(f)
        
        epochs = [x["epoch"] for x in ft_data]
        val_r2 = [x["val_r2"] for x in ft_data]
        val_mse = [x["val_mse"] for x in ft_data]
        
        ax1.plot(epochs, val_r2, label=f"Fold {fold}", color=fold_colors[fold-1], linewidth=1.5)
        ax2.plot(epochs, val_mse, label=f"Fold {fold}", color=fold_colors[fold-1], linewidth=1.5)

ax1.set_xlabel("Epoch")
ax1.set_ylabel(r"Hệ số Xác định $R^2$ Kiểm thử")
ax1.set_title(r"Đường cong hội tụ $R^2$ qua 5-Fold Cross Validation")
ax1.set_ylim(-0.5, 1.0)
ax1.axhline(0, color="gray", linestyle="--", linewidth=0.8)
ax1.legend(loc="lower right")
ax1.grid(True, linestyle=":", alpha=0.6)

ax2.set_xlabel("Epoch")
ax2.set_ylabel("Sai số Bình phương Trung bình (MSE)")
ax2.set_title("Quá trình hội tụ MSE qua 5-Fold Cross Validation")
ax2.set_ylim(0, 0.006)
ax2.legend()
ax2.grid(True, linestyle=":", alpha=0.6)

plt.tight_layout()
epoch_out = os.path.join(image_dir, "epoch.jpg")
plt.savefig(epoch_out, bbox_inches="tight", dpi=300)
plt.close()
print(f"Generated: {epoch_out}")

# ==========================================================
# 3. VISUALIZE AI PREDICTION SCATTER (hinh3_7_regression_scatter.png)
# ==========================================================
pareto_path = os.path.join(checkpoints_dir, "C2012-04_pareto_results.json")
if os.path.exists(pareto_path):
    with open(pareto_path, "r", encoding="utf-8") as f:
        pareto_data = json.load(f)
    
    if "ai_predictions" in pareto_data:
        preds = pareto_data["ai_predictions"]
        
        expected_delay = [x["expected_delay"] for x in preds.values()]
        uncertainty_sigma = [x["uncertainty_sigma"] for x in preds.values()]
        
        fig, ax = plt.subplots(figsize=(8, 5.5), dpi=300)
        sns.regplot(x=expected_delay, y=uncertainty_sigma, ax=ax, color="#7c3aed",
                    scatter_kws={"s": 60, "alpha": 0.7, "edgecolors": "black"},
                    line_kws={"color": "red", "lw": 2})
        
        ax.set_xlabel("Dự báo Độ trễ Kỳ vọng (expected_delay - giờ)", fontweight="bold")
        ax.set_ylabel("Độ bất định Dự báo (uncertainty_sigma - giờ)", fontweight="bold")
        ax.set_title("Phân tích mối tương quan giữa Độ trễ dự báo và Độ bất định của AI", fontsize=12, fontweight="bold", pad=15)
        ax.grid(True, linestyle=":", alpha=0.6)
        
        scatter_out = os.path.join(image_dir, "hinh3_7_regression_scatter.png")
        plt.savefig(scatter_out, bbox_inches="tight", dpi=300)
        plt.close()
        print(f"Generated: {scatter_out}")

# ==========================================================
# 4. VISUALIZE PARETO FRONTIER (pareto_frontier.png)
# ==========================================================
if os.path.exists(pareto_path):
    with open(pareto_path, "r", encoding="utf-8") as f:
        pareto_data = json.load(f)
    
    if "pareto_options" in pareto_data:
        options = pareto_data["pareto_options"]
        options = sorted(options, key=lambda x: x["makespan_days"])
        
        makespan = [x["makespan_days"] for x in options]
        cost = [x["total_cost"] for x in options]
        risk = [x["risk_pct"] * 100 for x in options]
        names = [x["option_name"] for x in options]
        
        fig, ax = plt.subplots(figsize=(9.5, 6.5), dpi=300)
        
        ax.plot(makespan, cost, color="#94a3b8", linestyle="-", linewidth=2, zorder=1)
        sc = ax.scatter(makespan, cost, c=risk, cmap="plasma", s=180, edgecolors="#1e293b", linewidth=1.5, zorder=2)
        
        for i, (m, c, name) in enumerate(zip(makespan, cost, names)):
            viet_name = name.replace("Option", "P").replace("Phương án [", "P").replace("]", "")
            ax.annotate(viet_name, (m, c), textcoords="offset points", xytext=(0,12), ha='center',
                        fontsize=10, fontweight="bold", color="#1e293b",
                        bbox=dict(boxstyle="round,pad=0.2", fc="yellow", alpha=0.6, ec="orange"))
            
        ax.set_xlabel("Thời gian hoàn thành dự án Makespan (ngày)", fontweight="bold", labelpad=10)
        ax.set_ylabel("Tổng chi phí dự án (USD)", fontweight="bold", labelpad=10)
        ax.set_title("Đường cong biên Pareto Frontier dự án C2012-04\n(Đánh đổi giữa Thời gian, Chi phí và Rủi ro trễ tiến độ)", fontsize=13, fontweight="bold", pad=15)
        
        formatter = ticker.FormatStrFormatter('$%1.2f')
        ax.yaxis.set_major_formatter(formatter)
        
        cbar = fig.colorbar(sc, ax=ax)
        cbar.set_label("Xác suất trễ tiến độ Monte Carlo (%)", fontweight="bold", labelpad=10)
        
        ax.grid(True, linestyle=":", alpha=0.6)
        plt.tight_layout()
        pareto_out = os.path.join(image_dir, "pareto_frontier.png")
        plt.savefig(pareto_out, bbox_inches="tight", dpi=300)
        plt.close()
        print(f"Generated: {pareto_out}")

# ==========================================================
# 5. VISUALIZE CUMULATIVE RISK CDF (cdf_risk.png)
# ==========================================================
if os.path.exists(pareto_path):
    with open(pareto_path, "r", encoding="utf-8") as f:
        pareto_data = json.load(f)
    
    if "monte_carlo_cpm" in pareto_data:
        mc = pareto_data["monte_carlo_cpm"]
        mean = mc["makespan_mean"]
        std = mc["makespan_std"]
        p50 = mc["p50"]
        p80 = mc["p80"]
        p95 = mc["p95"]
        
        # Simulate Normal Distribution to plot CDF
        np.random.seed(42)
        samples = np.random.normal(mean, std, 10000)
        sorted_samples = np.sort(samples)
        y = np.arange(1, len(sorted_samples) + 1) / len(sorted_samples)
        
        fig, ax = plt.subplots(figsize=(8, 5.5), dpi=300)
        ax.plot(sorted_samples, y * 100, color="#2563eb", linewidth=2.5, label="Đường cong tích lũy CDF")
        
        # Mark percentiles
        percentiles = [50, 80, 95]
        values = [p50, p80, p95]
        colors = ["#10b981", "#f59e0b", "#ef4444"]
        
        for pct, val, col in zip(percentiles, values, colors):
            ax.axvline(val, color=col, linestyle="--", linewidth=1.2)
            ax.axhline(pct, color=col, linestyle="--", linewidth=1.2)
            ax.plot(val, pct, marker="o", color=col, markersize=8)
            ax.text(val + 10, pct - 4, f"P{pct} = {val:.1f}h", color=col, fontweight="bold")
            
        ax.set_xlabel("Thời gian hoàn thành dự án (giờ)", fontweight="bold")
        ax.set_ylabel("Xác suất tích lũy hoàn thành (%)", fontweight="bold")
        ax.set_title("Phân phối tích lũy CDF rủi ro tiến độ Monte Carlo\n(Dự án C2012-04)", fontsize=12, fontweight="bold", pad=15)
        ax.grid(True, linestyle=":", alpha=0.6)
        
        cdf_out = os.path.join(image_dir, "cdf_risk.png")
        plt.savefig(cdf_out, bbox_inches="tight", dpi=300)
        plt.close()
        print(f"Generated: {cdf_out}")

# ==========================================================
# 6. VISUALIZE RESOURCE PROFILES (hinh3_3_resource_before.png, hinh3_4_resource_after.png)
# ==========================================================
if os.path.exists(pareto_path):
    with open(pareto_path, "r", encoding="utf-8") as f:
        pareto_data = json.load(f)
    
    if "pareto_options" in pareto_data:
        options = pareto_data["pareto_options"]
        
        # We will use Option 1 (intensive crashing, before leveling optimization) and Option 7 (leveled option)
        # to demonstrate before vs after resource load leveling.
        opt_before = options[0] # Option 1
        opt_after = options[-1] # Option 7
        
        def calculate_load(op):
            schedule = op.get("tasks_schedule", {})
            makespan_hours = int(op.get("makespan_hours", 0))
            load = np.zeros(makespan_hours)
            for tid, t in schedule.items():
                s = int(t["start_hours"])
                f = int(t["finish_hours"])
                w = int(t["assigned_workers"]) + int(t.get("extra_workers", 0))
                load[s:f] += w
            return load
        
        load_before = calculate_load(opt_before)
        load_after = calculate_load(opt_after)
        
        # Plot Before leveling
        fig, ax = plt.subplots(figsize=(10, 4.5), dpi=300)
        ax.fill_between(range(len(load_before)), load_before, color="#fca5a5", alpha=0.6, label="Nhu cầu nhân lực")
        ax.plot(range(len(load_before)), load_before, color="#dc2626", linewidth=1.5)
        ax.axhline(13.0, color="purple", linestyle="--", linewidth=1.5, label="Định ngạch giới hạn (Peak=13)")
        ax.set_xlabel("Thời gian thực hiện dự án (giờ)")
        ax.set_ylabel("Số lượng nhân lực huy động (người)")
        ax.set_title("Biểu đồ phân bổ tài nguyên nhân lực TRƯỚC khi tối ưu hóa làm mịn", fontsize=11, fontweight="bold")
        ax.legend(loc="upper right")
        ax.set_ylim(0, 15)
        ax.grid(True, linestyle=":", alpha=0.6)
        res_before_out = os.path.join(image_dir, "hinh3_3_resource_before.png")
        plt.savefig(res_before_out, bbox_inches="tight", dpi=300)
        plt.close()
        print(f"Generated: {res_before_out}")
        
        # Plot After leveling
        fig, ax = plt.subplots(figsize=(10, 4.5), dpi=300)
        ax.fill_between(range(len(load_after)), load_after, color="#86efac", alpha=0.6, label="Nhu cầu nhân lực")
        ax.plot(range(len(load_after)), load_after, color="#16a34a", linewidth=1.5)
        ax.axhline(11.0, color="purple", linestyle="--", linewidth=1.5, label="Định ngạch giới hạn (Peak=11)")
        ax.set_xlabel("Thời gian thực hiện dự án (giờ)")
        ax.set_ylabel("Số lượng nhân lực huy động (người)")
        ax.set_title("Biểu đồ phân bổ tài nguyên nhân lực SAU khi tối ưu hóa làm mịn", fontsize=11, fontweight="bold")
        ax.legend(loc="upper right")
        ax.set_ylim(0, 15)
        ax.grid(True, linestyle=":", alpha=0.6)
        res_after_out = os.path.join(image_dir, "hinh3_4_resource_after.png")
        plt.savefig(res_after_out, bbox_inches="tight", dpi=300)
        plt.close()
        print(f"Generated: {res_after_out}")
