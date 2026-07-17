"""
Custom exceptions for the Federated Learning Training API.

This module defines custom exception classes for better error handling
and more specific error reporting throughout the application.
"""

from typing import Optional, Dict, Any


class TrainingServiceError(Exception):
    """Base exception for training service errors."""
    
    def __init__(self, message: str, error_code: str = "TRAINING_ERROR", details: Optional[Dict[str, Any]] = None):
        """
        Initialize training service error.
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class RunNotFoundError(TrainingServiceError):
    """Exception raised when a requested run is not found."""
    
    def __init__(self, run_id: str):
        """
        Initialize run not found error.
        
        Args:
            run_id: The run ID that was not found
        """
        super().__init__(
            message=f"Training run '{run_id}' not found",
            error_code="RUN_NOT_FOUND",
            details={"run_id": run_id}
        )
        self.run_id = run_id


class ActiveRunExistsError(TrainingServiceError):
    """Exception raised when trying to start a run while another is active."""
    
    def __init__(self, active_run_id: str):
        """
        Initialize active run exists error.
        
        Args:
            active_run_id: The ID of the currently active run
        """
        super().__init__(
            message=f"Cannot start new run: run '{active_run_id}' is already active",
            error_code="ACTIVE_RUN_EXISTS",
            details={"active_run_id": active_run_id}
        )
        self.active_run_id = active_run_id


class NoActiveRunError(TrainingServiceError):
    """Exception raised when trying to stop a run but no run is active."""
    
    def __init__(self):
        """Initialize no active run error."""
        super().__init__(
            message="No training run is currently active",
            error_code="NO_ACTIVE_RUN",
            details={}
        )


class StorageError(TrainingServiceError):
    """Exception raised for storage-related errors."""
    
    def __init__(self, message: str, operation: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize storage error.
        
        Args:
            message: Human-readable error message
            operation: The storage operation that failed
            details: Additional error details
        """
        super().__init__(
            message=f"Storage operation '{operation}' failed: {message}",
            error_code="STORAGE_ERROR",
            details={"operation": operation, **(details or {})}
        )
        self.operation = operation


class ConfigurationError(TrainingServiceError):
    """Exception raised for configuration-related errors."""
    
    def __init__(self, message: str, config_key: Optional[str] = None):
        """
        Initialize configuration error.
        
        Args:
            message: Human-readable error message
            config_key: The configuration key that caused the error
        """
        details = {"config_key": config_key} if config_key else {}
        super().__init__(
            message=f"Configuration error: {message}",
            error_code="CONFIGURATION_ERROR",
            details=details
        )
        self.config_key = config_key


class FLServerError(TrainingServiceError):
    """Exception raised for FL server execution errors."""
    
    def __init__(self, message: str, run_id: str, error_type: str = "EXECUTION_ERROR"):
        """
        Initialize FL server error.
        
        Args:
            message: Human-readable error message
            run_id: The run ID where the error occurred
            error_type: Type of FL server error
        """
        super().__init__(
            message=f"FL server error for run '{run_id}': {message}",
            error_code=f"FL_SERVER_{error_type}",
            details={"run_id": run_id, "error_type": error_type}
        )
        self.run_id = run_id
        self.error_type = error_type


class ValidationError(TrainingServiceError):
    """Exception raised for validation errors."""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None):
        """
        Initialize validation error.
        
        Args:
            message: Human-readable error message
            field: The field that failed validation
            value: The invalid value
        """
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)
            
        super().__init__(
            message=f"Validation error: {message}",
            error_code="VALIDATION_ERROR",
            details=details
        )
        self.field = field
        self.value = value


class ResourceError(TrainingServiceError):
    """Exception raised for resource-related errors (files, directories, permissions)."""
    
    def __init__(self, message: str, resource_type: str, resource_path: Optional[str] = None):
        """
        Initialize resource error.
        
        Args:
            message: Human-readable error message
            resource_type: Type of resource (file, directory, etc.)
            resource_path: Path to the resource that caused the error
        """
        details = {"resource_type": resource_type}
        if resource_path:
            details["resource_path"] = resource_path
            
        super().__init__(
            message=f"Resource error ({resource_type}): {message}",
            error_code="RESOURCE_ERROR",
            details=details
        )
        self.resource_type = resource_type
        self.resource_path = resource_path