"""
Core training service with background orchestration.

This module provides the TrainingService class that manages federated learning
training runs, including background thread management, run validation, and
progress tracking.
"""

import logging
import secrets
import threading
import json
import sys
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable

# Add the model directory to the Python path for FL server imports
model_path = Path(__file__).parent.parent.parent.parent / "model"
if str(model_path) not in sys.path:
    sys.path.insert(0, str(model_path))

from core.config import settings
from core.exceptions import (
    RunNotFoundError, ActiveRunExistsError, StorageError, 
    FLServerError, ResourceError, ValidationError, NoActiveRunError
)
from schemas.training import RunMetadata, RunStatusEnum, RunMetrics, LogEntry, ErrorEntry, RoundMetrics, LogLevelEnum
from storage.run_store import RunStore

logger = logging.getLogger(__name__)


class TrainingService:
    """
    Core service for managing federated learning training runs.
    
    Handles run lifecycle management, background thread orchestration,
    and integration with the FL server process.
    """
    
    def __init__(self, run_store: RunStore):
        """
        Initialize the training service.
        
        Args:
            run_store: RunStore instance for metadata persistence
        """
        self.run_store = run_store
        self._active_threads: Dict[str, threading.Thread] = {}
        self._thread_lock = threading.Lock()
        self._service_start_time = time.time()
        self._metrics_callbacks: Dict[str, Callable] = {}
        
        # Cooperative cancellation infrastructure
        self._stop_events: Dict[str, threading.Event] = {}
        self._stop_lock = threading.Lock()
        
        # Port management for Windows compatibility
        self._used_ports: set = set()
        self._port_lock = threading.Lock()
        self._base_port = 8080
        
        logger.info("TrainingService initialized")
    
    def generate_run_id(self) -> str:
        """
        Generate a unique run ID with timestamp and random suffix.
        
        Returns:
            Unique run ID in format: run_YYYYMMDD_HHMMSS_<suffix>
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        random_suffix = secrets.token_hex(2)  # 4 character hex string
        return f"run_{timestamp}_{random_suffix}"
    
    def start_training_run(self, config: Optional[Dict[str, Any]] = None) -> RunMetadata:
        """
        Start a new federated learning training run.
        
        Validates that no active run exists, generates unique run_id,
        creates directory structure, initializes run metadata, and
        spawns FL server in background thread.
        
        Args:
            config: Optional training configuration overrides
            
        Returns:
            RunMetadata for the newly created run
            
        Raises:
            ValueError: If a training run is already active
            OSError: If run directories cannot be created
        """
        # Check for active runs
        active_run = self.run_store.get_active_run()
        if active_run is not None:
            raise ActiveRunExistsError(active_run.run_id)
        
        # Generate unique run ID
        run_id = self.generate_run_id()
        
        # Create run directories
        try:
            settings.ensure_run_directories(run_id)
            logs_path = str(settings.get_run_logs_path(run_id))
            results_path = str(settings.get_run_results_path(run_id))
        except OSError as e:
            logger.error(f"Failed to create directories for run {run_id}: {e}")
            raise ResourceError(
                message=f"Failed to create run directories: {e}",
                resource_type="directory",
                resource_path=str(settings.get_run_logs_path(run_id).parent)
            )
        
        # Allocate port for FL server
        try:
            fl_server_port = self._get_available_port()
            logger.info(f"Allocated port {fl_server_port} for run {run_id}")
        except Exception as e:
            logger.error(f"Failed to allocate port for run {run_id}: {e}")
            raise ResourceError(
                message=f"Failed to allocate port for FL server: {e}",
                resource_type="port",
                resource_path="network"
            )
        
        # Initialize run metadata
        run_metadata = RunMetadata(
            run_id=run_id,
            status=RunStatusEnum.IDLE,
            start_time=datetime.utcnow(),
            config=config or {},
            logs_path=logs_path,
            results_path=results_path,
            fl_server_port=fl_server_port
        )
        
        # Store run metadata
        try:
            self.run_store.create_run(run_metadata)
        except ValueError as e:
            # Re-raise ValueError as-is (run already exists)
            raise
        except Exception as e:
            logger.error(f"Failed to store run metadata for {run_id}: {e}")
            raise StorageError(
                message=f"Failed to store run metadata: {e}",
                operation="create_run",
                details={"run_id": run_id}
            )
        
        # Create stop event for cooperative cancellation
        stop_event = self._create_stop_event(run_id)
        
        # Start background training thread
        try:
            self._start_background_training(run_id, config or {})
        except Exception as e:
            # Update run status to ERROR if thread creation fails
            self.run_store.update_run(run_id, {
                "status": RunStatusEnum.ERROR,
                "error_message": f"Failed to start training thread: {str(e)}",
                "end_time": datetime.utcnow().isoformat()
            })
            logger.error(f"Failed to start background training for {run_id}: {e}")
            raise
        
        logger.info(f"Started training run {run_id}")
        return run_metadata
    
    def _start_background_training(self, run_id: str, config: Dict[str, Any]) -> None:
        """
        Start the FL server in a background thread with comprehensive error handling.
        
        Args:
            run_id: Unique identifier for the training run
            config: Training configuration
        """
        def training_thread():
            """Background thread function for FL server execution with graceful error handling."""
            thread_start_time = time.time()
            
            try:
                logger.info(f"Starting FL server for run {run_id}")
                
                # Update run status to TRAINING with retry logic
                self._update_run_status_with_retry(run_id, {
                    "status": RunStatusEnum.TRAINING,
                    "start_time": datetime.utcnow().isoformat()
                })
                
                # Execute FL server with comprehensive error handling
                self._execute_fl_server_with_error_handling(run_id, config)
                
                # Update run status to COMPLETED
                self._update_run_status_with_retry(run_id, {
                    "status": RunStatusEnum.COMPLETED,
                    "end_time": datetime.utcnow().isoformat()
                })
                
                logger.info(f"FL server completed successfully for run {run_id}")
                
            except ImportError as e:
                # Handle FL server import failures
                error_msg = f"FL server components not available: {e}"
                logger.error(f"Import error for run {run_id}: {error_msg}")
                self._handle_training_error(run_id, error_msg, "IMPORT_ERROR")
                raise FLServerError(error_msg, run_id, "IMPORT_ERROR")
                
            except FileNotFoundError as e:
                # Handle missing configuration files
                error_msg = f"Required configuration files not found: {e}"
                logger.error(f"Configuration error for run {run_id}: {error_msg}")
                self._handle_training_error(run_id, error_msg, "CONFIG_ERROR")
                raise FLServerError(error_msg, run_id, "CONFIG_ERROR")
                
            except PermissionError as e:
                # Handle permission issues
                error_msg = f"Permission denied accessing required resources: {e}"
                logger.error(f"Permission error for run {run_id}: {error_msg}")
                self._handle_training_error(run_id, error_msg, "PERMISSION_ERROR")
                raise ResourceError(error_msg, "permission", str(e))
                
            except OSError as e:
                # Handle OS-level errors (network, file system, etc.)
                error_msg = f"System error during training: {e}"
                logger.error(f"OS error for run {run_id}: {error_msg}")
                self._handle_training_error(run_id, error_msg, "SYSTEM_ERROR")
                raise ResourceError(error_msg, "system", str(e))
                
            except KeyboardInterrupt:
                # Handle cooperative cancellation
                logger.info(f"Training run {run_id} was stopped by user request")
                self._update_run_status_with_retry(run_id, {
                    "status": RunStatusEnum.ERROR,
                    "error_message": "Training stopped by user request",
                    "error_type": "USER_TERMINATED",
                    "end_time": datetime.utcnow().isoformat()
                })
                return  # Exit gracefully
                
            except Exception as e:
                # Handle all other unexpected errors
                error_msg = f"Unexpected error during training: {e}"
                logger.error(f"Unexpected error for run {run_id}: {error_msg}", exc_info=True)
                self._handle_training_error(run_id, error_msg, "UNEXPECTED_ERROR")
                raise FLServerError(error_msg, run_id, "UNEXPECTED_ERROR")
                
            finally:
                # Clean up thread reference and resources
                thread_duration = time.time() - thread_start_time
                logger.info(f"Training thread for run {run_id} finished after {thread_duration:.2f} seconds")
                
                with self._thread_lock:
                    self._active_threads.pop(run_id, None)
                
                # Unregister metrics callback if it exists
                self._unregister_metrics_callback(run_id)
                
                # Clean up stop event
                self._cleanup_stop_event(run_id)
                
                # Clean up any remaining port allocations for this run
                try:
                    run_metadata = self.run_store.get_run(run_id)
                    if run_metadata and hasattr(run_metadata, 'fl_server_port'):
                        port = getattr(run_metadata, 'fl_server_port', None)
                        if port:
                            self._release_port(port)
                            logger.debug(f"Released port {port} for completed run {run_id}")
                except Exception as e:
                    logger.warning(f"Could not clean up port for run {run_id}: {e}")
        
        # Create and start the background thread
        thread = threading.Thread(
            target=training_thread,
            name=f"FL-Server-{run_id}",
            daemon=True
        )
        
        with self._thread_lock:
            self._active_threads[run_id] = thread
        
        thread.start()
        logger.debug(f"Background training thread started for run {run_id}")
    
    def _update_run_status_with_retry(self, run_id: str, updates: Dict[str, Any], max_retries: int = 3) -> None:
        """
        Update run status with retry logic for handling storage failures.
        
        Args:
            run_id: Unique identifier for the training run
            updates: Dictionary of fields to update
            max_retries: Maximum number of retry attempts
        """
        for attempt in range(max_retries + 1):
            try:
                self.run_store.update_run(run_id, updates)
                return
            except Exception as e:
                if attempt < max_retries:
                    logger.warning(f"Failed to update run status (attempt {attempt + 1}): {e}. Retrying...")
                    time.sleep(0.1 * (2 ** attempt))  # Exponential backoff
                else:
                    logger.error(f"Failed to update run status after {max_retries} attempts: {e}")
                    # Don't raise - we want the training to continue even if status updates fail
    
    def _handle_training_error(self, run_id: str, error_message: str, error_type: str) -> None:
        """
        Handle training errors with consistent error reporting and status updates.
        
        Args:
            run_id: Unique identifier for the training run
            error_message: Human-readable error message
            error_type: Error type classification
        """
        try:
            self._update_run_status_with_retry(run_id, {
                "status": RunStatusEnum.ERROR,
                "error_message": error_message,
                "error_type": error_type,
                "end_time": datetime.utcnow().isoformat()
            })
        except Exception as e:
            logger.error(f"Failed to update error status for run {run_id}: {e}")
    
    def _execute_fl_server_with_error_handling(self, run_id: str, config: Dict[str, Any]) -> None:
        """
        Execute the FL server with comprehensive error handling and graceful degradation.
        
        Args:
            run_id: Unique identifier for the training run
            config: Training configuration
        """
        try:
            # Call the original FL server execution method
            self._execute_fl_server(run_id, config)
            
        except ImportError as e:
            # Re-raise import errors for specific handling
            raise ImportError(f"FL server components unavailable: {e}")
            
        except Exception as e:
            # Wrap other exceptions with additional context
            raise RuntimeError(f"FL server execution failed: {e}") from e
    
    def _execute_fl_server(self, run_id: str, config: Dict[str, Any]) -> None:
        """
        Execute the federated learning server.
        
        Integrates with the existing FL server from the model directory,
        sets up metrics callbacks, and handles the actual training process.
        
        Args:
            run_id: Unique identifier for the training run
            config: Training configuration
        """
        try:
            # Import FL server components
            from fl_server.server import FederatedServer, start_server
            from fl_server.config_loader import ConfigLoader
            
            logger.info(f"Starting FL server integration for run {run_id}")
            
            # Set up configuration paths relative to server_api/v1
            server_config_path = "configs/server_config.yaml"
            model_config_path = "configs/model_config.yaml"
            data_config_path = "configs/data_config.yaml"
            
            # Ensure config files exist
            if not Path(server_config_path).exists():
                logger.warning(f"Server config not found at {server_config_path}, using defaults")
                server_config_path = None
            
            if not Path(model_config_path).exists():
                logger.warning(f"Model config not found at {model_config_path}")
                model_config_path = None
                
            if not Path(data_config_path).exists():
                logger.warning(f"Data config not found at {data_config_path}")
                data_config_path = None
            
            # Register metrics callback for this run
            self._register_metrics_callback(run_id)
            
            # Initialize the FL server with run_id for consistent logging
            logger.info("Initializing FederatedServer...")
            fl_server = FederatedServer(
                server_config_path=server_config_path,
                data_config_path=data_config_path,
                model_config_path=model_config_path,
                run_id=run_id
            )
            
            # Extract configuration from FL server
            server_config = fl_server.federated_config.get('server', {})
            total_rounds = server_config.get('rounds', config.get('num_rounds', 10))
            min_fit_clients = server_config.get('min_fit_clients', config.get('clients_per_round', 2))
            
            # Get the pre-allocated port from run metadata
            current_run = self.run_store.get_run(run_id)
            if not current_run or not current_run.fl_server_port:
                raise RuntimeError(f"No port allocated for run {run_id}")
            fl_server_port = current_run.fl_server_port
            
            # Update run metadata with actual configuration
            self.run_store.update_run(run_id, {
                "total_rounds": total_rounds,
                "clients_expected": min_fit_clients
            })
            
            logger.info(f"FL server configured: {total_rounds} rounds, {min_fit_clients} min clients, port {fl_server_port}")
            
            # Create strategy with metrics callback integration
            strategy = fl_server.create_strategy()
            
            # Monkey patch the strategy to include our metrics callback
            original_aggregate_fit = strategy.aggregate_fit
            original_aggregate_evaluate = strategy.aggregate_evaluate
            
            def aggregate_fit_with_callback(server_round, results, failures):
                """Wrapper for aggregate_fit that calls our metrics callback and checks for stop signal"""
                try:
                    # Check for cooperative cancellation BEFORE processing
                    if self._should_stop(run_id):
                        logger.info(f"Stop signal detected in round {server_round}, terminating training")
                        # Raise an exception to break out of the FL server loop
                        raise KeyboardInterrupt("Training stopped by user request")
                    
                    # Call original aggregate_fit
                    aggregated_result = original_aggregate_fit(server_round, results, failures)
                    
                    # Extract metrics and call our callback
                    if results:
                        # Calculate average metrics from client results
                        total_examples = sum([r.num_examples for r, _ in results])
                        avg_loss = sum([r.metrics.get('loss', 0) * r.num_examples for r, _ in results]) / total_examples if total_examples > 0 else 0
                        avg_accuracy = sum([r.metrics.get('accuracy', 0) * r.num_examples for r, _ in results]) / total_examples if total_examples > 0 else 0
                        
                        # Call our metrics callback
                        self._call_metrics_callback(run_id, server_round, {
                            'loss': avg_loss,
                            'accuracy': avg_accuracy,
                            'clients_participated': len(results),
                            'duration': 0  # Duration will be calculated elsewhere
                        })
                    
                    return aggregated_result
                except KeyboardInterrupt:
                    # Re-raise KeyboardInterrupt to stop FL server
                    raise
                except Exception as e:
                    logger.error(f"Error in aggregate_fit callback: {e}")
                    return original_aggregate_fit(server_round, results, failures)
            
            def aggregate_evaluate_with_callback(server_round, results, failures):
                """Wrapper for aggregate_evaluate that logs evaluation results and checks for stop signal"""
                try:
                    # Check for cooperative cancellation BEFORE processing
                    if self._should_stop(run_id):
                        logger.info(f"Stop signal detected in evaluation round {server_round}, terminating training")
                        raise KeyboardInterrupt("Training stopped by user request")
                    
                    # Call original aggregate_evaluate
                    aggregated_result = original_aggregate_evaluate(server_round, results, failures)
                    
                    # Log evaluation results
                    if aggregated_result and len(aggregated_result) >= 2:
                        loss, metrics = aggregated_result[0], aggregated_result[1]
                        logger.info(f"Round {server_round} evaluation - Loss: {loss:.4f}, Metrics: {metrics}")
                    
                    return aggregated_result
                except KeyboardInterrupt:
                    # Re-raise KeyboardInterrupt to stop FL server
                    raise
                except Exception as e:
                    logger.error(f"Error in aggregate_evaluate callback: {e}")
                    return original_aggregate_evaluate(server_round, results, failures)
            
            # Apply the monkey patches
            strategy.aggregate_fit = aggregate_fit_with_callback
            strategy.aggregate_evaluate = aggregate_evaluate_with_callback
            
            # Import Flower components
            import flwr as fl
            
            # Create server configuration
            config_obj = fl.server.ServerConfig(num_rounds=total_rounds)
            
            logger.info(f"Starting FL server for run {run_id} with {total_rounds} rounds on port {fl_server_port}")
            
            # Check for stop signal before starting FL server
            if self._should_stop(run_id):
                logger.info(f"Stop signal detected before FL server start, aborting run {run_id}")
                raise KeyboardInterrupt("Training stopped by user request")
            
            # Start the FL server (this will block until training completes)
            # Use a more targeted approach to handle signal registration in background thread
            import signal
            import threading
            
            # Check if we're in the main thread
            is_main_thread = threading.current_thread() is threading.main_thread()
            
            if not is_main_thread:
                # Temporarily patch signal registration to avoid the error
                original_signal = signal.signal
                def safe_signal(sig, handler):
                    # Only register signals in main thread, ignore in background threads
                    if threading.current_thread() is threading.main_thread():
                        return original_signal(sig, handler)
                    else:
                        # Return a dummy handler for background threads
                        return lambda: None
                
                signal.signal = safe_signal
                
                try:
                    fl.server.start_server(
                        server_address=f"0.0.0.0:{fl_server_port}",
                        config=config_obj,
                        strategy=strategy,
                    )
                except KeyboardInterrupt:
                    logger.info(f"FL server for run {run_id} stopped by user request")
                    # This is expected when cooperative cancellation is triggered
                    return
                finally:
                    # Restore original signal function
                    signal.signal = original_signal
                    # Release the port
                    self._release_port(fl_server_port)
            else:
                # We're in main thread, signal handling will work normally
                try:
                    fl.server.start_server(
                        server_address=f"0.0.0.0:{fl_server_port}",
                        config=config_obj,
                        strategy=strategy,
                    )
                except KeyboardInterrupt:
                    logger.info(f"FL server for run {run_id} stopped by user request")
                    # This is expected when cooperative cancellation is triggered
                    return
                finally:
                    # Release the port
                    self._release_port(fl_server_port)
            
            logger.info(f"FL server completed successfully for run {run_id}")
            
            # Unregister metrics callback
            self._unregister_metrics_callback(run_id)
                
        except ImportError as e:
            logger.error(f"Failed to import FL server components: {e}")
            raise RuntimeError(f"FL server integration failed: {e}")
        except RuntimeError as e:
            if "Failed to bind to address" in str(e):
                # Port binding error - try to handle gracefully
                logger.error(f"Port binding failed for run {run_id}: {e}")
                # Release the port we tried to use
                try:
                    run_metadata = self.run_store.get_run(run_id)
                    if run_metadata and hasattr(run_metadata, 'fl_server_port'):
                        port = getattr(run_metadata, 'fl_server_port', None)
                        if port:
                            self._release_port(port)
                except Exception:
                    pass
                # Provide helpful error message
                if hasattr(os, 'name') and os.name == 'nt':  # Windows
                    error_msg = (
                        "FL server port binding failed on Windows. This typically happens when:\n"
                        "1. A previous training run hasn't fully released the port\n"
                        "2. Another process is using the port\n"
                        "3. Windows is holding the port in TIME_WAIT state\n\n"
                        "Solutions:\n"
                        "- Wait 30-60 seconds before starting a new run\n"
                        "- Check if any FL server processes are still running\n"
                        "- Restart the API server if the problem persists"
                    )
                else:
                    error_msg = "FL server port binding failed. Please wait a moment and try again."
                
                raise RuntimeError(error_msg) from e
            else:
                logger.error(f"FL server execution failed for run {run_id}: {e}", exc_info=True)
                raise
        except Exception as e:
            logger.error(f"FL server execution failed for run {run_id}: {e}", exc_info=True)
            raise
    
    def _register_metrics_callback(self, run_id: str) -> None:
        """
        Register a metrics callback for the specified run.
        
        Args:
            run_id: Unique identifier for the training run
        """
        def metrics_callback(round_num: int, metrics: Dict[str, Any]) -> None:
            """Callback function to update run progress during training"""
            self.update_run_progress(run_id, round_num, metrics)
        
        self._metrics_callbacks[run_id] = metrics_callback
        logger.debug(f"Registered metrics callback for run {run_id}")
    
    def _unregister_metrics_callback(self, run_id: str) -> None:
        """
        Unregister the metrics callback for the specified run.
        
        Args:
            run_id: Unique identifier for the training run
        """
        if run_id in self._metrics_callbacks:
            del self._metrics_callbacks[run_id]
            logger.debug(f"Unregistered metrics callback for run {run_id}")
    
    def _create_stop_event(self, run_id: str) -> threading.Event:
        """
        Create a stop event for cooperative cancellation.
        
        Args:
            run_id: Unique identifier for the training run
            
        Returns:
            Threading event for signaling stop
        """
        with self._stop_lock:
            stop_event = threading.Event()
            self._stop_events[run_id] = stop_event
            logger.debug(f"Created stop event for run {run_id}")
            return stop_event
    
    def _signal_stop(self, run_id: str) -> bool:
        """
        Signal a training run to stop cooperatively.
        
        Args:
            run_id: Unique identifier for the training run
            
        Returns:
            True if stop event was signaled, False if no event exists
        """
        with self._stop_lock:
            stop_event = self._stop_events.get(run_id)
            if stop_event:
                stop_event.set()
                logger.info(f"Signaled stop for run {run_id}")
                return True
            return False
    
    def _should_stop(self, run_id: str) -> bool:
        """
        Check if a training run should stop.
        
        Args:
            run_id: Unique identifier for the training run
            
        Returns:
            True if the run should stop, False otherwise
        """
        with self._stop_lock:
            stop_event = self._stop_events.get(run_id)
            return stop_event.is_set() if stop_event else False
    
    def _cleanup_stop_event(self, run_id: str) -> None:
        """
        Clean up the stop event for a completed run.
        
        Args:
            run_id: Unique identifier for the training run
        """
        with self._stop_lock:
            if run_id in self._stop_events:
                del self._stop_events[run_id]
                logger.debug(f"Cleaned up stop event for run {run_id}")
    
    def _get_available_port(self) -> int:
        """
        Get an available port for FL server, avoiding conflicts.
        
        Returns:
            Available port number
        """
        import socket
        
        with self._port_lock:
            # Try ports starting from base_port
            for port_offset in range(100):  # Try up to 100 ports
                port = self._base_port + port_offset
                
                # Skip if port is already marked as used
                if port in self._used_ports:
                    continue
                
                # Test if port is actually available
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        sock.bind(('0.0.0.0', port))
                        # Port is available
                        self._used_ports.add(port)
                        logger.info(f"Allocated port {port} for FL server")
                        return port
                except OSError:
                    # Port is in use, try next one
                    continue
            
            # If we get here, no ports were available
            raise RuntimeError(f"No available ports found in range {self._base_port}-{self._base_port + 99}")
    
    def _release_port(self, port: int) -> None:
        """
        Release a port back to the available pool.
        
        Args:
            port: Port number to release
        """
        with self._port_lock:
            self._used_ports.discard(port)
            logger.debug(f"Released port {port}")
    
    def _wait_for_port_release(self, port: int, timeout: float = 10.0) -> bool:
        """
        Wait for a port to be released (Windows-specific).
        
        Args:
            port: Port number to wait for
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if port was released, False if timeout
        """
        import socket
        import time
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    sock.bind(('0.0.0.0', port))
                    # Port is available
                    return True
            except OSError:
                # Port still in use, wait a bit
                time.sleep(0.5)
        
        return False
    
    def _call_metrics_callback(self, run_id: str, round_num: int, metrics: Dict[str, Any]) -> None:
        """
        Call the metrics callback for the specified run.
        
        Args:
            run_id: Unique identifier for the training run
            round_num: Current round number
            metrics: Round metrics to report
        """
        if run_id in self._metrics_callbacks:
            try:
                self._metrics_callbacks[run_id](round_num, metrics)
            except Exception as e:
                logger.error(f"Error calling metrics callback for run {run_id}: {e}")

    def update_run_progress(self, run_id: str, round_num: int, metrics: Dict[str, Any]) -> None:
        """
        Update run metadata with progress information during training.
        
        Args:
            run_id: Unique identifier for the training run
            round_num: Current round number (1-based)
            metrics: Round metrics including loss, accuracy, etc.
        """
        try:
            # Get current run data to access existing round metrics
            current_run = self.run_store.get_run(run_id)
            if not current_run:
                logger.error(f"Cannot update progress for non-existent run: {run_id}")
                return
            
            # Create round metrics entry
            round_metrics = RoundMetrics(
                round_number=round_num,
                timestamp=datetime.utcnow(),
                loss=metrics.get("loss"),
                accuracy=metrics.get("accuracy"),
                clients_participated=metrics.get("clients_participated", 0),
                duration=metrics.get("duration")
            )
            
            # Get existing round metrics or initialize empty list
            existing_round_metrics_data = current_run.round_metrics or []
            
            # Convert existing data to RoundMetrics objects
            existing_round_metrics = []
            for rm_data in existing_round_metrics_data:
                try:
                    if isinstance(rm_data, dict):
                        existing_round_metrics.append(RoundMetrics(**rm_data))
                    else:
                        existing_round_metrics.append(rm_data)
                except Exception as e:
                    logger.warning(f"Failed to parse existing round metric: {e}")
                    continue
            
            # Update or append the round metrics
            updated = False
            for i, existing_metric in enumerate(existing_round_metrics):
                if existing_metric.round_number == round_num:
                    existing_round_metrics[i] = round_metrics
                    updated = True
                    break
            
            if not updated:
                existing_round_metrics.append(round_metrics)
            
            # Sort round metrics by round number
            existing_round_metrics.sort(key=lambda x: x.round_number)
            
            # Prepare updates
            updates = {
                "rounds_completed": round_num,
                "round_metrics": [rm.dict() for rm in existing_round_metrics]
            }
            
            self.run_store.update_run(run_id, updates)
            logger.debug(f"Updated progress for run {run_id}: round {round_num} with metrics {metrics}")
            
        except Exception as e:
            logger.error(f"Failed to update progress for run {run_id}: {e}")
    
    def get_current_status(self) -> Dict[str, Any]:
        """
        Get the status of the current or most recent training run.
        
        Returns:
            Dictionary containing current system status information
        """
        # Check for active run first
        active_run = self.run_store.get_active_run()
        if active_run:
            return {
                "status": active_run.status,
                "run_id": active_run.run_id,
                "start_time": active_run.start_time,
                "end_time": active_run.end_time,
                "rounds_completed": active_run.rounds_completed,
                "total_rounds": active_run.total_rounds,
                "fl_server_port": getattr(active_run, 'fl_server_port', None)
            }
        
        # If no active run, get the most recent run
        latest_run = self.run_store.get_latest_run()
        if latest_run:
            return {
                "status": RunStatusEnum.IDLE,  # System is idle
                "run_id": latest_run.run_id,
                "start_time": latest_run.start_time,
                "end_time": latest_run.end_time,
                "rounds_completed": latest_run.rounds_completed,
                "total_rounds": latest_run.total_rounds,
                "fl_server_port": getattr(latest_run, 'fl_server_port', None)
            }
        
        # No runs exist
        return {
            "status": RunStatusEnum.IDLE,
            "run_id": None,
            "start_time": None,
            "end_time": None,
            "rounds_completed": None,
            "total_rounds": None,
            "fl_server_port": None
        }
    
    def get_all_runs(
        self,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None,
        sort: str = "desc"
    ) -> List[RunMetadata]:
        """
        Retrieve filtered and paginated list of historical runs.
        
        Args:
            limit: Maximum number of runs to return
            offset: Number of runs to skip
            status: Filter by run status (optional)
            sort: Sort order by start_time ("asc" or "desc")
            
        Returns:
            List of RunMetadata objects matching the criteria
        """
        try:
            return self.run_store.filter_runs(
                status=status,
                limit=limit,
                offset=offset,
                sort=sort
            )
        except Exception as e:
            logger.error(f"Failed to retrieve runs: {e}")
            return []
    
    def get_run_by_id(self, run_id: str) -> RunMetadata:
        """
        Retrieve detailed metadata for a specific run.
        
        Args:
            run_id: Unique identifier for the training run
            
        Returns:
            RunMetadata object if found
            
        Raises:
            RunNotFoundError: If the run doesn't exist
            StorageError: If storage access fails
        """
        try:
            run_metadata = self.run_store.get_run(run_id)
            if run_metadata is None:
                raise RunNotFoundError(run_id)
            return run_metadata
        except RunNotFoundError:
            # Re-raise RunNotFoundError as-is
            raise
        except Exception as e:
            logger.error(f"Failed to retrieve run {run_id}: {e}")
            raise StorageError(
                message=f"Failed to retrieve run: {e}",
                operation="get_run",
                details={"run_id": run_id}
            )
    
    def get_run_metrics(self, run_id: str) -> Optional[RunMetrics]:
        """
        Retrieve metrics for a specific run.
        
        Includes real-time data for active runs and final data for completed runs.
        
        Args:
            run_id: Unique identifier for the training run
            
        Returns:
            RunMetrics object if found, None otherwise
        """
        try:
            run_metadata = self.run_store.get_run(run_id)
            if not run_metadata:
                return None
            
            # Convert stored round metrics back to RoundMetrics objects
            round_metrics = []
            if run_metadata.round_metrics:
                for rm_dict in run_metadata.round_metrics:
                    try:
                        round_metrics.append(RoundMetrics(**rm_dict))
                    except Exception as e:
                        logger.warning(f"Failed to parse round metrics for run {run_id}: {e}")
                        continue
            
            # Calculate progress percentage
            progress_percentage = None
            if run_metadata.total_rounds and run_metadata.total_rounds > 0:
                completed = run_metadata.rounds_completed or 0
                progress_percentage = (completed / run_metadata.total_rounds) * 100.0
            
            # Determine current round for active runs
            current_round = None
            if run_metadata.status == RunStatusEnum.TRAINING:
                current_round = run_metadata.rounds_completed
            
            # For active runs, include real-time connection info
            clients_connected = None
            if run_metadata.status == RunStatusEnum.TRAINING:
                clients_connected = run_metadata.clients_expected
            
            return RunMetrics(
                run_id=run_id,
                status=run_metadata.status,
                current_round=current_round,
                total_rounds=run_metadata.total_rounds,
                progress_percentage=progress_percentage,
                clients_connected=clients_connected,
                clients_expected=run_metadata.clients_expected,
                round_metrics=round_metrics,
                last_update_time=datetime.utcnow() if run_metadata.status == RunStatusEnum.TRAINING else None
            )
            
        except Exception as e:
            logger.error(f"Failed to retrieve metrics for run {run_id}: {e}")
            return None
    
    def get_active_run_metrics(self) -> Optional[RunMetrics]:
        """
        Retrieve metrics for the currently active run.
        
        Returns:
            RunMetrics object for active run, None if no active run
        """
        try:
            active_run = self.run_store.get_active_run()
            if not active_run:
                return None
            
            return self.get_run_metrics(active_run.run_id)
            
        except Exception as e:
            logger.error(f"Failed to retrieve active run metrics: {e}")
            return None
    
    def is_run_active(self, run_id: str) -> bool:
        """
        Check if a specific run is currently active.
        
        Args:
            run_id: Unique identifier for the training run
            
        Returns:
            True if the run is active, False otherwise
        """
        active_run = self.run_store.get_active_run()
        return active_run is not None and active_run.run_id == run_id
    
    def get_active_run_id(self) -> Optional[str]:
        """
        Get the ID of the currently active run.
        
        Returns:
            Run ID if there's an active run, None otherwise
        """
        active_run = self.run_store.get_active_run()
        return active_run.run_id if active_run else None
    
    def get_service_uptime(self) -> float:
        """
        Get the service uptime in seconds.
        
        Returns:
            Service uptime in seconds since initialization
        """
        return time.time() - self._service_start_time
    
    def get_service_health(self) -> Dict[str, Any]:
        """
        Get comprehensive service health information with graceful degradation.
        
        Returns:
            Dictionary containing service health status and diagnostics
        """
        health_status = {
            "status": "healthy",
            "uptime_seconds": self.get_service_uptime(),
            "active_runs": 0,
            "total_runs": 0,
            "storage_accessible": True,
            "background_threads": {},
            "degraded_services": []
        }
        
        try:
            # Check storage accessibility
            try:
                all_runs = self.run_store.get_all_runs()
                health_status["total_runs"] = len(all_runs)
                health_status["storage_accessible"] = True
            except Exception as e:
                logger.error(f"Storage health check failed: {e}")
                health_status["storage_accessible"] = False
                health_status["degraded_services"].append("storage")
                health_status["status"] = "degraded"
            
            # Check active runs and background threads
            try:
                active_run = self.run_store.get_active_run()
                if active_run:
                    health_status["active_runs"] = 1
                    
                    # Check if the background thread is still alive
                    with self._thread_lock:
                        thread = self._active_threads.get(active_run.run_id)
                        if thread:
                            health_status["background_threads"][active_run.run_id] = {
                                "alive": thread.is_alive(),
                                "name": thread.name
                            }
                            
                            # If thread is dead but run is still marked as active, it's degraded
                            if not thread.is_alive():
                                health_status["degraded_services"].append("background_processing")
                                health_status["status"] = "degraded"
                        else:
                            # Active run but no thread - definitely degraded
                            health_status["degraded_services"].append("background_processing")
                            health_status["status"] = "degraded"
                            
            except Exception as e:
                logger.error(f"Active run health check failed: {e}")
                health_status["degraded_services"].append("run_monitoring")
                health_status["status"] = "degraded"
            
            # Check thread status for all active threads
            try:
                with self._thread_lock:
                    for run_id, thread in self._active_threads.items():
                        if run_id not in health_status["background_threads"]:
                            health_status["background_threads"][run_id] = {
                                "alive": thread.is_alive(),
                                "name": thread.name
                            }
            except Exception as e:
                logger.error(f"Thread status check failed: {e}")
                health_status["degraded_services"].append("thread_monitoring")
                health_status["status"] = "degraded"
            
            # If there are degraded services, mark as degraded
            if health_status["degraded_services"]:
                health_status["status"] = "degraded"
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)
        
        return health_status
    
    def stop_training_run(self, run_id: str) -> RunMetadata:
        """
        Stop a currently running training run.
        
        Terminates the background thread, updates run status, and performs cleanup.
        
        Args:
            run_id: Unique identifier for the training run to stop
            
        Returns:
            RunMetadata for the stopped run
            
        Raises:
            RunNotFoundError: If the run doesn't exist
            NoActiveRunError: If no run is currently active
            StorageError: If storage operations fail
        """
        logger.info(f"Attempting to stop training run: {run_id}")
        
        try:
            # Check if run exists
            run_metadata = self.run_store.get_run(run_id)
            if run_metadata is None:
                raise RunNotFoundError(run_id)
            
            # Check if run is actually active
            if run_metadata.status != RunStatusEnum.TRAINING:
                raise ValueError(f"Run '{run_id}' is not currently active (status: {run_metadata.status})")
            
            # Signal the training run to stop cooperatively
            stop_signaled = self._signal_stop(run_id)
            
            # Get the port used by this run for cleanup
            fl_server_port = None
            try:
                current_run = self.run_store.get_run(run_id)
                if current_run and hasattr(current_run, 'fl_server_port'):
                    fl_server_port = getattr(current_run, 'fl_server_port', None)
            except Exception:
                pass
            
            # Check if we have an active thread for this run
            with self._thread_lock:
                thread = self._active_threads.get(run_id)
                
                if not thread:
                    logger.warning(f"No active thread found for run {run_id}, updating status only")
                elif stop_signaled:
                    logger.info(f"Cooperative stop signaled for run {run_id}, waiting for graceful shutdown...")
                    
                    # Wait for the thread to finish gracefully (with timeout)
                    thread.join(timeout=30.0)  # 30 second timeout
                    
                    if thread.is_alive():
                        logger.warning(f"Thread {run_id} did not stop gracefully within timeout")
                        # Remove from tracking anyway - thread becomes orphaned
                        del self._active_threads[run_id]
                    else:
                        logger.info(f"Thread {run_id} stopped gracefully")
                        # Thread already removed itself from _active_threads in finally block
                else:
                    logger.warning(f"Could not signal stop for run {run_id} (no stop event found)")
            
            # On Windows, wait for port to be released to avoid binding conflicts
            if fl_server_port and hasattr(os, 'name') and os.name == 'nt':  # Windows
                logger.info(f"Waiting for port {fl_server_port} to be released (Windows)")
                port_released = self._wait_for_port_release(fl_server_port, timeout=10.0)
                if port_released:
                    logger.info(f"Port {fl_server_port} successfully released")
                else:
                    logger.warning(f"Port {fl_server_port} may still be in use - subsequent starts may fail")
            
            # Update run status to indicate it was stopped
            end_time = datetime.utcnow().isoformat()
            updates = {
                "status": RunStatusEnum.ERROR,  # Mark as ERROR since it was terminated early
                "end_time": end_time,
                "error_message": "Training run stopped by user request",
                "error_type": "USER_TERMINATED"
            }
            
            # Calculate duration if we have start time
            if run_metadata.start_time:
                try:
                    # Handle both datetime objects and ISO strings
                    if isinstance(run_metadata.start_time, datetime):
                        start_dt = run_metadata.start_time
                    else:
                        start_dt = datetime.fromisoformat(run_metadata.start_time.replace('Z', '+00:00'))
                    
                    end_dt = datetime.fromisoformat(end_time)
                    duration = int((end_dt - start_dt).total_seconds())
                    updates["duration"] = duration
                except Exception as e:
                    logger.warning(f"Could not calculate duration for stopped run {run_id}: {e}")
            
            # Update run metadata with retry logic
            self._update_run_status_with_retry(run_id, updates)
            
            # Unregister metrics callback
            self._unregister_metrics_callback(run_id)
            
            # Get updated run metadata
            updated_run = self.run_store.get_run(run_id)
            
            logger.info(f"Successfully stopped training run: {run_id}")
            return updated_run
            
        except (RunNotFoundError, ValueError) as e:
            # Re-raise these specific exceptions
            raise
        except Exception as e:
            logger.error(f"Failed to stop training run {run_id}: {e}", exc_info=True)
            raise StorageError(
                message=f"Failed to stop run: {e}",
                operation="stop_run",
                details={"run_id": run_id}
            )
    
    def stop_active_training_run(self) -> RunMetadata:
        """
        Stop the currently active training run.
        
        Convenience method that finds and stops the active run.
        
        Returns:
            RunMetadata for the stopped run
            
        Raises:
            NoActiveRunError: If no run is currently active
            StorageError: If storage operations fail
        """
        logger.info("Attempting to stop active training run")
        
        # Find the active run
        active_run = self.run_store.get_active_run()
        if active_run is None:
            raise NoActiveRunError()
        
        # Stop the active run
        return self.stop_training_run(active_run.run_id)
    
    def cleanup_completed_runs(self, max_runs: int = 1000) -> int:
        """
        Clean up old completed runs to prevent unlimited storage growth.
        
        Args:
            max_runs: Maximum number of runs to keep
            
        Returns:
            Number of runs cleaned up
        """
        try:
            return self.run_store.cleanup_old_runs(max_runs)
        except Exception as e:
            logger.error(f"Failed to cleanup old runs: {e}")
            return 0
    
    def get_thread_status(self) -> Dict[str, bool]:
        """
        Get the status of background training threads.
        
        Returns:
            Dictionary mapping run_id to thread alive status
        """
        with self._thread_lock:
            return {
                run_id: thread.is_alive()
                for run_id, thread in self._active_threads.items()
            }
    
    def get_run_logs(
        self,
        run_id: str,
        lines: int = 100,
        offset: int = 0,
        level: Optional[str] = None,
        tail: bool = False
    ) -> List[LogEntry]:
        """
        Retrieve filtered logs for a specific run with comprehensive error handling.
        
        Includes buffered logs for active runs and merges with disk logs.
        
        Args:
            run_id: Unique identifier for the training run
            lines: Maximum number of log lines to return
            offset: Number of lines to skip from the beginning
            level: Filter logs by minimum level (optional)
            tail: Return lines from the end of the log
            
        Returns:
            List of LogEntry objects matching the criteria
        """
        try:
            # Validate input parameters
            if lines < 0:
                logger.warning(f"Invalid lines parameter: {lines}. Using default.")
                lines = 100
            if offset < 0:
                logger.warning(f"Invalid offset parameter: {offset}. Using 0.")
                offset = 0
            
            # Check if run exists
            run_metadata = self.run_store.get_run(run_id)
            if not run_metadata:
                logger.debug(f"Run {run_id} not found")
                return []
            
            # Get log file path with error handling
            try:
                log_file_path = settings.get_run_logs_path(run_id) / "fl_server.log"
            except Exception as e:
                logger.error(f"Failed to get log path for run {run_id}: {e}")
                return []
            
            # Read logs from disk with error handling
            try:
                disk_logs = self._read_logs_from_disk(log_file_path, level)
            except Exception as e:
                logger.error(f"Failed to read disk logs for run {run_id}: {e}")
                disk_logs = []
            
            # For active runs, merge with buffered logs
            all_logs = disk_logs
            if self.is_run_active(run_id):
                try:
                    buffered_logs = self._get_buffered_logs(run_id, level)
                    all_logs = disk_logs + buffered_logs
                except Exception as e:
                    logger.warning(f"Failed to get buffered logs for run {run_id}: {e}")
                    # Continue with just disk logs
            
            # Sort by timestamp with error handling
            try:
                all_logs.sort(key=lambda x: x.timestamp)
            except Exception as e:
                logger.warning(f"Failed to sort logs for run {run_id}: {e}")
                # Continue with unsorted logs
            
            # Apply pagination with bounds checking
            try:
                if tail:
                    # Return last 'lines' entries, skipping 'offset' from the end
                    start_idx = max(0, len(all_logs) - offset - lines)
                    end_idx = len(all_logs) - offset if offset > 0 else len(all_logs)
                    end_idx = max(start_idx, end_idx)  # Ensure end_idx >= start_idx
                    return all_logs[start_idx:end_idx]
                else:
                    # Return 'lines' entries starting from 'offset'
                    start_idx = min(offset, len(all_logs))
                    end_idx = min(start_idx + lines, len(all_logs))
                    return all_logs[start_idx:end_idx]
            except Exception as e:
                logger.error(f"Failed to apply pagination for run {run_id}: {e}")
                return []
                
        except Exception as e:
            logger.error(f"Unexpected error retrieving logs for run {run_id}: {e}", exc_info=True)
            return []
    
    def get_run_errors(self, run_id: str) -> List[ErrorEntry]:
        """
        Extract and return error-level log entries for a specific run.
        
        Args:
            run_id: Unique identifier for the training run
            
        Returns:
            List of ErrorEntry objects for the run
        """
        try:
            # Get all logs for the run, filtering for ERROR level and above
            error_logs = self.get_run_logs(run_id, lines=10000, level="ERROR")
            
            # Convert LogEntry objects to ErrorEntry objects
            error_entries = []
            for log_entry in error_logs:
                if log_entry.level in [LogLevelEnum.ERROR, LogLevelEnum.CRITICAL]:
                    error_entry = ErrorEntry(
                        timestamp=log_entry.timestamp,
                        error_type=log_entry.level.value,
                        message=log_entry.message,
                        traceback=log_entry.extra.get("traceback") if log_entry.extra else None,
                        context=log_entry.extra,
                        run_id=log_entry.run_id
                    )
                    error_entries.append(error_entry)
            
            return error_entries
            
        except Exception as e:
            logger.error(f"Failed to retrieve errors for run {run_id}: {e}")
            return []
    
    def get_active_run_logs(
        self,
        lines: int = 100,
        offset: int = 0,
        level: Optional[str] = None,
        tail: bool = False
    ) -> List[LogEntry]:
        """
        Get logs for the currently active run or most recent run.
        
        Args:
            lines: Maximum number of log lines to return
            offset: Number of lines to skip from the beginning
            level: Filter logs by minimum level (optional)
            tail: Return lines from the end of the log
            
        Returns:
            List of LogEntry objects, empty if no runs exist
        """
        try:
            # Check for active run first
            active_run = self.run_store.get_active_run()
            if active_run:
                return self.get_run_logs(active_run.run_id, lines, offset, level, tail)
            
            # If no active run, get the most recent run
            latest_run = self.run_store.get_latest_run()
            if latest_run:
                return self.get_run_logs(latest_run.run_id, lines, offset, level, tail)
            
            # No runs exist
            return []
            
        except Exception as e:
            logger.error(f"Failed to retrieve active/recent run logs: {e}")
            return []
    
    def _read_logs_from_disk(self, log_file_path: Path, level_filter: Optional[str] = None) -> List[LogEntry]:
        """
        Read and parse log entries from a disk file with comprehensive error handling.
        
        Args:
            log_file_path: Path to the log file
            level_filter: Minimum log level to include (optional)
            
        Returns:
            List of LogEntry objects from the file
        """
        log_entries = []
        
        if not log_file_path.exists():
            logger.debug(f"Log file does not exist: {log_file_path}")
            return log_entries
        
        # Define log level hierarchy for filtering
        level_hierarchy = {
            "DEBUG": 0,
            "INFO": 1,
            "WARNING": 2,
            "ERROR": 3,
            "CRITICAL": 4
        }
        
        min_level = level_hierarchy.get(level_filter, 0) if level_filter else 0
        
        try:
            # Check file permissions before attempting to read
            if not os.access(log_file_path, os.R_OK):
                logger.error(f"No read permission for log file: {log_file_path}")
                return log_entries
            
            with open(log_file_path, 'r', encoding='utf-8', errors='replace') as f:
                line_number = 0
                for line in f:
                    line_number += 1
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        # Try to parse as JSON (structured log) first
                        log_data = json.loads(line)
                        
                        # Check log level filter
                        log_level = log_data.get("level", "INFO")
                        if level_hierarchy.get(log_level, 0) < min_level:
                            continue
                        
                        # Create LogEntry object with validation
                        timestamp_str = log_data.get("timestamp", datetime.utcnow().isoformat())
                        try:
                            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        except (ValueError, TypeError):
                            timestamp = datetime.utcnow()
                        
                        try:
                            level_enum = LogLevelEnum(log_level)
                        except ValueError:
                            level_enum = LogLevelEnum.INFO
                        
                        log_entry = LogEntry(
                            timestamp=timestamp,
                            level=level_enum,
                            source=log_data.get("source", "unknown"),
                            run_id=log_data.get("run_id"),
                            message=log_data.get("message", ""),
                            extra=log_data.get("extra")
                        )
                        log_entries.append(log_entry)
                        
                    except (json.JSONDecodeError, ValueError):
                        # Handle plain text log lines (format: "YYYY-MM-DD HH:MM:SS UTC - LEVEL - [RUN:run_id] - message")
                        try:
                            # Parse plain text log format
                            parts = line.split(" - ", 3)
                            if len(parts) >= 4:
                                timestamp_str = parts[0]
                                log_level = parts[1]
                                run_info = parts[2]
                                message = parts[3]
                                
                                # Extract run_id from [RUN:run_id] format
                                run_id_match = None
                                if run_info.startswith("[RUN:") and run_info.endswith("]"):
                                    run_id_match = run_info[5:-1]
                                
                                # Parse timestamp
                                try:
                                    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S UTC")
                                except (ValueError, TypeError):
                                    timestamp = datetime.utcnow()
                                
                                # Check log level filter
                                if level_hierarchy.get(log_level, 0) < min_level:
                                    continue
                                
                                # Convert log level to enum
                                try:
                                    level_enum = LogLevelEnum(log_level)
                                except ValueError:
                                    level_enum = LogLevelEnum.INFO
                                
                                log_entry = LogEntry(
                                    timestamp=timestamp,
                                    level=level_enum,
                                    source="fl_server",
                                    run_id=run_id_match,
                                    message=message,
                                    extra=None
                                )
                                log_entries.append(log_entry)
                            else:
                                # Fallback for unrecognized format
                                log_entry = LogEntry(
                                    timestamp=datetime.utcnow(),
                                    level=LogLevelEnum.INFO,
                                    source="unknown",
                                    run_id=None,
                                    message=line,
                                    extra=None
                                )
                                log_entries.append(log_entry)
                        except Exception:
                            # Final fallback for any parsing errors
                            log_entry = LogEntry(
                                timestamp=datetime.utcnow(),
                                level=LogLevelEnum.INFO,
                                source="unknown",
                                run_id=None,
                                message=line,
                                extra=None
                            )
                            log_entries.append(log_entry)
                    
                    except Exception as e:
                        # Handle any other parsing errors
                        logger.warning(f"Failed to process log line {line_number}: {e}")
                        continue
                        
        except FileNotFoundError:
            logger.warning(f"Log file not found: {log_file_path}")
        except PermissionError:
            logger.error(f"Permission denied reading log file: {log_file_path}")
        except OSError as e:
            logger.error(f"OS error reading log file {log_file_path}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error reading log file {log_file_path}: {e}")
        
        return log_entries
    
    def _get_buffered_logs(self, run_id: str, level_filter: Optional[str] = None) -> List[LogEntry]:
        """
        Get buffered log entries for an active run.
        
        This is a placeholder implementation. In a real system, this would
        access in-memory log buffers or recent log entries that haven't
        been written to disk yet.
        
        Args:
            run_id: Unique identifier for the training run
            level_filter: Minimum log level to include (optional)
            
        Returns:
            List of LogEntry objects from memory buffers
        """
        # Placeholder implementation - in a real system this would access
        # in-memory log handlers or buffers for the active run
        buffered_logs = []
        
        # For now, return empty list since we don't have actual buffered logs
        # This would be implemented when integrating with the actual FL server
        # that maintains in-memory log buffers
        
        return buffered_logs