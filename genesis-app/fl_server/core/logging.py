"""
Structured logging infrastructure for the Federated Learning Training API.

This module provides structured JSON logging with run-specific context,
log rotation, and thread-safe operations.
"""

import json
import logging
import logging.handlers
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from .config import settings


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs structured JSON log entries.
    
    Each log entry includes timestamp, level, source, run_id (if available),
    message, and optional traceback information.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format a log record as structured JSON.
        
        Args:
            record: The log record to format
            
        Returns:
            str: JSON-formatted log entry
        """
        # Build the base log object
        log_obj = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "source": record.name,
            "message": record.getMessage(),
        }
        
        # Add run_id if available in the record
        if hasattr(record, 'run_id') and record.run_id:
            log_obj["run_id"] = record.run_id
        
        # Add extra fields if present
        if hasattr(record, 'extra') and record.extra:
            log_obj["extra"] = record.extra
        
        # Add traceback if exception info is present
        if record.exc_info:
            log_obj["traceback"] = self.formatException(record.exc_info)
        
        # Add stack info if present
        if record.stack_info:
            log_obj["stack_info"] = record.stack_info
        
        return json.dumps(log_obj, ensure_ascii=False)


class RunContextFilter(logging.Filter):
    """
    Logging filter that adds run context to log records.
    
    This filter injects run_id and other contextual information
    into log records when available from thread-local storage.
    """
    
    def __init__(self):
        super().__init__()
        self._local = threading.local()
    
    def set_run_context(self, run_id: str, extra: Optional[Dict[str, Any]] = None):
        """
        Set the run context for the current thread.
        
        Args:
            run_id: Unique identifier for the training run
            extra: Additional context information
        """
        self._local.run_id = run_id
        self._local.extra = extra or {}
    
    def clear_run_context(self):
        """Clear the run context for the current thread."""
        if hasattr(self._local, 'run_id'):
            delattr(self._local, 'run_id')
        if hasattr(self._local, 'extra'):
            delattr(self._local, 'extra')
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Add run context to the log record if available.
        
        Args:
            record: The log record to filter
            
        Returns:
            bool: Always True (don't filter out records)
        """
        # Add run_id if available in thread-local storage
        if hasattr(self._local, 'run_id'):
            record.run_id = self._local.run_id
        
        # Add extra context if available
        if hasattr(self._local, 'extra'):
            record.extra = self._local.extra
        
        return True


class ThreadSafeRotatingFileHandler(logging.handlers.RotatingFileHandler):
    """
    Thread-safe rotating file handler with enhanced rotation logic.
    
    This handler ensures thread-safe log rotation and supports both
    size-based and time-based rotation policies.
    """
    
    def __init__(self, filename: str, maxBytes: int = 0, backupCount: int = 0):
        """
        Initialize the thread-safe rotating file handler.
        
        Args:
            filename: Path to the log file
            maxBytes: Maximum file size before rotation
            backupCount: Number of backup files to keep
        """
        super().__init__(filename, maxBytes=maxBytes, backupCount=backupCount)
        self._rotation_lock = threading.Lock()
    
    def doRollover(self):
        """
        Perform log rotation in a thread-safe manner.
        """
        with self._rotation_lock:
            super().doRollover()


