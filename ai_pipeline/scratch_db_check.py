import psycopg2
conn = psycopg2.connect(host='db', port=5432, user='glpo_admin', password='glpo_password', dbname='glpo_db')
cur = conn.cursor()

# Check project_constraint_time
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='project_constraint_time' ORDER BY ordinal_position")
print("=== project_constraint_time columns ===")
for r in cur.fetchall():
    print(r[0])

cur.execute("SELECT * FROM project_constraint_time WHERE project_id=19 LIMIT 5")
print("\n=== P19 time constraints ===")
for r in cur.fetchall():
    print(r)

# Check project info 
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='projects' ORDER BY ordinal_position")
print("\n=== projects columns ===")
for r in cur.fetchall():
    print(r[0])

cur.execute("SELECT * FROM projects WHERE id=19")
print("\n=== project 19 ===")
for r in cur.fetchall():
    print(r)

# Check for calendar type and overtime
cur.execute("SELECT id, task_name, calendar_type, overtime_hours, overtime_cost, baseline_start FROM tasks WHERE project_id=19 AND (overtime_hours > 0 OR calendar_type IS NOT NULL)")
print("\n=== tasks with OT or calendar_type ===")
for r in cur.fetchall():
    print(r)

conn.close()
