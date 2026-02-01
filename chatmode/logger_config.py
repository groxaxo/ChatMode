"""
Centralized logging configuration for ChatMode.

Provides consistent logging across the application with support for:
- Console output with color formatting
- File-based logging with rotation
- Configurable log levels via environment variables
- Structured logging for production deployments
- Request tracing with correlation IDs
- Performance timing for debugging
"""

import functools
import json
import logging
import logging.handlers
import os
import sys
import threading
import time
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Thread-local storage for correlation IDs
_local = threading.local()


class ColoredFormatter(logging.Formatter):
    """Custom formatter with color support for console output."""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record):
        # Add color to levelname
        levelname = record.levelname
        if levelname in self.COLORS and sys.stdout.isatty():
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"

        # Add emoji indicators for key levels
        if not hasattr(record, "emoji"):
            if record.levelno >= logging.CRITICAL:
                record.emoji = "💥"
            elif record.levelno >= logging.ERROR:
                record.emoji = "❌"
            elif record.levelno >= logging.WARNING:
                record.emoji = "⚠️"
            elif record.levelno >= logging.INFO:
                record.emoji = "ℹ️"
            else:
                record.emoji = "🔍"

        return super().format(record)


# Correlation ID management
def get_correlation_id() -> str:
    """Get the current correlation ID for request tracing."""
    if not hasattr(_local, "correlation_id"):
        _local.correlation_id = str(uuid.uuid4())[:8]
    return _local.correlation_id


def set_correlation_id(correlation_id: Optional[str] = None) -> str:
    """Set a correlation ID for the current thread."""
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())[:8]
    _local.correlation_id = correlation_id
    return correlation_id


def clear_correlation_id():
    """Clear the correlation ID for the current thread."""
    if hasattr(_local, "correlation_id"):
        delattr(_local, "correlation_id")


@contextmanager
def correlation_context(correlation_id: Optional[str] = None):
    """Context manager for correlation ID scoping."""
    previous_id = getattr(_local, "correlation_id", None)
    new_id = set_correlation_id(correlation_id)
    try:
        yield new_id
    finally:
        if previous_id:
            _local.correlation_id = previous_id
        else:
            clear_correlation_id()


class StructuredLogFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": getattr(_local, "correlation_id", None),
            "source": {
                "filename": record.filename,
                "lineno": record.lineno,
                "funcName": record.funcName,
            },
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in [
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
            ]:
                try:
                    json.dumps(value)  # Test if serializable
                    log_data[key] = value
                except (TypeError, ValueError):
                    log_data[key] = str(value)

        return json.dumps(log_data, default=str)


