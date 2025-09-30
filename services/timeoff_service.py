# services/timeoff_service.py
from db import get_database
from repos.audit_repo import AuditRepo
from repos.timeoff_repo import TimeOffRepo


def _conn():
    return get_database()


class TimeOffService:
    def _repo(self) -> TimeOffRepo:
        return TimeOffRepo(_conn())

    def _audit(self) -> AuditRepo:
        return AuditRepo(_conn())

    def add(self, tech_id: int, date: str, user):
        # idempotent add
        if self._repo().tech_off_on(tech_id, date):
            return
        self._repo().insert(tech_id, date, user["id"])
        self._audit().log(user["id"], "timeoff.add", "tech", tech_id, {"date": date})
