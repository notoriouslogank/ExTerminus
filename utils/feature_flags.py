from flask import current_app


def feature(name: str) -> bool:
    return bool(current_app.config.get(name, False))
