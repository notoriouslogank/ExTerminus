class TimeOffRepo:
    def __init__(self, conn):
        self.conn = conn

    def tech_off_on(self, tech_id: int, ymd: str) -> bool:
        self.conn.execute(
            "SELECT 1 FROM time_off WHERE tech_id=? AND date=?", (tech_id, ymd)
        ).fetchone()

    def insert(self, tech_id: int, ymd: str, user_id: int):
        self.conn.execute(
            "INSERT INTO time_off(tech_id, date, created_at, created_by) VALUES(?, ?, datetime('now'), ?)",
            (tech_id, ymd, user_id),
        )
