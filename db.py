"""Database utilities for ExTerminus (SQLite).

Provides:
    - ``get_database()``: open a configured SQLite connection (WAL, FKs on).
    - ``ensure_pragmas()``: no-op that touches a connection to apply PRAGMAs.
    - ``init_db()``: create tables if missing and bootstrap a default admin.

Notes:
    - File path is ``db.sqlite3`` under the package directory.
    - PRAGMAs: ``foreign_keys=ON`` and ``journal_mode=WAL``.
"""

import sqlite3
from pathlib import Path

from werkzeug.security import generate_password_hash

from utils.logger import setup_logger

logger = setup_logger(level=0)
BASE_DIR = Path(__file__).parent
DATABASE = str(BASE_DIR / "db.sqlite3")


def get_database() -> sqlite3.Connection:
    """Open a SQLite connection with standard app settings.

    Configures:
        - ``row_factory = sqlite3.Row`` for dict-like rows.
        - ``PRAGMA foreign_keys = ON`` to enforce FK constraints.
        - ``PRAGMA journal_mode = WAL`` for better concurrency and durability.

    Returns:
        sqlite3.Connection: An open connection pointing at ``DATABASE``.
    """
    logger.debug(f"Connecting to sqlite3: {DATABASE}")
    conn = sqlite3.connect(DATABASE, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def ensure_pragmas() -> None:
    """Ensure database PRAGMAs are applied.

    Opens and closes a connection so the PRAGMA settings in ``get_database()`` take effect at least once during app lifetime.

    Returns:
        None
    """
    conn = get_database()
    conn.close()


def init_db() -> None:
    """Create all tables if they don't exist and seed a default admin.

    Creates tables:
        - ``users``: basic auth and role info.
        - ``technicians``: technician roster.
        - ``jobs``: scheduled work items with optional technician and audit cols.
        - ``locks``: per-day lock to prevent scheduling.
        - ``time_off``: technician time-off ranges (inclusive).

    Bootstraps:
        - When there are no users, inserts an ``admin`` user with username ``"admin"`` and password ``"changeme"`` and sets a force-reset flag.

    Returns:
        None

    """
    logger.debug("Initializing database...")
    conn = get_database()
    cur = conn.cursor()

    # USERS
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT,
        last_name TEXT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'tech',
        must_reset_password INTEGER NOT NULL DEFAULT 0,
        last_password_change TEXT
    );
    """
    )

    # TECHNICIANS
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS technicians (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    );
    """
    )

    # JOBS
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT,
        start_time TEXT,
        end_time TEXT,
        time_range TEXT,
        job_type TEXT,
        price REAL,
        fumigation_type TEXT,
        target_pest TEXT,
        custom_pest TEXT,
        exclusion_subtype TEXT,
        notes TEXT,
        rei_zip TEXT,
        rei_quantity INTEGER,
        rei_city_name TEXT,
        technician_id INTEGER,
        two_man INTEGER NOT NULL DEFAULT 0,
        created_by INTEGER,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        last_modified TEXT,
        last_modified_by INTEGER,
        FOREIGN KEY (technician_id) REFERENCES technicians(id) ON DELETE SET NULL,
        FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (last_modified_by) REFERENCES users(id) ON DELETE SET NULL
    );
    """
    )

    # LOCKS
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS locks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT UNIQUE NOT NULL,
        locked_by INTEGER,
        locked_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (locked_by) REFERENCES users(id) ON DELETE SET NULL
    );
    """
    )

    # TIME OFF
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS time_off (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        technician_id INTEGER NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT NOT NULL,
        reason TEXT,
        FOREIGN KEY (technician_id) REFERENCES technicians(id) ON DELETE CASCADE
    );
    """
    )

    # bootstrap admin if not exist
    cur.execute("SELECT COUNT(*) AS c FROM users")
    if cur.fetchone()["c"] == 0:
        logger.warning(
            "No users found; creating default admin (username 'admin' / password 'changeme')."
        )
        cur.execute(
            "INSERT INTO users (first_name,last_name,username,password,role,must_reset_password) VALUES (?,?,?,?,?,?)",
            ("Admin", "User", "admin", generate_password_hash("changeme"), "admin", 1),
        )

    cur.execute("CREATE INDEX IF NOT EXISTS idx_jobs_start ON jobs(start_date);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_jobs_end ON jobs(end_date);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_timeoff_start ON time_off(start_date);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_timeoff_end ON time_off(end_date);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_locks_date ON locks(date);")

    conn.commit()
    conn.close()
    logger.info("Database ready.")
