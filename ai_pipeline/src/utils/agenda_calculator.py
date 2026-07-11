"""
Mô-đun Agenda Calculator - Tính toán thời lượng dựa trên lịch làm việc
=======================================================================
Utility module cung cấp các hàm tính duration dựa trên agenda thực tế
từ database (project_constraint_time), thay vì dùng hệ số cứng (24h/day).

Nguồn dữ liệu:
    - Bảng `project_constraint_time` trong database chứa:
        - weekly_schedule: JSON mô tả giờ làm việc từng ngày trong tuần
        - overtime_multiplier: hệ số nhân overtime (ví dụ: 1.5)
"""

from typing import Dict, Tuple, Optional
import re


def parse_weekly_schedule(schedule_json: dict) -> Tuple[float, float]:
    """
    Trích xuất hours_per_day và days_per_week từ weekly_schedule JSON.
    
    Args:
        schedule_json: Dict dạng:
            {
                "monday": ["08:00-12:00", "13:00-17:00"],
                "tuesday": ["08:00-12:00", "13:00-17:00"],
                ...
                "saturday": [],
                "sunday": []
            }
    
    Returns:
        Tuple (hours_per_day, days_per_week):
            - hours_per_day: trung bình giờ làm việc mỗi ngày có làm việc
            - days_per_week: số ngày có làm việc trong tuần
    """
    if not schedule_json or not isinstance(schedule_json, dict):
        return 8.0, 5.0  # Default: 8h/day, 5 days/week
    
    total_hours = 0.0
    working_days = 0
    
    for day_name, time_slots in schedule_json.items():
        if not time_slots:
            continue
        
        day_hours = 0.0
        for slot in time_slots:
            slot_str = str(slot).strip()
            # Parse "08:00-12:00" format
            match = re.match(r'(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})', slot_str)
            if match:
                start_h, start_m = int(match.group(1)), int(match.group(2))
                end_h, end_m = int(match.group(3)), int(match.group(4))
                hours = (end_h + end_m / 60.0) - (start_h + start_m / 60.0)
                if hours > 0:
                    day_hours += hours
        
        if day_hours > 0:
            total_hours += day_hours
            working_days += 1
    
    if working_days == 0:
        return 8.0, 5.0  # Fallback
    
    hours_per_day = total_hours / working_days
    days_per_week = float(working_days)
    
    return hours_per_day, days_per_week


def calculate_duration_hours(
    d_months: float = 0.0,
    d_weeks: float = 0.0,
    d_days: float = 0.0,
    d_hours: float = 0.0,
    hours_per_day: float = 8.0,
    days_per_week: float = 5.0,
    calendar_type: str = 'Agenda'
) -> float:
    """
    Tính duration thực tế (đơn vị: giờ) dựa trên agenda.
    
    Logic:
        - Nếu calendar_type là "Elapsed (24/7)": dùng 24h/day, 7 days/week
        - Nếu calendar_type là "Agenda" (mặc định): dùng hours_per_day, days_per_week
    
    Quy đổi:
        - 1 month = 4 weeks
        - 1 week = days_per_week days
        - 1 day = hours_per_day hours
    
    Args:
        d_months: Duration component tính theo tháng
        d_weeks: Duration component tính theo tuần
        d_days: Duration component tính theo ngày
        d_hours: Duration component tính theo giờ
        hours_per_day: Giờ làm việc mỗi ngày (từ agenda)
        days_per_week: Ngày làm việc mỗi tuần (từ agenda)
        calendar_type: Loại lịch ('Agenda' hoặc 'Elapsed (24/7)')
    
    Returns:
        float: Tổng thời lượng tính bằng giờ
    """
    import math
    
    # Sanitize NaN/None inputs
    def safe(v):
        try:
            val = float(v)
            return 0.0 if math.isnan(val) or math.isinf(val) else val
        except (ValueError, TypeError):
            return 0.0
    
    d_months = safe(d_months)
    d_weeks = safe(d_weeks)
    d_days = safe(d_days)
    d_hours = safe(d_hours)
    
    cal = str(calendar_type).lower() if calendar_type else 'agenda'
    
    if '24/7' in cal or 'elapsed' in cal:
        # Elapsed: 24h/day, 7 days/week, 30 days/month
        total_h = d_months * 30.0 * 24.0 + d_weeks * 7.0 * 24.0 + d_days * 24.0 + d_hours
    else:
        # Agenda-based: dùng hours_per_day và days_per_week thực tế
        # 1 month ≈ 4 weeks
        total_h = (
            d_months * 4.0 * days_per_week * hours_per_day +
            d_weeks * days_per_week * hours_per_day +
            d_days * hours_per_day +
            d_hours
        )
    
    return max(0.0, total_h)


def load_agenda_from_db(project_id: int, db_url: str = None) -> Dict:
    """
    Load agenda trực tiếp từ database (bảng project_constraint_time).
    
    Args:
        project_id: ID của project
        db_url: Connection string (mặc định lấy từ env DATABASE_URL_SYNC)
    
    Returns:
        Dict với keys:
            - hours_per_day: float
            - days_per_week: float
            - overtime_multiplier: float
            - weekly_schedule: dict (raw JSON)
            - holidays_list: list
    """
    import os
    
    if db_url is None:
        db_url = os.environ.get(
            'DATABASE_URL_SYNC',
            'postgresql://glpo_admin:glpo_password@db:5432/glpo_db'
        )
    
    # Convert asyncpg URL to psycopg2 format if needed
    db_url = db_url.replace('postgresql+asyncpg://', 'postgresql://')
    
    result = {
        'hours_per_day': 8.0,
        'days_per_week': 5.0,
        'overtime_multiplier': 1.0,
        'weekly_schedule': {},
        'holidays_list': [],
    }
    
    try:
        import psycopg2
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        cur.execute(
            "SELECT weekly_schedule, holidays_list, overtime_multiplier "
            "FROM project_constraint_time WHERE project_id = %s LIMIT 1",
            (project_id,)
        )
        row = cur.fetchone()
        
        if row:
            weekly_schedule = row[0] if row[0] else {}
            holidays_list = row[1] if row[1] else []
            overtime_mult = float(row[2]) if row[2] else 1.0
            
            hours_per_day, days_per_week = parse_weekly_schedule(weekly_schedule)
            
            result['hours_per_day'] = hours_per_day
            result['days_per_week'] = days_per_week
            result['overtime_multiplier'] = overtime_mult
            result['weekly_schedule'] = weekly_schedule
            result['holidays_list'] = holidays_list
        
        conn.close()
    except Exception as e:
        print(f"[WARNING] Không thể đọc agenda từ DB: {e}. Sử dụng giá trị mặc định (8h/day, 5d/week).")
    
    return result
