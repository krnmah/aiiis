import json
import logging
from datetime import datetime, timezone
from logging.config import dictConfig
from typing import Any


class JsonFormatter(logging.Formatter):
    # keeps logs structured as json so filters/search are easier later in observability tools.
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        # includes custom fields passed via logger extra={...} while excluding internals.
        skip = {
            "name",
            "msg",
            "args",
            "levelname",
            "levelno",
            "pathname",
            "filename",
            "module",
            "exc_info",
            "exc_text",
            "stack_info",
            "lineno",
            "funcName",
            "created",
            "msecs",
            "relativeCreated",
            "thread",
            "threadName",
            "processName",
            "process",
            "message",
        }
        for key, value in record.__dict__.items():
            if key not in skip and not key.startswith("_"):
                payload[key] = value

        return json.dumps(payload, default=str)


def configure_logging(log_level: str) -> None:
    # centralized logging setup here so every module gets the same format and level.
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "()": "app.core.logging_config.JsonFormatter",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "json",
                }
            },
            "root": {
                "level": log_level.upper(),
                "handlers": ["console"],
            },
        }
    )
