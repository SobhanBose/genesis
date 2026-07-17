"""
Simplified strategy factory for creating Flower built-in federated learning strategies.

This module provides a factory pattern for creating lightweight wrapper classes
around Flower's built-in strategies (FedAvg, FedProx, FedAdam) with comprehensive
logging, parameter validation, and centralized server parameter initialization.

## Server Parameter Initialization

All strategies now use centralized server parameter initialization to ensure consistent
starting conditions across all clients. The parameter initialization flow:

1. **Server Model Initialization**: Server initializes the global model using existing methods
2. **Parameter Extraction**: Server extracts model parameters as numpy arrays from PyTorch state_dict
3. **Parameter Validation**: Comprehensive validation of parameter shapes, formats, and values
4. **Parameter Conversion**: Parameters converted to Flower's Parameters format using ndarrays_to_parameters()
5. **Strategy Creation**: All strategies receive initial_parameters in their constructor
6. **Automatic Distribution**: Flower framework automatically distributes initial parameters to clients
7. **Client Parameter Loading**: Clients receive and load parameters before starting local training

## Enhanced Validation

The system includes comprehensive parameter validation at multiple levels:
- Server model validation (existence, initialization, accessibility)
- Individual parameter tensor validation (shape, size, device accessibility)
- Parameter array validation (data types, value ranges, problematic values)
- Parameter collection validation (consistency, total size limits)
- Flower Parameters validation (format compatibility, round-trip conversion)

## Error Handling

Robust error handling ensures system stability:
- Graceful fallback to dummy parameters when server model is unavailable
- Comprehensive logging for debugging and monitoring
- Safe handling of servers without loggers
- Clear error messages for common failure scenarios
"""

from typing import Dict, Any, List, Tuple, Optional
import flwr as fl
from flwr.server.strategy import FedAvg, FedProx, FedAdam
from flwr.common import Metrics, Parameters
from flwr.server.client_proxy import ClientProxy
from flwr.server.client_manager import ClientManager


