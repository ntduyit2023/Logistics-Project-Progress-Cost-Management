import pandas as pd
import sys
import traceback
sys.path.append('/')

def test():
    try:
        from ai_pipeline.models.moi.calendar_engine import CalendarEngine
        cal = CalendarEngine()
        min_proj_dt = pd.to_datetime('2010-01-01T08:00:00Z', utc=True)
        task_start_dt = cal.add_working_hours(min_proj_dt, 0)
        
        if task_start_dt.tzinfo is None:
            task_start_dt = task_start_dt.tz_localize('UTC')
        
        start_str = task_start_dt.strftime('%Y-%m-%dT%H:%M:%S%z')
        if start_str.endswith('+0000'):
            start_str = start_str[:-2] + ':00'
        
        print("OK:", start_str)
    except Exception as e:
        traceback.print_exc()

sys.path.append('/')
test()
