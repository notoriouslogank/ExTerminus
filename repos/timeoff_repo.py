from sqlite3 import Connection
from typing import Mapping


def insert_time_off(conn: Connection, data: Mapping) -> int:
    cur = conn.execute(
        """
        INSERT INTO time_off (technician_id, start_date, end_date, reason, created_by)
        VALUES (?, ?, ?, ?, ?)
    """,
        (
            data["technician_id"],
            data["start_date"],
            data["end_date"],
            data["reason"],
            data["created_by"],
        ),
    )
    conn.commit()
    return cur.lastrowid
