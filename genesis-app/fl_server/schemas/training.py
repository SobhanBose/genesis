"""
Pydantic schemas for training-related API models.

This module defines all data models used for API request/response validation
and serialization in the federated learning training system.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

from pydantic import BaseModel, Field, validator


class RunStatusEnum(str, Enum):
    """Enumeration of possible training run statuses."""
    IDLE = "IDLE"
    TRAINING = "TRAINING"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"


class LogLevelEnum(str, Enum):
    """Enumeration of log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class HealthStatusEnum(str, Enum):
    """Enumeration of health check statuses."""
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"


class RoundMetrics(BaseModel):
    """Per-round training metrics."""
    round_number: int = Field(..., description="Round number (1-based)")
    timestamp: datetime = Field(..., description="When this round completed")
    loss: Optional[float] = Field(None, description="Training loss for this round")
    accuracy: Optional[float] = Field(None, description="Training accuracy for this round")
    clients_participated: int = Field(..., description="Number of clients that participated")
    duration: Optional[float] = Field(None, description="Round duration in seconds")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RunMetrics(BaseModel):
    """Training metrics for a run."""
    run_id: str = Field(..., description="Unique run identifier")
    status: RunStatusEnum = Field(..., description="Current run status")
    current_round: Optional[int] = Field(None, description="Current round number (1-based)")
    total_rounds: Optional[int] = Field(None, description="Total number of rounds planned")
    progress_percentage: Optional[float] = Field(None, description="Training progress as percentage")
    clients_connected: Optional[int] = Field(None, description="Number of clients currently connected")
    clients_expected: Optional[int] = Field(None, description="Expected number of clients")
    round_metrics: List[RoundMetrics] = Field(default_factory=list, description="Per-round metrics data")
    last_update_time: Optional[datetime] = Field(None, description="When metrics were last updated")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class LogEntry(BaseModel):
    """Single log entry."""
    timestamp: datetime = Field(..., description="When the log entry was created")
    level: LogLevelEnum = Field(..., description="Log level")
    source: str = Field(..., description="Source component that generated the log")
    run_id: Optional[str] = Field(None, description="Associated run ID")
    message: str = Field(..., description="Log message")
    extra: Optional[Dict[str, Any]] = Field(None, description="Additional context data")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ErrorEntry(BaseModel):
    """Error log entry with additional error details."""
    timestamp: datetime = Field(..., description="When the error occurred")
    error_type: str = Field(..., description="Type of error")
    message: str = Field(..., description="Error message")
    traceback: Optional[str] = Field(None, description="Full error traceback")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional error context")
    run_id: Optional[str] = Field(None, description="Associated run ID")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RunMetadata(BaseModel):
    """Complete metadata for a training run."""
    run_id: str = Field(..., description="Unique run identifier")
    status: RunStatusEnum = Field(..., description="Current run status")
    start_time: datetime = Field(..., description="When the run started")
    end_time: Optional[datetime] = Field(None, description="When the run completed")
    duration: Optional[int] = Field(None, description="Run duration in seconds")
    config: Optional[Dict[str, Any]] = Field(None, description="Training configuration used")
    rounds_completed: Optional[int] = Field(None, description="Number of rounds completed")
    total_rounds: Optional[int] = Field(None, description="Total number of rounds planned")
    clients_expected: Optional[int] = Field(None, description="Expected number of clients")
    clients_participated: Optional[int] = Field(None, description="Number of clients that participated")
    final_metrics: Optional[Dict[str, float]] = Field(None, description="Final training metrics")
    round_metrics: Optional[List[Dict[str, Any]]] = Field(None, description="Per-round metrics data")
    error_message: Optional[str] = Field(None, description="Error message if run failed")
    results_path: Optional[str] = Field(None, description="Path to results directory")
    logs_path: Optional[str] = Field(None, description="Path to logs directory")
    fl_server_port: Optional[int] = Field(None, description="Port number used by the FL server")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RunSummary(BaseModel):
    """Abbreviated run information for list endpoints."""
    run_id: str = Field(..., description="Unique run identifier")
    status: RunStatusEnum = Field(..., description="Current run status")
    start_time: datetime = Field(..., description="When the run started")
    end_time: Optional[datetime] = Field(None, description="When the run completed")
    duration: Optional[int] = Field(None, description="Run duration in seconds")
    rounds_completed: Optional[int] = Field(None, description="Number of rounds completed")
    total_rounds: Optional[int] = Field(None, description="Total number of rounds planned")
    fl_server_port: Optional[int] = Field(None, description="Port number used by the FL server")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RunCreateResponse(BaseModel):
    """Response for starting a new training run."""
    run_id: str = Field(..., description="Unique identifier for the new run")
    status: RunStatusEnum = Field(..., description="Initial run status")
    start_time: datetime = Field(..., description="When the run was started")
    message: str = Field(..., description="Success message")
    fl_server_port: Optional[int] = Field(None, description="Port number allocated for the FL server")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RunStopResponse(BaseModel):
    """Response for stopping a training run."""
    run_id: str = Field(..., description="Unique identifier for the stopped run")
    status: RunStatusEnum = Field(..., description="Final run status after stopping")
    end_time: datetime = Field(..., description="When the run was stopped")
    message: str = Field(..., description="Stop operation message")
    fl_server_port: Optional[int] = Field(None, description="Port number that was used by the FL server")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RunStatus(BaseModel):
    """Current run status response."""
    status: RunStatusEnum = Field(..., description="Current system status")
    run_id: Optional[str] = Field(None, description="ID of current/most recent run")
    start_time: Optional[datetime] = Field(None, description="When the current/recent run started")
    end_time: Optional[datetime] = Field(None, description="When the run completed (if finished)")
    rounds_completed: Optional[int] = Field(None, description="Number of rounds completed")
    total_rounds: Optional[int] = Field(None, description="Total number of rounds planned")
    fl_server_port: Optional[int] = Field(None, description="Port number used by the FL server")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class HealthStatus(BaseModel):
    """Health check response."""
    status: HealthStatusEnum = Field(..., description="Overall system health status")
    timestamp: datetime = Field(..., description="When the health check was performed")
    uptime: float = Field(..., description="System uptime in seconds")
    active_run: Optional[str] = Field(None, description="ID of currently active run")
    message: Optional[str] = Field(None, description="Additional status information")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PaginatedRunList(BaseModel):
    """Paginated list of training runs."""
    runs: List[RunSummary] = Field(..., description="List of run summaries")
    total: int = Field(..., description="Total number of runs matching filters")
    limit: int = Field(..., description="Maximum number of items per page")
    offset: int = Field(..., description="Number of items skipped")
    has_more: bool = Field(..., description="Whether there are more items available")
    
    @validator('has_more', always=True)
    def calculate_has_more(cls, v, values):
        """Calculate if there are more items available."""
        if 'total' in values and 'limit' in values and 'offset' in values:
            return values['offset'] + values['limit'] < values['total']
        return v