def log_execution_time(
    logger: Optional[logging.Logger] = None, level: int = logging.DEBUG
):
    """Decorator to log function execution time."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            log = logger or logging.getLogger(f"chatmode.{func.__module__}")
            start_time = time.time()
            correlation_id = get_correlation_id()

            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                log.log(
                    level,
                    f"⏱️  {func.__name__} completed in {elapsed:.3f}s",
                    extra={
                        "function": func.__name__,
                        "duration_ms": elapsed * 1000,
                        "correlation_id": correlation_id,
                        "status": "success",
                    },
                )
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                log.log(
                    level,
                    f"⏱️  {func.__name__} failed after {elapsed:.3f}s: {e}",
                    extra={
                        "function": func.__name__,
                        "duration_ms": elapsed * 1000,
                        "correlation_id": correlation_id,
                        "status": "error",
                        "error": str(e),
                    },
                )
                raise

        return wrapper

    return decorator


@contextmanager
def log_operation(
    logger: logging.Logger,
    operation: str,
    level: int = logging.DEBUG,
    extra: Optional[Dict[str, Any]] = None,
):
    """Context manager to log an operation with timing and correlation ID."""
    start_time = time.time()
    correlation_id = get_correlation_id()

    log_extra = {
        "operation": operation,
        "correlation_id": correlation_id,
        **(extra or {}),
    }

    logger.log(level, f"▶️  Starting: {operation}", extra=log_extra)

    try:
        yield
        elapsed = time.time() - start_time
        logger.log(
            level,
            f"✅ Completed: {operation} in {elapsed:.3f}s",
            extra={**log_extra, "duration_ms": elapsed * 1000, "status": "success"},
        )
    except Exception as e:
        elapsed = time.time() - start_time
        logger.log(
            level,
            f"❌ Failed: {operation} after {elapsed:.3f}s: {e}",
            extra={
                **log_extra,
                "duration_ms": elapsed * 1000,
                "status": "error",
                "error": str(e),
            },
        )
        raise


def setup_logging(
    log_level: Optional[str] = None,
    log_dir: Optional[str] = None,
    log_to_file: bool = True,
    log_to_console: bool = True,
    app_name: str = "chatmode",
    structured: bool = False,
    debug_mode: bool = False,
) -> logging.Logger:
    """
    Setup centralized logging configuration.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                  Defaults to value from LOG_LEVEL env var or INFO.
        log_dir: Directory for log files. Defaults to ./logs
        log_to_file: Whether to log to file. Defaults to True.
        log_to_console: Whether to log to console. Defaults to True.
        app_name: Application name for logger. Defaults to "chatmode".
        structured: Whether to use JSON structured logging. Defaults to False.
        debug_mode: Enable debug mode with extra verbose output. Defaults to False.

    Returns:
        Configured root logger for the application.
    """
    # Determine log level
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    # Debug mode overrides log level
    if debug_mode or os.getenv("DEBUG_MODE", "false").lower() == "true":
        log_level = "DEBUG"
        structured = False  # Use human-readable format in debug mode

    level = getattr(logging, log_level, logging.INFO)

    # Get or create logger
    logger = logging.getLogger(app_name)
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    logger.handlers = []

    # Create formatters
    if structured:
        console_formatter = StructuredLogFormatter()
        file_formatter = StructuredLogFormatter()
    else:
        # Enhanced console formatter with correlation ID
        console_format = "%(emoji)s %(asctime)s - %(name)s - %(levelname)s"
        if debug_mode:
            console_format += (
                " - [%(correlation_id)s]" if hasattr(_local, "correlation_id") else ""
            )
        console_format += " - %(message)s"

        console_formatter = ColoredFormatter(
            console_format,
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Enhanced file formatter with more context
        file_format = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(funcName)s() - %(message)s"
        file_formatter = logging.Formatter(
            file_format,
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    # File handler with rotation
    if log_to_file:
        if log_dir is None:
            log_dir = os.getenv("LOG_DIR", "./logs")

        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        # Main log file with rotation (10 MB max, keep 5 backups)
        log_file = log_path / f"{app_name}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # Debug log file (detailed logging when in debug mode)
        if debug_mode or level <= logging.DEBUG:
            debug_file = log_path / f"{app_name}_debug.log"
            debug_handler = logging.handlers.RotatingFileHandler(
                debug_file, maxBytes=10 * 1024 * 1024, backupCount=3, encoding="utf-8"
            )
            debug_handler.setLevel(logging.DEBUG)
            debug_handler.setFormatter(file_formatter)
            logger.addHandler(debug_handler)

        # Error log file (separate file for errors)
        error_file = log_path / f"{app_name}_errors.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        logger.addHandler(error_handler)

    # Log startup message with configuration details
    logger.info(
        f"🚀 Logging initialized",
        extra={
            "log_level": log_level,
            "log_to_file": log_to_file,
            "log_to_console": log_to_console,
            "structured": structured,
            "debug_mode": debug_mode,
            "app_name": app_name,
        },
    )

    if debug_mode:
        logger.debug("🔧 Debug mode enabled - verbose logging active")

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    This is a convenience wrapper around logging.getLogger that ensures
    the logger inherits from the root 'chatmode' logger configuration.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(f"chatmode.{name}")


def log_request_response(
    logger: logging.Logger,
    method: str,
    url: str,
    status_code: Optional[int] = None,
    duration_ms: Optional[float] = None,
    error: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
):
    """Log HTTP request/response details for debugging API calls."""
    correlation_id = get_correlation_id()

    log_data = {
        "method": method,
        "url": url,
        "correlation_id": correlation_id,
        **(extra or {}),
    }

    if status_code is not None:
        log_data["status_code"] = status_code
    if duration_ms is not None:
        log_data["duration_ms"] = duration_ms
    if error is not None:
        log_data["error"] = error

    if error:
        logger.error(f"❌ HTTP {method} {url} failed: {error}", extra=log_data)
    elif status_code and status_code >= 400:
        logger.warning(
            f"⚠️  HTTP {method} {url} returned {status_code}", extra=log_data
        )
    else:
        duration_str = f" in {duration_ms:.1f}ms" if duration_ms else ""
        logger.debug(f"🌐 HTTP {method} {url}{duration_str}", extra=log_data)


def log_dict(
    logger: logging.Logger,
    message: str,
    data: Dict[str, Any],
    level: int = logging.DEBUG,
):
    """Log a dictionary with proper formatting for debugging."""
    try:
        data_str = json.dumps(data, indent=2, default=str)
        logger.log(level, f"{message}\n{data_str}")
    except (TypeError, ValueError):
        logger.log(level, f"{message}: {data}")


# Legacy compatibility - for modules already using logging.getLogger(__name__)
def configure_root_logger(debug_mode: bool = False):
    """
    Configure the root logger for modules that use logging.getLogger(__name__).
    This ensures all loggers in the application have consistent formatting.

    Args:
        debug_mode: Enable debug mode with extra verbose output
    """
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    if debug_mode or os.getenv("DEBUG_MODE", "false").lower() == "true":
        log_level = "DEBUG"

    level = getattr(logging, log_level, logging.INFO)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    root_logger.handlers = []

    # Add console handler with enhanced formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_format = "%(emoji)s %(asctime)s - %(name)s - %(levelname)s"
    if debug_mode:
        console_format += " - %(funcName)s()"
    console_format += " - %(message)s"

    console_formatter = ColoredFormatter(
        console_format,
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # Add file handler with detailed formatting
    log_dir = os.getenv("LOG_DIR", "./logs")
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    log_file = log_path / "chatmode.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setLevel(level)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(funcName)s() - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # Add debug file handler in debug mode
    if debug_mode or level <= logging.DEBUG:
        debug_file = log_path / "chatmode_debug.log"
        debug_handler = logging.handlers.RotatingFileHandler(
            debug_file, maxBytes=10 * 1024 * 1024, backupCount=3, encoding="utf-8"
        )
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(file_formatter)
        root_logger.addHandler(debug_handler)

    return root_logger
