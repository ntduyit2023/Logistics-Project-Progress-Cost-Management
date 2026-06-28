import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GATConv, global_mean_pool

from hierarchical_encoder import HierarchicalAttentionEncoder

class LogisticsGATModel(nn.Module):
    """
    Khối 2: Graph Attention Network (GAT)
    Kết hợp Khối 1 (Hierarchical Encoder) để đọc cấu trúc Đồ thị.
    """
    def __init__(self, feature_dim=72, hidden_dim=64, num_groups=13, out_dim=32, heads=4):
        super(LogisticsGATModel, self).__init__()
        
        # 1. Khối 1: Encoder 3 Tầng (Trích xuất 13 Group Features)
        self.hierarchical_encoder = HierarchicalAttentionEncoder(feature_dim=feature_dim)
        
        # 2. Linear projection từ 13 Group (S_g) sang hidden space của GNN
        # S_g có shape (num_nodes, 13)
        self.node_proj = nn.Linear(num_groups, hidden_dim)
        
        # 3. Các lớp GAT (Graph Attention Network)
        # GAT cho phép node "chọn lọc" thông tin từ predecessors/successors
        self.gat1 = GATConv(hidden_dim, hidden_dim, heads=heads, concat=True)
        self.gat2 = GATConv(hidden_dim * heads, out_dim, heads=1, concat=False)
        
        # 4. Đầu ra Global của toàn bộ Đồ thị (Dành cho PPO State)
        self.global_proj = nn.Linear(out_dim, out_dim)

    def forward(self, data):
        """
        data: PyG Data object (x, edge_index, edge_attr, u)
        """
        x, edge_index = data.x, data.edge_index
        
        # Bước 1: Trích xuất S_g (Tầng 1 & 2 của Evaluation Architecture)
        # S_g shape: (num_nodes, 13)
        S_g, group_masks = self.hierarchical_encoder(x)
        
        # Bước 2: Đưa S_g vào không gian ẩn
        h = F.leaky_relu(self.node_proj(S_g))
        
        # Bước 3: Message Passing qua đồ thị (GAT)
        h = self.gat1(h, edge_index)
        h = F.elu(h)
        h = F.dropout(h, p=0.2, training=self.training)
        
        h = self.gat2(h, edge_index)
        node_embeddings = h # Shape: (num_nodes, out_dim)
        
        # Bước 4: Global Pooling (Tạo Graph Embedding)
        # Tính gộp toàn bộ dự án thành 1 vector duy nhất
        batch = data.batch if hasattr(data, 'batch') else torch.zeros(x.shape[0], dtype=torch.long, device=x.device)
        graph_embedding = global_mean_pool(node_embeddings, batch)
        graph_embedding = self.global_proj(graph_embedding)
        
        return node_embeddings, graph_embedding

if __name__ == "__main__":
    # Test GAT Model
    from data_loader import GlPoDataset
    import os
    
    processed_dir = r"E:\University\Year 3-3\DA3\ai_pipeline\data\processed"
    if os.path.exists(processed_dir):
        print(f"Loading dataset from {processed_dir}...")
        dataset = GlPoDataset(processed_dir)
        if len(dataset) > 0:
            data = dataset[0]
            
            model = LogisticsGATModel(feature_dim=72)
            model.eval()
            
            with torch.no_grad():
                node_emb, graph_emb = model(data)
                
            print("\n=== TEST GAT MODEL ===")
            print(f"Input X shape: {data.x.shape}")
            print(f"Node Embeddings shape: {node_emb.shape} (Nodes, out_dim)")
            print(f"Graph Embedding shape: {graph_emb.shape} (1, out_dim)")
