"""
FastAPI application entry point.
Initializes the FastAPI application, sets up middleware, and includes the main API router.
"""

import logging
import traceback
from typing import Any, Dict

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
import uvicorn

from api.v1.routes import router as api_v1_router
from core.config import settings
from core.exceptions import (
    TrainingServiceError, RunNotFoundError, ActiveRunExistsError,
    StorageError, ConfigurationError, FLServerError, ValidationError, ResourceError
)

logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        FastAPI: Configured FastAPI application instance
    """
    # Validate configuration and ensure paths exist
    settings.validate_paths()
    
    app = FastAPI(
        title=settings.APP_NAME,
        description="API for controlling and monitoring federated learning training runs",
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add global exception handlers
    add_exception_handlers(app)
    
    # Include API routers
    app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)
    
    return app


def add_exception_handlers(app: FastAPI) -> None:
    """
    Add global exception handlers for consistent error responses.
    
    Args:
        app: FastAPI application instance
    """
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        """
        Handle HTTP exceptions with consistent error format.
        
        Args:
            request: The incoming request
            exc: The HTTP exception
            
        Returns:
            JSONResponse with standardized error format
        """
        logger.warning(f"HTTP exception on {request.method} {request.url}: {exc.detail}")
        
        # If detail is already a dict, use it as-is, otherwise wrap it
        if isinstance(exc.detail, dict):
            error_detail = exc.detail
        else:
            error_detail = {
                "error": "HTTP Error",
                "message": str(exc.detail),
                "error_code": f"HTTP_{exc.status_code}"
            }
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": error_detail,
                "timestamp": settings.get_current_timestamp(),
                "path": str(request.url.path)
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """
        Handle request validation errors with detailed field information.
        
        Args:
            request: The incoming request
            exc: The validation error
            
        Returns:
            JSONResponse with validation error details
        """
        logger.warning(f"Validation error on {request.method} {request.url}: {exc.errors()}")
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": {
                    "error": "Validation Error",
                    "message": "Request validation failed",
                    "error_code": "VALIDATION_ERROR",
                    "validation_errors": exc.errors()
                },
                "timestamp": settings.get_current_timestamp(),
                "path": str(request.url.path)
            }
        )
    
    @app.exception_handler(ValidationError)
    async def pydantic_validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
        """
        Handle Pydantic validation errors.
        
        Args:
            request: The incoming request
            exc: The Pydantic validation error
            
        Returns:
            JSONResponse with validation error details
        """
        logger.warning(f"Pydantic validation error on {request.method} {request.url}: {exc.errors()}")
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": {
                    "error": "Data Validation Error",
                    "message": "Data validation failed",
                    "error_code": "PYDANTIC_VALIDATION_ERROR",
                    "validation_errors": exc.errors()
                },
                "timestamp": settings.get_current_timestamp(),
                "path": str(request.url.path)
            }
        )
    
    @app.exception_handler(TrainingServiceError)
    async def training_service_error_handler(request: Request, exc: TrainingServiceError) -> JSONResponse:
        """
        Handle custom training service errors with detailed information.
        
        Args:
            request: The incoming request
            exc: The TrainingServiceError exception
            
        Returns:
            JSONResponse with detailed error information
        """
        logger.warning(f"Training service error on {request.method} {request.url}: {exc.message}")
        
        # Determine appropriate HTTP status code based on error type
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        if isinstance(exc, RunNotFoundError):
            status_code = status.HTTP_404_NOT_FOUND
        elif isinstance(exc, ActiveRunExistsError):
            status_code = status.HTTP_409_CONFLICT
        elif isinstance(exc, ValidationError):
            status_code = status.HTTP_400_BAD_REQUEST
        elif isinstance(exc, ConfigurationError):
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        elif isinstance(exc, ResourceError):
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        elif isinstance(exc, StorageError):
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        elif isinstance(exc, FLServerError):
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        
        return JSONResponse(
            status_code=status_code,
            content={
                "detail": {
                    "error": exc.__class__.__name__,
                    "message": exc.message,
                    "error_code": exc.error_code,
                    "details": exc.details
                },
                "timestamp": settings.get_current_timestamp(),
                "path": str(request.url.path)
            }
        )
    
    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        """
        Handle ValueError exceptions (e.g., invalid run states).
        
        Args:
            request: The incoming request
            exc: The ValueError exception
            
        Returns:
            JSONResponse with error details
        """
        logger.warning(f"Value error on {request.method} {request.url}: {exc}")
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "detail": {
                    "error": "Invalid Value",
                    "message": str(exc),
                    "error_code": "VALUE_ERROR"
                },
                "timestamp": settings.get_current_timestamp(),
                "path": str(request.url.path)
            }
        )
    
    @app.exception_handler(FileNotFoundError)
    async def file_not_found_handler(request: Request, exc: FileNotFoundError) -> JSONResponse:
        """
        Handle file not found errors.
        
        Args:
            request: The incoming request
            exc: The FileNotFoundError exception
            
        Returns:
            JSONResponse with error details
        """
        logger.error(f"File not found on {request.method} {request.url}: {exc}")
        
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "detail": {
                    "error": "Resource Not Found",
                    "message": "The requested resource could not be found",
                    "error_code": "FILE_NOT_FOUND"
                },
                "timestamp": settings.get_current_timestamp(),
                "path": str(request.url.path)
            }
        )
    
    @app.exception_handler(PermissionError)
    async def permission_error_handler(request: Request, exc: PermissionError) -> JSONResponse:
        """
        Handle permission errors.
        
        Args:
            request: The incoming request
            exc: The PermissionError exception
            
        Returns:
            JSONResponse with error details
        """
        logger.error(f"Permission error on {request.method} {request.url}: {exc}")
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": {
                    "error": "Permission Denied",
                    "message": "Insufficient permissions to access the requested resource",
                    "error_code": "PERMISSION_ERROR"
                },
                "timestamp": settings.get_current_timestamp(),
                "path": str(request.url.path)
            }
        )
    
    @app.exception_handler(OSError)
    async def os_error_handler(request: Request, exc: OSError) -> JSONResponse:
        """
        Handle OS-level errors (file system, network, etc.).
        
        Args:
            request: The incoming request
            exc: The OSError exception
            
        Returns:
            JSONResponse with error details
        """
        logger.error(f"OS error on {request.method} {request.url}: {exc}")
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": {
                    "error": "System Error",
                    "message": "A system-level error occurred",
                    "error_code": "OS_ERROR"
                },
                "timestamp": settings.get_current_timestamp(),
                "path": str(request.url.path)
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """
        Handle all other unhandled exceptions.
        
        Args:
            request: The incoming request
            exc: The unhandled exception
            
        Returns:
            JSONResponse with generic error message
        """
        # Log the full traceback for debugging
        logger.error(
            f"Unhandled exception on {request.method} {request.url}: {exc}",
            exc_info=True
        )
        
        # In production, don't expose internal error details
        error_message = "An internal server error occurred"
        if settings.DEBUG:
            error_message = f"Internal error: {str(exc)}"
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": {
                    "error": "Internal Server Error",
                    "message": error_message,
                    "error_code": "INTERNAL_SERVER_ERROR"
                },
                "timestamp": settings.get_current_timestamp(),
                "path": str(request.url.path)
            }
        )

# Create the FastAPI app instance
app = create_app()

def main():
    """Run the application with uvicorn."""
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )

if __name__ == "__main__":
    main()
