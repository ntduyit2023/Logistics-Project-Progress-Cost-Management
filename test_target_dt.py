import pandas as pd
from datetime import datetime

target_deadline = "2013-05-30 17:00:00"
target_dt = pd.to_datetime(target_deadline)
target_dt = target_dt.tz_localize(None)
print("target_dt:", target_dt)

min_proj_dt = pd.to_datetime("2010-01-01T08:00:00")
print("min_proj_dt:", min_proj_dt)

if target_dt < min_proj_dt:
    target_dt = target_dt.replace(year=min_proj_dt.year)
print("final target_dt:", target_dt)

actual_finish_dt = pd.to_datetime("2011-06-15T17:00:00")
print("actual_finish_dt:", actual_finish_dt)

delta_days = (actual_finish_dt - target_dt).total_seconds() / 86400.0
print("delta_days:", delta_days)

bonus_per_day = 3000
if delta_days < 0 and bonus_per_day > 0:
    bonus_amount = round(abs(delta_days) * bonus_per_day, 2)
    print("bonus_amount:", bonus_amount)
