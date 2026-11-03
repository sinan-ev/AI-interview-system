"""
Structured Logging Module.
Provides JSON formatting, context tracking (request_id, user_id, etc.),
and automatic redaction of sensitive credentials and tokens.
"""
import json
import logging
import re
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# Context variables for request tracing
request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id_ctx", default=None)
user_id_ctx: ContextVar[Optional[str]] = ContextVar("user_id_ctx", default=None)
interview_id_ctx: ContextVar[Optional[str]] = ContextVar("interview_id_ctx", default=None)

# Sensitive keys to redact
SENSITIVE_KEYS = {
    "password", "password_hash", "token", "access_token", "refresh_token",
    "jwt", "api_key", "secret", "secret_key", "authorization", "cookie"
}


def redact_sensitive_data(data: Any) -> Any:
    """Recursively redact sensitive key values in dictionaries or strings."""
    if isinstance(data, dict):
        cleaned = {}
        for k, v in data.items():
            if any(sensitive in k.lower() for sensitive in SENSITIVE_KEYS):
                cleaned[k] = "[REDACTED]"
            elif isinstance(v, (dict, list)):
                cleaned[k] = redact_sensitive_data(v)
            else:
                cleaned[k] = v
        return cleaned
    elif isinstance(data, list):
        return [redact_sensitive_data(item) for item in data]
    elif isinstance(data, str):
        # Redact Bearer tokens
        return re.sub(r"Bearer\s+([a-zA-Z0-9_\-\.]+)", "Bearer [REDACTED]", data)
    return data


class StructuredJSONFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects with context metadata."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", request_id_ctx.get()),
            "user_id": getattr(record, "user_id", user_id_ctx.get()),
            "interview_id": getattr(record, "interview_id", interview_id_ctx.get()),
        }

        # Include extra attributes if passed in logger calls
        for attr in ("question_id", "agent", "provider", "model", "latency_ms", "status", "error_code"):
            val = getattr(record, attr, None)
            if val is not None:
                log_entry[attr] = val

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Redact any accidental sensitive content
        sanitized_entry = redact_sensitive_data(log_entry)
        return json.dumps(sanitized_entry, default=str)


def setup_logging(level: str = "INFO", json_format: bool = True) -> logging.Logger:
    """Configure the root logger and return the application logger."""
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    if json_format:
        handler.setFormatter(StructuredJSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s")
        )

    root_logger.addHandler(handler)

    # Quiet external noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    return logging.getLogger("ai_interview")


logger = setup_logging()
