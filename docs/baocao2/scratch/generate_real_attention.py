import os
import json
import torch
import torch.nn.functional as F
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Path configuration
project_id = "C2012-04"
workspace_dir = r"E:\University\Year 3 - 3\DA3"
project_dir = os.path.join(workspace_dir, "ai_pipeline", "models", "moi", "data", project_id)
checkpoints_dir = os.path.join(workspace_dir, "ai_pipeline", "models", "moi", "checkpoints")
image_dir = os.path.join(workspace_dir, "docs", "baocao2", "image")

# 1. Load project data and build HeteroData graph
from ai_pipeline.models.moi.utils.data_loader import load_project_data
from ai_pipeline.models.moi.hetero_graph_builder import HeteroGraphBuilder

print("Loading project data...")
tasks_df, logic_df, res_df, task_res_df, info_df, project_type, weekly_schedule, holidays_list = load_project_data(project_dir)

print("Building heterogeneous graph...")
builder = HeteroGraphBuilder(project_id, project_type)
data = builder.build(tasks_df, logic_df, res_df, task_res_df, info_df)

# 2. Load HGT model and weights
from ai_pipeline.models.moi.hgt_model import HGTTaskPredictor
model_path = os.path.join(checkpoints_dir, "hgt_fold2.pt")

model = HGTTaskPredictor(
    in_dim=41,
    res_dim=6,
    shift_dim=5,
    hidden_dim=64,
    num_heads=4,
    num_layers=2
)

if os.path.exists(model_path):
    model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
    print(f"Loaded weights from {model_path}")
else:
    raise FileNotFoundError(f"Model weights not found at {model_path}")

# 3. Model evaluation to get real embeddings
model.eval()
with torch.no_grad():
    preds = model(
        x_dict=data.x_dict,
        edge_index_dict=data.edge_index_dict
    )

# 4. Extract embeddings and compute actual cosine similarity
task_emb = preds['task_embeddings']
res_emb = preds['resource_embeddings']

task_norm = F.normalize(task_emb, p=2, dim=1)
res_norm = F.normalize(res_emb, p=2, dim=1)
sim_matrix = torch.matmul(task_norm, res_norm.t()).numpy() # [N_task, N_res]

# Get mapping names
res_id_map = {idx: r_id for r_id, idx in builder.resource_id_map.items()}
resources_list = [res_id_map[i] for i in range(len(res_id_map))]

# Use 15 consecutive tasks on the critical path to visualize
critical_task_ids = [
    'C2012-04_1', 'C2012-04_2', 'C2012-04_3', 'C2012-04_4', 'C2012-04_5',
    'C2012-04_6', 'C2012-04_7', 'C2012-04_9', 'C2012-04_11', 'C2012-04_19',
    'C2012-04_14', 'C2012-04_17', 'C2012-04_20', 'C2012-04_22', 'C2012-04_41'
]

# Extract similarity values for these specific tasks
task_indices = [builder.task_id_map[tid] for tid in critical_task_ids]
sub_matrix = sim_matrix[task_indices, :] # Shape [15, 8]

# 5. Plot the real task-resource attention heatmap
plt.rcParams.update({
    "font.size": 10,
    "font.family": "serif",
    "text.usetex": False
})

fig, ax = plt.subplots(figsize=(9, 6.5), dpi=300)
sns.heatmap(
    sub_matrix,
    xticklabels=resources_list,
    yticklabels=critical_task_ids,
    cmap="YlOrRd",
    annot=True,
    fmt=".3f",
    linewidths=0.5,
    cbar_kws={'label': 'Độ tương đồng Cosine (Attention Score)'},
    ax=ax
)

ax.set_title('Bản đồ nhiệt Trọng số Bottleneck Attention thực tế (HGT Cosine Similarity)\ngiữa các công việc găng và tài nguyên (C2012-04)', fontsize=11, fontweight='bold', pad=15)
ax.set_xlabel('Nút Tài nguyên ($V_{Resource}$)', fontsize=10, fontweight='bold', labelpad=10)
ax.set_ylabel('Nút Công việc trên đường găng ($V_{Task}$)', fontsize=10, fontweight='bold', labelpad=10)
plt.xticks(rotation=45, ha='right')

# Save plot
out_path = os.path.join(image_dir, "hinh3_8_attention_heatmap.png")
plt.savefig(out_path, bbox_inches="tight", dpi=300)
plt.close()
print(f"Success! Generated real attention heatmap at: {out_path}")
