#!/usr/bin/env python3
"""
Configuration validation script for client sampling in federated learning.
This script validates the configuration and explains how client sampling works.
"""

import yaml
from pathlib import Path

def load_config(config_path):
    """Load YAML configuration file"""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def validate_client_sampling_config():
    """Validate the client sampling configuration"""
    print("=" * 60)
    print("CLIENT SAMPLING CONFIGURATION VALIDATION")
    print("=" * 60)
    
    # Load federated configuration
    config_path = "configs/federated_config.yaml"
    if not Path(config_path).exists():
        print(f"❌ Configuration file not found: {config_path}")
        return False
    
    config = load_config(config_path)
    federated_config = config.get('federated', {})
    server_config = federated_config.get('server', {})
    
    print("📋 Current Configuration:")
    print(f"  - Total available clients: {server_config.get('min_available_clients', 'Not set')}")
    print(f"  - Minimum fit clients: {server_config.get('min_fit_clients', 'Not set')}")
    print(f"  - Fraction fit: {server_config.get('fraction_fit', 'Not set')}")
    print(f"  - Fraction evaluate: {server_config.get('fraction_evaluate', 'Not set')}")
    print(f"  - Strategy: {federated_config.get('strategy', 'Not set')}")
    print()
    
    # Validate configuration
    min_available = server_config.get('min_available_clients')
    min_fit = server_config.get('min_fit_clients')
    fraction_fit = server_config.get('fraction_fit')
    
    if min_available is None:
        print("❌ min_available_clients not set in configuration")
        return False
    
    if min_fit is None:
        print("❌ min_fit_clients not set in configuration")
        return False
    
    if fraction_fit is None:
        print("❌ fraction_fit not set in configuration")
        return False
    
    # Calculate expected clients per round
    expected_clients_per_round = int(min_available * fraction_fit)
    
    print("✅ Configuration Validation:")
    print(f"  - Total clients available: {min_available}")
    print(f"  - Sampling fraction: {fraction_fit:.2f}")
    print(f"  - Expected clients per round: {expected_clients_per_round}")
    print(f"  - Minimum required clients: {min_fit}")
    
    if expected_clients_per_round < min_fit:
        print(f"❌ Warning: Expected clients per round ({expected_clients_per_round}) is less than minimum required ({min_fit})")
        return False
    
    print("✅ Configuration is valid!")
    print()
    
    # Explain how it works
    print("🔍 How Client Sampling Works:")
    print(f"  1. You have {min_available} total clients available")
    print(f"  2. In each round, the server randomly samples {fraction_fit:.1%} of available clients")
    print(f"  3. This means approximately {expected_clients_per_round} clients participate per round")
    print(f"  4. The selection is random, so different clients may be chosen each round")
    print(f"  5. At least {min_fit} clients must participate for training to proceed")
    print()
    
    # Show example sampling patterns
    print("📊 Example Sampling Patterns (3 clients, 2 sampled per round):")
    print("  Round 1: Clients [0, 1] participate")
    print("  Round 2: Clients [1, 2] participate") 
    print("  Round 3: Clients [0, 2] participate")
    print("  Round 4: Clients [0, 1] participate")
    print("  ... and so on")
    print()
    
    # Check if federated data exists
    federated_data_dir = Path("federated_data/non_iid_partition/clients")
    if federated_data_dir.exists():
        client_dirs = [d for d in federated_data_dir.iterdir() if d.is_dir() and d.name.startswith('client_')]
        print(f"✅ Found {len(client_dirs)} client data directories")
        for client_dir in sorted(client_dirs):
            client_id = client_dir.name.split('_')[1]
            train_file = client_dir / "train.csv"
            test_file = client_dir / "test.csv"
            train_samples = len(open(train_file).readlines()) - 1 if train_file.exists() else 0
            test_samples = len(open(test_file).readlines()) - 1 if test_file.exists() else 0
            print(f"  - Client {client_id}: {train_samples} train samples, {test_samples} test samples")
    else:
        print("❌ Federated data not found. Please run data preparation first.")
        print("   python src/data/create_federated_dataset.py")
    
    print()
    print("🚀 To start federated learning with this configuration:")
    print("   python test_client_sampling.py")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    validate_client_sampling_config() 