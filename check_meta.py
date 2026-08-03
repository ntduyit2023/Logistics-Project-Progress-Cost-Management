import sqlite3
import json

conn = sqlite3.connect('e:/University/Year 3 - 3/DA3/backend/sqlite.db')
c = conn.cursor()
c.execute("SELECT metadata_json FROM projects WHERE project_id = 'C2011-07'")
row = c.fetchone()
if row and row[0]:
    meta = json.loads(row[0])
    print('applied_task_ids:', len(meta.get('applied_task_ids', [])))
    print('applied_task_details:', len(meta.get('applied_task_details', {})))
else:
    print('No data')
conn.close()
