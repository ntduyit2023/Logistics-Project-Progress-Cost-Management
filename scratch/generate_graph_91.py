import re
import os
import json

md_path = r"E:\University\Year 3 - 3\DA3\docs\foundations\node_features_comprehensive.md"
html_template_path = r"E:\University\Year 3 - 3\DA3\docs\feature_relationship_graph.html"
output_html_path = r"E:\University\Year 3 - 3\DA3\docs\feature_relationship_graph_91.html"

# Read markdown content
with open(md_path, 'r', encoding='utf-8') as f:
    md_content = f.read()

# Define groups
GROUPS_DEFINITION = [
    {"id": 0, "name": "NHÓM 1: CHI PHÍ TRỰC TIẾP", "color": "#ff6b6b", "short": "CP Trực tiếp"},
    {"id": 1, "name": "NHÓM 2: CHI PHÍ GIÁN TIẾP", "color": "#f5a623", "short": "CP Gián tiếp"},
    {"id": 2, "name": "NHÓM 3: CHI PHÍ CƠ HỘI & CHI PHÍ CHÌM", "color": "#ffd166", "short": "CP Cơ hội/Chìm"},
    {"id": 3, "name": "NHÓM 4: CHI PHÍ HỢP ĐỒNG & PHÁP LÝ", "color": "#06d6a0", "short": "CP Hợp đồng/Pháp lý"},
    {"id": 4, "name": "NHÓM 5: CHI PHÍ LOGISTICS & CHUỖI CUNG ỨNG", "color": "#118ab2", "short": "Logistics & SCM"},
    {"id": 5, "name": "NHÓM 6: YẾU TỐ THỜI GIAN", "color": "#073b4c", "short": "Thời gian"},
    {"id": 6, "name": "NHÓM 7: YẾU TỐ TÀI NGUYÊN", "color": "#8338ec", "short": "Tài nguyên"},
    {"id": 7, "name": "NHÓM 8: YẾU TỐ CẤU TRÚC ĐỒ THỊ", "color": "#3a86c8", "short": "Cấu trúc Đồ thị"},
    {"id": 8, "name": "NHÓM 9: YẾU TỐ RỦI RO & BẤT ĐỊNH", "color": "#e05780", "short": "Rủi ro & Bất định"},
    {"id": 9, "name": "NHÓM 10: YẾU TỐ CHẤT LƯỢNG & GIÁ TRỊ", "color": "#ff007f", "short": "Chất lượng & Giá trị"},
    {"id": 10, "name": "NHÓM 11: YẾU TỐ CON NGƯỜI & TỔ CHỨC", "color": "#ffb5a7", "short": "Con người & Tổ chức"},
    {"id": 11, "name": "NHÓM 12: YẾU TỐ MÔI TRƯỜNG, XÃ HỘI & QUẢN TRỊ - ESG", "color": "#00f5d4", "short": "ESG"},
]

# Parse markdown to extract features
nodes = []
current_group_id = -1

lines = md_content.split('\n')
for line in lines:
    line = line.strip()
    if not line:
        continue
    
    # Identify group header
    if line.startswith('## '):
        header_text = line.replace('## ', '').strip()
        # Find matching group
        for g in GROUPS_DEFINITION:
            if g["name"] in header_text or header_text.startswith(g["name"].split(':')[0]):
                current_group_id = g["id"]
                break
        continue
        
    # Table row check
    if line.startswith('|') and not line.startswith('|:'):
        # Split row columns
        parts = [p.strip() for p in line.split('|')]
        # Filter empty border elements
        parts = [p for p in parts if p != '']
        if len(parts) >= 5:
            idx_str = parts[0]
            # Verify if it looks like index e.g. "1.1", "10.2", "12.3"
            if re.match(r'^\d+\.\d+$', idx_str):
                raw_name = parts[1]
                desc = parts[2]
                unit = parts[3]
                ref = parts[4]
                
                # Extract English name inside parenthesis if any
                english = ""
                # Strip bold marks
                clean_name = raw_name.replace('**', '').strip()
                match_eng = re.search(r'\(([^)]+)\)', clean_name)
                if match_eng:
                    english = match_eng.group(1).strip()
                    # Remove english name from the name
                    clean_name = re.sub(r'\s*\([^)]+\)', '', clean_name).strip()
                
                nodes.append({
                    "idx_str": idx_str,
                    "label": clean_name,
                    "group": current_group_id,
                    "desc": desc,
                    "unit": unit,
                    "source": ref,
                    "english": english
                })

