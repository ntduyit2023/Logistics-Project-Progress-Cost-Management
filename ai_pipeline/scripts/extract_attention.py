import os
import torch
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from torch.nn.functional import cosine_similarity
import sys

# Ensure the correct working directory and path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(os.path.join(PROJECT_ROOT, 'ai_pipeline'))
sys.path.append(PROJECT_ROOT)

from models.moi.hgt_model import HGTTaskPredictor

def extract_attention_heatmap():
    print("=== Bắt đầu trích xuất Attention Heatmap ===")
    
    # 1. Đường dẫn tới dữ liệu và mô hình (Sử dụng Fold 2 theo yêu cầu)
    project_dir = os.path.join(PROJECT_ROOT, 'ai_pipeline', 'data', 'processed', 'C2012-04')
    model_path = os.path.join(PROJECT_ROOT, 'ai_pipeline', 'models', 'moi', 'checkpoints', 'hgt_fold2.pt')
    output_image_path = os.path.join(PROJECT_ROOT, 'docs', 'baocao2', 'image', 'hinh3_8_attention_heatmap.png')
    
    # 2. Build dữ liệu C2012-04 bằng HeteroGraphBuilder
    from models.moi.hetero_graph_builder import HeteroGraphBuilder
    if not os.path.exists(project_dir):
        print(f"[LỖI] Không tìm thấy thư mục dự án: {project_dir}")
        return
        
    print(f"Đang dựng đồ thị HeteroData từ {project_dir}...")
    builder = HeteroGraphBuilder(project_dir)
    data = builder.build()
    print(f"Đã dựng thành công! Số lượng Task: {data['task'].x.shape[0]}, Số lượng Resource: {data['resource'].x.shape[0]}")
    
    # 3. Khởi tạo và Load trọng số mô hình Fold 2
    if not os.path.exists(model_path):
        print(f"[LỖI] Không tìm thấy file trọng số: {model_path}")
        return
        
    in_channels_dict = {
        'task': data['task'].x.shape[1],
        'resource': data['resource'].x.shape[1],
        'shift': data['shift'].x.shape[1]
    }
    
    # Tạo mô hình với các tham số gốc
    model = HGTTaskPredictor(
        in_channels_dict=in_channels_dict,
        hidden_dim=128, 
        num_heads=4, 
        num_layers=2
    )
    
    # Load state_dict
    state_dict = torch.load(model_path, map_location='cpu')
    model.load_state_dict(state_dict)
    model.eval()
    print("Đã load thành công trọng số hgt_fold2.pt")
    
    # 4. Truyền dữ liệu qua mô hình để lấy Node Embeddings
    with torch.no_grad():
        x_dict = {}
        for node_type in data.node_types:
            x_dict[node_type] = model.proj_dict[node_type](data[node_type].x)
            
        for conv in model.hgt_layers:
            x_dict = conv(x_dict, data.edge_index_dict)
            
        task_emb = x_dict['task']       # Shape: [67, 128]
        resource_emb = x_dict['resource'] # Shape: [16, 128]
        
    # 5. Tính toán Bottleneck Attention Score (Cosine Similarity)
    print("Đang tính toán ma trận Cosine Similarity...")
    num_tasks = task_emb.shape[0]
    num_resources = resource_emb.shape[0]
    
    attention_matrix = np.zeros((num_tasks, num_resources))
    
    for i in range(num_tasks):
        for j in range(num_resources):
            # Tính Cosine Similarity giữa task i và resource j
            sim = cosine_similarity(task_emb[i].unsqueeze(0), resource_emb[j].unsqueeze(0)).item()
            attention_matrix[i, j] = sim
            
    # Chuẩn hóa Min-Max Scaling từng Task (hàng) về [0, 1] để biểu đồ nhiệt rõ ràng
    row_mins = attention_matrix.min(axis=1, keepdims=True)
    row_maxs = attention_matrix.max(axis=1, keepdims=True)
    attention_matrix_norm = (attention_matrix - row_mins) / (row_maxs - row_mins + 1e-8)
    
    # 6. Vẽ Heatmap và Lưu
    print(f"Đang vẽ Heatmap ({num_tasks}x{num_resources})...")
    plt.figure(figsize=(12, 18)) # Ảnh dài do có 67 hàng
    
    # Tạo labels
    y_labels = [f"Task {i+1}" for i in range(num_tasks)]
    x_labels = [f"Res {j+1}" for j in range(num_resources)]
    
    ax = sns.heatmap(
        attention_matrix_norm, 
        cmap='YlOrRd', # Màu từ Vàng sang Đỏ (Nóng)
        xticklabels=x_labels, 
        yticklabels=y_labels,
        linewidths=0.5,
        linecolor='gray',
        cbar_kws={"shrink": 0.5, "label": "Mức độ Chú ý (Normalized Cosine Similarity)"}
    )
    
    plt.title("Bottleneck Attention Map: Dự án C2012-04 (Mô hình hgt_fold2.pt)", fontsize=16, pad=20)
    plt.xlabel("Tài Nguyên (Resources)", fontsize=14, labelpad=10)
    plt.ylabel("Công Việc (Tasks)", fontsize=14, labelpad=10)
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    
    # Đảm bảo thư mục lưu tồn tại
    os.makedirs(os.path.dirname(output_image_path), exist_ok=True)
    plt.savefig(output_image_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Hoàn thành! Ảnh đã được lưu tại: {output_image_path}")

if __name__ == "__main__":
    extract_attention_heatmap()
