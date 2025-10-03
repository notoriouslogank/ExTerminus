import sqlite3
from typing import Mapping, Optional, Sequence


class JobsRepo:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    # Core

    def create(self, data: Mapping) -> int:
        q = """
        INSERT INTO jobs(title, date, start_date, end_date, is_multiday,
                         created_at, updated_at, created_by, updated_by,
                         assigned_to, assignment_mode, price, notes, rei_city, rei_zip)
                         VALUES(:title, :date, :start_date, :end_date, :is_multiday,
                                :created_at, :updated_at, :created_by, :updated_by,
                                :assigned_to, :assignment_mode, :price, :notes, :rei_city, :rei_zip)
        """
        cur = self.conn.execute(q, data)
        return cur.lastrowid

    def get(self, job_id: int) -> Optional[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM jobs WHERE id = ?", (job_id,)
        ).fetchone()

    def update(self, job_id: int, data: Mapping) -> None:
        sets = ", ".join(f"{k}=:{k}" for k in data.keys())
        params = {**data, "job_id": job_id}
        self.conn.execute(f"UPDATE jobs SET {sets} WHERE id=:job_id", params)

    def delete(self, job_id: int) -> None:
        self.conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))

    # Queries by services

    def by_date(self, ymd: str) -> Sequence[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM jobs WHERE date = ? ORDER BY id", (ymd,)
        ).fetchall()

    def overlaps_range(self, start: str, end: str) -> Sequence[sqlite3.Row]:
        q = """
        SELECT * FROM jobs
        WHERE COALESCE(start_date, date) <= :end
          AND COALESCE(end_date, date)   >= :start
        """
        return self.conn.execute(q, {"start": start, "end": end}).fetchall()

    def for_day_projected(self, ymd: str):
        """
        Return rows whose span includes ymd.
        Single-day: date = ymd
        Multi-day: start_date <= ymd <= end_date
        """

        q = """
        SELECT *
        FROM jobs
        WHERE
          (is_multiday = 0 AND date = :d)
          OR
          (is_multiday = 1 AND start_date <= :d AND end_date >= :d)
        ORDER BY id
        """
        return self.conn.execute(q, {"d": ymd}).fetchall()
