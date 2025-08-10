import sqlite3
from pathlib import Path
from .utils.logger import setup_logger
from werkzeug.security import generate_password_hash

logger = setup_logger(level=0)
BASE_DIR = Path(__file__).parent
DATABASE = str(BASE_DIR / "db.sqlite3")


def get_database():
    logger.debug(f"Connecting to sqlite3: {DATABASE}")
    conn = sqlite3.connect(DATABASE, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def ensure_pragmas():
    conn = get_database()
    conn.close()


def init_db():
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
        force_password_change INTEGER NOT NULL DEFAULT 0
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
            "INSERT INTO users (first_name,last_name,username,password,role,force_password_change) VALUES (?,?,?,?,?,?)",
            ("Admin", "User", "admin", generate_password_hash("changeme"), "admin", 1),
        )

    conn.commit()
    conn.close()
    logger.info("Database ready.")
