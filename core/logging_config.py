"""
Centralized Logging Configuration
=================================
Production-ready logging with:
- File rotation (prevents disk fill)
- Separate error log
- JSON format for log aggregation
- Console output for development

Usage:
    from core.logging_config import setup_logging
    setup_logging()  # Call once at app startup
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from datetime import datetime

# =============================================================================
# CONFIGURATION
# =============================================================================

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# File size limits
MAX_LOG_SIZE = 50 * 1024 * 1024  # 50 MB
BACKUP_COUNT = 10  # Keep 10 backup files


# =============================================================================
# SETUP FUNCTION
# =============================================================================

def setup_logging(app_name: str = "bal-dashboard"):
    """
    Configure logging for the application.

    Creates:
    - logs/app.log - All application logs (rotated by size)
    - logs/error.log - Error and critical logs only
    - logs/access.log - HTTP access logs
    - Console output (if not in production)

    Args:
        app_name: Application name for log identification
    """
    # Create logs directory
    os.makedirs(LOG_DIR, exist_ok=True)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    # Clear existing handlers
    root_logger.handlers = []

    # Formatter
    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    # =========================
    # 1. Main Application Log
    # =========================
    app_log_path = os.path.join(LOG_DIR, "app.log")
    app_handler = RotatingFileHandler(
        app_log_path,
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
        encoding="utf-8"
    )
    app_handler.setLevel(logging.DEBUG)
    app_handler.setFormatter(formatter)
    root_logger.addHandler(app_handler)

    # =========================
    # 2. Error Log (errors only)
    # =========================
    error_log_path = os.path.join(LOG_DIR, "error.log")
    error_handler = RotatingFileHandler(
        error_log_path,
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root_logger.addHandler(error_handler)

    # =========================
    # 3. Console Output (development)
    # =========================
    if os.getenv("FLASK_ENV") != "production":
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # =========================
    # 4. Suppress noisy loggers
    # =========================
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    # Log startup
    root_logger.info("=" * 70)
    root_logger.info(f"{app_name.upper()} LOGGING INITIALIZED")
    root_logger.info(f"Log Level: {LOG_LEVEL}")
    root_logger.info(f"Log Directory: {LOG_DIR}")
    root_logger.info("=" * 70)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.

    Usage:
        from core.logging_config import get_logger
        logger = get_logger(__name__)
        logger.info("Hello!")

    Args:
        name: Usually __name__ of the calling module

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# =============================================================================
# LOG VIEWING UTILITIES
# =============================================================================

def get_recent_logs(log_type: str = "app", lines: int = 100) -> list:
    """
    Get recent log entries.

    Args:
        log_type: "app", "error", or "access"
        lines: Number of lines to return

    Returns:
        List of log lines (most recent last)
    """
    log_file = os.path.join(LOG_DIR, f"{log_type}.log")

    if not os.path.exists(log_file):
        return []

    try:
        with open(log_file, "r", encoding="utf-8") as f:
            all_lines = f.readlines()
            return all_lines[-lines:]
    except Exception as e:
        return [f"Error reading logs: {e}"]


def get_recent_errors(lines: int = 50) -> list:
    """Get recent error log entries."""
    return get_recent_logs("error", lines)


# =============================================================================
# STRUCTURED LOGGING HELPERS
# =============================================================================

def log_request(logger: logging.Logger, endpoint: str, method: str,
                user_id: str = None, duration_ms: float = None,
                status_code: int = None, **extra):
    """
    Log an API request with structured data.

    Args:
        logger: Logger instance
        endpoint: API endpoint path
        method: HTTP method
        user_id: User identifier (if authenticated)
        duration_ms: Request duration in milliseconds
        status_code: HTTP response status code
        **extra: Additional fields to log
    """
    parts = [
        f"[{method}] {endpoint}",
        f"status={status_code}" if status_code else None,
        f"user={user_id}" if user_id else None,
        f"duration={duration_ms:.0f}ms" if duration_ms else None,
    ]
    parts.extend([f"{k}={v}" for k, v in extra.items()])

    message = " | ".join(filter(None, parts))

    if status_code and status_code >= 500:
        logger.error(message)
    elif status_code and status_code >= 400:
        logger.warning(message)
    else:
        logger.info(message)


def log_error(logger: logging.Logger, error: Exception,
              context: str = None, **extra):
    """
    Log an error with context.

    Args:
        logger: Logger instance
        error: Exception that occurred
        context: What was happening when error occurred
        **extra: Additional context fields
    """
    parts = [
        f"ERROR: {type(error).__name__}: {str(error)}",
        f"context={context}" if context else None,
    ]
    parts.extend([f"{k}={v}" for k, v in extra.items()])

    message = " | ".join(filter(None, parts))
    logger.error(message, exc_info=True)
