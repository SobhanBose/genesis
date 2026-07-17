"""
Federated Learning Module

This module contains the federated learning implementation for pathogenicity
prediction using Flower's federated learning framework.

Components:
- Clean federated client and server using strategy factory pattern
- Support for FedAvg, FedProx, and FedAdam strategies
- Lightweight wrappers around Flower's built-in strategies
- Simplified configuration management
"""

from .client import FederatedClient
from .server import FederatedServer, start_server
from .strategy_factory import StrategyFactory
from .config_loader import ConfigLoader

__all__ = [
    'FederatedClient',
    'FederatedServer', 
    'start_server',
    'StrategyFactory',
    'ConfigLoader'
]