"""
Configuration management for the Federated Learning Training API.

This module provides centralized configuration using Pydantic BaseSettings
with environment variable loading and validation.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    
    All configuration parameters can be set via environment variables
    or loaded from a .env file.
    """
    
    # Application metadata
    APP_NAME: str = Field(
        default="Federated Learning Training API",
        description="Application name"
    )
    APP_VERSION: str = Field(
        default="1.0.0",
        description="Application version"
    )
    
    # Logging configuration
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging verbosity level"
    )
    
    # Path configuration
    RUNS_DATA_PATH: str = Field(
        default="data/runs.json",
        description="Path to runs metadata JSON file"
    )
    LOGS_BASE_PATH: str = Field(
        default="logs",
        description="Base directory for application logs"
    )
    RESULTS_BASE_PATH: str = Field(
        default="results",
        description="Base directory for training results"
    )
    
    # Log rotation and retention limits
    MAX_LOG_FILE_SIZE: int = Field(
        default=100 * 1024 * 1024,  # 100MB in bytes
        description="Maximum log file size before rotation (bytes)"
    )
    LOG_RETENTION_DAYS: int = Field(
        default=30,
        description="Number of days to retain log files"
    )
    
    # Server configuration
    HOST: str = Field(
        default="0.0.0.0",
        description="Server host address"
    )
    PORT: int = Field(
        default=8000,
        description="Server port"
    )
    
    # API configuration
    API_V1_PREFIX: str = Field(
        default="/api/v1",
        description="API v1 prefix path"
    )
    
    # Debug configuration
    DEBUG: bool = Field(
        default=False,
        description="Enable debug mode with detailed error messages"
    )
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
    
    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        """Validate log level is a valid Python logging level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v.upper()
    
    @validator("MAX_LOG_FILE_SIZE")
    def validate_max_log_file_size(cls, v):
        """Validate max log file size is positive."""
        if v <= 0:
            raise ValueError("MAX_LOG_FILE_SIZE must be positive")
        return v
    
    @validator("LOG_RETENTION_DAYS")
    def validate_log_retention_days(cls, v):
        """Validate log retention days is positive."""
        if v <= 0:
            raise ValueError("LOG_RETENTION_DAYS must be positive")
        return v
    
    @validator("PORT")
    def validate_port(cls, v):
        """Validate port is in valid range."""
        if not (1 <= v <= 65535):
            raise ValueError("PORT must be between 1 and 65535")
        return v
    
    def validate_paths(self) -> None:
        """
        Validate that required paths exist and are accessible.
        
        Creates directories if they don't exist and validates permissions.
        
        Raises:
            PermissionError: If paths are not writable
            OSError: If paths cannot be created
        """
        # Ensure base directories exist
        paths_to_create = [
            Path(self.LOGS_BASE_PATH),
            Path(self.RESULTS_BASE_PATH),
            Path(self.RUNS_DATA_PATH).parent,
        ]
        
        for path in paths_to_create:
            try:
                path.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                raise OSError(f"Cannot create directory {path}: {e}")
        
        # Validate write permissions
        paths_to_check = [
            Path(self.LOGS_BASE_PATH),
            Path(self.RESULTS_BASE_PATH),
            Path(self.RUNS_DATA_PATH).parent,
        ]
        
        for path in paths_to_check:
            if not os.access(path, os.W_OK):
                raise PermissionError(f"No write permission for {path}")
    
    def get_run_logs_path(self, run_id: str) -> Path:
        """
        Get the logs directory path for a specific run.
        
        Args:
            run_id: Unique identifier for the training run
            
        Returns:
            Path: Path to the run's log directory
        """
        return Path(self.LOGS_BASE_PATH) / "runs" / run_id
    
    def get_run_results_path(self, run_id: str) -> Path:
        """
        Get the results directory path for a specific run.
        
        Args:
            run_id: Unique identifier for the training run
            
        Returns:
            Path: Path to the run's results directory
        """
        return Path(self.RESULTS_BASE_PATH) / run_id
    
    def ensure_run_directories(self, run_id: str) -> None:
        """
        Ensure that directories for a specific run exist.
        
        Args:
            run_id: Unique identifier for the training run
            
        Raises:
            OSError: If directories cannot be created
        """
        logs_path = self.get_run_logs_path(run_id)
        results_path = self.get_run_results_path(run_id)
        
        try:
            logs_path.mkdir(parents=True, exist_ok=True)
            results_path.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise OSError(f"Cannot create run directories for {run_id}: {e}")
    
    def get_current_timestamp(self) -> str:
        """
        Get the current timestamp in ISO format.
        
        Returns:
            str: Current timestamp in ISO 8601 format
        """
        return datetime.utcnow().isoformat() + "Z"


# Global settings instance
settings = Settings()