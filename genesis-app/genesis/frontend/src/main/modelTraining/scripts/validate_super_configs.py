#!/usr/bin/env python3
"""
Configuration Validation Script

This script validates super-node and super-link configurations to ensure
they are properly formatted and contain valid parameters.
"""

import sys
import argparse
from pathlib import Path
from typing import List, Tuple

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.federated.super_node.config import (
    load_super_node_config_from_file,
    validate_super_node_config,
    create_default_super_node_config
)
from src.federated.super_link.config import (
    load_super_link_config_from_file,
    validate_super_link_config,
    create_default_super_link_config
)


def validate_super_node_configs(config_paths: List[str]) -> List[Tuple[str, bool, str]]:
    """
    Validate super-node configuration files.
    
    Args:
        config_paths: List of configuration file paths
        
    Returns:
        List of tuples (path, is_valid, message)
    """
    results = []
    
    for config_path in config_paths:
        try:
            config = load_super_node_config_from_file(config_path)
            results.append((config_path, True, f"Valid super-node config: {config.node_id}"))
        except FileNotFoundError:
            results.append((config_path, False, "Configuration file not found"))
        except Exception as e:
            results.append((config_path, False, f"Validation error: {e}"))
    
    return results


def validate_super_link_configs(config_paths: List[str]) -> List[Tuple[str, bool, str]]:
    """
    Validate super-link configuration files.
    
    Args:
        config_paths: List of configuration file paths
        
    Returns:
        List of tuples (path, is_valid, message)
    """
    results = []
    
    for config_path in config_paths:
        try:
            config = load_super_link_config_from_file(config_path)
            results.append((config_path, True, f"Valid super-link config: {config.link_id}"))
        except FileNotFoundError:
            results.append((config_path, False, "Configuration file not found"))
        except Exception as e:
            results.append((config_path, False, f"Validation error: {e}"))
    
    return results


def test_default_configs():
    """Test creation of default configurations."""
    print("Testing default configuration creation...")
    
    try:
        # Test default super-node config
        super_node_config = create_default_super_node_config("test_node", "localhost")
        print(f"✓ Default super-node config created: {super_node_config.node_id}")
        
        # Test default super-link config
        super_link_config = create_default_super_link_config("test_link", "localhost")
        print(f"✓ Default super-link config created: {super_link_config.link_id}")
        
        return True
    except Exception as e:
        print(f"✗ Error creating default configs: {e}")
        return False


def main():
    """Main validation function."""
    parser = argparse.ArgumentParser(description="Validate super-node and super-link configurations")
    parser.add_argument("--super-node", nargs="*", default=[],
                       help="Super-node configuration files to validate")
    parser.add_argument("--super-link", nargs="*", default=[],
                       help="Super-link configuration files to validate")
    parser.add_argument("--all", action="store_true",
                       help="Validate all configuration files in configs/ directory")
    parser.add_argument("--test-defaults", action="store_true",
                       help="Test default configuration creation")
    
    args = parser.parse_args()
    
    all_valid = True
    
    # Test default configurations if requested
    if args.test_defaults:
        if not test_default_configs():
            all_valid = False
        print()
    
    # Determine configuration files to validate
    super_node_configs = args.super_node
    super_link_configs = args.super_link
    
    if args.all:
        # Find all configuration files
        configs_dir = Path("configs")
        super_node_configs.extend([
            str(p) for p in configs_dir.glob("**/super_node*.yaml")
        ])
        super_link_configs.extend([
            str(p) for p in configs_dir.glob("**/super_link*.yaml")
        ])
    
    # Default configurations if none specified
    if not super_node_configs and not super_link_configs and not args.test_defaults:
        super_node_configs = ["configs/super_node_config.yaml"]
        super_link_configs = ["configs/super_link_config.yaml"]
    
    # Validate super-node configurations
    if super_node_configs:
        print("Validating super-node configurations...")
        results = validate_super_node_configs(super_node_configs)
        
        for path, is_valid, message in results:
            status = "✓" if is_valid else "✗"
            print(f"  {status} {path}: {message}")
            if not is_valid:
                all_valid = False
        print()
    
    # Validate super-link configurations
    if super_link_configs:
        print("Validating super-link configurations...")
        results = validate_super_link_configs(super_link_configs)
        
        for path, is_valid, message in results:
            status = "✓" if is_valid else "✗"
            print(f"  {status} {path}: {message}")
            if not is_valid:
                all_valid = False
        print()
    
    # Summary
    if all_valid:
        print("✓ All configurations are valid!")
        return 0
    else:
        print("✗ Some configurations have validation errors.")
        return 1


if __name__ == "__main__":
    sys.exit(main())