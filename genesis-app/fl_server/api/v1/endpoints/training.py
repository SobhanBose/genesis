"""
Training endpoints for the federated learning API.
Defines all training-related API endpoints using FastAPI's APIRouter.
"""

import logging
from datetime import datetime
from typing import Dict, Optional, Any, List

from fastapi import APIRouter, HTTPException, Depends, status, Query
from pydantic import ValidationError

from core.config import settings
from core.exceptions import (
    TrainingServiceError, RunNotFoundError, ActiveRunExistsError,
    StorageError, ResourceError, FLServerError, NoActiveRunError
)
from schemas.training import (
    RunCreateResponse, RunStopResponse, RunStatus, TrainingStartRequest, 
    RunStatusEnum, HealthStatus, HealthStatusEnum,
    PaginatedRunList, RunSummary, RunMetadata, RunsQueryParams, RunMetrics,
    LogEntry, ErrorEntry, LogsQueryParams, LogLevelEnum
)
from services.training import TrainingService
from storage.run_store import RunStore

logger = logging.getLogger(__name__)

# Create the training router
router = APIRouter()

# Global instances - these will be initialized when the app starts
_run_store: Optional[RunStore] = None
_training_service: Optional[TrainingService] = None

def get_run_store() -> RunStore:
    """Dependency to get the RunStore instance."""
    global _run_store
    if _run_store is None:
        _run_store = RunStore(settings.RUNS_DATA_PATH)
    return _run_store

def get_training_service() -> TrainingService:
    """Dependency to get the TrainingService instance."""
    global _training_service
    if _training_service is None:
        run_store = get_run_store()
        _training_service = TrainingService(run_store)
    return _training_service

@router.post(
    "/start",
    response_model=RunCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new training run",
    description="Start a new federated learning training run with optional configuration overrides"
)
async def start_training_run(
    request: TrainingStartRequest = TrainingStartRequest(),
    training_service: TrainingService = Depends(get_training_service)
) -> RunCreateResponse:
    """
    Start a new federated learning training run.
    
    Creates a new training run with a unique ID, sets up directories,
    and starts the FL server in a background thread.
    
    Args:
        request: Training configuration request
        training_service: Injected training service
        
    Returns:
        RunCreateResponse with run details
        
    Raises:
        HTTPException: 409 if a run is already active, 500 for other errors
    """
    try:
        logger.info("Received request to start new training run")
        
        # Start the training run
        run_metadata = training_service.start_training_run(request.config)
        
        logger.info(f"Successfully started training run: {run_metadata.run_id}")
        
        return RunCreateResponse(
            run_id=run_metadata.run_id,
            status=run_metadata.status,
            start_time=run_metadata.start_time,
            message=f"Training run {run_metadata.run_id} started successfully",
            fl_server_port=run_metadata.fl_server_port
        )
        
    except (ValueError, ActiveRunExistsError) as e:
        # This handles the case where a run is already active
        logger.warning(f"Cannot start training run: {e}")
        if isinstance(e, ActiveRunExistsError):
            # Custom exception with detailed information
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "Training run already active",
                    "message": e.message,
                    "error_code": e.error_code,
                    "details": e.details
                }
            )
        else:
            # Legacy ValueError handling
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "Training run already active",
                    "message": str(e),
                    "error_code": "ACTIVE_RUN_EXISTS"
                }
            )
    except (OSError, ResourceError) as e:
        # This handles directory creation failures and resource errors
        logger.error(f"Failed to create run directories: {e}")
        if isinstance(e, ResourceError):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "Resource Error",
                    "message": e.message,
                    "error_code": e.error_code,
                    "details": e.details
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "Failed to initialize training run",
                    "message": "Could not create required directories",
                    "error_code": "DIRECTORY_CREATION_FAILED"
                }
            )
    except Exception as e:
        # Handle any other unexpected errors
        logger.error(f"Unexpected error starting training run: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "message": "An unexpected error occurred while starting the training run",
                "error_code": "INTERNAL_ERROR"
            }
        )

