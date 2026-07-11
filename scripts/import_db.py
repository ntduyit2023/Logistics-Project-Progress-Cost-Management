import os
import subprocess

print("Importing data from database/init.sql into Database...")
try:
    with open("database/init.sql", "r", encoding="utf-8") as in_f:
        subprocess.run(
            ["docker", "exec", "-i", "glpo_postgres", "psql", "-U", "glpo_admin", "-d", "glpo_db"],
            stdin=in_f,
            check=True
        )
    print("SUCCESS: Data imported! You can now use the system.")
except Exception as e:
    print("ERROR:", e)
