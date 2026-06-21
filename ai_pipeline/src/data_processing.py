import os
import json
import pandas as pd

# Đường dẫn tương đối từ vị trí thư mục src/
RAW_DATA_PATH = "../data/raw/ppc_dataset.json"
PROCESSED_DIR = "../data/processed/"

def process_ppc_dataset(file_path):
    print(f"🚀 [ETL Pipeline] Đang nạp dữ liệu thô từ: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"❌ Lỗi: Không tìm thấy file {file_path}. Vui lòng kiểm tra lại!")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    project_info = data.get("project", {})
    tasks = data.get("tasks", [])
    
    print(f"✅ Đã tải thành công Project: {project_info.get('name', 'PPC_Casestudy')} với {len(tasks)} tasks.")

    # 1. Khởi tạo mảng chứa Data theo chuẩn 12 Chủ Đề (Topic-based Schema)
    fact_tasks = []
    bridge_dependencies = []

    print("⏳ Đang tiền xử lý (Preprocessing) và map dữ liệu...")
    for task in tasks:
        task_id = task["id"]
        task_label = task.get("label", f"T_{task_id}")
        duration = task.get("duration", 0)
        
        # Giả lập Feature Rủi Ro (Risk Features) cho AI
        opt_time = max(1, duration - int(duration * 0.2)) # Thời gian lạc quan (Nhanh hơn 20%)
        pess_time = duration + int(duration * 0.5)        # Thời gian bi quan (Chậm hơn 50%)
        
        # Ánh xạ vào bảng FACT_TASKS và DIM_TOPIC_RISK
        fact_tasks.append({
            "task_id": task_id,
            "project_id": 1,  # Hardcoded ID cho PPC CaseStudy
            "task_label": task_label,
            "task_name": task.get("name", "Unknown Task"),
            "duration_planned": duration,
            "optimistic_time": opt_time,
            "pessimistic_time": pess_time
        })
        
        # Ánh xạ vào bảng BRIDGE_TASK_DEPENDENCIES (Đồ thị DAG)
        for pred in task.get("predecessors", []):
            bridge_dependencies.append({
                "project_id": 1,
                "predecessor_id": pred,
                "successor_id": task_id,
                "dependency_type": "FS", # Finish-to-Start
                "lag_days": 0
            })
            
    # Chuyển đổi thành Pandas DataFrame để tối ưu hóa vector
    df_tasks = pd.DataFrame(fact_tasks)
    df_edges = pd.DataFrame(bridge_dependencies)
    
    # 2. Xuất dữ liệu (Load) ra thư mục Processed
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    
    tasks_out_path = os.path.join(PROCESSED_DIR, "fact_tasks_clean.csv")
    edges_out_path = os.path.join(PROCESSED_DIR, "bridge_dependencies_clean.csv")
    
    df_tasks.to_csv(tasks_out_path, index=False)
    df_edges.to_csv(edges_out_path, index=False)
    
    print("\n🎉 [Hoàn tất] Dữ liệu đã được làm sạch và sẵn sàng cho AI/Database!")
    print(f"📊 Dữ liệu Node (fact_tasks): {len(df_tasks)} dòng -> {tasks_out_path}")
    print(f"🕸️ Dữ liệu Cạnh (bridge_dependencies): {len(df_edges)} dòng -> {edges_out_path}")

if __name__ == "__main__":
    # Đảm bảo đường dẫn luôn đúng dù bạn chạy script từ thư mục nào
    current_dir = os.path.dirname(os.path.abspath(__file__))
    raw_path = os.path.join(current_dir, RAW_DATA_PATH)
    processed_path = os.path.join(current_dir, PROCESSED_DIR)
    
    process_ppc_dataset(raw_path)
