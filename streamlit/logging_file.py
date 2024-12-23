from logging.config import dictConfig
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
# Create the logs directory if it doesn't exist
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)-8s] [%(filename)-12s:%(lineno)s] ::: %(message)s "
        },
        "simple": {"format": "%(asctime)s [%(levelname)-8s] ::: %(message)s "},
    },
    "handlers": {
        "server": {
            "level": "DEBUG",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": f"{str(LOG_DIR)}/server.log",
            "when": "midnight",
            "interval": 1,
            "encoding": "utf-8",
            "backupCount": 5,
            "formatter": "simple",
        },
        "request_handler": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": f"{str(LOG_DIR)}/requests.log",
            "maxBytes": 1024 * 1024 * 10,  # 10 MB
            "backupCount": 10,
            "formatter": "simple",
        },
        "database_handler": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": f"{str(LOG_DIR)}/database.log",
            "maxBytes": 1024 * 1024 * 10,  # 10 MB
            "backupCount": 10,
            "formatter": "simple",
        },
        "code_handler": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": f"{str(LOG_DIR)}/code_debug.log",
            "maxBytes": 1024 * 1024 * 10,  # 10 MB
            "backupCount": 10,
            "formatter": "standard",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["server"],
            "level": "INFO",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["database_handler"],
            "level": "DEBUG",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["request_handler"],
            "level": "DEBUG",
            "propagate": False,
        },
        "dev_logger": {
            "handlers": ["code_handler"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}
