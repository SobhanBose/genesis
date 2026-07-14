#!/usr/bin/env python3
"""
Test script for k-fold cross validation functionality
"""

import yaml
import pandas as pd
from pathlib import Path
from scripts.run_improved_training import AdvancedTrainer

def test_kfold_cv():
    """Test k-fold cross validation with a small subset of data"""
    print("🧪 Testing k-fold cross validation functionality...")
    
    # Load data
    data_dir = Path("data/processed")
    train_data = pd.read_csv(data_dir / "train.csv")
    val_data = pd.read_csv(data_dir / "validation.csv")
    
    # Use a smaller subset for testing
    train_subset = train_data.head(1000)  # Use first 1000 samples for testing
    val_subset = val_data.head(200)       # Use first 200 samples for validation
    
    print(f"📊 Using subset - Train: {train_subset.shape}, Validation: {val_subset.shape}")
    
    # Create a temporary config with k-fold CV enabled
    config = {
        'model': {
            'architecture': {
                'model_type': 'lightweight',  # Use lightweight for faster testing
                'output_dim': 2
            },
            'training': {
                'batch_size': 16,
                'learning_rate': 1e-3,
                'optimizer': 'adam',
                'loss_function': 'cross_entropy',
                'max_epochs': 10,  # Short training for testing
                'use_weighted_sampler': False
            },
            'regularization': {
                'patience': 5,
                'min_delta': 1e-4
            },
            'evaluation': {
                'use_cross_validation': True,  # Enable k-fold CV
                'cv_folds': 3,  # Use 3 folds for testing
                'cv_random_state': 42
            },
            'feature_engineering': {
                'enabled': False  # Disable feature engineering for faster testing
            }
        }
    }
    
    # Save temporary config
    temp_config_path = "configs/temp_kfold_test_config.yaml"
    with open(temp_config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    try:
        # Initialize trainer with temporary config
        trainer = AdvancedTrainer(temp_config_path)
        
        # Run k-fold cross validation
        results = trainer.train(train_subset, val_subset, val_subset)  # test_data not used in k-fold CV
        
        print("✅ K-fold cross validation test completed successfully!")
        print(f"📊 Results saved to: results/advanced_training/")
        
        # Print summary
        if 'cv_statistics' in results:
            cv_stats = results['cv_statistics']
            print(f"📈 Cross-validation summary:")
            print(f"   Mean ROC_AUC: {cv_stats['mean_roc_auc']:.4f} ± {cv_stats['std_roc_auc']:.4f}")
            print(f"   Mean Accuracy: {cv_stats['mean_accuracy']:.4f} ± {cv_stats['std_accuracy']:.4f}")
            print(f"   Mean F1: {cv_stats['mean_f1']:.4f} ± {cv_stats['std_f1']:.4f}")
            print(f"   Best fold: {results['best_fold']}")
        
        return True
        
    except Exception as e:
        print(f"❌ K-fold cross validation test failed: {e}")
        return False
    
    finally:
        # Clean up temporary config
        if Path(temp_config_path).exists():
            Path(temp_config_path).unlink()

def test_standard_training():
    """Test standard training (without k-fold CV)"""
    print("🧪 Testing standard training functionality...")
    
    # Load data
    data_dir = Path("data/processed")
    train_data = pd.read_csv(data_dir / "train.csv")
    test_data = pd.read_csv(data_dir / "test.csv")
    val_data = pd.read_csv(data_dir / "validation.csv")
    
    # Use a smaller subset for testing
    train_subset = train_data.head(1000)
    test_subset = test_data.head(200)
    val_subset = val_data.head(200)
    
    print(f"📊 Using subset - Train: {train_subset.shape}, Test: {test_subset.shape}, Validation: {val_subset.shape}")
    
    # Create a temporary config with standard training
    config = {
        'model': {
            'architecture': {
                'model_type': 'lightweight',
                'output_dim': 2
            },
            'training': {
                'batch_size': 16,
                'learning_rate': 1e-3,
                'optimizer': 'adam',
                'loss_function': 'cross_entropy',
                'max_epochs': 10,
                'use_weighted_sampler': False
            },
            'regularization': {
                'patience': 5,
                'min_delta': 1e-4
            },
            'evaluation': {
                'use_cross_validation': False  # Standard training
            },
            'feature_engineering': {
                'enabled': False
            }
        }
    }
    
    # Save temporary config
    temp_config_path = "configs/temp_standard_test_config.yaml"
    with open(temp_config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    try:
        # Initialize trainer with temporary config
        trainer = AdvancedTrainer(temp_config_path)
        
        # Run standard training
        results = trainer.train(train_subset, test_subset, val_subset)
        
        print("✅ Standard training test completed successfully!")
        print(f"📊 Results saved to: results/advanced_training/")
        
        # Print summary
        print(f"📈 Training summary:")
        print(f"   Final Validation Accuracy: {results['final_val_accuracy']:.4f}")
        print(f"   Final Validation ROC_AUC: {results['final_val_roc_auc']:.4f}")
        print(f"   Final Validation F1: {results['final_val_f1']:.4f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Standard training test failed: {e}")
        return False
    
    finally:
        # Clean up temporary config
        if Path(temp_config_path).exists():
            Path(temp_config_path).unlink()

if __name__ == "__main__":
    print("🚀 Testing ClinVar training pipeline with k-fold cross validation...")
    
    # Test standard training
    standard_success = test_standard_training()
    
    # Test k-fold cross validation
    kfold_success = test_kfold_cv()
    
    if standard_success and kfold_success:
        print("🎉 All tests passed! Both standard training and k-fold cross validation are working.")
    else:
        print("⚠️ Some tests failed. Check the error messages above.") 