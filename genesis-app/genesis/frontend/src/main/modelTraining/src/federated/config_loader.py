"""
Configuration loader for federated learning with support for new modular structure.

This module provides utilities for loading and validating federated learning
configurations. It supports both the new modular structure (separate server/client
configs) and backward compatibility with the old monolithic structure.
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union


class ConfigLoader:
    """Configuration loader for federated learning with modular structure support."""
    
    @staticmethod
    def load_server_config(path: str = "configs/server_config.yaml") -> Dict[str, Any]:
        """
        Load server configuration from YAML file.
        
        Args:
            path: Path to the server configuration file
            
        Returns:
            Dictionary containing server configuration
            
        Raises:
            FileNotFoundError: If configuration file doesn't exist
            ValueError: If configuration is invalid
        """
        config_path = Path(path)
        if not config_path.exists():
            raise FileNotFoundError(f"Server configuration file not found: {path}")
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Validate server configuration structure
        ConfigLoader._validate_server_config(config)
        
        return config
    
    @staticmethod
    def load_client_config(path: str = "configs/client_config.yaml") -> Dict[str, Any]:
        """
        Load client configuration from YAML file.
        
        Args:
            path: Path to the client configuration file
            
        Returns:
            Dictionary containing client configuration
            
        Raises:
            FileNotFoundError: If configuration file doesn't exist
            ValueError: If configuration is invalid
        """
        config_path = Path(path)
        if not config_path.exists():
            raise FileNotFoundError(f"Client configuration file not found: {path}")
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Validate client configuration structure
        ConfigLoader._validate_client_config(config)
        
        return config
    
    @staticmethod
    def load_federated_config(path: str) -> Dict[str, Any]:
        """
        Load federated configuration from YAML file (backward compatibility).
        
        This method maintains backward compatibility with the old monolithic
        configuration structure while detecting and providing migration guidance.
        
        Args:
            path: Path to the federated configuration file
            
        Returns:
            Dictionary containing federated configuration
            
        Raises:
            FileNotFoundError: If configuration file doesn't exist
            ValueError: If configuration is invalid
        """
        config_path = Path(path)
        if not config_path.exists():
            # Check if this is an attempt to load old config format
            if "federated_config" in str(path):
                ConfigLoader._provide_migration_guidance(path)
            raise FileNotFoundError(f"Configuration file not found: {path}")
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Check if this is the old format
        if 'federated' in config:
            logging.warning(
                f"Loading legacy federated configuration format from {path}. "
                "Consider migrating to the new modular structure with separate "
                "server_config.yaml and client_config.yaml files."
            )
            federated_config = config['federated']
            ConfigLoader._validate_legacy_config(federated_config)
            return federated_config
        else:
            # This might be a new format file loaded incorrectly
            raise ValueError(
                f"Configuration file {path} does not contain 'federated' section. "
                "If using the new modular structure, use load_server_config() or "
                "load_client_config() instead."
            )
    
    @staticmethod
    def get_strategy_config(config: Dict[str, Any], strategy_name: str) -> Dict[str, Any]:
        """
        Extract strategy-specific configuration.
        
        Args:
            config: Full configuration (server config or legacy federated config)
            strategy_name: Name of the strategy
            
        Returns:
            Strategy-specific configuration dictionary
        """
        strategy_name_lower = strategy_name.lower()
        
        # Check if this is new format (server config)
        if 'strategy' in config and isinstance(config['strategy'], dict):
            strategy_section = config['strategy']
            if strategy_name_lower in strategy_section:
                return strategy_section[strategy_name_lower]
            else:
                return {}
        
        # Legacy format handling
        # Get strategy-specific config from strategies section
        strategies_config = config.get('strategies', {})
        strategy_config = strategies_config.get(strategy_name_lower, {})
        
        # For backward compatibility, check for top-level proximal_mu
        if strategy_name_lower == 'fedprox' and 'proximal_mu' not in strategy_config:
            if 'proximal_mu' in config:
                strategy_config['proximal_mu'] = config['proximal_mu']
        
        return strategy_config
    
    @staticmethod
    def get_strategy_name(config: Dict[str, Any]) -> str:
        """
        Get strategy name from configuration with backward compatibility.
        
        Args:
            config: Configuration dictionary (server config or legacy federated config)
            
        Returns:
            Strategy name (defaults to 'FedProx' for backward compatibility)
        """
        # Check for new format (server config)
        if 'strategy' in config and isinstance(config['strategy'], dict):
            strategy_section = config['strategy']
            if 'name' in strategy_section:
                strategy_name = strategy_section['name'].lower()
                # Normalize to proper case
                if strategy_name == 'fedavg':
                    return 'FedAvg'
                elif strategy_name == 'fedprox':
                    return 'FedProx'
                elif strategy_name == 'fedadam':
                    return 'FedAdam'
                else:
                    # Return original if not recognized (will be caught by validation)
                    return strategy_section['name']
        
        # Legacy format handling
        # Check for explicit strategy field
        if 'strategy' in config and isinstance(config['strategy'], str):
            strategy_name = config['strategy'].lower()
            # Normalize to proper case
            if strategy_name == 'fedavg':
                return 'FedAvg'
            elif strategy_name == 'fedprox':
                return 'FedProx'
            elif strategy_name == 'fedadam':
                return 'FedAdam'
            else:
                # Return original if not recognized (will be caught by validation)
                return config['strategy']
        
        # Backward compatibility: default to FedProx if proximal_mu is present
        if 'proximal_mu' in config or ('strategies' in config and 'fedprox' in config['strategies']):
            return 'FedProx'
        
        # Default to FedProx for backward compatibility
        return 'FedProx'
    
    @staticmethod
    def _validate_server_config(config: Dict[str, Any]):
        """
        Validate server configuration structure.
        
        Args:
            config: Server configuration to validate
            
        Raises:
            ValueError: If configuration is invalid
        """
        # Check required sections
        if 'server' not in config:
            raise ValueError("Server configuration must contain 'server' section")
        
        if 'strategy' not in config:
            raise ValueError("Server configuration must contain 'strategy' section")
        
        # Validate server parameters
        server_config = config['server']
        required_server_fields = ['rounds', 'min_fit_clients', 'min_available_clients', 
                                'fraction_fit', 'fraction_evaluate']
        for field in required_server_fields:
            if field not in server_config:
                raise ValueError(f"Server configuration must contain '{field}' field")
        
        # Validate strategy configuration
        strategy_config = config['strategy']
        if 'name' not in strategy_config:
            raise ValueError("Strategy configuration must contain 'name' field")
        
        strategy_name = strategy_config['name']
        ConfigLoader._validate_strategy_name(strategy_name)
        
        # Validate strategy-specific parameters
        ConfigLoader._validate_new_strategy_config(strategy_config, strategy_name)
    
    @staticmethod
    def _validate_client_config(config: Dict[str, Any]):
        """
        Validate client configuration structure.
        
        Args:
            config: Client configuration to validate
            
        Raises:
            ValueError: If configuration is invalid
        """
        # Check required sections
        if 'client' not in config:
            raise ValueError("Client configuration must contain 'client' section")
        
        # Validate client parameters
        client_config = config['client']
        required_client_fields = ['local_epochs', 'batch_size']
        for field in required_client_fields:
            if field not in client_config:
                raise ValueError(f"Client configuration must contain '{field}' field")
        
        # Validate optimizer configuration if present
        if 'optimizer' in client_config:
            optimizer_config = client_config['optimizer']
            if 'name' not in optimizer_config:
                raise ValueError("Optimizer configuration must contain 'name' field")
            if 'learning_rate' not in optimizer_config:
                raise ValueError("Optimizer configuration must contain 'learning_rate' field")
    
    @staticmethod
    def _validate_legacy_config(config: Dict[str, Any]):
        """
        Validate legacy federated configuration structure.
        
        Args:
            config: Legacy federated configuration to validate
            
        Raises:
            ValueError: If configuration is invalid
        """
        # Check required sections
        required_sections = ['server', 'client']
        for section in required_sections:
            if section not in config:
                raise ValueError(f"Configuration must contain '{section}' section")
        
        # Validate server configuration
        server_config = config['server']
        required_server_fields = ['rounds', 'min_fit_clients', 'min_available_clients']
        for field in required_server_fields:
            if field not in server_config:
                raise ValueError(f"Server configuration must contain '{field}' field")
        
        # Validate client configuration
        client_config = config['client']
        required_client_fields = ['local_epochs']
        for field in required_client_fields:
            if field not in client_config:
                raise ValueError(f"Client configuration must contain '{field}' field")
        
        # Validate strategy name if present
        if 'strategy' in config:
            ConfigLoader._validate_strategy_name(config['strategy'])
        
        # Validate strategy configuration if present
        if 'strategies' in config:
            ConfigLoader._validate_strategy_configs(config['strategies'])
    
    @staticmethod
    def _validate_strategy_name(strategy_name: str):
        """
        Validate strategy name.
        
        Args:
            strategy_name: Name of the strategy to validate
            
        Raises:
            ValueError: If strategy name is not supported
        """
        supported_strategies = ['fedavg', 'fedprox', 'fedadam']
        if strategy_name.lower() not in supported_strategies:
            raise ValueError(f"Unknown strategy '{strategy_name}'. Supported: FedAvg, FedProx, FedAdam")
    
    @staticmethod
    def _validate_strategy_configs(strategies_config: Dict[str, Any]):
        """
        Validate strategy-specific configurations (legacy format).
        
        Args:
            strategies_config: Dictionary of strategy configurations
            
        Raises:
            ValueError: If any strategy configuration is invalid
        """
        for strategy_name, strategy_config in strategies_config.items():
            if strategy_name == 'fedprox':
                ConfigLoader._validate_fedprox_config(strategy_config)
            elif strategy_name == 'fedadam':
                ConfigLoader._validate_fedadam_config(strategy_config)
            elif strategy_name == 'fedavg':
                # FedAvg has no specific parameters to validate
                pass
            else:
                raise ValueError(f"Unknown strategy in configuration: {strategy_name}")
    
    @staticmethod
    def _validate_new_strategy_config(strategy_config: Dict[str, Any], strategy_name: str):
        """
        Validate strategy-specific configurations (new format).
        
        Args:
            strategy_config: Strategy configuration dictionary
            strategy_name: Name of the strategy
            
        Raises:
            ValueError: If strategy configuration is invalid
        """
        strategy_name_lower = strategy_name.lower()
        
        if strategy_name_lower == 'fedprox':
            if 'fedprox' in strategy_config:
                ConfigLoader._validate_fedprox_config(strategy_config['fedprox'])
        elif strategy_name_lower == 'fedadam':
            if 'fedadam' in strategy_config:
                ConfigLoader._validate_fedadam_config(strategy_config['fedadam'])
        elif strategy_name_lower == 'fedavg':
            # FedAvg has no specific parameters to validate
            pass
        else:
            raise ValueError(f"Unknown strategy: {strategy_name}")
    
    @staticmethod
    def _provide_migration_guidance(old_path: str):
        """
        Provide guidance for migrating from old to new configuration format.
        
        Args:
            old_path: Path to the old configuration file that wasn't found
        """
        logging.error(f"Configuration file not found: {old_path}")
        logging.info("=" * 60)
        logging.info("CONFIGURATION MIGRATION GUIDANCE")
        logging.info("=" * 60)
        logging.info("The federated learning configuration system has been updated.")
        logging.info("The old monolithic 'federated_config.yaml' has been replaced with:")
        logging.info("  - configs/server_config.yaml (server-side parameters)")
        logging.info("  - configs/client_config.yaml (client-side parameters)")
        logging.info("")
        logging.info("To migrate your configuration:")
        logging.info("1. Check if backup/configs/federated_config.yaml exists")
        logging.info("2. Use the new server_config.yaml and client_config.yaml templates")
        logging.info("3. Copy your parameters to the appropriate new files")
        logging.info("4. Update your code to use load_server_config() and load_client_config()")
        logging.info("")
        logging.info("For detailed migration instructions, see the migration guide.")
        logging.info("=" * 60)
    
    @staticmethod
    def _validate_fedprox_config(config: Dict[str, Any]):
        """
        Validate FedProx strategy configuration.
        
        Args:
            config: FedProx configuration
            
        Raises:
            ValueError: If configuration is invalid
        """
        if 'proximal_mu' in config:
            proximal_mu = config['proximal_mu']
            if not isinstance(proximal_mu, (int, float)) or proximal_mu < 0:
                raise ValueError(f"FedProx proximal_mu must be non-negative number, got {proximal_mu}")
    
    @staticmethod
    def _validate_fedadam_config(config: Dict[str, Any]):
        """
        Validate FedAdam strategy configuration.
        
        Args:
            config: FedAdam configuration
            
        Raises:
            ValueError: If configuration is invalid
        """
        # Validate beta1
        if 'beta1' in config:
            beta1 = config['beta1']
            if not isinstance(beta1, (int, float)) or not 0 <= beta1 < 1:
                raise ValueError(f"FedAdam beta1 must be in [0,1), got {beta1}")
        
        # Validate beta2
        if 'beta2' in config:
            beta2 = config['beta2']
            if not isinstance(beta2, (int, float)) or not 0 <= beta2 < 1:
                raise ValueError(f"FedAdam beta2 must be in [0,1), got {beta2}")
        
        # Validate server_lr
        if 'server_lr' in config:
            server_lr = config['server_lr']
            if not isinstance(server_lr, (int, float)) or server_lr <= 0:
                raise ValueError(f"FedAdam server_lr must be positive, got {server_lr}")
        
        # Validate epsilon
        if 'epsilon' in config:
            epsilon = config['epsilon']
            # Handle string representation of scientific notation
            if isinstance(epsilon, str):
                try:
                    epsilon = float(epsilon)
                except ValueError:
                    raise ValueError(f"FedAdam epsilon must be a valid number, got {epsilon}")
            if not isinstance(epsilon, (int, float)) or epsilon <= 0:
                raise ValueError(f"FedAdam epsilon must be positive, got {epsilon}")


    @staticmethod
    def get_supported_strategies() -> List[str]:
        """
        Get list of supported strategy names.
        
        Returns:
            List of supported strategy names in proper case
        """
        return ['FedAvg', 'FedProx', 'FedAdam']
    
    @staticmethod
    def is_strategy_supported(strategy_name: str) -> bool:
        """
        Check if a strategy is supported.
        
        Args:
            strategy_name: Name of the strategy to check
            
        Returns:
            True if strategy is supported, False otherwise
        """
        return strategy_name.lower() in ['fedavg', 'fedprox', 'fedadam']
    
    @staticmethod
    def validate_full_config(config: Dict[str, Any], config_type: str = "legacy") -> bool:
        """
        Perform comprehensive validation of configuration.
        
        Args:
            config: Configuration dictionary to validate
            config_type: Type of configuration ("server", "client", or "legacy")
            
        Returns:
            True if configuration is valid
            
        Raises:
            ValueError: If configuration is invalid
        """
        if config_type == "server":
            ConfigLoader._validate_server_config(config)
        elif config_type == "client":
            ConfigLoader._validate_client_config(config)
        else:  # legacy
            ConfigLoader._validate_legacy_config(config)
        
        # For server and legacy configs, validate strategy
        if config_type in ["server", "legacy"]:
            strategy_name = ConfigLoader.get_strategy_name(config)
            ConfigLoader._validate_strategy_name(strategy_name)
            
            # Validate strategy-specific configuration
            strategy_config = ConfigLoader.get_strategy_config(config, strategy_name)
            if strategy_name.lower() == 'fedprox':
                ConfigLoader._validate_fedprox_config(strategy_config)
            elif strategy_name.lower() == 'fedadam':
                ConfigLoader._validate_fedadam_config(strategy_config)
        
        return True
    
    @staticmethod
    def detect_config_format(config_path: str) -> str:
        """
        Detect the format of a configuration file.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            Configuration format: "server", "client", or "legacy"
            
        Raises:
            FileNotFoundError: If configuration file doesn't exist
            ValueError: If configuration format cannot be determined
        """
        config_path_obj = Path(config_path)
        if not config_path_obj.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Check for new format indicators
        if 'server' in config and 'strategy' in config:
            return "server"
        elif 'client' in config and 'optimizer' in config.get('client', {}):
            return "client"
        elif 'federated' in config:
            return "legacy"
        else:
            raise ValueError(f"Cannot determine configuration format for {config_path}")
    
    @staticmethod
    def is_legacy_format(config_path: str) -> bool:
        """
        Check if a configuration file uses the legacy format.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            True if legacy format, False otherwise
        """
        try:
            return ConfigLoader.detect_config_format(config_path) == "legacy"
        except (FileNotFoundError, ValueError):
            return False


    @staticmethod
    def load_config_with_fallback(server_config_path: str = "configs/server_config.yaml",
                                client_config_path: str = "configs/client_config.yaml",
                                legacy_config_path: str = "configs/federated_config.yaml") -> Dict[str, Dict[str, Any]]:
        """
        Load configuration with automatic fallback to legacy format.
        
        This method attempts to load the new modular configuration format first,
        and falls back to the legacy format if the new files are not found.
        
        Args:
            server_config_path: Path to server configuration file
            client_config_path: Path to client configuration file  
            legacy_config_path: Path to legacy federated configuration file
            
        Returns:
            Dictionary containing 'server' and 'client' configuration sections
            
        Raises:
            FileNotFoundError: If no valid configuration files are found
            ValueError: If configuration is invalid
        """
        server_config_exists = Path(server_config_path).exists()
        client_config_exists = Path(client_config_path).exists()
        legacy_config_exists = Path(legacy_config_path).exists()
        
        if server_config_exists and client_config_exists:
            # Load new modular format
            logging.info("Loading modular configuration format")
            server_config = ConfigLoader.load_server_config(server_config_path)
            client_config = ConfigLoader.load_client_config(client_config_path)
            
            return {
                'server': server_config,
                'client': client_config
            }
        
        elif legacy_config_exists:
            # Load legacy format and convert
            logging.warning(
                "Loading legacy configuration format. Consider migrating to "
                "the new modular structure for better maintainability."
            )
            legacy_config = ConfigLoader.load_federated_config(legacy_config_path)
            
            # Convert legacy format to modular structure
            return ConfigLoader._convert_legacy_to_modular(legacy_config)
        
        else:
            # No valid configuration found
            missing_files = []
            if not server_config_exists:
                missing_files.append(server_config_path)
            if not client_config_exists:
                missing_files.append(client_config_path)
            if not legacy_config_exists:
                missing_files.append(legacy_config_path)
            
            raise FileNotFoundError(
                f"No valid configuration files found. Missing: {missing_files}. "
                "Please ensure either the new modular configuration files "
                "(server_config.yaml, client_config.yaml) or the legacy "
                "federated_config.yaml file exists."
            )
    
    @staticmethod
    def _convert_legacy_to_modular(legacy_config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Convert legacy configuration format to modular structure.
        
        Args:
            legacy_config: Legacy federated configuration
            
        Returns:
            Dictionary with 'server' and 'client' sections in new format
        """
        # Extract server configuration
        server_section = {
            'server': legacy_config.get('server', {}),
            'strategy': {
                'name': ConfigLoader.get_strategy_name(legacy_config)
            }
        }
        
        # Add strategy-specific parameters
        strategy_name = server_section['strategy']['name'].lower()
        strategy_config = ConfigLoader.get_strategy_config(legacy_config, strategy_name)
        if strategy_config:
            server_section['strategy'][strategy_name] = strategy_config
        
        # Add evaluation section if present
        if 'evaluation' in legacy_config:
            server_section['evaluation'] = legacy_config['evaluation']
        
        # Extract client configuration with defaults for missing fields
        legacy_client = legacy_config.get('client', {})
        client_section = {
            'client': {
                'local_epochs': legacy_client.get('local_epochs', 20),
                'batch_size': legacy_client.get('batch_size', 300),  # Add default batch_size
                'optimizer': {
                    'name': legacy_client.get('optimizer', 'adamw'),
                    'learning_rate': legacy_client.get('learning_rate', 5e-4),
                    'weight_decay': legacy_client.get('weight_decay', 1e-3)
                }
            }
        }
        
        # Copy any additional client parameters from legacy config
        for key, value in legacy_client.items():
            if key not in client_section['client']:
                client_section['client'][key] = value
        
        return {
            'server': server_section,
            'client': client_section
        }


def load_yaml_config(path: str) -> Dict[str, Any]:
    """
    Load YAML configuration file.
    
    Args:
        path: Path to YAML configuration file
        
    Returns:
        Configuration dictionary
        
    Raises:
        FileNotFoundError: If file doesn't exist
        yaml.YAMLError: If file is not valid YAML
    """
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)