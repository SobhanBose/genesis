"""
Thread-safe run metadata storage implementation.

This module provides the RunStore class for managing persistent storage
of training run metadata in a JSON file with thread-safe operations.
"""

import json
import threading
import time
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

from schemas.training import RunMetadata, RunStatusEnum

logger = logging.getLogger(__name__)


class RunStore:
    """
    Thread-safe storage for training run metadata.
    
    Manages persistent storage of run metadata in a JSON file with
    thread-safe read/write operations, CRUD functionality, and
    comprehensive error handling for file system operations.
    """
    
    def __init__(self, storage_path: str = "data/runs.json", max_retries: int = 3, retry_delay: float = 0.1):
        """
        Initialize the RunStore with the specified storage path.
        
        Args:
            storage_path: Path to the JSON file for storing run metadata
            max_retries: Maximum number of retry attempts for failed operations
            retry_delay: Delay between retry attempts in seconds
        """
        self.storage_path = Path(storage_path)
        self._lock = threading.RLock()  # Reentrant lock for nested operations
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Ensure the data directory exists
        self._ensure_directory_exists()
        
        # Initialize storage file if it doesn't exist
        self._initialize_storage()
    
    def _ensure_directory_exists(self) -> None:
        """Ensure the storage directory exists with proper error handling."""
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error(f"Failed to create storage directory {self.storage_path.parent}: {e}")
            raise
    
    def _initialize_storage(self) -> None:
        """Initialize the storage file if it doesn't exist or is corrupted."""
        for attempt in range(self.max_retries + 1):
            try:
                if not self.storage_path.exists():
                    logger.info(f"Creating new run storage file at {self.storage_path}")
                    self._write_store_with_retry({"runs": {}})
                else:
                    # Validate existing file by attempting to read it
                    self._read_store_with_retry()
                    logger.info(f"Using existing run storage file at {self.storage_path}")
                return
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Corrupted storage file detected (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries:
                    # Try to backup corrupted file before reinitializing
                    self._backup_corrupted_file()
                    time.sleep(self.retry_delay)
                    continue
                else:
                    logger.error("Max retries reached. Reinitializing storage file.")
                    self._write_store_with_retry({"runs": {}})
                    return
            except Exception as e:
                if attempt < self.max_retries:
                    logger.warning(f"Storage initialization failed (attempt {attempt + 1}): {e}")
                    time.sleep(self.retry_delay)
                    continue
                else:
                    logger.error(f"Failed to initialize storage after {self.max_retries} attempts: {e}")
                    raise
    
    def _backup_corrupted_file(self) -> None:
        """Create a backup of corrupted storage file for debugging."""
        try:
            if self.storage_path.exists():
                backup_path = self.storage_path.with_suffix(f'.corrupted.{int(time.time())}')
                self.storage_path.rename(backup_path)
                logger.info(f"Backed up corrupted file to {backup_path}")
        except Exception as e:
            logger.warning(f"Failed to backup corrupted file: {e}")
    
    def _read_store(self) -> Dict[str, Any]:
        """
        Thread-safe read operation from the JSON storage file.
        
        Returns:
            Dictionary containing the storage data
            
        Raises:
            json.JSONDecodeError: If the file contains invalid JSON
            FileNotFoundError: If the storage file doesn't exist
        """
        with self._lock:
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Ensure the expected structure exists
                    if "runs" not in data:
                        data["runs"] = {}
                    return data
            except FileNotFoundError:
                logger.warning(f"Storage file not found: {self.storage_path}")
                # Initialize and return empty structure
                self._write_store({"runs": {}})
                return {"runs": {}}
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in storage file: {e}")
                raise
    
    def _read_store_with_retry(self) -> Dict[str, Any]:
        """
        Read operation with retry logic for handling temporary failures.
        
        Returns:
            Dictionary containing the storage data
            
        Raises:
            Exception: If all retry attempts fail
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return self._read_store()
            except (OSError, IOError, json.JSONDecodeError) as e:
                last_exception = e
                if attempt < self.max_retries:
                    logger.warning(f"Read attempt {attempt + 1} failed: {e}. Retrying...")
                    time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                    continue
                else:
                    logger.error(f"All read attempts failed. Last error: {e}")
                    break
        
        raise last_exception
    
    def _write_store(self, data: Dict[str, Any]) -> None:
        """
        Thread-safe write operation to the JSON storage file.
        
        Args:
            data: Dictionary to write to storage
            
        Raises:
            OSError: If there are file system permission issues
        """
        with self._lock:
            temp_path = None
            try:
                # Write to temporary file first for atomic operation
                temp_path = self.storage_path.with_suffix('.tmp')
                with open(temp_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False, default=str)
                
                # Atomic move to final location
                temp_path.replace(self.storage_path)
                
            except OSError as e:
                logger.error(f"Failed to write storage file: {e}")
                # Clean up temporary file if it exists
                if temp_path and temp_path.exists():
                    try:
                        temp_path.unlink()
                    except OSError:
                        pass  # Ignore cleanup errors
                raise
    
    def _write_store_with_retry(self, data: Dict[str, Any]) -> None:
        """
        Write operation with retry logic for handling temporary failures.
        
        Args:
            data: Dictionary to write to storage
            
        Raises:
            Exception: If all retry attempts fail
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                self._write_store(data)
                return
            except (OSError, IOError) as e:
                last_exception = e
                if attempt < self.max_retries:
                    logger.warning(f"Write attempt {attempt + 1} failed: {e}. Retrying...")
                    time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                    continue
                else:
                    logger.error(f"All write attempts failed. Last error: {e}")
                    break
        
        raise last_exception
    
    def create_run(self, run_metadata: RunMetadata) -> None:
        """
        Add a new run record to storage.
        
        Args:
            run_metadata: RunMetadata object to store
            
        Raises:
            ValueError: If a run with the same ID already exists
            Exception: If storage operations fail after retries
        """
        with self._lock:
            try:
                data = self._read_store_with_retry()
                
                if run_metadata.run_id in data["runs"]:
                    raise ValueError(f"Run {run_metadata.run_id} already exists")
                
                # Convert RunMetadata to dict for JSON serialization
                run_dict = run_metadata.dict()
                data["runs"][run_metadata.run_id] = run_dict
                
                self._write_store_with_retry(data)
                logger.info(f"Created run record: {run_metadata.run_id}")
                
            except ValueError:
                # Re-raise ValueError as-is (business logic error)
                raise
            except Exception as e:
                logger.error(f"Failed to create run {run_metadata.run_id}: {e}")
                raise
    
    def update_run(self, run_id: str, updates: Dict[str, Any]) -> None:
        """
        Update an existing run record with partial updates.
        
        Args:
            run_id: ID of the run to update
            updates: Dictionary of fields to update
            
        Raises:
            ValueError: If the run doesn't exist
            Exception: If storage operations fail after retries
        """
        with self._lock:
            try:
                data = self._read_store_with_retry()
                
                if run_id not in data["runs"]:
                    raise ValueError(f"Run {run_id} not found")
                
                # Update the run data
                run_data = data["runs"][run_id]
                run_data.update(updates)
                
                # Update timestamps for certain status changes
                if "status" in updates:
                    if updates["status"] == RunStatusEnum.TRAINING:
                        run_data["start_time"] = datetime.utcnow().isoformat()
                    elif updates["status"] in [RunStatusEnum.COMPLETED, RunStatusEnum.ERROR]:
                        if "end_time" not in updates:
                            run_data["end_time"] = datetime.utcnow().isoformat()
                        
                        # Calculate duration if both start and end times exist
                        if run_data.get("start_time") and run_data.get("end_time"):
                            try:
                                start = datetime.fromisoformat(run_data["start_time"].replace('Z', '+00:00'))
                                end = datetime.fromisoformat(run_data["end_time"].replace('Z', '+00:00'))
                                run_data["duration"] = int((end - start).total_seconds())
                            except (ValueError, TypeError) as e:
                                logger.warning(f"Failed to calculate duration for run {run_id}: {e}")
                
                self._write_store_with_retry(data)
                logger.debug(f"Updated run {run_id} with: {updates}")
                
            except ValueError:
                # Re-raise ValueError as-is (business logic error)
                raise
            except Exception as e:
                logger.error(f"Failed to update run {run_id}: {e}")
                raise
    
    def get_run(self, run_id: str) -> Optional[RunMetadata]:
        """
        Retrieve a single run by ID.
        
        Args:
            run_id: ID of the run to retrieve
            
        Returns:
            RunMetadata object if found, None otherwise
        """
        with self._lock:
            try:
                data = self._read_store_with_retry()
                run_data = data["runs"].get(run_id)
                
                if run_data is None:
                    return None
                
                try:
                    return RunMetadata(**run_data)
                except Exception as e:
                    logger.error(f"Failed to parse run metadata for {run_id}: {e}")
                    return None
                    
            except Exception as e:
                logger.error(f"Failed to retrieve run {run_id}: {e}")
                return None
    
    def get_all_runs(self) -> List[RunMetadata]:
        """
        Retrieve all run records.
        
        Returns:
            List of RunMetadata objects
        """
        with self._lock:
            try:
                data = self._read_store_with_retry()
                runs = []
                
                for run_id, run_data in data["runs"].items():
                    try:
                        runs.append(RunMetadata(**run_data))
                    except Exception as e:
                        logger.error(f"Failed to parse run metadata for {run_id}: {e}")
                        continue
                
                return runs
                
            except Exception as e:
                logger.error(f"Failed to retrieve all runs: {e}")
                return []
    
    def get_active_run(self) -> Optional[RunMetadata]:
        """
        Get the currently active training run.
        
        Returns:
            RunMetadata for the active run, or None if no run is active
        """
        runs = self.get_all_runs()
        for run in runs:
            if run.status == RunStatusEnum.TRAINING:
                return run
        return None
    
    def get_latest_run(self) -> Optional[RunMetadata]:
        """
        Get the most recently started run.
        
        Returns:
            RunMetadata for the latest run, or None if no runs exist
        """
        runs = self.get_all_runs()
        if not runs:
            return None
        
        # Sort by start_time descending and return the first one
        try:
            latest_run = max(runs, key=lambda r: r.start_time)
            return latest_run
        except (ValueError, TypeError) as e:
            logger.error(f"Failed to find latest run: {e}")
            return None
    
    def filter_runs(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        sort: str = "desc"
    ) -> List[RunMetadata]:
        """
        Retrieve filtered and paginated list of runs.
        
        Args:
            status: Filter by run status (optional)
            limit: Maximum number of runs to return
            offset: Number of runs to skip
            sort: Sort order by start_time ("asc" or "desc")
            
        Returns:
            List of RunMetadata objects matching the criteria
        """
        runs = self.get_all_runs()
        
        # Filter by status if specified
        if status:
            try:
                status_enum = RunStatusEnum(status.upper())
                runs = [run for run in runs if run.status == status_enum]
            except ValueError:
                logger.warning(f"Invalid status filter: {status}")
                return []
        
        # Sort by start_time
        try:
            reverse_sort = sort.lower() == "desc"
            runs.sort(key=lambda r: r.start_time, reverse=reverse_sort)
        except (ValueError, TypeError) as e:
            logger.error(f"Failed to sort runs: {e}")
        
        # Apply pagination
        start_idx = max(0, offset)
        end_idx = start_idx + limit
        
        return runs[start_idx:end_idx]
    
    def get_run_count(self, status: Optional[str] = None) -> int:
        """
        Get the total count of runs, optionally filtered by status.
        
        Args:
            status: Filter by run status (optional)
            
        Returns:
            Total number of runs matching the criteria
        """
        runs = self.get_all_runs()
        
        if status:
            try:
                status_enum = RunStatusEnum(status.upper())
                runs = [run for run in runs if run.status == status_enum]
            except ValueError:
                return 0
        
        return len(runs)
    
    def delete_run(self, run_id: str) -> bool:
        """
        Delete a run record from storage.
        
        Args:
            run_id: ID of the run to delete
            
        Returns:
            True if the run was deleted, False if it didn't exist
        """
        with self._lock:
            try:
                data = self._read_store_with_retry()
                
                if run_id not in data["runs"]:
                    return False
                
                del data["runs"][run_id]
                self._write_store_with_retry(data)
                logger.info(f"Deleted run record: {run_id}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to delete run {run_id}: {e}")
                return False
    
    def cleanup_old_runs(self, max_runs: int = 1000) -> int:
        """
        Clean up old run records to prevent unlimited growth.
        
        Args:
            max_runs: Maximum number of runs to keep
            
        Returns:
            Number of runs deleted
        """
        if max_runs <= 0:
            return 0
        
        runs = self.get_all_runs()
        if len(runs) <= max_runs:
            return 0
        
        # Sort by start_time and keep the most recent ones
        try:
            runs.sort(key=lambda r: r.start_time, reverse=True)
            runs_to_delete = runs[max_runs:]
            
            deleted_count = 0
            for run in runs_to_delete:
                if self.delete_run(run.run_id):
                    deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} old run records")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old runs: {e}")
            return 0