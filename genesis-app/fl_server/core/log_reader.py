"""
Log reading utilities for the Federated Learning Training API.

This module provides utilities for reading, parsing, and filtering
structured JSON log files with pagination support.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

from schemas.training import LogEntry, ErrorEntry


class LogReader:
    """
    Utility class for reading and parsing structured JSON log files.
    
    Provides methods for reading logs with filtering, pagination,
    and error extraction capabilities.
    """
    
    def __init__(self, log_files: List[Path]):
        """
        Initialize the log reader with a list of log files.
        
        Args:
            log_files: List of log file paths to read from
        """
        self.log_files = log_files
        self.logger = logging.getLogger(__name__)
    
    def read_logs(
        self,
        lines: int = 100,
        offset: int = 0,
        level: Optional[str] = None,
        tail: bool = False
    ) -> List[LogEntry]:
        """
        Read log entries with filtering and pagination.
        
        Args:
            lines: Maximum number of log entries to return
            offset: Number of entries to skip from the beginning
            level: Filter by log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            tail: If True, read from the end of the logs
            
        Returns:
            List[LogEntry]: List of parsed log entries
        """
        all_entries = []
        
        # Read all log entries from all files
        for log_file in self.log_files:
            if not log_file.exists():
                continue
                
            try:
                entries = self._read_log_file(log_file)
                all_entries.extend(entries)
            except Exception as e:
                self.logger.warning(f"Failed to read log file {log_file}: {e}")
                continue
        
        # Sort by timestamp (newest first if tail=True, oldest first otherwise)
        all_entries.sort(
            key=lambda x: x.timestamp,
            reverse=tail
        )
        
        # Apply level filtering
        if level:
            level_upper = level.upper()
            all_entries = [
                entry for entry in all_entries
                if entry.level == level_upper
            ]
        
        # Apply pagination
        if tail:
            # For tail mode, take the last 'lines' entries after offset
            start_idx = offset
            end_idx = offset + lines
            return all_entries[start_idx:end_idx]
        else:
            # For normal mode, skip offset entries and take 'lines' entries
            start_idx = offset
            end_idx = offset + lines
            return all_entries[start_idx:end_idx]
    
    def read_errors(self) -> List[ErrorEntry]:
        """
        Read and extract error entries from log files.
        
        Returns:
            List[ErrorEntry]: List of error log entries with traceback info
        """
        error_entries = []
        
        for log_file in self.log_files:
            if not log_file.exists():
                continue
                
            try:
                entries = self._read_log_file(log_file)
                # Filter for ERROR and CRITICAL level entries
                errors = [
                    entry for entry in entries
                    if entry.level in ["ERROR", "CRITICAL"]
                ]
                
                # Convert to ErrorEntry objects
                for entry in errors:
                    error_entry = ErrorEntry(
                        timestamp=entry.timestamp,
                        error_type=entry.level,
                        message=entry.message,
                        traceback=getattr(entry, 'traceback', None),
                        context=getattr(entry, 'extra', {}),
                        source=entry.source,
                        run_id=getattr(entry, 'run_id', None)
                    )
                    error_entries.append(error_entry)
                    
            except Exception as e:
                self.logger.warning(f"Failed to read log file {log_file}: {e}")
                continue
        
        # Sort by timestamp (newest first)
        error_entries.sort(key=lambda x: x.timestamp, reverse=True)
        return error_entries
    
    def _read_log_file(self, log_file: Path) -> List[LogEntry]:
        """
        Read and parse a single log file.
        
        Args:
            log_file: Path to the log file
            
        Returns:
            List[LogEntry]: List of parsed log entries
        """
        entries = []
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        # Parse JSON log entry
                        log_data = json.loads(line)
                        entry = self._parse_log_entry(log_data)
                        if entry:
                            entries.append(entry)
                    except json.JSONDecodeError as e:
                        self.logger.warning(
                            f"Invalid JSON in {log_file}:{line_num}: {e}"
                        )
                        continue
                    except Exception as e:
                        self.logger.warning(
                            f"Error parsing log entry in {log_file}:{line_num}: {e}"
                        )
                        continue
                        
        except Exception as e:
            self.logger.error(f"Failed to read log file {log_file}: {e}")
            raise
        
        return entries
    
    def _parse_log_entry(self, log_data: Dict) -> Optional[LogEntry]:
        """
        Parse a log data dictionary into a LogEntry object.
        
        Args:
            log_data: Dictionary containing log entry data
            
        Returns:
            Optional[LogEntry]: Parsed log entry or None if invalid
        """
        try:
            # Parse timestamp
            timestamp_str = log_data.get('timestamp', '')
            if timestamp_str.endswith('Z'):
                timestamp_str = timestamp_str[:-1] + '+00:00'
            
            timestamp = datetime.fromisoformat(timestamp_str)
            
            # Create LogEntry object
            entry = LogEntry(
                timestamp=timestamp,
                level=log_data.get('level', 'INFO'),
                source=log_data.get('source', 'unknown'),
                message=log_data.get('message', ''),
                run_id=log_data.get('run_id'),
                extra=log_data.get('extra', {}),
                traceback=log_data.get('traceback')
            )
            
            return entry
            
        except Exception as e:
            self.logger.warning(f"Failed to parse log entry: {e}")
            return None
    
    @staticmethod
    def get_log_reader_for_run(run_id: str) -> 'LogReader':
        """
        Create a LogReader instance for a specific run.
        
        Args:
            run_id: Unique identifier for the training run
            
        Returns:
            LogReader: Configured log reader for the run
        """
        from .config import settings
        from .logging import logging_manager
        
        log_files = logging_manager.get_log_files(run_id)
        return LogReader(log_files)
    
    @staticmethod
    def get_application_log_reader() -> 'LogReader':
        """
        Create a LogReader instance for application logs.
        
        Returns:
            LogReader: Configured log reader for application logs
        """
        from .config import settings
        
        app_log_path = Path(settings.LOGS_BASE_PATH) / "application.log"
        log_files = []
        
        # Find all application log files (including rotated ones)
        if app_log_path.parent.exists():
            for file_path in app_log_path.parent.iterdir():
                if file_path.is_file() and (
                    file_path.name == "application.log" or
                    file_path.name.startswith("application.log.")
                ):
                    log_files.append(file_path)
        
        # Sort by modification time (newest first)
        log_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return LogReader(log_files)