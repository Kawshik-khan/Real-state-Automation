import sqlite3

conn = sqlite3.connect("real_estate.db")
cursor = conn.cursor()
cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table';")
schemas = cursor.fetchall()
print(f"Total tables: {len(schemas)}")
for name, sql in sorted(schemas):
    print(f"=== Table: {name} ===")
    print(sql)
    print()
conn.close()