@router.post(
    "/stop",
    response_model=RunStopResponse,
    status_code=status.HTTP_200_OK,
    summary="Stop the active training run",
    description="Stop the currently active federated learning training run"
)
async def stop_training_run(
    training_service: TrainingService = Depends(get_training_service)
) -> RunStopResponse:
    """
    Stop the currently active training run.
    
    Terminates the background FL server process, updates run status to ERROR
    with termination reason, and performs cleanup operations.
    
    Args:
        training_service: Injected training service
        
    Returns:
        RunStopResponse with stop operation details
        
    Raises:
        HTTPException: 404 if no active run exists, 500 for other errors
    """
    try:
        logger.info("Received request to stop active training run")
        
        # Stop the active training run
        stopped_run = training_service.stop_active_training_run()
        
        logger.info(f"Successfully stopped training run: {stopped_run.run_id}")
        
        # Handle end_time conversion properly
        if stopped_run.end_time:
            if isinstance(stopped_run.end_time, datetime):
                end_time = stopped_run.end_time
            else:
                end_time = datetime.fromisoformat(stopped_run.end_time)
        else:
            end_time = datetime.utcnow()
        
        return RunStopResponse(
            run_id=stopped_run.run_id,
            status=stopped_run.status,
            end_time=end_time,
            message=f"Training run {stopped_run.run_id} stopped successfully",
            fl_server_port=stopped_run.fl_server_port
        )
        
    except NoActiveRunError as e:
        logger.warning("No active run to stop")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "No active run",
                "message": e.message,
                "error_code": e.error_code,
                "details": e.details
            }
        )
    except (ValueError, RunNotFoundError) as e:
        # Handle cases where run exists but isn't active
        logger.warning(f"Cannot stop training run: {e}")
        if isinstance(e, RunNotFoundError):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Run not found",
                    "message": e.message,
                    "error_code": e.error_code,
                    "details": e.details
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "Cannot stop run",
                    "message": str(e),
                    "error_code": "RUN_NOT_STOPPABLE"
                }
            )
    except (StorageError, ResourceError) as e:
        # Handle storage and resource errors
        logger.error(f"Failed to stop training run: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Stop operation failed",
                "message": e.message,
                "error_code": e.error_code,
                "details": e.details
            }
        )
    except Exception as e:
        # Handle any other unexpected errors
        logger.error(f"Unexpected error stopping training run: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "message": "An unexpected error occurred while stopping the training run",
                "error_code": "INTERNAL_ERROR"
            }
        )

@router.get(
    "/status",
    response_model=RunStatus,
    summary="Get current training status",
    description="Get the status of the current or most recent training run"
)
async def get_training_status(
    training_service: TrainingService = Depends(get_training_service)
) -> RunStatus:
    """
    Get the status of the current or most recent training run.
    
    Returns information about the currently active run, or if no run
    is active, returns information about the most recent completed run.
    
    Args:
        training_service: Injected training service
        
    Returns:
        RunStatus with current system status
    """
    try:
        logger.debug("Retrieving current training status")
        
        # Get current status from training service
        status_data = training_service.get_current_status()
        
        return RunStatus(**status_data)
        
    except Exception as e:
        logger.error(f"Error retrieving training status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to retrieve status",
                "message": "An error occurred while retrieving the training status",
                "error_code": "STATUS_RETRIEVAL_ERROR"
            }
        )

