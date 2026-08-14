"""
extract_logic_from_raw.py
"""
import os, re, json
import pandas as pd

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAW_DIR = os.path.join(BASE_DIR, "ai_pipeline", "data", "raw", "DSLIB_Logistics_Subset", "use")
PROCESSED_DIR = os.path.join(BASE_DIR, "ai_pipeline", "data", "processed")

PROJECTS = {
    "C2011-07": "C2011-07 Patient Transport System.xlsx",
    "C2012-04": "C2012-04 Asti-Cuneo Highway.xlsx",
    "C2012-08": "C2012-08 Sea Electricity.xlsx",
    "C2018-09": "C2018-09 CarSharing platform.xlsx",
    "C2019-16": "C2019-16 Lock Ganzepoot Excel.xlsx",
}

def load_agenda(project_id):
    with open(os.path.join(PROCESSED_DIR, project_id, "agenda.json"), "r", encoding="utf-8") as f:
        agenda = json.load(f)
    weekly = agenda.get("weekly_schedule", {})
    total_h, working_days = 0.0, 0
    for day_data in weekly.values():
        if day_data.get("is_working", False):
            day_h = sum(s.get("hours", 0.0) for s in day_data.get("shifts", []))
            total_h += day_h
            working_days += 1
    avg_hpd = (total_h / working_days) if working_days > 0 else 8.0
    return {"hours_per_day": avg_hpd, "hours_per_week": avg_hpd * working_days, "working_days": working_days}

def parse_lag_to_hours(lag_str, agenda):
    if not lag_str: return 0.0
    lag_str = lag_str.strip()
    sign = 1.0
    if lag_str.startswith("-"): sign = -1.0; lag_str = lag_str[1:]
    elif lag_str.startswith("+"): lag_str = lag_str[1:]
    total = 0.0
    hpd = agenda["hours_per_day"]
    hpw = agenda["hours_per_week"]
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*(mo|w|d|h)", lag_str, re.IGNORECASE):
        v, u = float(m.group(1)), m.group(2).lower()
        if u == "mo": total += v * 4 * hpw
        elif u == "w": total += v * hpw
        elif u == "d": total += v * hpd
        elif u == "h": total += v
    return round(sign * total, 2)

def parse_cell(cell_val, agenda):
    results = []
    if not cell_val or str(cell_val).strip().lower() in ("nan", ""): return results
    for part in str(cell_val).strip().split(";"):
        part = part.strip()
        m = re.match(r"^(\d+)(FS|SS|FF|SF)(([+-].*))?$", part, re.IGNORECASE)
        if m:
            results.append((m.group(1), m.group(2).upper(), parse_lag_to_hours(m.group(3) or "", agenda)))
        else:
            m2 = re.match(r"^(\d+)$", part)
            if m2: results.append((m2.group(1), "FS", 0.0))
    return results

def extract_project(project_id, xlsx_filename):
    print(f"\n=== {project_id} ===")
    agenda = load_agenda(project_id)
    print(f"  Agenda: {agenda['working_days']} working days/week, {agenda['hours_per_day']:.1f}h/day")
    df_raw = pd.read_excel(os.path.join(RAW_DIR, xlsx_filename), sheet_name="Baseline Schedule", header=None)
    header = df_raw.iloc[1]
    col_id, col_pred = None, None
    for i, val in enumerate(header):
        v = str(val).strip().lower()
        if v == "id": col_id = i
        elif "predecessor" in v: col_pred = i
    if col_id is None or col_pred is None:
        print("  [ERROR] Cannot find ID or Predecessors column"); return
    data = df_raw.iloc[2:].reset_index(drop=True)
    id_vals = data.iloc[:, col_id]
    pred_vals = data.iloc[:, col_pred]
    task_map = {}
    for idx in range(len(data)):
        raw = str(id_vals.iloc[idx]).strip()
        if raw and raw.lower() != "nan":
            try: task_map[str(int(float(raw)))] = f"{project_id}_{int(float(raw))}"
            except: pass
    rows = []
    dep_types, non_zero = set(), 0
    for idx in range(len(data)):
        raw = str(id_vals.iloc[idx]).strip()
        if not raw or raw.lower() == "nan": continue
        try: succ_int = int(float(raw))
        except: continue
        succ_uid = f"{project_id}_{succ_int}"
        cell = str(pred_vals.iloc[idx]).strip()
        if cell.lower() == "nan": continue
        for (pred_raw, dep_type, lag_h) in parse_cell(cell, agenda):
            pred_uid = task_map.get(pred_raw)
            if pred_uid:
                rows.append({"predecessor_id": pred_uid, "successor_id": succ_uid, "dependency_type": dep_type, "lag_hours": lag_h})
                dep_types.add(dep_type)
                if lag_h != 0.0: non_zero += 1
    df_out = pd.DataFrame(rows, columns=["predecessor_id", "successor_id", "dependency_type", "lag_hours"])
    out_path = os.path.join(PROCESSED_DIR, project_id, "logic.csv")
    df_out.to_csv(out_path, index=False)
    print(f"  [OK] {len(df_out)} rows, types={sorted(dep_types)}, non-zero lags={non_zero}")
    if non_zero: print(df_out[df_out['lag_hours'] != 0].head(5).to_string(index=False))

if __name__ == "__main__":
    for pid, fname in PROJECTS.items():
        extract_project(pid, fname)
    print("\n[DONE] All logic.csv re-extracted!")

