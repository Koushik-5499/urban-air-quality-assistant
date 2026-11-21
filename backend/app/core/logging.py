"""Centralized logging configuration with secret redaction."""

import logging
import re
import sys
from typing import Any
from app.core.config import get_settings

SENSITIVE_PATTERNS = [
    (re.compile(r"(?:AIzaSy|AQ\.)[a-zA-Z0-9_\-]{28,60}"), "[REDACTED_GEMINI_KEY]"),
    (re.compile(r"re_[a-zA-Z0-9]{20,}"), "[REDACTED_RESEND_KEY]"),
    (re.compile(r"(?i)(bearer\s+)[a-zA-Z0-9_\-\.]{16,}"), r"\1[REDACTED_TOKEN]"),
    (re.compile(r"(?i)(admin[_-]?secret\s*[:=]\s*)[^\s,]+"), r"\1[REDACTED_SECRET]"),
    (re.compile(r"(?i)(password\s*[:=]\s*)[^\s,]+"), r"\1[REDACTED_PASSWORD]"),
    (re.compile(r"://([^:]+):([^@]+)@"), r"://\1:***@"),
]


def redact_secrets(text: Any) -> Any:
    """Mask sensitive tokens, credentials, and API keys from strings."""
    if not isinstance(text, str):
        return text
    result = text
    for pattern, replacement in SENSITIVE_PATTERNS:
        result = pattern.sub(replacement, result)
    return result


class SecretRedactionFilter(logging.Filter):
    """Logging filter that scrubs sensitive credentials from log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact_secrets(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: redact_secrets(v) if isinstance(v, str) else v
                    for k, v in record.args.items()
                }
            elif isinstance(record.args, (list, tuple)):
                record.args = tuple(
                    redact_secrets(v) if isinstance(v, str) else v
                    for v in record.args
                )
        return True


def setup_logging() -> None:
    """Configure structured console logging with secret sanitization for the application."""
    settings = get_settings()
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    log_format = "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(SecretRedactionFilter())

    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt=date_format,
        handlers=[handler],
        force=True,
    )

    # Suppress overly verbose third-party loggers
    logging.getLogger("uvicorn.access").setLevel(log_level)


def get_logger(name: str) -> logging.Logger:
    """Return a logger instance with the specified module name."""
    logger = logging.getLogger(name)
    logger.addFilter(SecretRedactionFilter())
    return logger
