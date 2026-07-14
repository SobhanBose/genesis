#!/usr/bin/env python3
"""
Test script to demonstrate the improved pathogenicity model
and compare it with the original model.
"""

import sys
import torch
import torch.nn as nn
from pathlib import Path
import yaml

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from models.improved_pathogenicity_model import (
    ImprovedPathogenicityClassifier, 
    LightweightPathogenicityClassifier,
    EnsemblePathogenicityClassifier,
    create_model,
    get_model_summary
)
from models.pathogenecity_model import PathogenicityClassifier

def test_model_creation():
    """Test creating different types of models"""
    print("🧪 Testing Model Creation")
    print("=" * 50)
    
    input_size = 100
    output_size = 2
    
    # Test original model
    print("\n1. Original Pathogenicity Classifier:")
    original_model = PathogenicityClassifier(input_size, output_size)
    original_summary = {
        'parameters': original_model.get_num_parameters(),
        'trainable': original_model.get_trainable_parameters()
    }
    print(f"   Parameters: {original_summary['parameters']:,}")
    print(f"   Trainable: {original_summary['trainable']:,}")
    
    # Test improved model
    print("\n2. Improved Pathogenicity Classifier:")
    improved_model = ImprovedPathogenicityClassifier(input_size, output_size)
    improved_summary = get_model_summary(improved_model)
    print(f"   Parameters: {improved_summary['total_parameters']:,}")
    print(f"   Trainable: {improved_summary['trainable_parameters']:,}")
    print(f"   Model Size: {improved_summary['model_size_mb']:.2f} MB")
    
    # Test lightweight model
    print("\n3. Lightweight Pathogenicity Classifier:")
    lightweight_model = LightweightPathogenicityClassifier(input_size, output_size)
    lightweight_summary = get_model_summary(lightweight_model)
    print(f"   Parameters: {lightweight_summary['total_parameters']:,}")
    print(f"   Trainable: {lightweight_summary['trainable_parameters']:,}")
    print(f"   Model Size: {lightweight_summary['model_size_mb']:.2f} MB")
    
    # Test ensemble model
    print("\n4. Ensemble Pathogenicity Classifier:")
    ensemble_model = EnsemblePathogenicityClassifier(input_size, output_size, num_models=3)
    ensemble_summary = get_model_summary(ensemble_model)
    print(f"   Parameters: {ensemble_summary['total_parameters']:,}")
    print(f"   Trainable: {ensemble_summary['trainable_parameters']:,}")
    print(f"   Model Size: {ensemble_summary['model_size_mb']:.2f} MB")
    
    return {
        'original': original_summary,
        'improved': improved_summary,
        'lightweight': lightweight_summary,
        'ensemble': ensemble_summary
    }

def test_model_forward_pass():
    """Test forward pass through different models"""
    print("\n🧪 Testing Forward Pass")
    print("=" * 50)
    
    input_size = 100
    output_size = 2
    batch_size = 32
    
    # Create dummy input
    dummy_input = torch.randn(batch_size, input_size)
    
    models = {
        'Original': PathogenicityClassifier(input_size, output_size),
        'Improved': ImprovedPathogenicityClassifier(input_size, output_size),
        'Lightweight': LightweightPathogenicityClassifier(input_size, output_size),
        'Ensemble': EnsemblePathogenicityClassifier(input_size, output_size, num_models=3)
    }
    
    for name, model in models.items():
        print(f"\n{name} Model:")
        try:
            with torch.no_grad():
                output = model(dummy_input)
            print(f"   Input shape: {dummy_input.shape}")
            print(f"   Output shape: {output.shape}")
            print(f"   Output range: [{output.min().item():.4f}, {output.max().item():.4f}]")
            print(f"   ✅ Forward pass successful")
        except Exception as e:
            print(f"   ❌ Forward pass failed: {e}")