# Request models for API endpoints

class TrainingStartRequest(BaseModel):
    """Request model for starting a training run."""
    config: Optional[Dict[str, Any]] = Field(None, description="Optional training configuration overrides")


class LogsQueryParams(BaseModel):
    """Query parameters for log retrieval endpoints."""
    lines: int = Field(100, ge=1, le=10000, description="Maximum number of log lines to return")
    offset: int = Field(0, ge=0, description="Number of lines to skip from the beginning")
    level: Optional[LogLevelEnum] = Field(None, description="Filter logs by minimum level")
    tail: bool = Field(False, description="Return lines from the end of the log")


class RunsQueryParams(BaseModel):
    """Query parameters for runs list endpoint."""
    limit: int = Field(50, ge=1, le=1000, description="Maximum number of runs to return")
    offset: int = Field(0, ge=0, description="Number of runs to skip")
    status: Optional[RunStatusEnum] = Field(None, description="Filter runs by status")
    sort: str = Field("desc", pattern="^(asc|desc)$", description="Sort order by start_time")


class HealthStatus(BaseModel):
    """Health status response model."""
    status: HealthStatusEnum = Field(..., description="Overall service health status")
    timestamp: datetime = Field(..., description="When the health check was performed")
    uptime: float = Field(..., description="Service uptime in seconds")
    active_run: Optional[str] = Field(None, description="ID of currently active run, if any")
    message: str = Field(..., description="Human-readable health status message")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }