import pandas as pd
from typing import Dict, Any, Optional

class WorkingCalendarEngine:
    """
    Động cơ Lịch Agenda: Quản lý lịch làm việc động theo ca.
    
    Động cơ này cho phép tính toán thời gian chi tiết dựa trên ca làm việc thực tế
    của từng Thứ (Thứ 2 -> Chủ Nhật) và hỗ trợ loại trừ danh sách ngày nghỉ lễ (holidays_list).
    Tuyệt đối không dùng số giờ khóa cứng tĩnh!

    Args:
        weekly_schedule (Optional[Dict[Any, float]]): Cấu hình ca làm việc trong tuần.
        holidays_list (Optional[list]): Danh sách các ngày nghỉ lễ (định dạng YYYY-MM-DD).
        default_hours_per_day (float): Số giờ làm việc mặc định trong ngày nếu không có ca (mặc định 8.0).
        default_days_per_week (float): Số ngày làm việc mặc định trong tuần (mặc định 5.0).
    """
    def __init__(
        self,
        weekly_schedule: Optional[Dict[Any, float]] = None,
        holidays_list: Optional[list] = None,
        default_hours_per_day: float = 8.0,
        default_days_per_week: float = 5.0
    ):
        self.weekly_schedule = {}
        self.shifts_by_day = {}
        day_map = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6}
        
        if weekly_schedule and isinstance(weekly_schedule, dict):
            for k, v in weekly_schedule.items():
                k_lower = str(k).strip().lower()
                day_idx = day_map.get(k_lower)
                if day_idx is None:
                    try:
                        day_idx = int(k) % 7
                    except (ValueError, TypeError):
                        continue
                
                # Tính tổng số giờ từ số hoặc cấu trúc shifts dict
                if isinstance(v, (int, float)):
                    self.weekly_schedule[day_idx] = max(0.0, float(v))
                    self.shifts_by_day[day_idx] = [(8.0, 8.0 + max(0.0, float(v)))]
                elif isinstance(v, dict):
                    if not v.get('is_working', True):
                        self.weekly_schedule[day_idx] = 0.0
                        self.shifts_by_day[day_idx] = []
                    else:
                        shifts = v.get('shifts', [])
                        parsed_shifts = []
                        if shifts:
                            total_h = 0.0
                            for s in shifts:
                                if isinstance(s, dict):
                                    h = float(s.get('hours', 0.0))
                                    total_h += h
                                    start_str = s.get('start_time', '08:00')
                                    try:
                                        sh, sm = map(int, start_str.split(':'))
                                        start_float = sh + sm/60.0
                                    except Exception:
                                        start_float = 8.0
                                    parsed_shifts.append((start_float, start_float + h))
                            self.weekly_schedule[day_idx] = max(0.0, total_h)
                            # Sort shifts chronologically
                            parsed_shifts.sort(key=lambda x: x[0])
                            self.shifts_by_day[day_idx] = parsed_shifts
                        else:
                            self.weekly_schedule[day_idx] = default_hours_per_day
                            self.shifts_by_day[day_idx] = [(8.0, 8.0 + default_hours_per_day)]
        if not self.shifts_by_day:
            for i in range(7):
                if i < default_days_per_week:
                    self.weekly_schedule[i] = default_hours_per_day
                    self.shifts_by_day[i] = [(8.0, 8.0 + default_hours_per_day)]
                else:
                    self.weekly_schedule[i] = 0.0
                    self.shifts_by_day[i] = []

        self.holidays_set = set(holidays_list or [])
        self.hours_per_week = sum(self.weekly_schedule.values())
        if self.hours_per_week <= 0:
            self.hours_per_week = max(1.0, default_hours_per_day * default_days_per_week)

        self.hours_per_month = round(self.hours_per_week * 4.33, 2)
        self.working_days_per_week = sum(1 for h in self.weekly_schedule.values() if h > 0)
        self.avg_hours_per_day = round(self.hours_per_week / max(1.0, float(self.working_days_per_week or 5.0)), 2)

    def get_shift_hours(self, weekday: int) -> float:
        """
        Lấy số giờ ca làm việc của 1 Thứ trong tuần.

        Args:
            weekday (int): Chỉ số ngày trong tuần (0=Thứ 2, ..., 6=Chủ Nhật).

        Returns:
            float: Tổng số giờ làm việc chuẩn trong ngày đó.
        """
        return self.weekly_schedule.get(int(weekday) % 7, 0.0)

    def calculate_task_total_hours(self, task_data: Dict[str, Any]) -> float:
        """
        Quy đổi thời lượng công việc sang tổng số giờ thi công thực tế (Hours).

        Args:
            task_data (Dict[str, Any]): Dictionary chứa thông tin công việc, bao gồm 
                                        các khóa duration_hours, duration_days, v.v.

        Returns:
            float: Tổng thời lượng quy đổi ra giờ (> 0.0).
        """
        d_h = float(task_data.get('duration_hours', task_data.get('duration', 0.0)) or 0.0)
        if d_h > 0.0:
            return max(0.1, d_h)
            
        d_m = float(task_data.get('duration_months', 0.0) or 0.0)
        d_w = float(task_data.get('duration_weeks', 0.0) or 0.0)
        d_d = float(task_data.get('duration_days', 0.0) or 0.0)
        
        total_hours = d_m * self.hours_per_month + d_w * self.hours_per_week + d_d * self.avg_hours_per_day
        return max(0.1, total_hours)

    def get_expanded_shifts(self, weekday: int, ot_hours: float) -> list:
        """
        Mở rộng ca làm việc (Shift) để bao gồm thêm giờ tăng ca (Overtime).

        Logic: 
            Giờ tăng ca sẽ được ưu tiên dồn vào cuối ca (chiều/tối).
            Nếu cuối ca không đủ sức chứa (trước 24h), sẽ đẩy sang trước ca (sáng sớm).

        Args:
            weekday (int): Chỉ số ngày trong tuần.
            ot_hours (float): Số giờ tăng ca dự kiến trong ngày.

        Returns:
            list: Danh sách các khoảng thời gian ca làm việc (gồm khoảng thời gian gốc + phần OT).
        """
        shifts = self.shifts_by_day.get(weekday, [])
        if not shifts or ot_hours <= 0:
            return shifts
        
        expanded = [list(s) for s in shifts]
        last_shift = expanded[-1]
        available_at_end = 24.0 - last_shift[1]
        
        if ot_hours <= available_at_end:
            last_shift[1] += ot_hours
        else:
            half = ot_hours / 2.0
            first_shift = expanded[0]
            available_at_start = first_shift[0] - 0.0
            add_before = min(half, available_at_start)
            add_after = ot_hours - add_before
            
            if add_after > available_at_end:
                add_after = available_at_end
                add_before = ot_hours - add_after
                if add_before > available_at_start:
                    add_before = available_at_start
            
            first_shift[0] -= add_before
            last_shift[1] += add_after
            
        return expanded

    def add_working_hours(self, start_dt: Any, working_hours: float, is_start_time: bool = False, ot_hours: float = 0.0) -> pd.Timestamp:
        """
        Cộng số giờ làm việc (working_hours) vào một mốc thời gian cụ thể (start_dt).

        Hỗ trợ tính toán loại trừ ngày nghỉ lễ, ngày nghỉ cuối tuần và tự động đẩy 
        mốc thời gian sang ca làm việc hợp lệ tiếp theo. Đặc biệt hỗ trợ giãn ca 
        nếu có phân bổ giờ tăng ca (ot_hours).

        Args:
            start_dt (Any): Mốc thời gian bắt đầu (Datetime).
            working_hours (float): Số giờ cần thực hiện.
            is_start_time (bool): Cờ hiệu chỉnh mốc thời gian bắt đầu. Nếu True, 
                                  hàm sẽ dời start_dt đến ca làm việc gần nhất.
            ot_hours (float): Số giờ tăng ca được phân bổ vào các ngày để đẩy nhanh tiến độ.

        Returns:
            pd.Timestamp: Mốc thời gian kết thúc tương ứng với logic lịch làm việc thực tế.
        """
        if working_hours < 0:
            return pd.to_datetime(start_dt)
        if working_hours == 0 and not is_start_time:
            return pd.to_datetime(start_dt)

        rem_h = float(working_hours)
        curr_dt = pd.to_datetime(start_dt)
        curr_hour = curr_dt.hour + curr_dt.minute / 60.0 + curr_dt.second / 3600.0
        
        if working_hours == 0 and is_start_time:
            rem_h = 0.0
            
        max_safety = 10000
        step = 0
        while step < max_safety:
            step += 1
            weekday = curr_dt.weekday()
            date_str = curr_dt.strftime('%Y-%m-%d')
            
            if date_str in self.holidays_set:
                shifts = []
            else:
                shifts = self.get_expanded_shifts(weekday, ot_hours)
                
            for start_h, end_h in shifts:
                if rem_h > 0:
                    if curr_hour < start_h:
                        add_h = start_h - curr_hour
                        curr_dt = curr_dt + pd.Timedelta(hours=add_h)
                        curr_hour = start_h
                        
                    if curr_hour < end_h:
                        avail_h = end_h - curr_hour
                        if rem_h <= avail_h:
                            curr_dt = curr_dt + pd.Timedelta(hours=rem_h)
                            curr_hour += rem_h
                            rem_h = 0
                        else:
                            rem_h -= avail_h
                            curr_dt = curr_dt + pd.Timedelta(hours=avail_h)
                            curr_hour = end_h
                
                if rem_h == 0:
                    if is_start_time:
                        if start_h <= curr_hour < end_h:
                            return curr_dt
                        elif curr_hour < start_h:
                            add_h = start_h - curr_hour
                            return curr_dt + pd.Timedelta(hours=add_h)
                    else:
                        return curr_dt
                        
            if rem_h > 0 or (rem_h == 0 and is_start_time):
                add_h = 24.0 - curr_hour
                curr_dt = (curr_dt + pd.Timedelta(hours=add_h)).replace(hour=0, minute=0, second=0, microsecond=0)
                curr_hour = 0.0
                
        return curr_dt

def calculate_task_total_hours(
    task_data: Dict[str, Any],
    hours_per_day: float = 8.0,
    days_per_week: float = 5.0
) -> float:
    """
    Hàm tiện ích bên ngoài giúp tính toán thời lượng giờ (hours) của một Task, 
    bằng cách khởi tạo nhanh một WorkingCalendarEngine dự phòng.

    Args:
        task_data (Dict[str, Any]): Dữ liệu task (duration_days, duration_months...).
        hours_per_day (float): Mặc định số giờ mỗi ngày.
        days_per_week (float): Mặc định số ngày làm việc mỗi tuần.

    Returns:
        float: Số giờ hoàn thành.
    """
    engine = WorkingCalendarEngine(default_hours_per_day=hours_per_day, default_days_per_week=days_per_week)
    return engine.calculate_task_total_hours(task_data)
