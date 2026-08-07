import pandas as pd
import math
import sys
import traceback
sys.path.append('/')
def test():
    try:
        from ai_pipeline.models.moi.domain_normalizers import WorkingCalendarEngine
        cal = WorkingCalendarEngine()
        min_proj_dt = pd.to_datetime('2010-01-01T08:00:00Z', utc=True)
        task_start_dt = cal.add_working_hours(min_proj_dt, float('nan'))
        print("OK:", task_start_dt)
    except Exception as e:
        traceback.print_exc()

test()
