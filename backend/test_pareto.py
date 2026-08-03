import requests
import json

url = "http://localhost:8000/api/v1/ai/C2011-07/glpo-optimize"
params = {
    "mc_iterations": 1000,
    "pareto_count": 20,
    "target_deadline": "2011-06-30 17:00",
    "penalty_per_day": 500.0,
    "bonus_per_day": 500.0
}

print(f"Calling API: {url}")
response = requests.post(url, params=params)

if response.status_code == 200:
    data = response.json()
    print("API Success!")
    
    res_data = data.get("data", {})
    if isinstance(res_data, list):
        pareto_front = res_data
    elif isinstance(res_data, dict):
        print(f"Keys: {res_data.keys()}")
        pareto_front = res_data.get("pareto_options", res_data.get("pareto_front", []))
    else:
        pareto_front = []
        
    if len(pareto_front) > 0:
        opt = pareto_front[-1] # Lấy phương án cuối (chắc chắn có crash)
        print(f"\n--- Cấu trúc của Phương án ({opt.get('option_name')}) ---")
        # Print top-level keys
        for k, v in opt.items():
            if k != "tasks_schedule":
                print(f"  {k}: {v}")
                
        tasks = opt.get("tasks_schedule", {})
        if len(tasks) > 0:
            t_id = list(tasks.keys())[0]
            t_data = tasks[t_id]
            print(f"\n--- Cấu trúc của 1 Task ({t_id}) ---")
            print(json.dumps(t_data, indent=2, ensure_ascii=False))
            
            # Tìm 1 task có is_crashed == True
            crashed_task = next((t for t in tasks.values() if t.get('is_ai_optimized') or t.get('overtime_hours', 0) > 0), None)
            if crashed_task:
                print(f"\n--- Cấu trúc của 1 Crashed Task ({crashed_task.get('task_id')}) ---")
                print(json.dumps(crashed_task, indent=2, ensure_ascii=False))
        else:
            print("Không có tasks_schedule!")
    else:
        print("Không có pareto_front trả về.")
else:
    print(f"API Error: {response.status_code}")
    print(response.text)
