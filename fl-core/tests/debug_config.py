#!/usr/bin/env python3
"""
Debug script to test configuration loading and learning rate parsing.
"""

import yaml
from pathlib import Path

def test_config_loading():
    """Test how the configuration files are being loaded."""
    
    # Load federated config
    federated_config_path = "configs/federated_config.yaml"
    with open(federated_config_path, 'r') as f:
        federated_config = yaml.safe_load(f)
    
    print("=== Federated Config ===")
    print(f"Type: {type(federated_config)}")
    print(f"Keys: {list(federated_config.keys())}")
    print(f"Learning rate scheduler: {federated_config.get('federated', {}).get('learning_rate_scheduler', {})}")
    
    # Load model config
    model_config_path = "configs/model_config.yaml"
    with open(model_config_path, 'r') as f:
        model_config = yaml.safe_load(f)
    
    print("\n=== Model Config ===")
    print(f"Type: {type(model_config)}")
    print(f"Keys: {list(model_config.keys())}")
    
    # Check learning rate specifically
    learning_rate = model_config.get('model', {}).get('training', {}).get('learning_rate')
    print(f"Learning rate: {learning_rate}")
    print(f"Learning rate type: {type(learning_rate)}")
    
    # Test conversion
    try:
        lr_float = float(learning_rate)
        print(f"Learning rate as float: {lr_float}")
        print(f"Learning rate as float type: {type(lr_float)}")
    except Exception as e:
        print(f"Error converting to float: {e}")
    
    # Test arithmetic operations
    try:
        test_result = learning_rate * 0.5
        print(f"Test multiplication: {learning_rate} * 0.5 = {test_result}")
    except Exception as e:
        print(f"Error in multiplication: {e}")
    
    # Test with float conversion
    try:
        lr_float = float(learning_rate)
        test_result = lr_float * 0.5
        print(f"Test multiplication with float: {lr_float} * 0.5 = {test_result}")
    except Exception as e:
        print(f"Error in float multiplication: {e}")

if __name__ == "__main__":
    test_config_loading() 