import logging
import os
from logging.handlers import TimedRotatingFileHandler

def get_logger(name: str) -> logging.Logger:
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(log_level)
    os.makedirs("logs", exist_ok=True)

    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    ch.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    ))

    fh = TimedRotatingFileHandler("logs/app.log", when="D", interval=1, backupCount=7, encoding="utf-8")
    fh.setLevel(log_level)
    fh.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(filename)s:%(lineno)d | %(message)s"
    ))

    logger.addHandler(ch)
    logger.addHandler(fh)
    return logger
