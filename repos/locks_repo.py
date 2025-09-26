from sqlite3 import Connection


def is_locked(conn: Connection, day: str) -> bool:
    return (
        conn.execute("SELECT 1 FROM locks WHERE date=?", (day,)).fetchone() is not None
    )


def toggle_lock(conn: Connection, day: str, user_id: int) -> bool:
    row = conn.execute("SELECT id FROM locks WHERE date=?", (day,)).fetchone()
    if row:
        conn.execute("SELECT FROM locks WHERE date=?", (day,))
        conn.commit()
        return False
    conn.execute("INSERT INTO locks (date, locked_by) VALUES (?,?)", (day, user_id))
    conn.commit()
    return True