class SimpleFedAvgStrategy(FedAvg):
    """
    Lightweight wrapper around Flower's FedAvg strategy with comprehensive logging
    and centralized server parameter initialization.
    
    This strategy implements Federated Averaging (FedAvg) with server-initialized parameters
    to ensure all clients start with identical model weights. The strategy automatically
    extracts parameters from the server's global model and distributes them to clients
    using Flower's built-in parameter distribution mechanism.
    
    Key Features:
    - Server-initialized parameters for consistent client starting conditions
    - Comprehensive logging of training and evaluation metrics
    - Automatic client sampling and configuration
    - Weighted metric aggregation across clients
    - Centralized evaluation on server validation set
    
    Args:
        server: The federated server instance with initialized global model
        initial_parameters: Optional pre-extracted parameters (auto-extracted if None)
        **kwargs: Additional arguments passed to parent FedAvg strategy
    """
    
    def __init__(self, server, initial_parameters=None, **kwargs):
        # Set up common callbacks for comprehensive logging and evaluation
        kwargs['evaluate_fn'] = self.evaluate_fn
        kwargs['on_fit_config_fn'] = self.on_fit_config_fn
        kwargs['fit_metrics_aggregation_fn'] = self.weighted_average_metrics
        kwargs['evaluate_metrics_aggregation_fn'] = self.weighted_average_metrics
        
        # Extract initial parameters from server model if not provided
        # This ensures all clients start with identical model weights from the server
        if initial_parameters is None:
            if hasattr(server, 'logger'):
                server.logger.log_info("FedAvg: Extracting initial parameters from server model")
            initial_parameters = StrategyFactory._extract_server_parameters(server)
        
        # Pass initial_parameters to parent FedAvg class for automatic distribution to clients
        # Flower will handle the parameter distribution during client initialization
        super().__init__(initial_parameters=initial_parameters, **kwargs)
        self.server = server
        
        # Log successful strategy initialization
        if hasattr(server, 'logger'):
            server.logger.log_info("FedAvg strategy initialized with server parameter initialization")
        
    def on_fit_config_fn(self, server_round: int) -> Dict[str, Any]:
        """Generate configuration for client training."""
        return {
            "learning_rate": self.server.get_learning_rate(server_round),
            "epochs": int(self.server.federated_config['client']['local_epochs']),
            "batch_size": int(self.server.model_config.get('training', {}).get('batch_size', 300)),
            "server_round": server_round,
            "strategy": "FedAvg",  # Pass strategy name to clients
        }
    
    def evaluate_fn(self, server_round: int, parameters: Parameters, config: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """Centralized evaluation with logging."""
        loss, metrics = self.server.evaluate_global_model(parameters)
        
        # Log centralized evaluation metrics from server validation set
        self.server.logger.log_info(
            f"Centralized evaluation (Round {server_round}): "
            f"Loss={loss:.4f}, Accuracy={metrics.get('accuracy', 0.0):.4f}"
        )
        return loss, {"accuracy": metrics.get("accuracy", 0.0), "loss": loss}
    
    def configure_fit(self, server_round: int, parameters: Parameters, client_manager: ClientManager):
        """Configure the next round of training with client sampling logging."""
        config = super().configure_fit(server_round, parameters, client_manager)
        
        # Log client sampling information
        sample_size = len(config)
        total_clients = len(client_manager.all())
        self.server.logger.log_info(
            f"Round {server_round}: Sampled {sample_size} clients out of {total_clients} available clients "
            f"(fraction_fit={self.fraction_fit:.2f})"
        )
        
        # Log which clients were sampled
        sampled_client_ids = [client_proxy.cid for client_proxy, _ in config]
        self.server.logger.log_info(f"Round {server_round}: Sampled clients: {sampled_client_ids}")
        
        return config
    
    def aggregate_fit(self, server_round: int, results: List[Tuple[ClientProxy, fl.common.FitRes]], failures: List[BaseException]):
        """Aggregate fit results with logging."""
        aggregated_parameters, aggregated_metrics = super().aggregate_fit(server_round, results, failures)
        
        # Log aggregated training metrics from clients
        if aggregated_metrics:
            metrics_str = ", ".join([f"{k}: {v:.4f}" for k, v in aggregated_metrics.items()])
            self.server.logger.log_info(f"Round {server_round}: Aggregated client training metrics - {metrics_str}")
        
        return aggregated_parameters, aggregated_metrics
    
    def configure_evaluate(self, server_round: int, parameters: Parameters, client_manager: ClientManager):
        """Configure client evaluation with logging."""
        config = super().configure_evaluate(server_round, parameters, client_manager)
        
        if config:
            sample_size = len(config)
            total_clients = len(client_manager.all())
            self.server.logger.log_info(
                f"Round {server_round}: Configured evaluation for {sample_size} clients out of {total_clients} available"
            )
        
        return config
    
    def aggregate_evaluate(self, server_round: int, results: List[Tuple[ClientProxy, fl.common.EvaluateRes]], failures: List[BaseException]):
        """Aggregate evaluation results with logging."""
        aggregated_loss, aggregated_metrics = super().aggregate_evaluate(server_round, results, failures)
        
        # Log aggregated client evaluation metrics
        if aggregated_metrics:
            client_metrics_str = ", ".join([f"{k}: {v:.4f}" for k, v in aggregated_metrics.items()])
            self.server.logger.log_info(f"Round {server_round}: Aggregated client evaluation metrics - {client_metrics_str}")
        
        return aggregated_loss, aggregated_metrics
    
    def weighted_average_metrics(self, metrics: List[Tuple[int, Metrics]]) -> Metrics:
        """Compute weighted average of metrics."""
        if not metrics:
            return {}
        
        all_keys = set()
        for _, metric_dict in metrics:
            all_keys.update(metric_dict.keys())
        
        aggregated_metrics = {}
        for key in all_keys:
            weighted_sum = 0.0
            total_examples = 0
            
            for num_examples, metric_dict in metrics:
                if key in metric_dict:
                    weighted_sum += num_examples * float(metric_dict[key])
                    total_examples += num_examples
            
            if total_examples > 0:
                aggregated_metrics[key] = weighted_sum / total_examples
        
        return aggregated_metrics


class SimpleFedProxStrategy(FedProx):
    """
    Lightweight wrapper around Flower's FedProx strategy with comprehensive logging
    and centralized server parameter initialization.
    
    This strategy implements Federated Proximal (FedProx) with server-initialized parameters
    and proximal regularization. FedProx adds a proximal term to the local objective function
    to handle system and statistical heterogeneity in federated learning environments.
    
    Key Features:
    - Server-initialized parameters for consistent client starting conditions
    - Proximal regularization with configurable proximal_mu parameter
    - Comprehensive logging of training and evaluation metrics
    - Automatic client sampling and configuration with proximal_mu distribution
    - Weighted metric aggregation across clients
    - Centralized evaluation on server validation set
    
    Args:
        server: The federated server instance with initialized global model
        proximal_mu: Proximal regularization parameter (default: 0.01)
        initial_parameters: Optional pre-extracted parameters (auto-extracted if None)
        **kwargs: Additional arguments passed to parent FedProx strategy
    """
    
    def __init__(self, server, proximal_mu=0.01, initial_parameters=None, **kwargs):
        # Set up common callbacks for comprehensive logging and evaluation
        kwargs['evaluate_fn'] = self.evaluate_fn
        kwargs['on_fit_config_fn'] = self.on_fit_config_fn
        kwargs['fit_metrics_aggregation_fn'] = self.weighted_average_metrics
        kwargs['evaluate_metrics_aggregation_fn'] = self.weighted_average_metrics
        
        # Extract initial parameters from server model if not provided
        # This ensures all clients start with identical model weights from the server
        if initial_parameters is None:
            if hasattr(server, 'logger'):
                server.logger.log_info(f"FedProx: Extracting initial parameters from server model (proximal_mu={proximal_mu})")
            initial_parameters = StrategyFactory._extract_server_parameters(server)
        
        # Pass initial_parameters and proximal_mu to parent FedProx class
        # Flower will handle parameter distribution and proximal regularization
        super().__init__(proximal_mu=proximal_mu, initial_parameters=initial_parameters, **kwargs)
        self.server = server
        
        # Log successful strategy initialization with proximal parameter
        if hasattr(server, 'logger'):
            server.logger.log_info(f"FedProx strategy initialized with server parameter initialization and proximal_mu={proximal_mu}")
        
    def on_fit_config_fn(self, server_round: int) -> Dict[str, Any]:
        """Generate configuration for client training."""
        return {
            "learning_rate": self.server.get_learning_rate(server_round),
            "epochs": int(self.server.federated_config['client']['local_epochs']),
            "batch_size": int(self.server.model_config.get('training', {}).get('batch_size', 300)),
            "server_round": server_round,
            "strategy": "FedProx",  # Pass strategy name to clients
            "proximal_mu": float(self.proximal_mu),  # Pass proximal_mu to clients
        }
    
    def evaluate_fn(self, server_round: int, parameters: Parameters, config: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """Centralized evaluation with logging."""
        loss, metrics = self.server.evaluate_global_model(parameters)
        
        # Log centralized evaluation metrics from server validation set
        self.server.logger.log_info(
            f"Centralized evaluation (Round {server_round}): "
            f"Loss={loss:.4f}, Accuracy={metrics.get('accuracy', 0.0):.4f}"
        )
        return loss, {"accuracy": metrics.get("accuracy", 0.0), "loss": loss}
    
    def configure_fit(self, server_round: int, parameters: Parameters, client_manager: ClientManager):
        """Configure the next round of training with client sampling logging."""
        config = super().configure_fit(server_round, parameters, client_manager)
        
        # Log client sampling information
        sample_size = len(config)
        total_clients = len(client_manager.all())
        self.server.logger.log_info(
            f"Round {server_round}: Sampled {sample_size} clients out of {total_clients} available clients "
            f"(fraction_fit={self.fraction_fit:.2f})"
        )
        
        # Log which clients were sampled
        sampled_client_ids = [client_proxy.cid for client_proxy, _ in config]
        self.server.logger.log_info(f"Round {server_round}: Sampled clients: {sampled_client_ids}")
        
        return config
    
    def aggregate_fit(self, server_round: int, results: List[Tuple[ClientProxy, fl.common.FitRes]], failures: List[BaseException]):
        """Aggregate fit results with logging."""
        aggregated_parameters, aggregated_metrics = super().aggregate_fit(server_round, results, failures)
        
        # Log aggregated training metrics from clients
        if aggregated_metrics:
            metrics_str = ", ".join([f"{k}: {v:.4f}" for k, v in aggregated_metrics.items()])
            self.server.logger.log_info(f"Round {server_round}: Aggregated client training metrics - {metrics_str}")
        
        return aggregated_parameters, aggregated_metrics
    
    def configure_evaluate(self, server_round: int, parameters: Parameters, client_manager: ClientManager):
        """Configure client evaluation with logging."""
        config = super().configure_evaluate(server_round, parameters, client_manager)
        
        if config:
            sample_size = len(config)
            total_clients = len(client_manager.all())
            self.server.logger.log_info(
                f"Round {server_round}: Configured evaluation for {sample_size} clients out of {total_clients} available"
            )
        
        return config
    
    def aggregate_evaluate(self, server_round: int, results: List[Tuple[ClientProxy, fl.common.EvaluateRes]], failures: List[BaseException]):
        """Aggregate evaluation results with logging."""
        aggregated_loss, aggregated_metrics = super().aggregate_evaluate(server_round, results, failures)
        
        # Log aggregated client evaluation metrics
        if aggregated_metrics:
            client_metrics_str = ", ".join([f"{k}: {v:.4f}" for k, v in aggregated_metrics.items()])
            self.server.logger.log_info(f"Round {server_round}: Aggregated client evaluation metrics - {client_metrics_str}")
        
        return aggregated_loss, aggregated_metrics
    
    def weighted_average_metrics(self, metrics: List[Tuple[int, Metrics]]) -> Metrics:
        """Compute weighted average of metrics."""
        if not metrics:
            return {}
        
        all_keys = set()
        for _, metric_dict in metrics:
            all_keys.update(metric_dict.keys())
        
        aggregated_metrics = {}
        for key in all_keys:
            weighted_sum = 0.0
            total_examples = 0
            
            for num_examples, metric_dict in metrics:
                if key in metric_dict:
                    weighted_sum += num_examples * float(metric_dict[key])
                    total_examples += num_examples
            
            if total_examples > 0:
                aggregated_metrics[key] = weighted_sum / total_examples
        
        return aggregated_metrics


class SimpleFedAdamStrategy(FedAdam):
    """
    Lightweight wrapper around Flower's FedAdam strategy with comprehensive logging
    and centralized server parameter initialization.
    
    This strategy implements Federated Adam (FedAdam) with server-initialized parameters
    and adaptive server-side optimization. FedAdam applies adaptive optimization techniques
    (similar to Adam optimizer) at the server level for improved convergence in federated
    learning scenarios with heterogeneous data and clients.
    
    Key Features:
    - Server-initialized parameters for consistent client starting conditions
    - Adaptive server-side optimization with configurable Adam parameters
    - Comprehensive logging of training and evaluation metrics
    - Automatic client sampling and configuration
    - Weighted metric aggregation across clients
    - Centralized evaluation on server validation set
    
    Args:
        server: The federated server instance with initialized global model
        beta_1: First moment decay rate for Adam optimizer (default: 0.9)
        beta_2: Second moment decay rate for Adam optimizer (default: 0.999)
        eta: Server learning rate for Adam optimizer (default: 0.001)
        tau: Numerical stability parameter for Adam optimizer (default: 1e-7)
        initial_parameters: Optional pre-extracted parameters (auto-extracted if None)
        **kwargs: Additional arguments passed to parent FedAdam strategy
    """
    
    def __init__(self, server, beta_1=0.9, beta_2=0.999, eta=0.001, tau=1e-7, initial_parameters=None, **kwargs):
        # Set up common callbacks for comprehensive logging and evaluation
        kwargs['evaluate_fn'] = self.evaluate_fn
        kwargs['on_fit_config_fn'] = self.on_fit_config_fn
        kwargs['fit_metrics_aggregation_fn'] = self.weighted_average_metrics
        kwargs['evaluate_metrics_aggregation_fn'] = self.weighted_average_metrics
        
        # Extract initial parameters from server model if not provided
        # This ensures all clients start with identical model weights from the server
        if initial_parameters is None:
            if hasattr(server, 'logger'):
                server.logger.log_info(f"FedAdam: Extracting initial parameters from server model (beta_1={beta_1}, beta_2={beta_2}, eta={eta})")
            initial_parameters = StrategyFactory._extract_server_parameters(server)
        
        # Pass all parameters to parent FedAdam class for adaptive server-side optimization
        # Flower will handle parameter distribution and adaptive optimization
        super().__init__(
            beta_1=beta_1,
            beta_2=beta_2,
            eta=eta,
            tau=tau,
            initial_parameters=initial_parameters,
            **kwargs
        )
        self.server = server
        
        # Log successful strategy initialization with Adam parameters
        if hasattr(server, 'logger'):
            server.logger.log_info(f"FedAdam strategy initialized with server parameter initialization and Adam parameters (beta_1={beta_1}, beta_2={beta_2}, eta={eta}, tau={tau})")
        
    def on_fit_config_fn(self, server_round: int) -> Dict[str, Any]:
        """Generate configuration for client training."""
        return {
            "learning_rate": self.server.get_learning_rate(server_round),
            "epochs": int(self.server.federated_config['client']['local_epochs']),
            "batch_size": int(self.server.model_config.get('training', {}).get('batch_size', 300)),
            "server_round": server_round,
            "strategy": "FedAdam",  # Pass strategy name to clients
            # FedAdam doesn't need proximal_mu
        }
    
    def evaluate_fn(self, server_round: int, parameters: Parameters, config: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """Centralized evaluation with logging."""
        loss, metrics = self.server.evaluate_global_model(parameters)
        
        # Log centralized evaluation metrics from server validation set
        self.server.logger.log_info(
            f"Centralized evaluation (Round {server_round}): "
            f"Loss={loss:.4f}, Accuracy={metrics.get('accuracy', 0.0):.4f}"
        )
        return loss, {"accuracy": metrics.get("accuracy", 0.0), "loss": loss}
    
    def configure_fit(self, server_round: int, parameters: Parameters, client_manager: ClientManager):
        """Configure the next round of training with client sampling logging."""
        config = super().configure_fit(server_round, parameters, client_manager)
        
        # Log client sampling information
        sample_size = len(config)
        total_clients = len(client_manager.all())
        self.server.logger.log_info(
            f"Round {server_round}: Sampled {sample_size} clients out of {total_clients} available clients "
            f"(fraction_fit={self.fraction_fit:.2f})"
        )
        
        # Log which clients were sampled
        sampled_client_ids = [client_proxy.cid for client_proxy, _ in config]
        self.server.logger.log_info(f"Round {server_round}: Sampled clients: {sampled_client_ids}")
        
        return config
    
    def aggregate_fit(self, server_round: int, results: List[Tuple[ClientProxy, fl.common.FitRes]], failures: List[BaseException]):
        """Aggregate fit results with logging."""
        aggregated_parameters, aggregated_metrics = super().aggregate_fit(server_round, results, failures)
        
        # Log aggregated training metrics from clients
        if aggregated_metrics:
            metrics_str = ", ".join([f"{k}: {v:.4f}" for k, v in aggregated_metrics.items()])
            self.server.logger.log_info(f"Round {server_round}: Aggregated client training metrics - {metrics_str}")
        
        return aggregated_parameters, aggregated_metrics
    
    def configure_evaluate(self, server_round: int, parameters: Parameters, client_manager: ClientManager):
        """Configure client evaluation with logging."""
        config = super().configure_evaluate(server_round, parameters, client_manager)
        
        if config:
            sample_size = len(config)
            total_clients = len(client_manager.all())
            self.server.logger.log_info(
                f"Round {server_round}: Configured evaluation for {sample_size} clients out of {total_clients} available"
            )
        
        return config
    
    def aggregate_evaluate(self, server_round: int, results: List[Tuple[ClientProxy, fl.common.EvaluateRes]], failures: List[BaseException]):
        """Aggregate evaluation results with logging."""
        aggregated_loss, aggregated_metrics = super().aggregate_evaluate(server_round, results, failures)
        
        # Log aggregated client evaluation metrics
        if aggregated_metrics:
            client_metrics_str = ", ".join([f"{k}: {v:.4f}" for k, v in aggregated_metrics.items()])
            self.server.logger.log_info(f"Round {server_round}: Aggregated client evaluation metrics - {client_metrics_str}")
        
        return aggregated_loss, aggregated_metrics
    
    def weighted_average_metrics(self, metrics: List[Tuple[int, Metrics]]) -> Metrics:
        """Compute weighted average of metrics."""
        if not metrics:
            return {}
        
        all_keys = set()
        for _, metric_dict in metrics:
            all_keys.update(metric_dict.keys())
        
        aggregated_metrics = {}
        for key in all_keys:
            weighted_sum = 0.0
            total_examples = 0
            
            for num_examples, metric_dict in metrics:
                if key in metric_dict:
                    weighted_sum += num_examples * float(metric_dict[key])
                    total_examples += num_examples
            
            if total_examples > 0:
                aggregated_metrics[key] = weighted_sum / total_examples
        
        return aggregated_metrics


class StrategyFactory:
    """
    Factory class for creating simplified federated learning strategy instances with
    centralized server parameter initialization and comprehensive validation.
    
    This factory creates lightweight wrapper classes around Flower's built-in strategies
    (FedAvg, FedProx, FedAdam) with the following enhanced capabilities:
    
    ## Server Parameter Initialization
    All strategies are automatically configured with server-initialized parameters to ensure
    consistent starting conditions across all clients. The parameter initialization process:
    
    1. Extracts parameters from the server's initialized global model
    2. Validates parameter integrity and format compatibility
    3. Converts parameters to Flower's Parameters format
    4. Passes parameters to strategy constructors for automatic client distribution
    
    ## Comprehensive Validation
    Multi-level parameter validation ensures system robustness:
    - Server model validation (existence, initialization, accessibility)
    - Parameter tensor validation (shapes, sizes, device compatibility)
    - Parameter array validation (data types, value ranges, edge cases)
    - Parameter collection validation (consistency, size limits)
    - Flower Parameters validation (format compatibility, conversion integrity)
    
    ## Enhanced Error Handling
    Robust error handling with graceful degradation:
    - Automatic fallback to dummy parameters when server model is unavailable
    - Comprehensive logging for debugging and monitoring
    - Safe operation with servers that don't have loggers
    - Clear error messages for common failure scenarios
    
    ## Supported Strategies
    - **FedAvg**: Federated Averaging with server parameter initialization
    - **FedProx**: Federated Proximal with proximal regularization and server parameters
    - **FedAdam**: Federated Adam with adaptive optimization and server parameters
    
    ## Usage Example
    ```python
    # Create strategy through factory
    config = {
        'server': {
            'min_fit_clients': 2,
            'min_available_clients': 2
        },
        'strategy': {
            'fedavg': {}  # or 'fedprox': {'proximal_mu': 0.01} or 'fedadam': {...}
        }
    }
    strategy = StrategyFactory.create_strategy('FedAvg', config, server)
    ```
    """
    
    @staticmethod
    def _extract_server_parameters(server):
        """
        Extract parameters from server model and convert to Flower Parameters format.
        
        This is the core method for centralized server parameter initialization. It extracts
        model parameters from the server's initialized global model and converts them to
        Flower's Parameters format for automatic distribution to clients.
        
        ## Parameter Extraction Flow:
        1. **Server Model Validation**: Comprehensive validation of server model state
        2. **Parameter Extraction**: Extract state_dict from PyTorch model
        3. **Tensor Validation**: Validate each parameter tensor individually
        4. **Array Conversion**: Convert PyTorch tensors to numpy arrays
        5. **Array Validation**: Validate numpy arrays for problematic values
        6. **Collection Validation**: Validate the complete parameter collection
        7. **Flower Conversion**: Convert to Flower Parameters format
        8. **Final Validation**: Ensure Flower Parameters are valid and convertible
        
        ## Validation Levels:
        - **Model Level**: Server existence, model initialization, state_dict accessibility
        - **Tensor Level**: Shape validation, size limits, device accessibility
        - **Array Level**: Data type validation, value range checks, NaN/Inf detection
        - **Collection Level**: Consistency checks, total parameter limits
        - **Format Level**: Flower Parameters compatibility, round-trip conversion
        
        ## Error Handling:
        - Graceful fallback to dummy parameters for non-critical failures
        - Comprehensive logging for debugging and monitoring
        - Safe operation with servers that don't have loggers
        - Clear error messages with context for failures
        
        Args:
            server: The federated server instance with an initialized model
            
        Returns:
            fl.common.Parameters: Server model parameters in Flower format, ready for
                                 automatic distribution to clients by Flower framework
            
        Raises:
            ValueError: If server model extraction fails critically or parameters are
                       fundamentally invalid (rare due to graceful fallback mechanisms)
        """
        import flwr as fl
        import numpy as np
        
        try:
            # Comprehensive server model validation
            validation_result = StrategyFactory._validate_server_model_comprehensive(server)
            if not validation_result['is_valid']:
                if hasattr(server, 'logger'):
                    server.logger.log_warning(
                        f"Server model validation failed: {validation_result['error_message']}. "
                        "Using dummy parameters for strategy initialization."
                    )
                return StrategyFactory._create_dummy_parameters()
            
            # Extract parameters from server model state_dict
            try:
                model_state_dict = server.model.state_dict()
                server.logger.log_info(f"Extracting parameters from model with {len(model_state_dict)} layers")
                
                # Convert PyTorch tensors to numpy arrays with validation
                numpy_arrays = []
                parameter_stats = {
                    'total_parameters': 0,
                    'layer_count': 0,
                    'parameter_shapes': [],
                    'parameter_dtypes': set(),
                    'has_nan_values': False,
                    'has_inf_values': False
                }
                
                for param_name, param_tensor in model_state_dict.items():
                    try:
                        # Validate tensor before conversion
                        tensor_validation = StrategyFactory._validate_parameter_tensor(param_name, param_tensor)
                        if not tensor_validation['is_valid']:
                            if hasattr(server, 'logger'):
                                server.logger.log_error(
                                    f"Parameter tensor validation failed for '{param_name}': {tensor_validation['error_message']}"
                                )
                            raise ValueError(f"Invalid parameter tensor '{param_name}': {tensor_validation['error_message']}")
                        
                        # Convert to numpy with validation
                        numpy_array = param_tensor.cpu().numpy()
                        
                        # Validate numpy array
                        array_validation = StrategyFactory._validate_parameter_array(param_name, numpy_array)
                        if not array_validation['is_valid']:
                            if hasattr(server, 'logger'):
                                server.logger.log_error(
                                    f"Parameter array validation failed for '{param_name}': {array_validation['error_message']}"
                                )
                            raise ValueError(f"Invalid parameter array '{param_name}': {array_validation['error_message']}")
                        
                        numpy_arrays.append(numpy_array)
                        
                        # Collect statistics
                        parameter_stats['total_parameters'] += numpy_array.size
                        parameter_stats['layer_count'] += 1
                        parameter_stats['parameter_shapes'].append(numpy_array.shape)
                        parameter_stats['parameter_dtypes'].add(str(numpy_array.dtype))
                        parameter_stats['has_nan_values'] = parameter_stats['has_nan_values'] or np.isnan(numpy_array).any()
                        parameter_stats['has_inf_values'] = parameter_stats['has_inf_values'] or np.isinf(numpy_array).any()
                        
                    except Exception as e:
                        if hasattr(server, 'logger'):
                            server.logger.log_error(
                                f"Failed to convert parameter '{param_name}' to numpy: {e}"
                            )
                        raise ValueError(f"Parameter conversion failed for '{param_name}': {e}")
                
                # Validate extracted parameters
                if not numpy_arrays:
                    if hasattr(server, 'logger'):
                        server.logger.log_warning(
                            "No valid parameters extracted from server model. Using dummy parameters."
                        )
                    return StrategyFactory._create_dummy_parameters()
                
                # Log parameter statistics
                StrategyFactory._log_parameter_statistics(server, parameter_stats)
                
                # Validate parameter collection
                collection_validation = StrategyFactory._validate_parameter_collection(numpy_arrays)
                if not collection_validation['is_valid']:
                    if hasattr(server, 'logger'):
                        server.logger.log_error(
                            f"Parameter collection validation failed: {collection_validation['error_message']}"
                        )
                    raise ValueError(f"Invalid parameter collection: {collection_validation['error_message']}")
                
                # Convert numpy arrays to Flower Parameters format
                try:
                    parameters = fl.common.ndarrays_to_parameters(numpy_arrays)
                    
                    # Final validation of Flower Parameters
                    flower_validation = StrategyFactory._validate_flower_parameters(parameters)
                    if not flower_validation['is_valid']:
                        if hasattr(server, 'logger'):
                            server.logger.log_error(
                                f"Flower Parameters validation failed: {flower_validation['error_message']}"
                            )
                        raise ValueError(f"Invalid Flower Parameters: {flower_validation['error_message']}")
                    
                    if hasattr(server, 'logger'):
                        server.logger.log_info(
                            f"Successfully extracted and validated {len(numpy_arrays)} parameter tensors "
                            f"({parameter_stats['total_parameters']} total parameters) from server model"
                        )
                    return parameters
                    
                except Exception as e:
                    if hasattr(server, 'logger'):
                        server.logger.log_error(
                            f"Failed to convert numpy arrays to Flower Parameters: {e}"
                        )
                    raise ValueError(f"Flower Parameters conversion failed: {e}")
                    
            except Exception as e:
                if hasattr(server, 'logger'):
                    server.logger.log_error(
                        f"Failed to access server model state_dict: {e}"
                    )
                # Fall back to dummy parameters for graceful degradation
                if hasattr(server, 'logger'):
                    server.logger.log_warning(
                        "Falling back to dummy parameters due to model access failure"
                    )
                return StrategyFactory._create_dummy_parameters()
                
        except Exception as e:
            # Critical error - log and re-raise
            if hasattr(server, 'logger'):
                server.logger.log_error(
                    f"Critical failure in parameter extraction: {e}"
                )
            raise ValueError(f"Server parameter extraction failed: {e}")
    
    @staticmethod
    def _validate_server_model(server):
        """
        Validate that server has a properly initialized model.
        
        Args:
            server: The federated server instance
            
        Returns:
            bool: True if server model is valid, False otherwise
        """
        if not hasattr(server, 'model'):
            return False
        
        if server.model is None:
            return False
            
        try:
            # Check if model has parameters
            state_dict = server.model.state_dict()
            return len(state_dict) > 0
        except Exception:
            return False
    
    @staticmethod
    def _validate_server_model_comprehensive(server):
        """
        Comprehensive validation of server model with detailed error reporting.
        
        Args:
            server: The federated server instance
            
        Returns:
            dict: Validation result with 'is_valid' boolean and 'error_message' string
        """
        # Check server instance
        if server is None:
            return {'is_valid': False, 'error_message': 'Server instance is None'}
        
        # Check if server has model attribute
        if not hasattr(server, 'model'):
            return {'is_valid': False, 'error_message': 'Server does not have model attribute'}
        
        # Check if model is initialized
        if server.model is None:
            return {'is_valid': False, 'error_message': 'Server model is None (not initialized)'}
        
        try:
            # Check if model has state_dict method
            if not hasattr(server.model, 'state_dict'):
                return {'is_valid': False, 'error_message': 'Server model does not have state_dict method'}
            
            # Check if model has parameters
            state_dict = server.model.state_dict()
            if not state_dict:
                return {'is_valid': False, 'error_message': 'Server model state_dict is empty'}
            
            # Check if parameters are valid tensors
            invalid_params = []
            for param_name, param_tensor in state_dict.items():
                if param_tensor is None:
                    invalid_params.append(f"{param_name} is None")
                elif not hasattr(param_tensor, 'cpu'):
                    invalid_params.append(f"{param_name} is not a tensor")
                elif param_tensor.numel() == 0:
                    invalid_params.append(f"{param_name} is empty tensor")
            
            if invalid_params:
                return {'is_valid': False, 'error_message': f'Invalid parameters: {", ".join(invalid_params)}'}
            
            return {'is_valid': True, 'error_message': ''}
            
        except Exception as e:
            return {'is_valid': False, 'error_message': f'Exception during model validation: {e}'}
    
    @staticmethod
    def _validate_parameter_tensor(param_name, param_tensor):
        """
        Validate individual parameter tensor before conversion.
        
        Args:
            param_name: Name of the parameter
            param_tensor: PyTorch tensor to validate
            
        Returns:
            dict: Validation result with 'is_valid' boolean and 'error_message' string
        """
        try:
            # Check if tensor exists
            if param_tensor is None:
                return {'is_valid': False, 'error_message': 'Tensor is None'}
            
            # Check if tensor has required methods
            if not hasattr(param_tensor, 'cpu') or not hasattr(param_tensor, 'numpy'):
                return {'is_valid': False, 'error_message': 'Tensor does not have required methods (cpu, numpy)'}
            
            # Check tensor properties
            if param_tensor.numel() == 0:
                return {'is_valid': False, 'error_message': 'Tensor is empty (0 elements)'}
            
            # Check for reasonable tensor size (prevent memory issues)
            max_elements = 100_000_000  # 100M elements max
            if param_tensor.numel() > max_elements:
                return {'is_valid': False, 'error_message': f'Tensor too large ({param_tensor.numel()} > {max_elements} elements)'}
            
            # Check tensor device accessibility
            try:
                _ = param_tensor.cpu()
            except Exception as e:
                return {'is_valid': False, 'error_message': f'Cannot move tensor to CPU: {e}'}
            
            return {'is_valid': True, 'error_message': ''}
            
        except Exception as e:
            return {'is_valid': False, 'error_message': f'Exception during tensor validation: {e}'}
    
    @staticmethod
    def _validate_parameter_array(param_name, numpy_array):
        """
        Validate numpy array after conversion from tensor.
        
        Args:
            param_name: Name of the parameter
            numpy_array: Numpy array to validate
            
        Returns:
            dict: Validation result with 'is_valid' boolean and 'error_message' string
        """
        import numpy as np
        
        try:
            # Check if array exists
            if numpy_array is None:
                return {'is_valid': False, 'error_message': 'Array is None'}
            
            # Check if it's actually a numpy array
            if not isinstance(numpy_array, np.ndarray):
                return {'is_valid': False, 'error_message': f'Not a numpy array, got {type(numpy_array)}'}
            
            # Check array properties
            if numpy_array.size == 0:
                return {'is_valid': False, 'error_message': 'Array is empty'}
            
            # Check for valid data type
            if not np.issubdtype(numpy_array.dtype, np.number):
                return {'is_valid': False, 'error_message': f'Array has non-numeric dtype: {numpy_array.dtype}'}
            
            # Check for problematic values
            if np.isnan(numpy_array).all():
                return {'is_valid': False, 'error_message': 'Array contains only NaN values'}
            
            if np.isinf(numpy_array).all():
                return {'is_valid': False, 'error_message': 'Array contains only infinite values'}
            
            # Check for reasonable value ranges (prevent extreme values)
            if np.isfinite(numpy_array).any():  # Only check if there are finite values
                finite_values = numpy_array[np.isfinite(numpy_array)]
                max_abs_value = np.abs(finite_values).max()
                if max_abs_value > 1e10:
                    return {'is_valid': False, 'error_message': f'Array contains extremely large values (max: {max_abs_value})'}
            
            return {'is_valid': True, 'error_message': ''}
            
        except Exception as e:
            return {'is_valid': False, 'error_message': f'Exception during array validation: {e}'}
    
    @staticmethod
    def _validate_parameter_collection(numpy_arrays):
        """
        Validate collection of parameter arrays.
        
        Args:
            numpy_arrays: List of numpy arrays
            
        Returns:
            dict: Validation result with 'is_valid' boolean and 'error_message' string
        """
        import numpy as np
        
        try:
            # Check if collection exists
            if numpy_arrays is None:
                return {'is_valid': False, 'error_message': 'Parameter collection is None'}
            
            # Check if collection is a list
            if not isinstance(numpy_arrays, list):
                return {'is_valid': False, 'error_message': f'Parameter collection is not a list, got {type(numpy_arrays)}'}
            
            # Check if collection is empty
            if len(numpy_arrays) == 0:
                return {'is_valid': False, 'error_message': 'Parameter collection is empty'}
            
            # Check total parameter count
            total_params = sum(arr.size for arr in numpy_arrays)
            if total_params == 0:
                return {'is_valid': False, 'error_message': 'Total parameter count is zero'}
            
            # Check for reasonable total size
            max_total_params = 1_000_000_000  # 1B parameters max
            if total_params > max_total_params:
                return {'is_valid': False, 'error_message': f'Too many total parameters ({total_params} > {max_total_params})'}
            
            # Check data type consistency
            dtypes = set(arr.dtype for arr in numpy_arrays)
            if len(dtypes) > 3:  # Allow some variation but not too much
                return {'is_valid': False, 'error_message': f'Too many different data types: {dtypes}'}
            
            return {'is_valid': True, 'error_message': ''}
            
        except Exception as e:
            return {'is_valid': False, 'error_message': f'Exception during collection validation: {e}'}
    
    @staticmethod
    def _validate_flower_parameters(parameters):
        """
        Validate Flower Parameters object.
        
        Args:
            parameters: Flower Parameters object
            
        Returns:
            dict: Validation result with 'is_valid' boolean and 'error_message' string
        """
        import flwr as fl
        
        try:
            # Check if parameters exist
            if parameters is None:
                return {'is_valid': False, 'error_message': 'Flower Parameters is None'}
            
            # Check if it's the correct type
            if not isinstance(parameters, fl.common.Parameters):
                return {'is_valid': False, 'error_message': f'Not a Flower Parameters object, got {type(parameters)}'}
            
            # Check if parameters can be converted back to arrays
            try:
                arrays = fl.common.parameters_to_ndarrays(parameters)
                if not arrays:
                    return {'is_valid': False, 'error_message': 'Flower Parameters converts to empty array list'}
            except Exception as e:
                return {'is_valid': False, 'error_message': f'Cannot convert Flower Parameters back to arrays: {e}'}
            
            return {'is_valid': True, 'error_message': ''}
            
        except Exception as e:
            return {'is_valid': False, 'error_message': f'Exception during Flower Parameters validation: {e}'}
    
    @staticmethod
    def _create_dummy_parameters():
        """
        Create minimal dummy parameters for graceful fallback.
        
        Returns:
            fl.common.Parameters: Minimal dummy parameters
        """
        import flwr as fl
        import numpy as np
        
        # Create a minimal dummy parameter that won't cause framework errors
        dummy_array = np.array([0.0], dtype=np.float32)
        return fl.common.ndarrays_to_parameters([dummy_array])
    
    @staticmethod
    def _log_parameter_statistics(server, parameter_stats):
        """
        Log detailed parameter statistics for debugging and monitoring.
        
        Args:
            server: The federated server instance
            parameter_stats: Dictionary containing parameter statistics
        """
        if not hasattr(server, 'logger'):
            return
        
        try:
            # Log basic statistics
            server.logger.log_info(
                f"Parameter extraction statistics: "
                f"{parameter_stats['layer_count']} layers, "
                f"{parameter_stats['total_parameters']} total parameters"
            )
            
            # Log data types
            dtypes_str = ", ".join(sorted(parameter_stats['parameter_dtypes']))
            server.logger.log_info(f"Parameter data types: {dtypes_str}")
            
            # Log shape information (first few shapes)
            shapes_to_log = parameter_stats['parameter_shapes'][:5]  # First 5 shapes
            shapes_str = ", ".join(str(shape) for shape in shapes_to_log)
            if len(parameter_stats['parameter_shapes']) > 5:
                shapes_str += f" ... ({len(parameter_stats['parameter_shapes']) - 5} more)"
            server.logger.log_info(f"Parameter shapes: {shapes_str}")
            
            # Log warnings for problematic values
            if parameter_stats['has_nan_values']:
                server.logger.log_warning("Some parameters contain NaN values")
            
            if parameter_stats['has_inf_values']:
                server.logger.log_warning("Some parameters contain infinite values")
                
        except Exception as e:
            if hasattr(server, 'logger'):
                server.logger.log_error(f"Failed to log parameter statistics: {e}")
    
    @staticmethod
    def create_strategy(strategy_name: str, config: dict, server) -> fl.server.strategy.Strategy:
        """
        Create strategy instance based on configuration with server parameter initialization.
        
        All strategies now use server-initialized parameters to ensure consistent starting
        conditions across all clients. The server model parameters are automatically
        extracted and distributed to clients using Flower's built-in mechanisms.
        
        Args:
            strategy_name: Name of the strategy to create ('FedAvg', 'FedProx', 'FedAdam')
            config: Configuration dictionary containing strategy parameters (supports both new and legacy formats)
            server: The federated server instance with initialized model
            
        Returns:
            Strategy instance (SimpleFedAvgStrategy, SimpleFedProxStrategy, or SimpleFedAdamStrategy)
            
        Raises:
            ValueError: If strategy name is unknown, configuration is invalid, or strategy creation fails
        """
        try:
            strategy_name_lower = strategy_name.lower()
            
            # Validate strategy name early
            if not StrategyFactory.is_strategy_available(strategy_name):
                available_strategies = ", ".join(StrategyFactory.get_available_strategies())
                raise ValueError(f"Unknown strategy '{strategy_name}'. Supported strategies: {available_strategies}")
            
            # Validate server instance
            if server is None:
                raise ValueError("Server instance cannot be None")
            
            # Log server model validation status and parameter initialization approach
            if hasattr(server, 'logger'):
                model_valid = StrategyFactory._validate_server_model(server)
                if model_valid:
                    server.logger.log_info(f"Creating {strategy_name} strategy with server-initialized parameters")
                    server.logger.log_info("Server parameter initialization: All clients will receive identical starting parameters")
                else:
                    server.logger.log_warning(f"Creating {strategy_name} strategy with server model not fully initialized")
                    server.logger.log_warning("Server parameter initialization: Will use dummy parameters as fallback")
            
            # Handle both new and legacy configuration formats
            if 'server' in config and isinstance(config['server'], dict):
                # New format or legacy format
                server_config = config['server']
            else:
                # Fallback: assume config is the server section itself
                server_config = config
            
            # Validate required configuration parameters
            required_params = ['min_fit_clients', 'min_available_clients']
            for param in required_params:
                if param not in server_config:
                    raise ValueError(f"Missing required server configuration parameter: {param}")
            
            # Common parameters for all strategies
            common_params = {
                'min_fit_clients': server_config['min_fit_clients'],
                'min_evaluate_clients': server_config.get('min_eval_clients', server_config['min_fit_clients']),
                'min_available_clients': server_config['min_available_clients'],
                'fraction_fit': server_config.get('fraction_fit', 1.0),
                'fraction_evaluate': server_config.get('fraction_evaluate', 1.0),
            }
            
            # Create strategy instance with error handling
            if strategy_name_lower == 'fedavg':
                try:
                    strategy = SimpleFedAvgStrategy(server=server, **common_params)
                    if hasattr(server, 'logger'):
                        server.logger.log_info("Successfully created FedAvg strategy with server parameter initialization")
                    return strategy
                except Exception as e:
                    raise ValueError(f"Failed to create FedAvg strategy: {e}")
                
            elif strategy_name_lower == 'fedprox':
                try:
                    # Get proximal_mu from strategy-specific config
                    proximal_mu = StrategyFactory._get_strategy_param(config, 'fedprox', 'proximal_mu', 0.01)
                    
                    # Validate proximal_mu parameter
                    if not isinstance(proximal_mu, (int, float)) or proximal_mu < 0:
                        raise ValueError(f"FedProx proximal_mu must be a non-negative number, got {proximal_mu}")
                    
                    strategy = SimpleFedProxStrategy(
                        server=server,
                        proximal_mu=proximal_mu,
                        **common_params
                    )
                    if hasattr(server, 'logger'):
                        server.logger.log_info(f"Successfully created FedProx strategy with proximal_mu={proximal_mu} and server parameter initialization")
                    return strategy
                except Exception as e:
                    raise ValueError(f"Failed to create FedProx strategy: {e}")
                
            elif strategy_name_lower == 'fedadam':
                try:
                    # Get FedAdam parameters with defaults and convert strings to floats
                    beta_1 = StrategyFactory._get_strategy_param(config, 'fedadam', 'beta1', 0.9)
                    beta_2 = StrategyFactory._get_strategy_param(config, 'fedadam', 'beta2', 0.999)
                    eta = StrategyFactory._get_strategy_param(config, 'fedadam', 'server_lr', 0.001)  # eta is server learning rate in Flower
                    tau = StrategyFactory._get_strategy_param(config, 'fedadam', 'epsilon', 1e-7)     # tau is epsilon in Flower
                    
                    # Convert string values to floats if needed
                    if isinstance(beta_1, str):
                        beta_1 = float(beta_1)
                    if isinstance(beta_2, str):
                        beta_2 = float(beta_2)
                    if isinstance(eta, str):
                        eta = float(eta)
                    if isinstance(tau, str):
                        tau = float(tau)
                    
                    # Validate FedAdam parameters
                    StrategyFactory._validate_fedadam_params(beta_1, beta_2, eta, tau)
                    
                    strategy = SimpleFedAdamStrategy(
                        server=server,
                        beta_1=beta_1,
                        beta_2=beta_2,
                        eta=eta,
                        tau=tau,
                        **common_params
                    )
                    if hasattr(server, 'logger'):
                        server.logger.log_info(f"Successfully created FedAdam strategy with server parameter initialization")
                    return strategy
                except Exception as e:
                    raise ValueError(f"Failed to create FedAdam strategy: {e}")
            
        except ValueError:
            # Re-raise ValueError with original message
            raise
        except Exception as e:
            # Catch any unexpected errors and wrap them
            error_msg = f"Unexpected error creating {strategy_name} strategy: {e}"
            if hasattr(server, 'logger'):
                server.logger.log_error(error_msg)
            raise ValueError(error_msg)
    
    @staticmethod
    def _get_strategy_param(config: dict, strategy_name: str, param_name: str, default_value):
        """
        Get strategy parameter from configuration, supporting both new and legacy formats.
        
        Args:
            config: Configuration dictionary
            strategy_name: Name of the strategy (e.g., 'fedprox', 'fedadam')
            param_name: Name of the parameter to retrieve
            default_value: Default value if parameter is not found
            
        Returns:
            Parameter value or default value
        """
        strategy_name_lower = strategy_name.lower()
        
        # Check new format first: config['strategy'][strategy_name][param_name]
        if 'strategy' in config and isinstance(config['strategy'], dict):
            strategy_section = config['strategy']
            if strategy_name_lower in strategy_section and isinstance(strategy_section[strategy_name_lower], dict):
                strategy_params = strategy_section[strategy_name_lower]
                if param_name in strategy_params:
                    return strategy_params[param_name]
        
        # Check legacy format: config['strategies'][strategy_name][param_name]
        if 'strategies' in config and isinstance(config['strategies'], dict):
            strategies_section = config['strategies']
            if strategy_name_lower in strategies_section and isinstance(strategies_section[strategy_name_lower], dict):
                strategy_params = strategies_section[strategy_name_lower]
                if param_name in strategy_params:
                    return strategy_params[param_name]
        
        # For FedProx backward compatibility, check top-level proximal_mu
        if strategy_name_lower == 'fedprox' and param_name == 'proximal_mu' and 'proximal_mu' in config:
            return config['proximal_mu']
        
        return default_value
    
    @staticmethod
    def _validate_fedadam_params(beta_1: float, beta_2: float, eta: float, tau: float):
        """
        Validate FedAdam parameters.
        
        Args:
            beta_1: First moment decay rate
            beta_2: Second moment decay rate  
            eta: Server learning rate
            tau: Numerical stability parameter
            
        Raises:
            ValueError: If any parameter is outside valid range
        """
        # Convert string values if needed
        if isinstance(beta_1, str):
            beta_1 = float(beta_1)
        if isinstance(beta_2, str):
            beta_2 = float(beta_2)
        if isinstance(eta, str):
            eta = float(eta)
        if isinstance(tau, str):
            tau = float(tau)
            
        if not 0 <= beta_1 < 1:
            raise ValueError(f"FedAdam beta1 must be in [0,1), got {beta_1}")
        if not 0 <= beta_2 < 1:
            raise ValueError(f"FedAdam beta2 must be in [0,1), got {beta_2}")
        if eta <= 0:
            raise ValueError(f"FedAdam eta (server_lr) must be positive, got {eta}")
        if tau <= 0:
            raise ValueError(f"FedAdam tau (epsilon) must be positive, got {tau}")
    
    @staticmethod
    def get_available_strategies() -> List[str]:
        """
        Get list of available strategy names.
        
        Returns:
            List of available strategy names
        """
        return ['FedAvg', 'FedProx', 'FedAdam']
    
    @staticmethod
    def is_strategy_available(strategy_name: str) -> bool:
        """
        Check if a strategy is available.
        
        Args:
            strategy_name: Name of the strategy to check
            
        Returns:
            True if strategy is available, False otherwise
        """
        return strategy_name.lower() in ['fedavg', 'fedprox', 'fedadam']