# Assign continuous IDs to nodes (0 to len-1) and create lookup map
node_id_map = {}
for idx, node in enumerate(nodes):
    node["id"] = idx
    node_id_map[node["idx_str"]] = idx

# Print some debug stats
print(f"Extracted {len(nodes)} nodes.")

# Define edges/relationships
edges = []

def add_edge(src_idx_str, tgt_idx_str, rel_type):
    if src_idx_str in node_id_map and tgt_idx_str in node_id_map:
        edges.append([node_id_map[src_idx_str], node_id_map[tgt_idx_str], rel_type])

# Construct a rich set of logical relationships
# Format: add_edge("source_idx", "target_idx", "type")
# Types: cost, time, risk, resource, quality, structural

# --- 1. Labor & Durations ---
add_edge("6.1", "1.1", "time")      # Planned Duration -> Internal Labor Cost
add_edge("7.2", "1.1", "resource")  # Total Resource Intensity -> Internal Labor Cost
add_edge("11.1", "1.1", "resource") # Required Skill Level -> Internal Labor Cost
add_edge("11.2", "1.1", "resource") # Assigned Staff Experience -> Internal Labor Cost

add_edge("6.1", "1.2", "time")      # Planned Duration -> Subcontracting Cost
add_edge("11.1", "1.2", "resource") # Required Skill Level -> Subcontracting Cost

add_edge("6.10", "1.2", "time")     # Onboarding Time -> Subcontracting Cost
add_edge("9.5", "1.3", "risk")      # Rework Probability -> Overtime Cost
add_edge("6.12", "1.3", "risk")     # Duration Variance -> Overtime Cost

# --- 2. Procurement & Materials ---
add_edge("1.4", "5.1", "cost")      # Material Cost -> Inventory Holding Cost
add_edge("6.11", "5.1", "time")     # Lead Time -> Inventory Holding Cost
add_edge("6.8", "5.1", "time")      # Wait/Queue Time -> Inventory Holding Cost
add_edge("1.4", "5.5", "cost")      # Material Cost -> International Freight
add_edge("5.5", "12.4", "cost")     # International Freight -> Carbon Tax/Credit

# --- 3. Indirect / Overhead ---
add_edge("6.1", "2.1", "time")      # Planned Duration -> PM Overhead
add_edge("6.1", "2.2", "time")      # Planned Duration -> Facility Rent
add_edge("6.1", "2.3", "time")      # Planned Duration -> Utilities
add_edge("11.6", "2.4", "resource") # Cross-functional Coordination Need -> Communication & Coordination Cost
add_edge("8.1", "2.4", "structural")# In-degree -> Communication & Coordination Cost
add_edge("8.2", "2.4", "structural")# Out-degree -> Communication & Coordination Cost

# --- 4. Contracts & Delay ---
add_edge("9.1", "4.1", "risk")      # Delay Probability -> Penalty/Liquidated Damages
add_edge("6.1", "4.1", "time")      # Planned Duration -> Penalty/Liquidated Damages
add_edge("6.1", "4.2", "time")      # Planned Duration -> Early Completion Bonus

# --- 5. Topological Features ---
add_edge("8.1", "9.4", "structural")# In-degree -> Technical Complexity Score
add_edge("8.7", "9.2", "structural")# Longest Path -> Criticality Index
add_edge("8.2", "10.4", "structural")# Out-degree -> Downstream Impact Score
add_edge("8.6", "10.4", "structural")# Path Count -> Downstream Impact Score

# --- 6. Quality & Value ---
add_edge("9.5", "10.6", "quality")  # Rework Probability -> Quality Standard Level
add_edge("10.1", "10.2", "quality") # Earned Value -> CPI
add_edge("10.1", "10.3", "quality") # Earned Value -> SPI

