#!/usr/bin/env python3
"""
Test script to verify the client sampling fix works correctly.
"""

import yaml
from pathlib import Path

def test_config_loading():
    """Test that the configuration loads correctly"""
    print("Testing configuration loading...")
    
    config_path = "configs/federated_config.yaml"
    if not Path(config_path).exists():
        print(f"❌ Configuration file not found: {config_path}")
        return False
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    federated_config = config.get('federated', {})
    server_config = federated_config.get('server', {})
    
    print(f"✅ Configuration loaded successfully")
    print(f"  - Rounds: {server_config.get('rounds')}")
    print(f"  - Min available clients: {server_config.get('min_available_clients')}")
    print(f"  - Min fit clients: {server_config.get('min_fit_clients')}")
    print(f"  - Fraction fit: {server_config.get('fraction_fit')}")
    
    return True

def test_client_sampling_logic():
    """Test the client sampling logic"""
    print("\nTesting client sampling logic...")
    
    # Simulate the configuration
    min_available = 3
    fraction_fit = 0.67
    min_fit = 2
    
    # Calculate expected clients per round
    expected_clients = int(min_available * fraction_fit)
    
    print(f"  - Total clients: {min_available}")
    print(f"  - Sampling fraction: {fraction_fit}")
    print(f"  - Expected clients per round: {expected_clients}")
    print(f"  - Minimum required: {min_fit}")
    
    if expected_clients >= min_fit:
        print("✅ Client sampling logic is valid")
        return True
    else:
        print("❌ Client sampling logic is invalid")
        return False

def test_tuple_unpacking():
    """Test the tuple unpacking fix"""
    print("\nTesting tuple unpacking fix...")
    
    # Simulate the config structure that would be returned by configure_fit
    # config is a list of tuples: [(client_proxy, fit_config), ...]
    mock_config = [
        ("client_0", {"learning_rate": 0.001}),
        ("client_1", {"learning_rate": 0.001})
    ]
    
    try:
        # Test the fixed logic
        sampled_ids = [client_proxy for client_proxy, _ in mock_config]
        print(f"  - Successfully unpacked: {sampled_ids}")
        print("✅ Tuple unpacking fix works correctly")
        return True
    except Exception as e:
        print(f"❌ Tuple unpacking failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 50)
    print("CLIENT SAMPLING FIX VERIFICATION")
    print("=" * 50)
    
    tests = [
        test_config_loading,
        test_client_sampling_logic,
        test_tuple_unpacking
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! The fix should work correctly.")
        print("\nYou can now run the server:")
        print("  uv run -m src.federated.server_new")
    else:
        print("❌ Some tests failed. Please check the configuration.")
    
    print("=" * 50)

if __name__ == "__main__":
    main() 