import sqlite3

def check_db():
    try:
        conn = sqlite3.connect("real_estate.db")
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [r[0] for r in cur.fetchall()]
        print(f"Total Tables in real_estate.db: {len(tables)}")
        for t in tables:
            if not t.startswith("sqlite_"):
                cur.execute(f"SELECT COUNT(*) FROM {t}")
                count = cur.fetchone()[0]
                print(f" - {t:<26}: {count} rows")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_db()
