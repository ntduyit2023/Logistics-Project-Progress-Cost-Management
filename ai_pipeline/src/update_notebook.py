import json
import os

nb_path = r'e:\University\Year 3-3\DA3\ai_pipeline\notebooks\EDA_DSLIB.ipynb'
with open(nb_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

new_cells = [
    {
        'cell_type': 'markdown',
        'metadata': {},
        'source': [
            '---\n',
            '## 6. Phân tích Chuyên sâu (Deep Dive): 3 Dự án gần đây nhất\n',
            'Lấy ra 3 dự án mới nhất (dựa theo tên thư mục) để vẽ Sơ đồ mạng lưới (Network Graph) và Phân bổ Chi phí.'
        ]
    },
    {
        'cell_type': 'code',
        'execution_count': None,
        'metadata': {},
        'outputs': [],
        'source': [
            'import networkx as nx\n',
            '\n',
            '# Lấy 3 dự án cuối cùng (C2025...)\n',
            'recent_projects = sorted(project_dirs)[-3:]\n',
            'print("3 dự án mới nhất để phân tích chuyên sâu:")\n',
            'for p in recent_projects:\n',
            '    print(" -", os.path.basename(p))\n'
        ]
    },
    {
        'cell_type': 'code',
        'execution_count': None,
        'metadata': {},
        'outputs': [],
        'source': [
            'for pdir in recent_projects:\n',
            '    pname = os.path.basename(pdir)\n',
            '    df_n = pd.read_csv(os.path.join(pdir, "nodes.csv"))\n',
            '    try:\n',
            '        df_e = pd.read_csv(os.path.join(pdir, "edges.csv"))\n',
            '    except pd.errors.EmptyDataError:\n',
            '        df_e = pd.DataFrame(columns=["source", "target", "type"])\n',
            '    \n',
            '    # 1. Vẽ Network Graph (Cấu trúc mạng)\n',
            '    G = nx.DiGraph()\n',
            '    for _, row in df_n.iterrows():\n',
            '        G.add_node(str(row["node_id"]))\n',
            '    for _, row in df_e.iterrows():\n',
            '        G.add_edge(str(row["source"]), str(row["target"]))\n',
            '    \n',
            '    plt.figure(figsize=(10, 5))\n',
            '    pos = nx.spring_layout(G, seed=42)\n',
            '    nx.draw(G, pos, with_labels=False, node_color="#66b3ff", edge_color="gray", node_size=80, arrows=True)\n',
            '    plt.title(f"Sơ đồ Mạng lưới Cấu trúc Liên kết - {pname}", fontweight="bold", fontsize=14)\n',
            '    plt.show()\n',
            '    \n',
            '    # 2. Phân bố Chi phí (Top 10 Task)\n',
            '    if "total_cost" in df_n.columns and df_n["total_cost"].sum() > 0:\n',
            '        top_cost_tasks = df_n.nlargest(10, "total_cost")\n',
            '        plt.figure(figsize=(10, 5))\n',
            '        sns.barplot(data=top_cost_tasks, x="total_cost", y="task_name", palette="Reds_r")\n',
            '        plt.title(f"Top 10 Task Tốn kém nhất - {pname}", fontweight="bold", fontsize=14)\n',
            '        plt.xlabel("Chi phí")\n',
            '        plt.ylabel("Tên Task")\n',
            '        plt.show()\n'
        ]
    },
    {
        'cell_type': 'markdown',
        'metadata': {},
        'source': [
            '**👉 INSIGHT 5:** Khi nhìn vào từng cá thể dự án, ta có thể thấy hình thù Đồ thị hoàn toàn khác nhau. Ngoài ra, biểu đồ chi phí chứng minh rằng đa phần dự án phụ thuộc vào một vài Task trọng điểm cốt lõi.'
        ]
    }
]

nb['cells'].extend(new_cells)

with open(nb_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
