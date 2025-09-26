from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from db import get_database
from repos.audit_repo import AuditRepo
from repos.jobs_repo import JobsRepo
from repos.locks_repo import LocksRepo
from repos.timeoff_repo import TimeOffRepo
from utils.clock import now_est_str


def _conn():
    return get_database()


@dataclass
class JobsService:
    def _jobs(self):
        return JobsRepo(_conn())

    def _timeoff(self):
        return TimeOffRepo(_conn())

    def _locks(self):
        return LocksRepo(_conn())

    def _audit(self):
        return AuditRepo(_conn())

    def _guard_day(self, date_str: str, user):
        if self._locks().is_locked(date_str) and user["role"] not in (
            "admin",
            "manager",
        ):
            raise PermissionError("That day is locked.")

    def _guard_timeoff(self, tech_id: Optional[int], ymd: str):
        if tech_id and self._timeoff().tech_off_on(tech_id, ymd):
            raise ValueError("Technician has time off that day.")

    def create_single(self, payload: dict, user) -> int:
        ymd = payload["date"]
        self._guard_day(ymd, user)
        self._guard_timeoff(payload.get("assigned_to"), ymd)

        base = {
            "created_at": now_est_str(),
            "updated_at": now_est_str(),
            "created_by": user["id"],
            "updated_by": user["id"],
            "assignment_mode": payload.get("assignment_mode", "single"),
            "is_multiday": 0,
        }
        job_id = self._jobs().create({**payload, **base})
        self._audit().log(user["id"], "job.create", "job", job_id, {"date": ymd})
        return job_id

    def create_multiday(self, payload: dict, user) -> int:
        start = payload["start_date"]
        end = payload["end_date"]

        d = datetime.fromisoformat(start)
        e = datetime.fromisoformat(end)
        while d <= e:
            ymd = d.date().isoformat()
            self._guard_day(ymd, user)
            self._guard_timeoff(payload.get("assigned_to"), ymd)
            d += timedelta(days=1)

        base = {
            "date": start,
            "start_date": start,
            "end_date": end,
            "is_multiday": 1,
            "assignment_mode": payload.get("assignment_mode", "single"),
            "created_at": now_est_str(),
            "updated_at": now_est_str(),
            "created_by": user["id"],
            "updated_by": user["id"],
        }
        job_id = self._jobs().create({**payload, **base})
        self._audit().log(
            user["id"],
            "job.create_multiday",
            "job",
            job_id,
            {"start": start, "end": end},
        )
        return job_id

    def move(self, job_id: int, new_date: str, user):
        job = self._jobs().get(job_id)
        if not job:
            raise LookupError("Job not found.")

        self._guard_day(new_date, user)
        self._guard_timeoff(job["assigned_to"], new_date)

        updates = {}
        if job["is_multiday"]:
            delta = datetime.fromisoformat(new_date) - datetime.fromisoformat(
                job["date"]
            )
            new_start = datetime.fromisoformat(job["start_date"]) + delta
            new_end = datetime.fromisoformat(job["end_date"]) + delta
            updates["date"] = new_date
            updates["start_date"] = new_start.date().isoformat()
            updates["end_date"] = new_end.date().isoformat()
        else:
            updates["date"] = new_date

        updates["updated_at"] = now_est_str()
        updates["updated_by"] = user["id"]

        self._jobs().update(job_id, updates)
        self._audit().log(user["id"], "job.move", "job", job_id, {"to": new_date})