class LoggingManager:
    """
    Centralized logging manager for the FL Training API.
    
    Manages application-wide logging configuration, run-specific loggers,
    and provides thread-safe logging operations.
    """
    
    def __init__(self):
        """Initialize the logging manager."""
        self._run_loggers: Dict[str, logging.Logger] = {}
        self._run_context_filter = RunContextFilter()
        self._setup_root_logger()
    
    def _setup_root_logger(self):
        """Configure the root logger with structured formatting."""
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, settings.LOG_LEVEL))
        
        # Clear any existing handlers
        root_logger.handlers.clear()
        
        # Create console handler with structured formatting
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(StructuredFormatter())
        console_handler.addFilter(self._run_context_filter)
        root_logger.addHandler(console_handler)
        
        # Create application log file handler
        app_log_path = Path(settings.LOGS_BASE_PATH) / "application.log"
        app_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        app_file_handler = ThreadSafeRotatingFileHandler(
            filename=str(app_log_path),
            maxBytes=settings.MAX_LOG_FILE_SIZE,
            backupCount=5
        )
        app_file_handler.setFormatter(StructuredFormatter())
        app_file_handler.addFilter(self._run_context_filter)
        root_logger.addHandler(app_file_handler)
    
    def get_run_logger(self, run_id: str) -> logging.Logger:
        """
        Get or create a run-specific logger.
        
        Args:
            run_id: Unique identifier for the training run
            
        Returns:
            logging.Logger: Logger configured for the specific run
        """
        if run_id not in self._run_loggers:
            self._run_loggers[run_id] = self._create_run_logger(run_id)
        
        return self._run_loggers[run_id]
    
    def _create_run_logger(self, run_id: str) -> logging.Logger:
        """
        Create a new run-specific logger.
        
        Args:
            run_id: Unique identifier for the training run
            
        Returns:
            logging.Logger: Configured run-specific logger
        """
        logger_name = f"fl_training.run.{run_id}"
        logger = logging.getLogger(logger_name)
        logger.setLevel(getattr(logging, settings.LOG_LEVEL))
        
        # Ensure run log directory exists
        run_log_dir = settings.get_run_logs_path(run_id)
        run_log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create run-specific file handler
        run_log_file = run_log_dir / "training.log"
        run_file_handler = ThreadSafeRotatingFileHandler(
            filename=str(run_log_file),
            maxBytes=settings.MAX_LOG_FILE_SIZE,
            backupCount=3
        )
        run_file_handler.setFormatter(StructuredFormatter())
        
        # Create a filter that always adds the run_id
        class RunSpecificFilter(logging.Filter):
            def filter(self, record):
                record.run_id = run_id
                return True
        
        run_file_handler.addFilter(RunSpecificFilter())
        logger.addHandler(run_file_handler)
        
        # Don't propagate to root logger to avoid duplicate entries
        logger.propagate = False
        
        return logger
    
    def set_run_context(self, run_id: str, extra: Optional[Dict[str, Any]] = None):
        """
        Set the run context for the current thread.
        
        Args:
            run_id: Unique identifier for the training run
            extra: Additional context information
        """
        self._run_context_filter.set_run_context(run_id, extra)
    
    def clear_run_context(self):
        """Clear the run context for the current thread."""
        self._run_context_filter.clear_run_context()
    
    def cleanup_run_logger(self, run_id: str):
        """
        Clean up resources for a run-specific logger.
        
        Args:
            run_id: Unique identifier for the training run
        """
        if run_id in self._run_loggers:
            logger = self._run_loggers[run_id]
            
            # Close all handlers
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)
            
            # Remove from cache
            del self._run_loggers[run_id]
    
    def get_log_files(self, run_id: str) -> list[Path]:
        """
        Get all log files for a specific run.
        
        Args:
            run_id: Unique identifier for the training run
            
        Returns:
            list[Path]: List of log file paths for the run
        """
        run_log_dir = settings.get_run_logs_path(run_id)
        if not run_log_dir.exists():
            return []
        
        # Find all log files (including rotated ones)
        log_files = []
        for file_path in run_log_dir.iterdir():
            if file_path.is_file() and (
                file_path.name == "training.log" or
                file_path.name.startswith("training.log.")
            ):
                log_files.append(file_path)
        
        # Sort by modification time (newest first)
        log_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return log_files


# Global logging manager instance
logging_manager = LoggingManager()


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: Logger name
        
    Returns:
        logging.Logger: Configured logger
    """
    return logging.getLogger(name)


def get_run_logger(run_id: str) -> logging.Logger:
    """
    Get a run-specific logger.
    
    Args:
        run_id: Unique identifier for the training run
        
    Returns:
        logging.Logger: Run-specific logger
    """
    return logging_manager.get_run_logger(run_id)


def set_run_context(run_id: str, extra: Optional[Dict[str, Any]] = None):
    """
    Set the run context for the current thread.
    
    Args:
        run_id: Unique identifier for the training run
        extra: Additional context information
    """
    logging_manager.set_run_context(run_id, extra)


def clear_run_context():
    """Clear the run context for the current thread."""
    logging_manager.clear_run_context()


def cleanup_run_logger(run_id: str):
    """
    Clean up resources for a run-specific logger.
    
    Args:
        run_id: Unique identifier for the training run
    """
    logging_manager.cleanup_run_logger(run_id)