import pandas as pd
try:
    target_dt = pd.to_datetime("2013-05-30+17:00:00")
    print("to_datetime:", target_dt)
    try:
        target_dt = target_dt.tz_localize(None)
    except Exception:
        target_dt = target_dt.tz_convert(None)
    print("final:", target_dt)
except Exception as e:
    print("ERROR:", repr(e))