@router.get(
    "/runs",
    response_model=PaginatedRunList,
    summary="List all training runs",
    description="Get a paginated list of all training runs with optional filtering and sorting"
)
async def get_training_runs(
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of runs to return"),
    offset: int = Query(0, ge=0, description="Number of runs to skip"),
    status: Optional[RunStatusEnum] = Query(None, description="Filter runs by status"),
    sort: str = Query("desc", pattern="^(asc|desc)$", description="Sort order by start_time"),
    training_service: TrainingService = Depends(get_training_service)
) -> PaginatedRunList:
    """
    Get a paginated list of all training runs.
    
    Supports filtering by status and sorting by start_time in ascending
    or descending order. Returns abbreviated run information suitable
    for list views.
    
    Args:
        limit: Maximum number of runs to return (1-1000)
        offset: Number of runs to skip for pagination
        status: Optional status filter (IDLE, TRAINING, COMPLETED, ERROR)
        sort: Sort order by start_time ("asc" or "desc")
        training_service: Injected training service
        
    Returns:
        PaginatedRunList with run summaries and pagination metadata
    """
    try:
        logger.debug(f"Retrieving runs: limit={limit}, offset={offset}, status={status}, sort={sort}")
        
        # Convert status enum to string for service layer
        status_str = status.value if status else None
        
        # Get filtered runs
        runs = training_service.get_all_runs(
            limit=limit,
            offset=offset,
            status=status_str,
            sort=sort
        )
        
        # Get total count for pagination
        total_count = training_service.run_store.get_run_count(status=status_str)
        
        # Convert RunMetadata to RunSummary for the response
        run_summaries = []
        for run in runs:
            run_summary = RunSummary(
                run_id=run.run_id,
                status=run.status,
                start_time=run.start_time,
                end_time=run.end_time,
                duration=run.duration,
                rounds_completed=run.rounds_completed,
                total_rounds=run.total_rounds
            )
            run_summaries.append(run_summary)
        
        # Calculate pagination metadata
        has_more = offset + limit < total_count
        
        return PaginatedRunList(
            runs=run_summaries,
            total=total_count,
            limit=limit,
            offset=offset,
            has_more=has_more
        )
        
    except Exception as e:
        logger.error(f"Error retrieving training runs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to retrieve runs",
                "message": "An error occurred while retrieving the training runs",
                "error_code": "RUNS_RETRIEVAL_ERROR"
            }
        )

@router.get(
    "/runs/{run_id}",
    response_model=RunMetadata,
    summary="Get detailed run metadata",
    description="Get detailed metadata for a specific training run by ID"
)
async def get_training_run_by_id(
    run_id: str,
    training_service: TrainingService = Depends(get_training_service)
) -> RunMetadata:
    """
    Get detailed metadata for a specific training run.
    
    Returns complete run information including configuration,
    progress, metrics, and file paths.
    
    Args:
        run_id: Unique identifier for the training run
        training_service: Injected training service
        
    Returns:
        RunMetadata with complete run information
        
    Raises:
        HTTPException: 404 if run not found, 500 for other errors
    """
    try:
        logger.debug(f"Retrieving run metadata for: {run_id}")
        
        # Get run by ID
        run_metadata = training_service.get_run_by_id(run_id)
        
        if run_metadata is None:
            logger.warning(f"Run not found: {run_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Run not found",
                    "message": f"Training run '{run_id}' does not exist",
                    "error_code": "RUN_NOT_FOUND"
                }
            )
        
        logger.debug(f"Successfully retrieved run metadata for: {run_id}")
        return run_metadata
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except RunNotFoundError:
        logger.warning(f"Run not found: {run_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Run not found",
                "message": f"Training run '{run_id}' does not exist",
                "error_code": "RUN_NOT_FOUND"
            }
        )
    except Exception as e:
        logger.error(f"Error retrieving run {run_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to retrieve run",
                "message": f"An error occurred while retrieving run '{run_id}'",
                "error_code": "RUN_RETRIEVAL_ERROR"
            }
        )

@router.get(
    "/metrics",
    response_model=RunMetrics,
    summary="Get metrics for active run",
    description="Get training metrics for the currently active run"
)
async def get_active_run_metrics(
    training_service: TrainingService = Depends(get_training_service)
) -> RunMetrics:
    """
    Get training metrics for the currently active run.
    
    Returns real-time metrics including current round, progress percentage,
    client connections, and per-round training data.
    
    Args:
        training_service: Injected training service
        
    Returns:
        RunMetrics with active run metrics data
        
    Raises:
        HTTPException: 404 if no active run exists, 500 for other errors
    """
    try:
        logger.debug("Retrieving metrics for active run")
        
        # Get metrics for active run
        metrics = training_service.get_active_run_metrics()
        
        if metrics is None:
            logger.warning("No active run found for metrics request")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "No active run",
                    "message": "No training run is currently active",
                    "error_code": "NO_ACTIVE_RUN"
                }
            )
        
        logger.debug(f"Successfully retrieved metrics for active run: {metrics.run_id}")
        return metrics
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except Exception as e:
        logger.error(f"Error retrieving active run metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to retrieve metrics",
                "message": "An error occurred while retrieving active run metrics",
                "error_code": "METRICS_RETRIEVAL_ERROR"
            }
        )

