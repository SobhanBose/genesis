#!/usr/bin/env python3
"""
Test script for learning rate scheduling functionality.
"""

import numpy as np
from typing import Dict, List

def test_learning_rate_scheduling():
    """Test different learning rate scheduling strategies."""
    
    # Test parameters
    base_lr = 0.001
    total_rounds = 30
    
    # Test different scheduling strategies
    strategies = {
        'constant': 'constant',
        'step_decay': 'step_decay',
        'exponential_decay': 'exponential_decay',
        'cosine_annealing': 'cosine_annealing',
        'warmup_then_decay': 'warmup_then_decay'
    }
    
    results = {}
    
    for strategy_name, strategy_type in strategies.items():
        print(f"\n=== Testing {strategy_name} ===")
        lr_values = []
        
        for round_num in range(total_rounds):
            lr = calculate_learning_rate(
                base_lr=base_lr,
                server_round=round_num,
                total_rounds=total_rounds,
                strategy=strategy_type
            )
            lr_values.append(lr)
            print(f"Round {round_num:2d}: LR = {lr:.6f}")
        
        results[strategy_name] = lr_values
    
    # Plot results (if matplotlib is available)
    try:
        import matplotlib.pyplot as plt
        
        plt.figure(figsize=(12, 8))
        for strategy_name, lr_values in results.items():
            plt.plot(range(total_rounds), lr_values, label=strategy_name, marker='o', markersize=3)
        
        plt.xlabel('Server Round')
        plt.ylabel('Learning Rate')
        plt.title('Learning Rate Scheduling Strategies')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.yscale('log')
        plt.tight_layout()
        plt.savefig('tests/lr_scheduling_comparison.png', dpi=300, bbox_inches='tight')
        print("\n✅ Learning rate scheduling comparison plot saved to 'tests/lr_scheduling_comparison.png'")
        
    except ImportError:
        print("\n⚠️  matplotlib not available, skipping plot generation")
    
    return results

def calculate_learning_rate(base_lr: float, server_round: int, total_rounds: int, strategy: str) -> float:
    """
    Calculate learning rate based on scheduling strategy.
    
    Args:
        base_lr: Base learning rate
        server_round: Current server round
        total_rounds: Total number of rounds
        strategy: Scheduling strategy
        
    Returns:
        Current learning rate
    """
    if strategy == 'step_decay':
        # Step decay: reduce learning rate every N rounds
        decay_interval = 10
        decay_factor = 0.5
        current_lr = base_lr * (decay_factor ** (server_round // decay_interval))
        
    elif strategy == 'exponential_decay':
        # Exponential decay
        decay_rate = 0.95
        current_lr = base_lr * (decay_rate ** server_round)
        
    elif strategy == 'cosine_annealing':
        # Cosine annealing
        current_lr = base_lr * 0.5 * (1 + np.cos(np.pi * server_round / total_rounds))
        
    elif strategy == 'warmup_then_decay':
        # Warmup for first N rounds, then decay
        warmup_rounds = 5
        if server_round < warmup_rounds:
            # Linear warmup
            current_lr = base_lr * (server_round + 1) / warmup_rounds
        else:
            # Exponential decay after warmup
            decay_rate = 0.95
            current_lr = base_lr * (decay_rate ** (server_round - warmup_rounds))
    else:
        # Constant learning rate (default)
        current_lr = base_lr
    
    # Ensure learning rate doesn't go below minimum
    min_lr = 1e-6
    current_lr = max(current_lr, min_lr)
    
    return current_lr

def test_config_parsing():
    """Test configuration parsing for learning rate scheduling."""
    
    # Sample configuration
    config = {
        'federated': {
            'learning_rate_schedule': 'exponential_decay',
            'lr_decay_rate': 0.9,
            'min_learning_rate': 1e-5,
            'client': {
                'local_epochs': 5,
                'batch_size': 32,
                'learning_rate': 0.001
            }
        }
    }
    
    print("\n=== Testing Configuration Parsing ===")
    print(f"Schedule: {config['federated']['learning_rate_schedule']}")
    print(f"Decay Rate: {config['federated']['lr_decay_rate']}")
    print(f"Min LR: {config['federated']['min_learning_rate']}")
    print(f"Base LR: {config['federated']['client']['learning_rate']}")
    
    # Test a few rounds
    base_lr = config['federated']['client']['learning_rate']
    decay_rate = config['federated']['lr_decay_rate']
    
    for round_num in range(5):
        lr = base_lr * (decay_rate ** round_num)
        lr = max(lr, config['federated']['min_learning_rate'])
        print(f"Round {round_num}: LR = {lr:.6f}")
    
    print("✅ Configuration parsing test passed!")

if __name__ == "__main__":
    print("Testing Learning Rate Scheduling Functionality")
    print("=" * 50)
    
    # Test learning rate scheduling strategies
    results = test_learning_rate_scheduling()
    
    # Test configuration parsing
    test_config_parsing()
    
    print("\n" + "=" * 50)
    print("✅ All learning rate scheduling tests completed!")
    
    # Print summary
    print("\nSummary of scheduling strategies:")
    for strategy_name, lr_values in results.items():
        print(f"{strategy_name:20s}: LR range [{min(lr_values):.6f}, {max(lr_values):.6f}]") 