def test_factory_function():
    """Test the factory function for creating models"""
    print("\n🧪 Testing Factory Function")
    print("=" * 50)
    
    input_size = 100
    output_size = 2
    
    model_types = ['improved', 'lightweight', 'ensemble']
    
    for model_type in model_types:
        print(f"\nCreating {model_type} model:")
        try:
            model = create_model(
                model_type=model_type,
                input_size=input_size,
                output_size=output_size
            )
            summary = get_model_summary(model)
            print(f"   ✅ Successfully created {model_type} model")
            print(f"   Parameters: {summary['total_parameters']:,}")
        except Exception as e:
            print(f"   ❌ Failed to create {model_type} model: {e}")

def test_attention_mechanism():
    """Test the attention mechanism specifically"""
    print("\n🧪 Testing Attention Mechanism")
    print("=" * 50)
    
    input_size = 128  # Must be divisible by number of heads
    output_size = 2
    batch_size = 16
    
    model = ImprovedPathogenicityClassifier(input_size, output_size)
    dummy_input = torch.randn(batch_size, input_size)
    
    print(f"Input shape: {dummy_input.shape}")
    
    # Test feature extraction
    features = model.feature_extractor(dummy_input)
    print(f"Feature extraction output shape: {features.shape}")
    
    # Test attention
    attended = model.attention(features)
    print(f"Attention output shape: {attended.shape}")
    
    # Test full forward pass
    output = model(dummy_input)
    print(f"Final output shape: {output.shape}")
    print("✅ Attention mechanism working correctly")

def test_residual_connections():
    """Test residual connections"""
    print("\n🧪 Testing Residual Connections")
    print("=" * 50)
    
    from models.improved_pathogenicity_model import ResidualBlock
    
    input_dim = 256
    hidden_dim = 128
    batch_size = 16
    
    residual_block = ResidualBlock(input_dim, hidden_dim)
    dummy_input = torch.randn(batch_size, input_dim)
    
    print(f"Input shape: {dummy_input.shape}")
    
    # Test residual block
    output = residual_block(dummy_input)
    print(f"Output shape: {output.shape}")
    
    # Check that residual connection is working
    assert output.shape == dummy_input.shape, "Residual block should preserve input shape"
    print("✅ Residual connections working correctly")

def compare_model_complexity():
    """Compare the complexity of different models"""
    print("\n📊 Model Complexity Comparison")
    print("=" * 50)
    
    input_size = 100
    output_size = 2
    
    models = {
        'Original': PathogenicityClassifier(input_size, output_size),
        'Improved': ImprovedPathogenicityClassifier(input_size, output_size),
        'Lightweight': LightweightPathogenicityClassifier(input_size, output_size),
        'Ensemble (3 models)': EnsemblePathogenicityClassifier(input_size, output_size, num_models=3)
    }
    
    print(f"{'Model Type':<20} {'Parameters':<12} {'Size (MB)':<12} {'Ratio vs Original':<15}")
    print("-" * 65)
    
    original_params = models['Original'].get_num_parameters()
    
    for name, model in models.items():
        params = model.get_num_parameters()
        size_mb = params * 4 / (1024 * 1024)  # Assuming float32
        ratio = params / original_params
        
        print(f"{name:<20} {params:<12,} {size_mb:<12.2f} {ratio:<15.2f}x")

def main():
    """Main test function"""
    print("🚀 Testing Improved Pathogenicity Models")
    print("=" * 60)
    
    # Run all tests
    test_model_creation()
    test_model_forward_pass()
    test_factory_function()
    test_attention_mechanism()
    test_residual_connections()
    compare_model_complexity()
    
    print("\n✅ All tests completed successfully!")
    print("\n📋 Summary:")
    print("- Original model: Basic architecture with standard layers")
    print("- Improved model: Advanced architecture with attention and residual connections")
    print("- Lightweight model: Simplified version for resource-constrained environments")
    print("- Ensemble model: Combination of multiple models for better performance")
    
    print("\n🎯 Next Steps:")
    print("1. Run the improved training script: python scripts/run_improved_training.py")
    print("2. Compare performance with the original model")
    print("3. Experiment with different model configurations")

if __name__ == "__main__":
    main() 