from pathlib import Path
import logging
from logging.config import dictConfig
from logging.handlers import TimedRotatingFileHandler


def setup_logging():
    Path("logs").mkdir(exist_ok=True)
    dictConfig({
        "version": 1,
        "disable_existing_loggers": False,

        "formatters": {
            "default": {
                "format": "%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            },
        },

        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
            },
            "file_app": {
                "class": "logging.handlers.TimedRotatingFileHandler",
                "filename": "logs/app.log",
                "formatter": "default",
                "when": "midnight",
                "interval": 1,
                "backupCount": 14,
                "encoding": "utf-8",
            },
            "file_error": {
                "class": "logging.handlers.TimedRotatingFileHandler",
                "filename": "logs/error.log",
                "formatter": "default",
                "when": "midnight",
                "interval": 1,
                "backupCount": 30,
                "level": "ERROR",
                "encoding": "utf-8",
            },
            "file_nao_encontrado": {
                "class": "logging.handlers.TimedRotatingFileHandler",
                "filename": "logs/nao_encontrado.log",
                "formatter": "default",
                "when": "midnight",
                "interval": 1,
                "backupCount": 90,
                "encoding": "utf-8",
            },
        },

        "loggers": {
            "app": {
                "level": "INFO",
                "handlers": ["console", "file_app", "file_error"],
                "propagate": False,
            },
            "app.nao_encontrado": {
                "level": "INFO",
                "handlers": ["console", "file_nao_encontrado"],
                "propagate": False,
            },
        },

        "root": {
            "level": "WARNING",
            "handlers": ["console"],
        },
    })