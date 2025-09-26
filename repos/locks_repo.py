class LocksRepo:
    def __init__(self, conn):
        self.conn = conn

    def is_lockaed(self, ymd: str) -> bool:
        r = self.conn.execute("SELECT 1 FROM day_locks WHERE date=?", (ymd,)).fetchone()
        return bool(r)