@router.get(
    "/runs/{run_id}/metrics",
    response_model=RunMetrics,
    summary="Get metrics for specific run",
    description="Get training metrics for a specific run by ID"
)
async def get_run_metrics_by_id(
    run_id: str,
    training_service: TrainingService = Depends(get_training_service)
) -> RunMetrics:
    """
    Get training metrics for a specific run.
    
    Returns metrics data including progress, per-round metrics, and
    client participation. For active runs, includes real-time data.
    For completed runs, includes final results.
    
    Args:
        run_id: Unique identifier for the training run
        training_service: Injected training service
        
    Returns:
        RunMetrics with run metrics data
        
    Raises:
        HTTPException: 404 if run not found, 500 for other errors
    """
    try:
        logger.debug(f"Retrieving metrics for run: {run_id}")
        
        # Get metrics for specific run
        metrics = training_service.get_run_metrics(run_id)
        
        if metrics is None:
            logger.warning(f"Run not found for metrics request: {run_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Run not found",
                    "message": f"Training run '{run_id}' does not exist",
                    "error_code": "RUN_NOT_FOUND"
                }
            )
        
        logger.debug(f"Successfully retrieved metrics for run: {run_id}")
        return metrics
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except RunNotFoundError:
        logger.warning(f"Run not found for metrics request: {run_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Run not found",
                "message": f"Training run '{run_id}' does not exist",
                "error_code": "RUN_NOT_FOUND"
            }
        )
    except Exception as e:
        logger.error(f"Error retrieving metrics for run {run_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to retrieve metrics",
                "message": f"An error occurred while retrieving metrics for run '{run_id}'",
                "error_code": "METRICS_RETRIEVAL_ERROR"
            }
        )

@router.get(
    "/logs",
    response_model=List[LogEntry],
    summary="Get logs for active/recent run",
    description="Get logs for the currently active run or most recent run"
)
async def get_active_run_logs(
    lines: int = Query(100, ge=1, le=10000, description="Maximum number of log lines to return"),
    offset: int = Query(0, ge=0, description="Number of lines to skip from the beginning"),
    level: Optional[LogLevelEnum] = Query(None, description="Filter logs by minimum level"),
    tail: bool = Query(False, description="Return lines from the end of the log"),
    training_service: TrainingService = Depends(get_training_service)
) -> List[LogEntry]:
    """
    Get logs for the currently active run or most recent run.
    
    This is a convenience endpoint that automatically selects the active run
    or falls back to the most recent run if no run is currently active.
    
    Args:
        lines: Maximum number of log lines to return (1-10000)
        offset: Number of lines to skip from the beginning
        level: Optional minimum log level filter
        tail: Return lines from the end of the log instead of beginning
        training_service: Injected training service
        
    Returns:
        List of LogEntry objects matching the criteria
        
    Raises:
        HTTPException: 404 if no runs exist, 500 for other errors
    """
    try:
        logger.debug(f"Retrieving active/recent run logs: lines={lines}, offset={offset}, level={level}, tail={tail}")
        
        # Convert level enum to string for service layer
        level_str = level.value if level else None
        
        # Get logs for active/recent run
        logs = training_service.get_active_run_logs(
            lines=lines,
            offset=offset,
            level=level_str,
            tail=tail
        )
        
        if not logs and lines > 0:
            # Check if any runs exist at all
            all_runs = training_service.get_all_runs(limit=1, offset=0)
            if not all_runs:
                logger.warning("No runs found for active/recent logs request")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "error": "No runs found",
                        "message": "No training runs exist in the system",
                        "error_code": "NO_RUNS_EXIST"
                    }
                )
        
        logger.debug(f"Successfully retrieved {len(logs)} log entries for active/recent run")
        return logs
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except Exception as e:
        logger.error(f"Error retrieving active/recent run logs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to retrieve logs",
                "message": "An error occurred while retrieving logs for the active/recent run",
                "error_code": "LOGS_RETRIEVAL_ERROR"
            }
        )

