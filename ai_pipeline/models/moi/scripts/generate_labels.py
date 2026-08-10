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

from ai_pipeline.models.moi.utils.data_loader import load_project_data

class SyntheticLabelGenerator:
    def __init__(self, tasks_df: pd.DataFrame, edges_df: pd.DataFrame):
        self.tasks_df = tasks_df
        self.edges_df = edges_df
        
        self.graph = nx.DiGraph()
        self._build_graph()
        
    def _build_graph(self):
        for _, row in self.tasks_df.iterrows():
            t_id = str(row['task_id'])
            planned_dur = float(row.get('duration_hours', 0.0))
            self.graph.add_node(t_id, planned_dur=planned_dur)
            
        for _, row in self.edges_df.iterrows():
            p_id, s_id = str(row['predecessor_id']), str(row['successor_id'])
            lag = float(row.get('lag_hours', 0.0))
            dep_type = str(row.get('dependency_type', 'FS')).upper()
            if p_id in self.graph and s_id in self.graph:
                self.graph.add_edge(p_id, s_id, lag=lag, dep_type=dep_type)
                
    def _run_forward_pass(self, d_factors: dict) -> dict:
        es = {}
        ef = {}
        topo_order = list(nx.topological_sort(self.graph))
        
        for t_id in topo_order:
            actual_dur = self.graph.nodes[t_id]['planned_dur'] * d_factors.get(t_id, 1.0)
            preds = list(self.graph.predecessors(t_id))
            
            if not preds:
                es[t_id] = 0.0
                ef[t_id] = actual_dur
                continue
                
            max_start_req = 0.0
            max_finish_req = 0.0
            
            for p in preds:
                edge = self.graph[p][t_id]
                lag = edge['lag']
                dep_type = edge['dep_type']
                
                if dep_type == 'FS':
                    max_start_req = max(max_start_req, ef[p] + lag)
                elif dep_type == 'SS':
                    max_start_req = max(max_start_req, es[p] + lag)
                elif dep_type == 'FF':
                    max_finish_req = max(max_finish_req, ef[p] + lag)
                elif dep_type == 'SF':
                    max_finish_req = max(max_finish_req, es[p] + lag)
                    
            final_es = max(max_start_req, max_finish_req - actual_dur, 0.0)
            es[t_id] = final_es
            ef[t_id] = final_es + actual_dur
            
        return ef

    def generate(self, num_simulations=50):
        # 1. Tinh toan Baseline EF (Khi duration_factor = 1.0, moi thu dung ke hoach)
        baseline_factors = {t: 1.0 for t in self.graph.nodes()}
        baseline_ef = self._run_forward_pass(baseline_factors)
        
        # 2. Chay 50 vong lap mo phong de tao ngau nhien su co
        results_d_factor = {t: [] for t in self.graph.nodes()}
        results_delay = {t: [] for t in self.graph.nodes()}
        
        for _ in range(num_simulations):
            sim_factors = {}
            for t in self.graph.nodes():
                # 20% dung han hoac som, 80% tre han
                if np.random.rand() < 0.2:
                    f = np.random.uniform(0.85, 1.0)
                else:
                    f = np.random.uniform(1.0, 1.5)
                sim_factors[t] = f
                
            sim_ef = self._run_forward_pass(sim_factors)
            
            for t in self.graph.nodes():
                results_d_factor[t].append(sim_factors[t])
                # Delay = Thuc te (Sim) - Ke hoach (Baseline)
                delay = max(0.0, sim_ef[t] - baseline_ef[t]) 
                results_delay[t].append(delay)
                
        # 3. Tong hop Nhãn
        labels = []
        for t in self.graph.nodes():
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
