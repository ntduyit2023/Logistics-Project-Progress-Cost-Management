"""
Script đánh giá tiền huấn luyện không giám sát (GAE + CPM) trên toàn bộ 5 dự án của dataset.
========================================================================================
"""

import sys
import os
import torch
import numpy as np
import pandas as pd

# Thiết lập UTF-8 cho stdout
sys.stdout.reconfigure(encoding='utf-8')

# Thiết lập đường dẫn project_root tuyệt đối
project_root = r"c:\CNTT\KY8-2026\Logistics-Project-Progress-Cost-Management"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Thêm paths của các modules con
sys.path.insert(0, os.path.join(project_root, 'ai_pipeline', 'models'))
sys.path.insert(0, os.path.join(project_root, 'ai_pipeline', 'training'))

from ai_pipeline.models.data_loader import GlPoDataset
from ai_pipeline.models.sequential_glpo_model import SequentialGLPOModel
from ai_pipeline.training.unsupervised_pretrainer import UnsupervisedPretrainer

def evaluate_all_projects():
    processed_dir = os.path.join(project_root, 'ai_pipeline', 'data', 'processed')
    print("=" * 80)
    print(f"  BẮT ĐẦU ĐÁNH GIÁ TRÊN 5 DỰ ÁN THỰC TẾ")
    print(f"  Thư mục dữ liệu: {processed_dir}")
    print("=" * 80)
    
    if not os.path.exists(processed_dir):
        print(f"❌ Không tìm thấy thư mục: {processed_dir}")
        return
        
    dataset = GlPoDataset(processed_dir)
    print(f"👉 Tìm thấy {len(dataset)} dự án.")
    
    results = []
    
    for idx, pg in enumerate(dataset.graphs):
        proj_id = pg.project_id
        data = pg.data
        
        print(f"\n⚡ [{idx+1}/{len(dataset)}] Xử lý dự án: {proj_id}")
        print(f"   - Số lượng Task: {data.num_nodes}")
        print(f"   - Số lượng Cạnh: {data.num_edges}")
        
        # Khởi tạo mô hình mới cho mỗi dự án
        model = SequentialGLPOModel(
            feature_dim=72,
            gat_out_dim=32,
            dagnn_out_dim=32
        )
        
        # Ghi nhận trạng thái TRƯỚC
        model.eval()
        with torch.no_grad():
            res_before = model(data)
            emb_before = res_before['node_embeddings'].clone()
            tgc_before = res_before['tgc'].clone()
            
        # Khởi tạo Pretrainer
        pretrainer = UnsupervisedPretrainer(model, device='cpu')
        
        # Chạy pretraining (50 epochs cho mỗi pha để đảm bảo tốc độ và đo lường)
        history = pretrainer.pretrain_all(
            data,
            gae_epochs=50,
            cpm_epochs=50,
            verbose=False
        )
        
        # Ghi nhận trạng thái SAU
        model.eval()
        with torch.no_grad():
            res_after = model(data)
            emb_after = res_after['node_embeddings'].clone()
            tgc_after = res_after['tgc'].clone()
            
        # Tính toán các chỉ số đánh giá
        emb_diff = float((emb_after - emb_before).norm(dim=1).mean())
        tgc_diff = float((tgc_after - tgc_before).abs().mean())
        
        gae_init = history['gae']['losses'][0]
        gae_final = history['gae']['losses'][-1]
        gae_auc = history['gae']['auc_scores'][-1]
        gae_ap = history['gae']['ap_scores'][-1]
        
        cpm_init = history['cpm']['losses'][0]
        cpm_final = history['cpm']['losses'][-1]
        
        mae_es = history['cpm']['mae_per_target']['Early Start']
        mae_tf = history['cpm']['mae_per_target']['Total Float']
        mae_crit = history['cpm']['mae_per_target']['Is Critical']
        mae_pl = history['cpm']['mae_per_target']['Path Length']
        
        crit_acc = history['cpm']['is_critical_metrics']['accuracy']
        crit_f1 = history['cpm']['is_critical_metrics']['f1_score']
        
        total_time = history['gae']['time_taken'] + history['cpm']['time_taken']
        
        print(f"   ✅ Hoàn thành tiền huấn luyện {proj_id}")
        print(f"      - GAE: AUC={gae_auc:.4f} | AP={gae_ap:.4f} | Time={history['gae']['time_taken']:.2f}s")
        print(f"      - CPM: Loss={cpm_final:.4f} | F1 Critical={crit_f1:.4f} | Time={history['cpm']['time_taken']:.2f}s")
        print(f"      - MAE ES: {mae_es:.4f} | MAE PL: {mae_pl:.4f}")
        
        results.append({
            'Project': proj_id,
            'Tasks': data.num_nodes,
            'Edges': data.num_edges,
            'GAE_AUC': gae_auc,
            'GAE_AP': gae_ap,
            'CPM_Final_Loss': cpm_final,
            'MAE_EarlyStart': mae_es,
            'MAE_TotalFloat': mae_tf,
            'Crit_Accuracy': crit_acc,
            'Crit_F1': crit_f1,
            'MAE_PathLength': mae_pl,
            'Time_Sec': total_time,
            'Emb_Shift': emb_diff,
            'TGC_Shift': tgc_diff
        })
        
    # Tạo dataframe tổng kết
    df = pd.DataFrame(results)
    
    print("\n" + "=" * 120)
    print("📊 BẢNG TỔNG HỢP KẾT QUẢ ĐÁNH GIÁ NÂNG CAO")
    print("=" * 120)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    print(df.to_string(index=False, formatters={
        'GAE_AUC': '{:,.4f}'.format,
        'GAE_AP': '{:,.4f}'.format,
        'CPM_Final_Loss': '{:,.4f}'.format,
        'MAE_EarlyStart': '{:,.4f}'.format,
        'MAE_TotalFloat': '{:,.4f}'.format,
        'Crit_Accuracy': '{:,.4f}'.format,
        'Crit_F1': '{:,.4f}'.format,
        'MAE_PathLength': '{:,.4f}'.format,
        'Time_Sec': '{:,.2f}s'.format,
        'Emb_Shift': '{:,.4f}'.format,
        'TGC_Shift': '{:,.4f}'.format
    }))
    print("=" * 120)
    
    # Tính trung bình toàn bộ dataset
    print("\n📉 TRUNG BÌNH TOÀN BỘ DATASET:")
    print(f"   - GAE AUC trung bình:           {df['GAE_AUC'].mean():.4f}")
    print(f"   - GAE AP trung bình:            {df['GAE_AP'].mean():.4f}")
    print(f"   - CPM Final Loss trung bình:    {df['CPM_Final_Loss'].mean():.4f}")
    print(f"   - MAE Early Start trung bình:   {df['MAE_EarlyStart'].mean():.4f}")
    print(f"   - MAE Path Length trung bình:   {df['MAE_PathLength'].mean():.4f}")
    print(f"   - Critical Accuracy trung bình: {df['Crit_Accuracy'].mean():.4f}")
    print(f"   - Critical F1-Score trung bình: {df['Crit_F1'].mean():.4f}")
    print(f"   - Tổng thời gian chạy TB/dự án: {df['Time_Sec'].mean():.2f}s")
    print(f"   - Độ dịch chuyển Embedding TB:  {df['Emb_Shift'].mean():.4f}")
    print("=" * 120)

if __name__ == '__main__':
    evaluate_all_projects()