@router.get(
    "/runs/{run_id}/logs",
    response_model=List[LogEntry],
    summary="Get logs for specific run",
    description="Get logs for a specific training run with filtering and pagination"
)
async def get_run_logs_by_id(
    run_id: str,
    lines: int = Query(100, ge=1, le=10000, description="Maximum number of log lines to return"),
    offset: int = Query(0, ge=0, description="Number of lines to skip from the beginning"),
    level: Optional[LogLevelEnum] = Query(None, description="Filter logs by minimum level"),
    tail: bool = Query(False, description="Return lines from the end of the log"),
    training_service: TrainingService = Depends(get_training_service)
) -> List[LogEntry]:
    """
    Get logs for a specific training run.
    
    Supports filtering by log level and pagination. For active runs,
    includes both disk logs and buffered logs. For completed runs,
    returns only disk logs.
    
    Args:
        run_id: Unique identifier for the training run
        lines: Maximum number of log lines to return (1-10000)
        offset: Number of lines to skip from the beginning
        level: Optional minimum log level filter
        tail: Return lines from the end of the log instead of beginning
        training_service: Injected training service
        
    Returns:
        List of LogEntry objects matching the criteria
        
    Raises:
        HTTPException: 404 if run not found, 500 for other errors
    """
    try:
        logger.debug(f"Retrieving logs for run {run_id}: lines={lines}, offset={offset}, level={level}, tail={tail}")
        
        # Check if run exists
        run_metadata = training_service.get_run_by_id(run_id)
        if run_metadata is None:
            logger.warning(f"Run not found for logs request: {run_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Run not found",
                    "message": f"Training run '{run_id}' does not exist",
                    "error_code": "RUN_NOT_FOUND"
                }
            )
        
        # Convert level enum to string for service layer
        level_str = level.value if level else None
        
        # Get logs for the specific run
        logs = training_service.get_run_logs(
            run_id=run_id,
            lines=lines,
            offset=offset,
            level=level_str,
            tail=tail
        )
        
        logger.debug(f"Successfully retrieved {len(logs)} log entries for run {run_id}")
        return logs
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except RunNotFoundError:
        logger.warning(f"Run not found for logs request: {run_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Run not found",
                "message": f"Training run '{run_id}' does not exist",
                "error_code": "RUN_NOT_FOUND"
            }
        )
    except Exception as e:
        logger.error(f"Error retrieving logs for run {run_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to retrieve logs",
                "message": f"An error occurred while retrieving logs for run '{run_id}'",
                "error_code": "LOGS_RETRIEVAL_ERROR"
            }
        )

@router.get(
    "/runs/{run_id}/errors",
    response_model=List[ErrorEntry],
    summary="Get errors for specific run",
    description="Get error-level log entries for a specific training run"
)
async def get_run_errors_by_id(
    run_id: str,
    training_service: TrainingService = Depends(get_training_service)
) -> List[ErrorEntry]:
    """
    Get error-level log entries for a specific training run.
    
    Extracts and returns only ERROR and CRITICAL level log entries,
    formatted as ErrorEntry objects with additional error context.
    
    Args:
        run_id: Unique identifier for the training run
        training_service: Injected training service
        
    Returns:
        List of ErrorEntry objects for the run
        
    Raises:
        HTTPException: 404 if run not found, 500 for other errors
    """
    try:
        logger.debug(f"Retrieving errors for run: {run_id}")
        
        # Check if run exists
        run_metadata = training_service.get_run_by_id(run_id)
        if run_metadata is None:
            logger.warning(f"Run not found for errors request: {run_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Run not found",
                    "message": f"Training run '{run_id}' does not exist",
                    "error_code": "RUN_NOT_FOUND"
                }
            )
        
        # Get error entries for the specific run
        errors = training_service.get_run_errors(run_id)
        
        logger.debug(f"Successfully retrieved {len(errors)} error entries for run {run_id}")
        return errors
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except RunNotFoundError:
        logger.warning(f"Run not found for errors request: {run_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Run not found",
                "message": f"Training run '{run_id}' does not exist",
                "error_code": "RUN_NOT_FOUND"
            }
        )
    except Exception as e:
        logger.error(f"Error retrieving errors for run {run_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to retrieve errors",
                "message": f"An error occurred while retrieving errors for run '{run_id}'",
                "error_code": "ERRORS_RETRIEVAL_ERROR"
            }
        )

