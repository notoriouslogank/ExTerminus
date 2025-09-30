import json
import time


class AuditRepo:
    def __init__(self, conn):
        self.conn = conn

    def log(self, actor_id, action, subject_type, subject_id, meta: dict):
        self.conn.execute(
            "INSERT INTO audit_log(actor_id, action, subject_type, subject_id, metadata, ts) VALUES(?, ?, ?, ?, ?, ?)",
            (
                actor_id,
                action,
                subject_type,
                subject_id,
                json.dumps(meta or {}),
                int(time.time()),
            ),
        )
