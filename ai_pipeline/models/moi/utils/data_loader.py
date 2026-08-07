import os
import json
import pandas as pd
from typing import Dict, Any, Tuple

def load_project_data(project_dir: str) -> Tuple[
    pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, str, Dict[Any, float], list
]:
    """
    Tập trung nạp tất cả các file dữ liệu tiêu chuẩn từ thư mục dự án (CSV, JSON).
    
    Hàm này đóng vai trò là Data Loader duy nhất cho toàn bộ Pipeline, giúp giảm
    thiểu việc đọc file rải rác ở nhiều class khác nhau.

    Args:
        project_dir (str): Đường dẫn tuyệt đối đến thư mục chứa dữ liệu dự án.
                           (yêu cầu phải chứa các file: tasks.csv, logic.csv, resources.csv, ...)

    Returns:
        Tuple chứa 8 thành phần:
            - tasks_df (pd.DataFrame): Bảng dữ liệu danh sách công việc.
            - edges_df (pd.DataFrame): Bảng dữ liệu mối quan hệ phụ thuộc (logic).
            - res_df (pd.DataFrame): Bảng dữ liệu danh mục tài nguyên.
            - task_res_df (pd.DataFrame): Bảng dữ liệu phân bổ tài nguyên cho công việc.
            - info_df (pd.DataFrame): Bảng dữ liệu thông tin chung của dự án.
            - project_type (str): Loại hình dự án (ví dụ: 'CON', 'ITLG', 'PRO'). Mặc định là 'ITLG'.
            - weekly_schedule (Dict[Any, float]): Cấu hình lịch ca làm việc trong tuần.
            - holidays_list (list): Danh sách các ngày nghỉ lễ.
    """
    # =========================================================================
    # BƯỚC 1: NẠP DỮ LIỆU TỪ CÁC FILE CSV TIÊU CHUẨN
    # =========================================================================
    tasks_df = pd.read_csv(os.path.join(project_dir, 'tasks.csv'))
    edges_df = pd.read_csv(os.path.join(project_dir, 'logic.csv'))
    res_df = pd.read_csv(os.path.join(project_dir, 'resources.csv'))
    task_res_df = pd.read_csv(os.path.join(project_dir, 'task_resources.csv'))
    
    # =========================================================================
    # BƯỚC 2: XỬ LÝ THÔNG TIN DỰ ÁN (PROJECT INFO)
    # =========================================================================
    info_path = os.path.join(project_dir, 'project_info.csv')
    if os.path.exists(info_path):
        info_df = pd.read_csv(info_path)
        project_type = str(info_df['project_type'].iloc[0]) if 'project_type' in info_df.columns else 'ITLG'
    else:
        info_df = pd.DataFrame()
        project_type = 'ITLG'

    # =========================================================================
    # BƯỚC 3: NẠP LỊCH TRÌNH VÀ NGÀY NGHỈ TỪ AGENDA.JSON
    # =========================================================================
    weekly_schedule = {}
    holidays_list = []
    agenda_json_path = os.path.join(project_dir, 'agenda.json')
    if os.path.exists(agenda_json_path):
        with open(agenda_json_path, 'r', encoding='utf-8') as f:
            ag_data = json.load(f)
            weekly_schedule = ag_data.get('weekly_schedule', {})
            holidays_list = ag_data.get('holidays_list', [])

    return tasks_df, edges_df, res_df, task_res_df, info_df, project_type, weekly_schedule, holidays_list
