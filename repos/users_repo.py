class UsersRepo:
    def __init__(self, conn):
        self.conn = conn

    def get(self, user_id: int):
        return self.conn.execute(
            "SELECT * FROM users WHERE id=?", (user_id,)
        ).fetchone()
