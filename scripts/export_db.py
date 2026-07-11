import os
import subprocess

print("Exporting data from Database to database/init.sql...")
try:
    with open("database/init.sql", "w", encoding="utf-8") as out_f:
        subprocess.run(
            ["docker", "exec", "glpo_postgres", "pg_dump", "-U", "glpo_admin", "-d", "glpo_db", "-c", "--if-exists", "-O"],
            stdout=out_f,
            check=True
        )
    print("SUCCESS: Data exported! Your colleagues can use this init.sql file.")
except Exception as e:
    print("ERROR:", e)