@router.get(
    "/health",
    response_model=HealthStatus,
    summary="Service health check",
    description="Check the health status of the federated learning training service"
)
async def health_check(
    training_service: TrainingService = Depends(get_training_service)
) -> HealthStatus:
    """
    Service health check endpoint with comprehensive error handling.
    
    Provides information about the service health, uptime, and any active runs.
    Returns appropriate HTTP status codes: 200 for healthy, 503 for degraded/unhealthy.
    Uses graceful degradation to ensure API remains responsive.
    
    Args:
        training_service: Injected training service
        
    Returns:
        HealthStatus with service health information
        
    Raises:
        HTTPException: 503 for degraded or unhealthy status
    """
    try:
        # Get comprehensive health information with graceful degradation
        health_info = training_service.get_service_health()
        
        # Map service health status to API health status
        status_mapping = {
            "healthy": HealthStatusEnum.HEALTHY,
            "degraded": HealthStatusEnum.DEGRADED,
            "unhealthy": HealthStatusEnum.UNHEALTHY
        }
        
        health_status = status_mapping.get(health_info["status"], HealthStatusEnum.UNHEALTHY)
        
        # Create health response with comprehensive information
        message = f"Service is {health_info['status']}"
        if health_info.get("degraded_services"):
            message += f". Degraded services: {', '.join(health_info['degraded_services'])}"
        
        health_response = HealthStatus(
            status=health_status,
            timestamp=datetime.utcnow(),
            uptime=health_info.get("uptime_seconds", 0.0),
            active_run=training_service.get_active_run_id(),
            message=message
        )
        
        # Return appropriate HTTP status code based on health
        if health_status == HealthStatusEnum.HEALTHY:
            return health_response
        else:
            # Return 503 Service Unavailable for degraded or unhealthy status
            # But still return the health information for diagnostics
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=health_response.dict()
            )
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 503) to preserve status codes
        raise
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        
        # Even if health check fails, try to provide basic information
        try:
            uptime = training_service.get_service_uptime()
        except Exception:
            uptime = 0.0
        
        # Return 503 for critical health check failures
        unhealthy_response = HealthStatus(
            status=HealthStatusEnum.UNHEALTHY,
            timestamp=datetime.utcnow(),
            uptime=uptime,
            active_run=None,
            message=f"Service health check failed: {str(e)}"
        )
        
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=unhealthy_response.dict()
        )


def _determine_health_status(training_service: TrainingService, active_run_id: Optional[str]) -> tuple[HealthStatusEnum, str]:
    """
    Determine the health status by checking various system components.
    
    Args:
        training_service: Training service instance
        active_run_id: ID of currently active run (if any)
        
    Returns:
        Tuple of (health_status, message)
    """
    issues = []
    
    try:
        # Check if we can access the run store
        training_service.get_current_status()
    except Exception as e:
        logger.warning(f"Run store access issue: {e}")
        issues.append("Run store access degraded")
    
    try:
        # Check if we can read from storage
        training_service.get_all_runs(limit=1)
    except Exception as e:
        logger.warning(f"Storage read issue: {e}")
        issues.append("Storage read operations degraded")
    
    # Check for active run with error status
    if active_run_id:
        try:
            active_run = training_service.get_run_by_id(active_run_id)
            if active_run and active_run.status == RunStatusEnum.ERROR:
                issues.append(f"Active run {active_run_id} is in error state")
        except Exception as e:
            logger.warning(f"Failed to check active run status: {e}")
            issues.append("Cannot verify active run status")
    
    # Check background thread health
    try:
        thread_status = training_service.get_thread_status()
        dead_threads = [run_id for run_id, is_alive in thread_status.items() if not is_alive]
        if dead_threads:
            issues.append(f"Background threads not running for runs: {', '.join(dead_threads)}")
    except Exception as e:
        logger.warning(f"Thread status check failed: {e}")
        issues.append("Cannot verify background thread status")
    
    # Check file system access
    try:
        settings.validate_paths()
    except Exception as e:
        logger.warning(f"File system access issue: {e}")
        issues.append("File system access issues detected")
    
    # Determine overall health status
    if not issues:
        return HealthStatusEnum.HEALTHY, "Service is running normally"
    elif len(issues) <= 2:
        return HealthStatusEnum.DEGRADED, f"Service is running but degraded: {'; '.join(issues)}"
    else:
        return HealthStatusEnum.UNHEALTHY, f"Service has multiple issues: {'; '.join(issues)}"