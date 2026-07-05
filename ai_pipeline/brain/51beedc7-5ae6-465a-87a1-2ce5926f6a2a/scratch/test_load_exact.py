import torch
import sys
import os

project_root = r"c:\CNTT\KY8-2026\Logistics-Project-Progress-Cost-Management"
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'ai_pipeline', 'models'))
sys.path.insert(0, os.path.join(project_root, 'ai_pipeline', 'training'))

from torch_geometric.data import Data
from ai_pipeline.models.sequential_glpo_model import SequentialGLPOModel
from ai_pipeline.training.unsupervised_pretrainer import UnsupervisedPretrainer, load_pretrained

# Setup dummy data
num_nodes = 15
torch.manual_seed(42)
x = torch.rand(num_nodes, 72)
x[:, 3] = torch.tensor([2, 3, 1, 4, 2, 3, 1, 5, 2, 4, 3, 1, 2, 3, 4], dtype=torch.float)
x[:, 4] = 0.0

edge_index = torch.tensor([
    [0, 0, 1, 2, 3, 4, 4, 5, 6, 7, 8, 9, 10, 11, 12],
    [1, 2, 3, 3, 4, 5, 6, 7, 7, 8, 9, 10, 11, 12, 13],
], dtype=torch.long)
edge_index = torch.cat([edge_index, torch.tensor([[13], [14]], dtype=torch.long)], dim=1)
u = torch.tensor([[8.0, 5.0, 10.0]], dtype=torch.float)
data = Data(x=x, edge_index=edge_index, u=u)

# Initialize model
model = SequentialGLPOModel(feature_dim=72, gat_out_dim=32, dagnn_out_dim=32)

# Pretrain ONLY GAE+DGI
pretrainer = UnsupervisedPretrainer(model, device='cpu')
pretrainer.pretrain_gae(data, epochs=10, verbose=False)

# Get GAT output right after GAE training
model.eval()
with torch.no_grad():
    res1 = model(data)
    emb_after_gae = res1['node_embeddings'].clone()

# Load weights to fresh model
fresh_model = SequentialGLPOModel(feature_dim=72, gat_out_dim=32, dagnn_out_dim=32)
success = load_pretrained(fresh_model)
print(f"Load success: {success}")

fresh_model.eval()
with torch.no_grad():
    res2 = fresh_model(data)
    emb_loaded = res2['node_embeddings']

diff = (emb_after_gae - emb_loaded).abs().max().item()
print(f"Max absolute difference between GAE-trained and Loaded embeddings: {diff}")
if diff < 1e-6:
    print("MATCHES EXACTLY!")
else:
    print("DOES NOT MATCH!")
