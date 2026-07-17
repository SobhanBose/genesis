#!/usr/bin/env python3
"""
Evaluate the best model from k-fold cross validation on train, test, and validation sets.
"""

import yaml
import pandas as pd
import torch
from pathlib import Path
from scripts.run_improved_training import AdvancedTrainer


def main():
    # Load config and k-fold results
    config_path = "configs/model_config.yaml"
    results_dir = Path("results/advanced_training")
    kfold_results_path = results_dir / "cv_final_results.yaml"
    if not kfold_results_path.exists():
        raise FileNotFoundError(f"K-fold results not found at {kfold_results_path}")
    with open(kfold_results_path, 'r') as f:
        kfold_results = yaml.safe_load(f)
    best_fold = kfold_results['best_fold']
    best_model_path = f"models/checkpoints/best_model_fold_{best_fold}.pt"
    print(f"🔍 Loading best model from fold {best_fold}: {best_model_path}")

    # Load data
    data_dir = Path("data/processed")
    train_data = pd.read_csv(data_dir / "train.csv")
    test_data = pd.read_csv(data_dir / "test.csv")
    val_data = pd.read_csv(data_dir / "validation.csv")

    # Initialize trainer
    trainer = AdvancedTrainer(config_path)

    # Preprocess data
    train_data = trainer.preprocess_data(train_data)
    test_data = trainer.preprocess_data(test_data)
    val_data = trainer.preprocess_data(val_data)

    # Create datasets and loaders
    batch_size = trainer.config['model']['training']['batch_size']
    from scripts.run_improved_training import ImprovedClinVarDataset
    from torch.utils.data import DataLoader
    train_dataset = ImprovedClinVarDataset(train_data)
    test_dataset = ImprovedClinVarDataset(test_data)
    val_dataset = ImprovedClinVarDataset(val_data)
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

    # Create model and load best weights
    input_size = len(train_dataset.feature_cols)
    model = trainer.create_model(input_size)
    model.load_state_dict(torch.load(best_model_path, map_location=trainer.device))
    model = model.to(trainer.device)
    loss_fn = trainer.get_loss_function()

    # Evaluate on all sets
    print("\nEvaluating best k-fold model on all sets...")
    train_metrics = trainer.evaluate(model, train_loader, loss_fn)
    test_metrics = trainer.evaluate(model, test_loader, loss_fn)
    val_metrics = trainer.evaluate(model, val_loader, loss_fn)

    print("\nResults:")
    print(f"Train:     Loss={train_metrics[0]:.4f}, Acc={train_metrics[1]:.4f}, ROC_AUC={train_metrics[2]:.4f}, Prec={train_metrics[3]:.4f}, Rec={train_metrics[4]:.4f}, F1={train_metrics[5]:.4f}")
    print(f"Test:      Loss={test_metrics[0]:.4f}, Acc={test_metrics[1]:.4f}, ROC_AUC={test_metrics[2]:.4f}, Prec={test_metrics[3]:.4f}, Rec={test_metrics[4]:.4f}, F1={test_metrics[5]:.4f}")
    print(f"Validation: Loss={val_metrics[0]:.4f}, Acc={val_metrics[1]:.4f}, ROC_AUC={val_metrics[2]:.4f}, Prec={val_metrics[3]:.4f}, Rec={val_metrics[4]:.4f}, F1={val_metrics[5]:.4f}")

    # Save results
    results = {
        'train': {
            'loss': train_metrics[0], 'accuracy': train_metrics[1], 'roc_auc': train_metrics[2],
            'precision': train_metrics[3], 'recall': train_metrics[4], 'f1': train_metrics[5]
        },
        'test': {
            'loss': test_metrics[0], 'accuracy': test_metrics[1], 'roc_auc': test_metrics[2],
            'precision': test_metrics[3], 'recall': test_metrics[4], 'f1': test_metrics[5]
        },
        'validation': {
            'loss': val_metrics[0], 'accuracy': val_metrics[1], 'roc_auc': val_metrics[2],
            'precision': val_metrics[3], 'recall': val_metrics[4], 'f1': val_metrics[5]
        },
        'best_model_path': best_model_path,
        'best_fold': best_fold
    }
    with open(results_dir / "best_kfold_model_evaluation.yaml", 'w') as f:
        yaml.dump(results, f, default_flow_style=False)
    print(f"\n✅ Results saved to {results_dir / 'best_kfold_model_evaluation.yaml'}")

if __name__ == "__main__":
    main() 