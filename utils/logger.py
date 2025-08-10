import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logger(name="exterminus", log_file=None, level=logging.DEBUG):
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
