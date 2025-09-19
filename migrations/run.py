import argparse
import glob
import os
import sqlite3
import sys


def _connect(db_path: str):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    return sqlite3.connect(db_path)


def _ensure_table(conn):
    conn.execute(
        """
    CREATE TABLE IF NOT EXISTS schema_migrations(
        id INTEGER PRIMARY KEY,
        filename TEXT UNIQUE NOT NULL,
        applied_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """
    )
    conn.commit()


def _applied(conn):
    return {row[0] for row in conn.execute("SELECT filename FROM schema_migrations")}


def _apply(conn, path):
    sql = open(path, "r", encoding="utf-8").read()
    with conn:
        conn.executescript(sql)
        conn.execute(
            "INSERT INTO schema_migrations(filename) VALUES (?)",
            (os.path.basename(path),),
        )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True, help="Path to SQLite file")
    ap.add_argument("--dir", default=os.path.join(os.path.dirname(__file__), "sql"))
    args = ap.parse_args()

    conn = _connect(args.db)
    _ensure_table(conn)

    files = sorted(glob.glob(os.path.join(args.dir, "*.sql")))
    already = _applied(conn)
    todo = [f for f in files if os.path.basename(f) not in already]

    if not todo:
        print("No new migrations.")
        return 0

    for f in todo:
        print(f"Applying {os.path.basename(f)} ...")
        _apply(conn, f)

    print("Applied:", ", ".join(os.path.basename(f) for f in todo))
    return 0


if __name__ == "__main__":
    sys.exit(main())