# --- 7. Risks & Uncertainty ---
add_edge("9.4", "9.5", "risk")      # Technical Complexity -> Rework Probability
add_edge("9.9", "6.8", "time")      # Weather/Seasonal Risk -> Wait/Queue Time
add_edge("9.10", "9.5", "risk")     # Technology Risk -> Rework Probability
add_edge("9.5", "9.7", "risk")      # Rework Probability -> Contingency Reserve
add_edge("9.6", "6.11", "time")     # External Dependency Level -> Lead Time

# --- 8. Human Factors ---
add_edge("11.1", "2.5", "resource") # Required Skill Level -> Internal Training Cost
add_edge("11.3", "7.7", "resource") # Learning Curve Effect -> Labor Productivity
add_edge("11.2", "7.7", "resource") # Assigned Staff Experience -> Labor Productivity
add_edge("11.4", "9.5", "risk")      # Fatigue/Burnout Risk -> Rework Probability

# --- 9. ESG ---
add_edge("12.5", "4.3", "quality")  # ESG Compliance Requirements -> Permits & Licensing
add_edge("12.1", "12.2", "quality") # Environmental Impact -> Waste Disposal Cost
add_edge("12.1", "12.4", "quality") # Environmental Impact -> Carbon Tax/Credit

print(f"Constructed {len(edges)} edges.")

# Write the new HTML file based on the template
with open(html_template_path, 'r', encoding='utf-8') as f:
    html_template = f.read()

# Replace GROUPS
groups_js_str = json.dumps(GROUPS_DEFINITION, indent=4, ensure_ascii=False)
html_template = re.sub(
    r'const GROUPS = \[.*?\];',
    f'const GROUPS = {groups_js_str};',
    html_template,
    flags=re.DOTALL
)

# Build the nodes raw structure:
# NODES_RAW = [ [id, label, group, rawDesc], ... ]
nodes_raw_data = []
for n in nodes:
    # Reconstruct rawDesc to match what javascript code parses
    # rawDesc format: Tiếng Anh: {english}. {desc}. Đơn vị: {unit}. Nguồn: {source}
    eng_part = f"Tiếng Anh: {n['english']}." if n['english'] else ""
    unit_part = f"Đơn vị: {n['unit']}." if n['unit'] else ""
    source_part = f"Nguồn: {n['source']}" if n['source'] else ""
    desc_part = f"{n['desc']}." if not n['desc'].endswith('.') else n['desc']
    
    raw_desc_parts = [p for p in [eng_part, desc_part, unit_part, source_part] if p != ""]
    raw_desc = " ".join(raw_desc_parts)
    
    nodes_raw_data.append([
        n["id"],
        n["label"],
        n["group"],
        raw_desc
    ])

nodes_raw_js_str = json.dumps(nodes_raw_data, indent=4, ensure_ascii=False)
html_template = re.sub(
    r'const NODES_RAW = \[.*?\];',
    f'const NODES_RAW = {nodes_raw_js_str};',
    html_template,
    flags=re.DOTALL
)

# Replace EDGES_RAW
edges_raw_js_str = json.dumps(edges, indent=4, ensure_ascii=False)
html_template = re.sub(
    r'const EDGES_RAW = \[.*?\];',
    f'const EDGES_RAW = {edges_raw_js_str};',
    html_template,
    flags=re.DOTALL
)

# Update page titles / headings
html_template = html_template.replace(
    '<title>Feature Relationship Graph — GLPO Node Features</title>',
    '<title>Comprehensive Feature Relationship Graph — 91 GLPO Features</title>'
)

html_template = html_template.replace(
    '<h2>📋 Danh Sách Thống Kê Đặc Trưng (72)</h2>',
    '<h2>📋 Danh Sách Thống Kê Đặc Trưng (91)</h2>'
)

html_template = html_template.replace(
    '<h3>📊 Nhóm Đặc trưng (12)</h3>',
    '<h3>📊 Nhóm Đặc trưng (12)</h3>'
)

# Write to output file
with open(output_html_path, 'w', encoding='utf-8') as f:
    f.write(html_template)

print("Generated E:\\University\\Year 3 - 3\\DA3\\docs\\feature_relationship_graph_91.html successfully.")
