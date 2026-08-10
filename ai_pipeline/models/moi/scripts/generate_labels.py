import os
import sys
import numpy as np
import pandas as pd
import networkx as nx

# Setup paths
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, "..", "..", "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ai_pipeline.src.algorithms.cpm import build_project_graph, calculate_cpm
from ai_pipeline.models.moi.utils.data_loader import load_project_data

class SyntheticLabelGenerator:
    def __init__(self, tasks_df: pd.DataFrame, edges_df: pd.DataFrame):
        self.tasks_df = tasks_df
        self.edges_df = edges_df
        
        # Convert df to lists for build_project_graph
        self.tasks_list = []
        for _, row in self.tasks_df.iterrows():
            task_dict = row.to_dict()
            task_dict['id'] = str(row['task_id'])
            # Ensure duration fields exist
            if 'duration' not in task_dict and 'duration_hours' in task_dict:
                task_dict['duration'] = float(task_dict['duration_hours'])
            self.tasks_list.append(task_dict)
            
        self.deps_list = []
        for _, row in self.edges_df.iterrows():
            p_id = str(row['predecessor_id'])
            s_id = str(row['successor_id'])
            attrs = {
                'lag_hours': float(row.get('lag_hours', 0.0)),
                'dependency_type': str(row.get('dependency_type', 'FS')).upper()
            }
            self.deps_list.append((p_id, s_id, attrs))
            
        self.base_graph = build_project_graph(self.tasks_list, self.deps_list)

    def calculate_risk_profile(self, task_data):
        import hashlib
        
        t_id = str(task_data.get('id', ''))
        total_cost = max(1.0, float(task_data.get('total_cost', 1.0)))
        labor = float(task_data.get('labor', 0.0))
        material = float(task_data.get('material', 0.0))
        equip = float(task_data.get('equipment', 0.0))
        duration = float(task_data.get('duration_hours', task_data.get('duration', 8.0)))
        
        labor_ratio = labor / total_cost
        mat_eq_ratio = (material + equip) / total_cost
        
        base_factor = 1.0
        
        # Phat rui ro do phu thuoc nhan cong (human factor) toi da 0.25
        base_factor += labor_ratio * 0.25
        
        # Phat rui ro chuoi cung ung (vat tu/may moc) toi da 0.15
        base_factor += mat_eq_ratio * 0.15
        
        # Phat cong viec keo dai (vi du > 40h) toi da 0.15
        if duration > 40:
            base_factor += min(0.15, (duration - 40) / 400.0)
            
        # Tao do nhieu co dinh (+/- 0.05) dua vao hash cua task_id de tranh tinh tuyen tinh tuyet doi
        hash_val = int(hashlib.md5(t_id.encode()).hexdigest(), 16)
        noise = (hash_val % 100) / 100.0 * 0.1 - 0.05
        base_factor += noise
        
        return max(0.85, base_factor)

    def generate(self, num_simulations=50):
        # 1. Tinh toan Baseline EF (Khi duration_factor = 1.0, moi thu dung ke hoach)
        # Tự động parse dependencies, lags và duration bằng engine chuẩn
        G_base, _ = calculate_cpm(self.base_graph.copy())
        baseline_ef = {n: float(G_base.nodes[n].get('ef', 0.0)) for n in G_base.nodes()}
        
        # Tinh truoc risk_profile (base_factor) cho tung cong viec
        risk_profiles = {}
        for t in self.base_graph.nodes():
            risk_profiles[t] = self.calculate_risk_profile(self.base_graph.nodes[t])
        
        # 2. Chay 50 vong lap mo phong de tao ngau nhien su co
        results_d_factor = {t: [] for t in self.base_graph.nodes()}
        results_delay = {t: [] for t in self.base_graph.nodes()}
        
        for _ in range(num_simulations):
            sim_factors = {}
            G_sim = self.base_graph.copy()
            
            for t in G_sim.nodes():
                profile = risk_profiles[t]
                # Lay ngau nhien theo phan phoi chuan (Gaussian) quanh profile voi do lech chuan = 8% cua profile
                f = np.random.normal(loc=profile, scale=0.08 * profile)
                # Gioi han de khong co he so qua nho
                f = max(0.5, f)
                sim_factors[t] = f
                
                # Ghi đè most_probable_duration để calculate_cpm nhận diện
                d_h = float(G_sim.nodes[t].get('duration_hours', G_sim.nodes[t].get('duration', 0.0)))
                G_sim.nodes[t]['most_probable_duration'] = max(0.1, d_h * f)
                
            # Chạy Forward/Backward Pass chuẩn xác với đủ 4 loại Dependency Type
            G_sim, _ = calculate_cpm(G_sim)
            
            for t in G_sim.nodes():
                results_d_factor[t].append(sim_factors[t])
                # Delay = Thuc te (Sim) - Ke hoach (Baseline)
                sim_ef = float(G_sim.nodes[t].get('ef', 0.0))
                delay = max(0.0, sim_ef - baseline_ef.get(t, 0.0)) 
                results_delay[t].append(delay)
                
        # 3. Tong hop Nhãn
        labels = []
        for t in self.base_graph.nodes():
            mean_df = np.mean(results_d_factor[t])
            mean_delay = np.mean(results_delay[t])
            # Cong them epsilon de sigma luon lon hon 0 (Tranh loi ham NLL)
            std_delay = np.std(results_delay[t]) + 1e-4 
            
            labels.append({
                'task_id': t,
                'duration_factor': round(mean_df, 4),
                'expected_delay': round(mean_delay, 4),
                'uncertainty_sigma': round(std_delay, 4)
            })
            
        return pd.DataFrame(labels)

def process_all_projects():
    processed_dir = os.path.join(project_root, 'ai_pipeline', 'data', 'processed')
    projects = ['C2011-07', 'C2012-04', 'C2012-08', 'C2018-09', 'C2019-16']
    
    print("="*60)
    print("BAT DAU SINH NHAN (GROUND TRUTH) CHO 5 DU AN")
    print("="*60)
    
    for p_id in projects:
        p_dir = os.path.join(processed_dir, p_id)
        if not os.path.exists(p_dir):
            print(f"[WARNING] Khong tim thay {p_id}, bo qua.")
            continue
            
        print(f"\n[INFO] Dang xu ly du an: {p_id}")
        tasks_df, edges_df, res_df, task_res_df, info_df, p_type, weekly, holidays = load_project_data(p_dir)
        
        generator = SyntheticLabelGenerator(tasks_df, edges_df)
        labels_df = generator.generate(num_simulations=50)
        
        out_path = os.path.join(p_dir, 'labels.csv')
        labels_df.to_csv(out_path, index=False)
        print(f"   -> Da luu thanh cong file nhan tai: {out_path}")
        print(f"   -> {len(labels_df)} tasks duoc cap nhat nhan (Duration Factor, Delay, Sigma).")
        
        # In thu 2 dong dau tien
        print("   -> Sample data:")
        print(labels_df.head(2))

if __name__ == "__main__":
    # Co dinh seed de ra ket qua chuan cho tat ca cac lan chay
    np.random.seed(42)
    process_all_projects()
