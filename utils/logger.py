"""Logging utilities for ExTerminus.

Provides:
    - ``setup_logger(name="exterminus", log_file=None, level=logging.INFO)``: configure and return a ``logging.Logger`` with a rotating file handler and a stderr stream handler.

Notes:
    - Log file defaults to ``./logs/exterminus.log`` relative to this module.
    - The ``logs`` directory is created if it doesn't exist.
    - Handlers are only added once per logger name to avoid duplicate output.
    - Format includes timestamp, level, message, and source (path:line).
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logger(
    name="exterminus", log_file: str | Path | None = None, level: int = logging.INFO
) -> logging.Logger:
    """Create or retrieve a configured logger.

    Configures a rotating file handler (512 KiB, 5 backups) and a stream handler to stderr, both using the same formatter:
    ``"%(asctime)s [%(levelname)s] %(message)s in %(pathname)s:%(lineno)d"``.

    If a logger with the given ``name`` already exists and has handlers, this function will not add duplicate handlers (idempotent per logger name).

    Args:
        name (str, optional): Logger name.Defaults to ``"exterminus"``.
        log_file (str | Path | None, optional): Path to the log file.  If ``None``, logs are written to ``./logs/exterminus.log`` (folder created if needed). Defaults to None.
        level (int, optional): Logging level (e.g., ``logging.INFO``, ``logging.DEBUG``). Defaults to logging.INFO.

    Returns:
        logging.Logger: The configured logger instance.
    """
    base = Path(__file__).parent
    logs_dir = base / "logs"
    logs_dir.mkdir(exist_ok=True)
    log_path = log_file or (logs_dir / "exterminus.log")

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        file_handler = RotatingFileHandler(log_path, maxBytes=512 * 1024, backupCount=5)
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s in %(pathname)s:%(lineno)d"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    return logger
