from flask import session


def get_identity():
    su = session.get("user") or {}
    uid = su.get("user_id")
    try:
        uid = int(uid) if uid is not None else None
    except ValueError:
        uid = None
    role = (su.get("role") or "").lower()
    return uid, role


def is_admin_or_manager(role: str) -> bool:
    return role in ("admin", "manager")
