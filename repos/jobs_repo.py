from sqlite3 import Connection
from typing import Mapping, Optional


def get_jobs_for_day(conn: Connection, day: str) -> list[Mapping]:
    return conn.execute(
        """
        SELECT j.*,
                t.name AS technician_name
        FROM jobs j
        LEFT JOIN technicians t ON t.id = j.technician_id
        WHERE date(j.start_date) = date(?)
        ORDER BY (j.start_time IS NULL), j.start_time, j.id
    """,
        (day,),
    ).fetchall()


def get_jobs_for_grid(conn: Connection, start: str, end: str) -> list[Mapping]:
    return conn.execute(
        """
        SELECT j.*,
            t.name AS technician_name
        FROM jobs j
        LEFT JOIN technicians t ON t.id = j.technician_id
        WHERE date(j.start_date) <= date(?)
            AND date(COALESCE(j.end_date, j.start_date)) >= date(?)
        ORDER BY date(j.start_date), (j.start_time IS NULL), j.start_time, j.id
    """,
        (end, start),
    ).fetchall()


def get_job(conn: Connection, job_id: int) -> Optional[Mapping]:
    return conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()


def insert_job(conn: Connection, data: Mapping) -> int:
    cols = ", ".join(data.keys())
    qs = ", ".join(["?"] * len(data))
    cur = conn.execute(f"INSERT INTO jobs ({cols}) VALUES ({qs})", tuple(data.values()))
    conn.commit()
    return cur.lastrowid


def update_job(conn: Connection, job_id: int, data: Mapping) -> None:
    sets = ", ".join([f"{k}=?" for k in data.keys()])
    conn.execute(f"UPDATE jobs SET {sets} WHERE id=?", (*data.values(), job_id))
    conn.commit()


def delete_job(conn: Connection, job_id: int) -> None:
    conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
    conn.commit()
