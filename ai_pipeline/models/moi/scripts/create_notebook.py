import os
import sys
import json
import re
import nbformat as nbf

def parse_hpo_log(log_path):
    trials = []
    if not os.path.exists(log_path):
        return trials
    with open(log_path, 'r') as f:
        lines = f.readlines()
    for line in lines:
        if line.startswith("[Trial "):
            # [Trial 0] Mean R2: 0.3440 | Params: {'lr': 0.00117, ...}
            match = re.search(r'\[Trial (\d+)\] Mean R2: ([-\d\.]+) \| Params: (\{.*\})', line)
            if match:
                trial_id = int(match.group(1))
                r2 = float(match.group(2))
                params = eval(match.group(3))
                trials.append({"trial": trial_id, "r2": r2, "params": params})
    return trials

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))
    
    nb = nbf.v4.new_notebook()
    
    text_1 = """# Báo cáo Toàn diện Hiệu suất HGT & Tối ưu hóa (HPO)
Báo cáo này được tự động xuất ra để:
1. Đánh giá Learning Curve qua các Epoch của mô hình xuất sắc nhất.
2. Phân tích quá trình dò tham số của Optuna (15 Trials).
3. So sánh mô hình hoàn thiện với các phiên bản Baseline trước đây.
4. Trực quan hóa giá trị Thực tế và Dự báo trên đồ thị phân tán."""
    
    code_1 = """import json
import os
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd

sns.set_theme(style="whitegrid")

# Load final evaluation data
data_path = "../ai_pipeline/data/results/final_evaluation.json"
with open(data_path, "r") as f:
    results = json.load(f)
    
# Load HPO Log Data (injected dynamically)
hpo_trials = [TRIAL_DATA_PLACEHOLDER]
"""

    text_2 = """## 1. So Sánh Các Phiên Bản Mô Hình (Baseline vs SOTA)
Sự tiến hóa của mô hình qua 3 giai đoạn:"""

    code_2 = """baseline_scores = {
    "Baseline HGT (No Context)": -0.11,
    "Transductive HGT (20% Context)": 0.24,
    "SOTA: Pretrain + Transductive + HPO": 0.38
}

plt.figure(figsize=(9, 5))
models = list(baseline_scores.keys())
r2_vals = list(baseline_scores.values())

colors = ['salmon', 'skyblue', 'teal']
ax = sns.barplot(x=r2_vals, y=models, palette=colors)
for p in ax.patches:
    ax.annotate(f"{p.get_width():.2f}", 
                (p.get_width(), p.get_y() + p.get_height() / 2.), 
                ha='left', va='center', fontsize=12, color='black', xytext=(5, 0), textcoords='offset points')

plt.title('Tiến trình cải thiện Mean R² qua các Phiên bản', fontsize=14, fontweight='bold')
plt.xlabel('Mean R² (Higher is better)', fontsize=12)
plt.axvline(0, color='red', linestyle='--', linewidth=1)
plt.xlim(-0.2, 0.5)
plt.tight_layout()
plt.show()
"""

    text_3 = """## 2. Đường Cong Huấn Luyện (Learning Curve) qua từng Epoch
Chi tiết quá trình học (Train/Val Loss và Val R²) qua 100 Epochs cho TOÀN BỘ 5 DỰ ÁN."""

    code_3 = """projects = results.get("projects", [])
if projects:
    fig, axes = plt.subplots(len(projects), 1, figsize=(10, 5 * len(projects)))
    if len(projects) == 1:
        axes = [axes]
        
    for idx, proj in enumerate(projects):
        history = results.get("epoch_history", {}).get(proj, {})
        ax1 = axes[idx]
        if history and len(history.get('train_loss', [])) > 0:
            epochs = range(1, len(history['train_loss']) + 1)
            
            # Loss Axis
            ax1.plot(epochs, history['train_loss'], 'b-', label='Train Loss')
            ax1.plot(epochs, history['val_loss'], 'r-', label='Val Loss')
            ax1.set_xlabel('Epochs', fontsize=11)
            ax1.set_ylabel('Loss', color='k', fontsize=11)
            ax1.legend(loc='upper right')
            
            # R2 Axis
            ax2 = ax1.twinx()
            ax2.plot(epochs, history['val_r2'], 'g--', label='Val R²')
            ax2.set_ylabel('R² Score', color='g', fontsize=11)
            ax2.legend(loc='lower right')
            
            ax1.set_title(f'Learning Curve - Dự án {proj}', fontsize=13, fontweight='bold')
        else:
            ax1.set_title(f'Dự án {proj} (Không có dữ liệu)', fontsize=13)
            ax1.axis('off')
            
    plt.tight_layout()
    plt.show()
else:
    print("Khong co du lieu epoch_history.")
"""
    
    text_4 = """## 3. Phân tích Các vòng lặp Tuning (Optuna HPO)
15 vòng lặp Optuna đã duyệt qua các tổ hợp tham số nào và tối ưu điểm R² ra sao?"""

    code_4 = """if hpo_trials and len(hpo_trials[0]) > 0:
    df_hpo = pd.DataFrame([
        {
            "Trial": t['trial'],
            "R2": t['r2'],
            "Learning Rate": t['params']['lr'],
            "Noise": t['params']['noise_std'],
            "Dropout": t['params']['edge_drop_rate'],
            "Mixup": t['params']['mixup_alpha']
        } for t in hpo_trials[0]
    ])
    
    # Plot R2 over trials
    plt.figure(figsize=(10, 4))
    plt.plot(df_hpo['Trial'], df_hpo['R2'], marker='o', color='purple', linestyle='-', linewidth=2)
    plt.title('Sự cải thiện R² qua 15 vòng lặp Optuna', fontsize=14, fontweight='bold')
    plt.xlabel('Trial', fontsize=12)
    plt.ylabel('Mean R²', fontsize=12)
    plt.grid(True)
    plt.tight_layout()
    plt.show()
    
    # Plot parameter scatter
    fig, axes = plt.subplots(1, 4, figsize=(18, 4))
    sns.scatterplot(x='Learning Rate', y='R2', data=df_hpo, ax=axes[0], color='blue')
    axes[0].set_xscale('log')
    sns.scatterplot(x='Noise', y='R2', data=df_hpo, ax=axes[1], color='orange')
    sns.scatterplot(x='Dropout', y='R2', data=df_hpo, ax=axes[2], color='green')
    sns.scatterplot(x='Mixup', y='R2', data=df_hpo, ax=axes[3], color='red')
    
    plt.suptitle('Ảnh hưởng của Siêu tham số đến Mean R²', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.show()
else:
    print("Khong tim thay du lieu HPO Trials.")
"""

    text_5 = """## 4. Kết quả R² Phân rã theo Kích thước Dự án
(Hiệu suất phụ thuộc vào số lượng công việc)"""
    
    code_5 = """fold_metrics = results['fold_metrics']
df_metrics = pd.DataFrame(fold_metrics)

plt.figure(figsize=(10, 5))
ax = sns.barplot(x='project', y='r2', data=df_metrics, palette='viridis')
plt.title('Điểm R² (Độ chuẩn xác) phân chia theo từng Dự án', fontsize=14, fontweight='bold')
plt.xlabel('Mã Dự án', fontsize=12)
plt.ylabel('R² Score', fontsize=12)
plt.axhline(0, color='red', linestyle='--', linewidth=1)

for p in ax.patches:
    ax.annotate(f"{p.get_height():.2f}", 
                (p.get_x() + p.get_width() / 2., p.get_height()), 
                ha='center', va='bottom', fontsize=11, color='black', xytext=(0, 5), textcoords='offset points')

for index, row in df_metrics.iterrows():
    ax.text(index, min(0, row['r2']) - 0.05, f"({row['total_tasks']} tasks)", color='blue', ha="center", fontsize=10)

plt.ylim(min(df_metrics['r2']) - 0.1, max(df_metrics['r2']) + 0.1)
plt.tight_layout()
plt.show()
"""

    text_6 = """## 5. So sánh Trực quan: Giá trị Thực tế vs Dự báo (Trên toàn bộ 5 dự án)
Trực quan hóa mức độ sai số trên cả 5 dự án. Các điểm dữ liệu càng bám sát đường chéo đứt khúc màu đỏ thì mô hình dự báo càng chuẩn."""

    code_6 = """projects = results.get("projects", [])
if projects:
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    axes = axes.flatten()
    
    for idx, proj in enumerate(projects):
        ax = axes[idx]
        y_true = np.array(results.get('predictions', {}).get(proj, {}).get('y_true', []))
        y_pred = np.array(results.get('predictions', {}).get(proj, {}).get('y_pred', []))
        
        if len(y_true) > 0:
            ax.scatter(y_true, y_pred, alpha=0.6, edgecolors='w', s=50, color='teal')
            
            # Line of perfect prediction
            min_val = min(min(y_true), min(y_pred))
            max_val = max(max(y_true), max(y_pred))
            ax.plot([min_val, max_val], [min_val, max_val], 'r--', lw=2)
            
            ax.set_title(f'{proj}', fontsize=12, fontweight='bold')
            ax.set_xlabel('Thực tế (True)')
            ax.set_ylabel('Dự báo (Pred)')
        else:
            ax.set_title(f'{proj} (No Data)')
            ax.axis('off')
            
    # Hide the 6th empty plot
    axes[-1].axis('off')
    
    plt.suptitle('Thực tế vs. Dự báo trên Toàn bộ 5 Dự án', fontsize=16, fontweight='bold')
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()
"""

    # Parse HPO Log and inject
    hpo_log_path = os.path.join(project_root, "train_log_hpo.txt")
    trials = parse_hpo_log(hpo_log_path)
    code_1 = code_1.replace("[TRIAL_DATA_PLACEHOLDER]", str(trials))

    nb['cells'] = [
        nbf.v4.new_markdown_cell(text_1),
        nbf.v4.new_code_cell(code_1),
        nbf.v4.new_markdown_cell(text_2),
        nbf.v4.new_code_cell(code_2),
        nbf.v4.new_markdown_cell(text_3),
        nbf.v4.new_code_cell(code_3),
        nbf.v4.new_markdown_cell(text_4),
        nbf.v4.new_code_cell(code_4),
        nbf.v4.new_markdown_cell(text_5),
        nbf.v4.new_code_cell(code_5),
        nbf.v4.new_markdown_cell(text_6),
        nbf.v4.new_code_cell(code_6)
    ]
    
    notebook_dir = os.path.join(project_root, "notebooks")
    os.makedirs(notebook_dir, exist_ok=True)
    out_file = os.path.join(notebook_dir, "Model_Evaluation_Report.ipynb")
    
    with open(out_file, 'w', encoding='utf-8') as f:
        nbf.write(nb, f)
        
    print(f"Created comprehensive notebook at {out_file}")

if __name__ == "__main__":
    main()
