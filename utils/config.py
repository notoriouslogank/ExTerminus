"""Flask configuration defaults for ExTerminus.

Reads a few settings from environment variables and provides sane defaults for local development.  Security-sensitive values should be overridden in production via the environment.

Env vars:
    - SECRET_KEY: Flask session/signing key.  Defaults to an insecure dev value.
    - SESSION_COOKIE_SECURE: "1" to mark session cookies Secure (HTTPS only).
"""

import os


def _b(v, default=False):
    return str(os.environ.get(v, str(default))).lower() in {"1", "true", "yes", "on"}


class BaseConfig:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me")
    DATABASE_URL = os.environ.get(
        "DATABASE_URL", "sqlite:///instance/exterminus.sqlite3"
    )
    # Feat flags
    FEATURE_UNSCEDULED_POOL = _b("FEATURE_UNSCHEDULED_POOL", False)
    FEATURE_ONBOARDING_TOUR = _b("FEATURE_ONBOARDING_TOUR", False)
    # block prod writes
    READ_ONLY_PROD = _b("READ_ONLY_PROD", False)


class DevConfig(BaseConfig):
    DEBUG = True


class ProdConfig(BaseConfig):
    DEBUG = False


# class Config:
#     """Application configuration container.

#     Attributes:
#         SECRET_KEY (str): Secret used to sign session cookies and CSRF tokens.  **Override in production** via ``SECRET_KEY`` env var.
#         SESSION_COOKIE_HTTPONLY (bool): Prevent client-side JS from reading the session cookie.
#         SESSION_COOKIE_SAMESITE (str): SameSite policy for the session cookie.  Defaults to ``"Lax"`` to mitigate CSRF while allowing top-level nav.
#         SESSION_COOKIE_SECURE (bool): If true, cookies are marked ``Secure`` and only sent over HTTPS.  Set via ``SESSION_COOKIE_SECURE`` env var (``"1"`` to enable).
#         PARMANENT_SESSION_LIFETIME (int): Session lifetime in seconds.  Defaults to 12 hours.
#     """

#     SECRET_KEY = os.environ.get("SECRET_KEY", "dev-insecure-change-me")
#     SESSION_COOKIE_HTTPONLY = True
#     SESSION_COOKIE_SAMESITE = "Lax"
#     SESSION_COOKIE_SECURE = bool(
#         int(os.environ.get("SESSION_COOKIE_SECURE", "0"))
#     )  # change to 1 in production
#     PERMANENT_SESSION_LIFETIME = 60 * 60 * 12  # 12h
