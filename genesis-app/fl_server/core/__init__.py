"""
Core module for the Federated Learning Training API.

This module provides core functionality including configuration management
and structured logging infrastructure.
"""

from .config import Settings, settings
from .logging import (
    StructuredFormatter,
    RunContextFilter,
    ThreadSafeRotatingFileHandler,
    LoggingManager,
    logging_manager,
    get_logger,
    get_run_logger,
    set_run_context,
    clear_run_context,
    cleanup_run_logger,
)
from .log_reader import LogReader

__all__ = [
    # Configuration
    "Settings",
    "settings",
    # Logging
    "StructuredFormatter",
    "RunContextFilter", 
    "ThreadSafeRotatingFileHandler",
    "LoggingManager",
    "logging_manager",
    "get_logger",
    "get_run_logger",
    "set_run_context",
    "clear_run_context",
    "cleanup_run_logger",
    "LogReader",
]