#!/usr/bin/env python3
"""
Test script to verify FedProx implementation
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_fedprox_import():
    """Test if FedProx can be imported"""
    try:
        from flwr.server.strategy import FedProx
        print("✓ FedProx import successful")
        return True
    except ImportError as e:
        print(f"✗ FedProx import failed: {e}")
        return False

def test_server_config():
    """Test if server configuration is correct"""
    try:
        import yaml
        with open('configs/federated_config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        strategy = config['federated']['strategy']
        proximal_mu = config['federated'].get('proximal_mu', None)
        
        print(f"✓ Strategy: {strategy}")
        print(f"✓ Proximal mu: {proximal_mu}")
        
        if strategy == "FedProx" and proximal_mu is not None:
            print("✓ FedProx configuration is correct")
            return True
        else:
            print("✗ FedProx configuration is incorrect")
            return False
            
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False

def test_server_import():
    """Test if server can be imported with FedProx"""
    try:
        from src.federated.server_new import FederatedServer, FederatedStrategy
        print("✓ Server import successful")
        return True
    except Exception as e:
        print(f"✗ Server import failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Testing FedProx implementation...")
    print("=" * 50)
    
    tests = [
        ("FedProx Import", test_fedprox_import),
        ("Server Configuration", test_server_config),
        ("Server Import", test_server_import),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        if test_func():
            passed += 1
        else:
            print(f"  Test failed!")
    
    print("\n" + "=" * 50)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed! FedProx is ready to use.")
    else:
        print("✗ Some tests failed. Please check the implementation.")

if __name__ == "__main__":
    main() 