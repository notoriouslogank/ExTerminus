from functools import wraps

from flask import abort, g


def role_required(*roles):
    def deco(fn):
        @wraps(fn)
        def inner(*a, **k):
            if g.user["role"] not in roles:
                abort(403)
            return fn(*a, **k)

        return inner

    return deco
