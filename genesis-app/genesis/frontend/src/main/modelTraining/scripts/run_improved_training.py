"""
Advanced training script for improved ClinVar pathogenicity prediction
with federated learning, enhanced model architecture, and advanced features.
"""

import os
import sys
import yaml
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler
import pandas as pd
import numpy as np
from pathlib import Path
import logging
from typing import Dict, List, Tuple, Optional
from tqdm import tqdm
import warnings

warnings.filterwarnings("ignore")

from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score
from sklearn.model_selection import KFold

# Add src to path
# sys.path.append(str(Path(__file__).parent.parent / "src"))

from src.models.improved_pathogenicity_model import ImprovedPathogenicityClassifier, create_model, get_model_summary
from src.models.pathogenecity_model import PathogenicityClassifier
from src.models.loss_functions import get_loss_function
from src.models.feature_engineering import GenomicFeatureEngineer
from src.federated.server import FederatedServer
from src.federated.client import FederatedClient
from src.utils.logger import Logger


class ImprovedClinVarDataset(Dataset):
    """Enhanced dataset for ClinVar data with advanced preprocessing"""

    def __init__(self, data: pd.DataFrame, target_col: str = "class", use_gene_embedding: bool = False):
        self.data = data.reset_index(drop=True)
        self.target_col = target_col
        self.use_gene_embedding = use_gene_embedding and ("gene" in data.columns)
        self.feature_cols = [col for col in data.columns if col != target_col and (col != "gene" or not self.use_gene_embedding)]
        self.gene_col = "gene" if self.use_gene_embedding and "gene" in data.columns else None

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        features = torch.tensor(self.data.iloc[idx][self.feature_cols].values, dtype=torch.float32)
        target = torch.tensor(self.data.iloc[idx][self.target_col], dtype=torch.long)
        if self.gene_col:
            gene_idx = torch.tensor(self.data.iloc[idx][self.gene_col], dtype=torch.long)
            return features, gene_idx, target
        else:
            return features, target


class AdvancedTrainer:
    """Advanced trainer with improved model architecture and training strategies"""

    def __init__(self, config_path: str = "configs/model_config.yaml"):
        self.config = self._load_config(config_path)
        self.logger = Logger(log_dir="logs/advanced_training")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.feature_engineer = GenomicFeatureEngineer()

        self.logger.log_info(f"🚀 Initializing Advanced Trainer on {self.device}")
        self.logger.log_info(f"📋 Configuration: {self.config}")

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        return config

    def create_model(self, input_size: int, gene_vocab_size: int = None, use_gene_embedding: bool = False) -> nn.Module:
        """Create model based on configuration"""
        model_config = self.config["model"]["architecture"]
        model_type = model_config.get("model_type", "basic")

        if model_type == "improved":
            # Get improved model specific settings
            improved_config = model_config.get("improved_model", {})
            model = create_model(
                model_type="improved",
                input_size=input_size,
                output_size=model_config["output_dim"],
                hidden_dims=improved_config.get("hidden_dims", model_config.get("hidden_dims", [512, 256, 128])),
                dropout=improved_config.get("dropout", model_config.get("dropout", 0.3)),
                gene_vocab_size=gene_vocab_size,
                use_gene_embedding=use_gene_embedding,
            )
            self.logger.log_info("🧠 Using Improved Pathogenicity Classifier")

        elif model_type == "lightweight":
            # Get lightweight model specific settings
            lightweight_config = model_config.get("lightweight_model", {})
            model = create_model(
                model_type="lightweight",
                input_size=input_size,
                output_size=model_config["output_dim"],
                hidden_dims=lightweight_config.get("hidden_dims", [256, 128, 64]),
                dropout=lightweight_config.get("dropout", 0.2),
                gene_vocab_size=gene_vocab_size,
                use_gene_embedding=use_gene_embedding,
            )
            self.logger.log_info("🧠 Using Lightweight Pathogenicity Classifier")

        elif model_type == "ensemble":
            # Get ensemble model specific settings
            ensemble_config = model_config.get("ensemble_model", {})
            member_type = ensemble_config.get("ensemble_member_type", "improved")
            if member_type == "improved":
                member_configs = ensemble_config.get("improved_member_settings", {})
            elif member_type == "lightweight":
                member_configs = ensemble_config.get("lightweight_member_settings", {})

            # Get hidden_dims for ensemble - should be a list of lists
            hidden_dims = member_configs.get("hidden_dims", [[512, 256, 128, 64, 32]] * ensemble_config.get("num_models", 3))

            # Ensure hidden_dims is a list of lists with correct length
            if not isinstance(hidden_dims, list) or not all(isinstance(dim, list) for dim in hidden_dims):
                # If it's a single list, repeat it for all models
                if isinstance(hidden_dims, list) and all(isinstance(dim, (int, float)) for dim in hidden_dims):
                    hidden_dims = [hidden_dims] * ensemble_config.get("num_models", 3)
                else:
                    # Fallback to default
                    hidden_dims = [[512, 256, 128, 64, 32]] * ensemble_config.get("num_models", 3)

            model = create_model(
                model_type="ensemble",
                input_size=input_size,
                output_size=model_config["output_dim"],
                ensemble_member_type=member_type,
                num_models=ensemble_config.get("num_models", 3),
                hidden_dims=hidden_dims,
                dropout=member_configs.get("dropout", 0.3),
                gene_vocab_size=gene_vocab_size,
                use_gene_embedding=use_gene_embedding,
            )
            self.logger.log_info(f"🧠 Using Ensemble Pathogenicity Classifier with {ensemble_config.get('num_models', 3)} models")

        else:  # basic model
            # Get basic model specific settings
            basic_config = model_config.get("basic_model", {})
            model = PathogenicityClassifier(input_size=input_size, output_size=model_config["output_dim"])
            self.logger.log_info("🧠 Using Basic Pathogenicity Classifier")

        model = model.to(self.device)

        # Get detailed model summary
        model_summary = get_model_summary(model)
        self.logger.log_info(f"📊 Model Summary: {model_summary}")

        return model

    def get_optimizer(self, model: nn.Module) -> optim.Optimizer:
        """Get optimizer based on configuration"""
        training_config = self.config["model"]["training"]
        optimizer_name = training_config["optimizer"]
        lr = float(training_config["learning_rate"])
        weight_decay = float(training_config.get("weight_decay", 1e-4))

        if optimizer_name == "adam":
            optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay, betas=(training_config.get("beta1", 0.9), training_config.get("beta2", 0.999)))
        elif optimizer_name == "adamw":
            optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay, betas=(training_config.get("beta1", 0.9), training_config.get("beta2", 0.999)))
        elif optimizer_name == "sgd":
            optimizer = optim.SGD(model.parameters(), lr=lr, momentum=training_config.get("momentum", 0.9), weight_decay=weight_decay)
        else:
            optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)

        self.logger.log_info(f"⚙️ Using {optimizer_name.upper()} optimizer")
        return optimizer

    def get_scheduler(self, optimizer: optim.Optimizer) -> optim.lr_scheduler._LRScheduler:
        """Get learning rate scheduler based on configuration"""
        training_config = self.config["model"]["training"]
        scheduler_type = training_config.get("learning_rate_schedule", "reduce_on_plateau")

        if scheduler_type == "cosine_annealing":
            scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=training_config.get("cosine_t_max", 50))
            self.logger.log_info("📈 Using Cosine Annealing LR scheduler")
        else:  # reduce_on_plateau
            scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="min", patience=10, factor=0.5)
            self.logger.log_info("📈 Using ReduceLROnPlateau scheduler")

        return scheduler

    def get_loss_function(self) -> nn.Module:
        """Get loss function based on configuration"""
        training_config = self.config["model"]["training"]
        loss_type = training_config["loss_function"]

        loss_kwargs = {}
        if loss_type == "focal":
            loss_kwargs.update({"alpha": training_config.get("focal_alpha", 1.0), "gamma": training_config.get("focal_gamma", 2.0)})
        elif loss_type == "label_smoothing":
            loss_kwargs.update({"smoothing": training_config.get("label_smoothing", 0.1)})
        elif loss_type == "combined":
            loss_kwargs.update({"alpha": training_config.get("focal_alpha", 1.0), "gamma": training_config.get("focal_gamma", 2.0), "smoothing": training_config.get("label_smoothing", 0.1)})
        elif loss_type == "uncertainty":
            loss_kwargs.update({"uncertainty_weight": training_config.get("uncertainty_weight", 0.1)})

        loss_fn = get_loss_function(loss_type, **loss_kwargs)
        self.logger.log_info(f"📉 Using {loss_type} loss function")
        return loss_fn

    def preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply advanced preprocessing and feature engineering"""
        feature_config = self.config["model"]["feature_engineering"]

        if not feature_config.get("enabled", True):
            self.logger.log_info("⚠️ Feature engineering disabled")
            return df

        self.logger.log_info("🔧 Starting advanced feature engineering...")

        # Apply feature engineering
        df = self.feature_engineer.engineer_all_features(df)

        # Feature selection
        if feature_config.get("feature_selection_enabled", False):
            if feature_config.get("feature_selection_method"):
                X = df.drop(["class"], axis=1)
                y = df["class"].astype(int)  # Ensure y is a Series with proper type
                X_selected = self.feature_engineer.select_features(X, y, method=feature_config["feature_selection_method"], k=feature_config.get("n_features", 100))
                df = pd.concat([X_selected, y], axis=1)

        # Dimensionality reduction
        if feature_config.get("use_pca", False):
            X = df.drop(["class"], axis=1)
            y = df["class"].astype(int)  # Ensure y is a Series with proper type
            X_reduced = self.feature_engineer.apply_pca(X, n_components=feature_config.get("pca_components", 50))
            df = pd.concat([X_reduced, y], axis=1)

        # Scaling
        if feature_config.get("scaling_method"):
            X = df.drop(["class"], axis=1)
            y = df["class"].astype(int)  # Ensure y is a Series with proper type
            X_scaled = self.feature_engineer.scale_features(X, method=feature_config["scaling_method"])
            df = pd.concat([X_scaled, y], axis=1)

        self.logger.log_info(f"✅ Feature engineering complete. Final shape: {df.shape}")
        return df

    def train_epoch(self, model: nn.Module, train_loader: DataLoader, optimizer: optim.Optimizer, loss_fn: nn.Module, use_gene_embedding: bool = False) -> Tuple[float, float, float, float, float, float]:
        """Train for one epoch and return loss, accuracy, roc_auc, precision, recall, f1"""
        model.train()
        total_loss = 0.0
        correct = 0
        total = 0
        all_targets = []
        all_preds = []
        all_probs = []

        for batch_idx, batch in tqdm(enumerate(train_loader), leave=False, desc="Training", total=len(train_loader)):
            if use_gene_embedding:
                features, gene_idx, target = batch
                features, gene_idx, target = features.to(self.device), gene_idx.to(self.device), target.to(self.device)
                optimizer.zero_grad()
                output = model(features, gene_idx=gene_idx)
                loss = loss_fn(output, target)
                loss.backward()
                # Gradient clipping
                if self.config["model"]["regularization"].get("gradient_clipping", False):
                    max_grad_norm = self.config["model"]["regularization"].get("max_grad_norm", 1.0)
                    torch.nn.utils.clip_grad_norm_(model.parameters(), max_grad_norm)
                optimizer.step()
            else:
                features, target = batch
                features, target = features.to(self.device), target.to(self.device)
                optimizer.zero_grad()
                output = model(features)
                loss = loss_fn(output, target)
                loss.backward()
                # Gradient clipping
                if self.config["model"]["regularization"].get("gradient_clipping", False):
                    max_grad_norm = self.config["model"]["regularization"].get("max_grad_norm", 1.0)
                    torch.nn.utils.clip_grad_norm_(model.parameters(), max_grad_norm)
                optimizer.step()
            total_loss += loss.item()
            _, predicted = torch.max(output.data, 1)
            total += target.size(0)
            correct += (predicted == target).sum().item()
            all_targets.extend(target.cpu().numpy())
            all_preds.extend(predicted.cpu().numpy())
            all_probs.extend(torch.softmax(output, dim=1)[:, 1].detach().cpu().numpy())
        avg_loss = total_loss / len(train_loader)
        accuracy = correct / total
        # Compute metrics
        try:
            roc_auc = roc_auc_score(all_targets, all_probs)
        except Exception:
            roc_auc = float("nan")
        precision = precision_score(all_targets, all_preds, zero_division=0)
        recall = recall_score(all_targets, all_preds, zero_division=0)
        f1 = f1_score(all_targets, all_preds, zero_division=0)
        return avg_loss, accuracy, roc_auc, precision, recall, f1

    def evaluate(self, model: nn.Module, test_loader: DataLoader, loss_fn: nn.Module, use_gene_embedding: bool = False) -> Tuple[float, float, float, float, float, float]:
        """Evaluate model and return loss, accuracy, roc_auc, precision, recall, f1"""
        model.eval()
        total_loss = 0.0
        correct = 0
        total = 0
        all_targets = []
        all_preds = []
        all_probs = []
        with torch.no_grad():
            for batch in test_loader:
                if use_gene_embedding:
                    features, gene_idx, target = batch
                    features, gene_idx, target = features.to(self.device), gene_idx.to(self.device), target.to(self.device)
                    output = model(features, gene_idx=gene_idx)
                else:
                    features, target = batch
                    features, target = features.to(self.device), target.to(self.device)
                    output = model(features)
                loss = loss_fn(output, target)
                total_loss += loss.item()
                _, predicted = torch.max(output.data, 1)
                total += target.size(0)
                correct += (predicted == target).sum().item()
                all_targets.extend(target.cpu().numpy())
                all_preds.extend(predicted.cpu().numpy())
                all_probs.extend(torch.softmax(output, dim=1)[:, 1].detach().cpu().numpy())
        avg_loss = total_loss / len(test_loader)
        accuracy = correct / total
        # Compute metrics
        try:
            roc_auc = roc_auc_score(all_targets, all_probs)
        except Exception:
            roc_auc = float("nan")
        precision = precision_score(all_targets, all_preds, zero_division=0)
        recall = recall_score(all_targets, all_preds, zero_division=0)
        f1 = f1_score(all_targets, all_preds, zero_division=0)
        return avg_loss, accuracy, roc_auc, precision, recall, f1

    def train_with_kfold_cv(self, train_data: pd.DataFrame, val_data: pd.DataFrame) -> Dict:
        """Train model using k-fold cross validation
        Args:
            train_data: Training data (will be split into k folds)
            val_data: Validation data (used for final evaluation)
        """
        self.logger.log_info("🔄 Starting k-fold cross validation training...")

        # Get cross validation settings from config
        cv_config = self.config["model"]["evaluation"]
        n_folds = cv_config.get("cv_folds", 5)
        random_state = cv_config.get("cv_random_state", 42)

        self.logger.log_info(f"📊 Using {n_folds}-fold cross validation")

        # Preprocess data
        train_data = self.preprocess_data(train_data)
        val_data = self.preprocess_data(val_data)

        # Initialize k-fold splitter
        kfold = KFold(n_splits=n_folds, shuffle=True, random_state=random_state)

        # Store results for each fold
        fold_results = []
        all_training_histories = []

        # Get feature columns (excluding target)
        feature_cols = [col for col in train_data.columns if col != "class"]
        X = train_data[feature_cols]
        y = train_data["class"]

        use_gene_embedding = self.config["model"]["feature_engineering"].get("use_gene_embedding", False)
        gene_vocab_size = self.feature_engineer.gene_vocab_size

        for fold_idx, (train_idx, test_idx) in tqdm.tqdm(enumerate(kfold.split(X)), leave=False, desc="K-Fold CV", total=n_folds):
            self.logger.log_info(f"🔄 Starting Fold {fold_idx + 1}/{n_folds}")

            # Split data for this fold
            X_train_fold, X_test_fold = X.iloc[train_idx], X.iloc[test_idx]
            y_train_fold, y_test_fold = y.iloc[train_idx], y.iloc[test_idx]

            # Create fold datasets
            train_fold_data = pd.concat([X_train_fold, y_train_fold], axis=1)
            test_fold_data = pd.concat([X_test_fold, y_test_fold], axis=1)

            train_dataset = ImprovedClinVarDataset(train_fold_data, use_gene_embedding=use_gene_embedding)
            test_dataset = ImprovedClinVarDataset(test_fold_data, use_gene_embedding=use_gene_embedding)

            # Create data loaders
            batch_size = self.config["model"]["training"]["batch_size"]

            # Weighted random sampler for class imbalance
            use_weighted_sampler = self.config["model"]["training"].get("use_weighted_sampler", True)
            if use_weighted_sampler:
                class_sample_count = train_fold_data["class"].value_counts().sort_index().values
                weights = 1.0 / np.array(class_sample_count, dtype=np.float32)
                class_to_weight = {cls: w for cls, w in zip(train_fold_data["class"].value_counts().sort_index().index, weights)}
                sample_weights = train_fold_data["class"].map(lambda x: class_to_weight[x]).values
                sampler = WeightedRandomSampler(weights=sample_weights, num_samples=len(sample_weights), replacement=True)
                train_loader = DataLoader(train_dataset, batch_size=batch_size, sampler=sampler)
            else:
                train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)

            test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

            # Create model for this fold
            input_size = len(train_dataset.feature_cols)
            model = self.create_model(input_size, gene_vocab_size=gene_vocab_size, use_gene_embedding=use_gene_embedding)

            # Create optimizer and loss function
            optimizer = self.get_optimizer(model)
            scheduler = self.get_scheduler(optimizer)
            loss_fn = self.get_loss_function()

            # Training loop for this fold
            best_test_loss = float("inf")
            patience = self.config["model"]["regularization"].get("patience", 10)
            patience_counter = 0
            training_history = []
            max_epochs = self.config["model"]["training"].get("max_epochs", 100)

            for epoch in range(max_epochs):
                # Train
                train_loss, train_acc, train_roc_auc, train_prec, train_rec, train_f1 = self.train_epoch(model, train_loader, optimizer, loss_fn, use_gene_embedding)
                # Per-epoch evaluation on test set
                test_loss, test_acc, test_roc_auc, test_prec, test_rec, test_f1 = self.evaluate(model, test_loader, loss_fn, use_gene_embedding)

                # Update scheduler
                if isinstance(scheduler, optim.lr_scheduler.ReduceLROnPlateau):
                    scheduler.step(test_loss)
                else:
                    scheduler.step()

                # Log progress (less verbose for k-fold)
                if (epoch + 1) % 10 == 0:
                    self.logger.log_info(
                        f"Fold {fold_idx + 1}, Epoch {epoch + 1:3d}: Train Loss: {train_loss:.4f}, Acc: {train_acc:.4f}, ROC_AUC: {train_roc_auc:.4f}, Precision: {train_prec:.4f}, Recall: {train_rec:.4f}; Test Loss: {test_loss:.4f}, Acc: {test_acc:.4f}, ROC_AUC: {test_roc_auc:.4f}, Precision: {test_prec:.4f}, Recall: {test_rec:.4f}"
                    )

                # Save training history
                training_history.append(
                    {
                        "fold": fold_idx + 1,
                        "epoch": epoch + 1,
                        "train_loss": train_loss,
                        "train_acc": train_acc,
                        "train_roc_auc": train_roc_auc,
                        "train_precision": train_prec,
                        "train_recall": train_rec,
                        "train_f1": train_f1,
                        "test_loss": test_loss,
                        "test_acc": test_acc,
                        "test_roc_auc": test_roc_auc,
                        "test_precision": test_prec,
                        "test_recall": test_rec,
                        "test_f1": test_f1,
                        "lr": optimizer.param_groups[0]["lr"],
                    }
                )

                # Early stopping
                if test_loss < best_test_loss - float(self.config["model"]["regularization"].get("min_delta", 1e-4)):
                    best_test_loss = test_loss
                    patience_counter = 0
                    # Save best model for this fold
                    torch.save(model.state_dict(), f"models/checkpoints/best_model_fold_{fold_idx + 1}.pt")
                else:
                    patience_counter += 1

                if patience_counter >= patience:
                    self.logger.log_info(f"🛑 Early stopping at epoch {epoch + 1} for fold {fold_idx + 1}")
                    break

            # Load best model for this fold
            model.load_state_dict(torch.load(f"models/checkpoints/best_model_fold_{fold_idx + 1}.pt"))

            # Final evaluation on test set for this fold
            final_test_loss, final_test_acc, final_test_roc_auc, final_test_prec, final_test_rec, final_test_f1 = self.evaluate(model, test_loader, loss_fn, use_gene_embedding)

            # Store fold results
            fold_result = {
                "fold": fold_idx + 1,
                "final_test_loss": final_test_loss,
                "final_test_accuracy": final_test_acc,
                "final_test_roc_auc": final_test_roc_auc,
                "final_test_precision": final_test_prec,
                "final_test_recall": final_test_rec,
                "final_test_f1": final_test_f1,
                "best_test_loss": best_test_loss,
                "epochs_trained": len(training_history),
            }

            fold_results.append(fold_result)
            all_training_histories.extend(training_history)

            self.logger.log_info(f"✅ Fold {fold_idx + 1} completed - Test Acc: {final_test_acc:.4f}, ROC_AUC: {final_test_roc_auc:.4f}, Precision: {final_test_prec:.4f}, Recall: {final_test_rec:.4f}, F1: {final_test_f1:.4f}")

        # Calculate cross-validation statistics
        cv_stats = self._calculate_cv_statistics(fold_results)

        # Final evaluation on validation set using the best fold model
        best_fold_idx = np.argmax([result["final_test_roc_auc"] for result in fold_results])
        best_model_path = f"models/checkpoints/best_model_fold_{best_fold_idx + 1}.pt"

        # Create validation dataset and loader
        val_dataset = ImprovedClinVarDataset(val_data, use_gene_embedding=use_gene_embedding)
        val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

        # Load best model and evaluate on validation set
        model = self.create_model(len(val_dataset.feature_cols), gene_vocab_size=gene_vocab_size, use_gene_embedding=use_gene_embedding)
        model.load_state_dict(torch.load(best_model_path))
        loss_fn = self.get_loss_function()

        final_val_loss, final_val_acc, final_val_roc_auc, final_val_prec, final_val_rec, final_val_f1 = self.evaluate(model, val_loader, loss_fn, use_gene_embedding)

        self.logger.log_info(f"🎯 Cross-validation completed!")
        self.logger.log_info(f"📊 CV Statistics - Mean ROC_AUC: {cv_stats['mean_test_roc_auc']:.4f} ± {cv_stats['std_test_roc_auc']:.4f}")
        self.logger.log_info(f"🎯 Final Validation Results - Loss: {final_val_loss:.4f}, Acc: {final_val_acc:.4f}, ROC_AUC: {final_val_roc_auc:.4f}, Precision: {final_test_prec:.4f}, Recall: {final_test_rec:.4f}, F1: {final_val_f1:.4f}")

        return {
            "fold_results": fold_results,
            "cv_statistics": cv_stats,
            "training_history": all_training_histories,
            "final_val_loss": final_val_loss,
            "final_val_accuracy": final_val_acc,
            "final_val_roc_auc": final_val_roc_auc,
            "final_val_precision": final_val_prec,
            "final_val_recall": final_val_rec,
            "final_val_f1": final_val_f1,
            "best_fold": best_fold_idx + 1,
            "feature_engineering_summary": self.feature_engineer.get_feature_summary(),
        }

    def _calculate_cv_statistics(self, fold_results: List[Dict]) -> Dict:
        """Calculate cross-validation statistics"""
        metrics = ["final_test_accuracy", "final_test_roc_auc", "final_test_precision", "final_test_recall", "final_test_f1"]

        cv_stats = {}
        for metric in metrics:
            values = [result[metric] for result in fold_results]
            cv_stats[f"mean_{metric.split('_', 1)[1]}"] = np.mean(values)
            cv_stats[f"std_{metric.split('_', 1)[1]}"] = np.std(values)
            cv_stats[f"min_{metric.split('_', 1)[1]}"] = np.min(values)
            cv_stats[f"max_{metric.split('_', 1)[1]}"] = np.max(values)

        return cv_stats

    def train(self, train_data: pd.DataFrame, test_data: pd.DataFrame, val_data: pd.DataFrame) -> Dict:
        """Complete training pipeline with optional k-fold cross validation
        Args:
            train_data: Training set
            test_data: Test set (used for per-epoch evaluation)
            val_data: Validation set (used for final evaluation after training)
        """
        # Check if k-fold cross validation is enabled
        cv_config = self.config["model"]["evaluation"]
        use_cv = cv_config.get("use_cross_validation", False)

        if use_cv:
            self.logger.log_info("🔄 K-fold cross validation enabled")
            # For k-fold CV, we use train_data for k-fold splits and val_data for final evaluation
            return self.train_with_kfold_cv(train_data, val_data)
        else:
            self.logger.log_info("🚀 Starting standard training pipeline...")
            # Standard training pipeline (existing code)
            # Preprocess data
            train_data = self.preprocess_data(train_data)
            test_data = self.preprocess_data(test_data)
            val_data = self.preprocess_data(val_data)
            # Create datasets
            train_dataset = ImprovedClinVarDataset(train_data)
            test_dataset = ImprovedClinVarDataset(test_data)
            val_dataset = ImprovedClinVarDataset(val_data)
            # Create data loaders
            batch_size = self.config["model"]["training"]["batch_size"]

            # Weighted random sampler for class imbalance (conditional)
            use_weighted_sampler = self.config["model"]["training"].get("use_weighted_sampler", True)
            if use_weighted_sampler:
                class_sample_count = train_data["class"].value_counts().sort_index().values
                weights = 1.0 / np.array(class_sample_count, dtype=np.float32)
                class_to_weight = {cls: w for cls, w in zip(train_data["class"].value_counts().sort_index().index, weights)}
                sample_weights = train_data["class"].map(lambda x: class_to_weight[x]).values
                sampler = WeightedRandomSampler(weights=sample_weights, num_samples=len(sample_weights), replacement=True)
                train_loader = DataLoader(train_dataset, batch_size=batch_size, sampler=sampler)
                self.logger.log_info("⚖️ Using weighted random sampler for class imbalance")
            else:
                train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
                self.logger.log_info("🔄 Using standard random sampling")

            test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)  # per-epoch evaluation
            val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)  # final evaluation
            # Create model
            input_size = len(train_dataset.feature_cols)
            use_gene_embedding = self.config["model"]["feature_engineering"].get("use_gene_embedding", False)
            gene_vocab_size = self.feature_engineer.gene_vocab_size
            model = self.create_model(input_size, gene_vocab_size=gene_vocab_size, use_gene_embedding=use_gene_embedding)
            # Create optimizer and loss function
            optimizer = self.get_optimizer(model)
            scheduler = self.get_scheduler(optimizer)
            loss_fn = self.get_loss_function()
            # Training loop
            best_test_loss = float("inf")
            patience = self.config["model"]["regularization"].get("patience", 10)
            patience_counter = 0
            training_history = []
            max_epochs = self.config["model"]["training"].get("max_epochs", 100)

            self.logger.log_info(f"🚀 Starting training for up to {max_epochs} epochs")
            self.logger.log_info(f"⏰ Early stopping patience: {patience}")

            for epoch in range(max_epochs):
                # Train
                train_loss, train_acc, train_roc_auc, train_prec, train_rec, train_f1 = self.train_epoch(model, train_loader, optimizer, loss_fn, use_gene_embedding)
                # Per-epoch evaluation on test set
                test_loss, test_acc, test_roc_auc, test_prec, test_rec, test_f1 = self.evaluate(model, test_loader, loss_fn, use_gene_embedding)
                # Update scheduler
                if isinstance(scheduler, optim.lr_scheduler.ReduceLROnPlateau):
                    scheduler.step(test_loss)
                else:
                    scheduler.step()
                # Log progress
                if (epoch + 1) % 1 == 0:
                    self.logger.log_info(
                        f"Epoch {epoch + 1:3d}: "
                        f"Train Loss: {train_loss:.4f}, Acc: {train_acc:.4f}, ROC_AUC: {train_roc_auc:.4f}, Prec: {train_prec:.4f}, Rec: {train_rec:.4f}, F1: {train_f1:.4f}; "
                        f"Test Loss: {test_loss:.4f}, Acc: {test_acc:.4f}, ROC_AUC: {test_roc_auc:.4f}, Prec: {test_prec:.4f}, Rec: {test_rec:.4f}, F1: {test_f1:.4f}; "
                        f"LR: {optimizer.param_groups[0]['lr']:.6f}"
                    )
                # Save training history
                training_history.append(
                    {
                        "epoch": epoch + 1,
                        "train_loss": train_loss,
                        "train_acc": train_acc,
                        "train_roc_auc": train_roc_auc,
                        "train_precision": train_prec,
                        "train_recall": train_rec,
                        "train_f1": train_f1,
                        "test_loss": test_loss,
                        "test_acc": test_acc,
                        "test_roc_auc": test_roc_auc,
                        "test_precision": test_prec,
                        "test_recall": test_rec,
                        "test_f1": test_f1,
                        "lr": optimizer.param_groups[0]["lr"],
                    }
                )
                # Early stopping
                if test_loss < best_test_loss - float(self.config["model"]["regularization"].get("min_delta", 1e-4)):
                    best_test_loss = test_loss
                    patience_counter = 0
                    # Save best model
                    torch.save(model.state_dict(), "models/checkpoints/best_model.pt")
                else:
                    patience_counter += 1
                if patience_counter >= patience:
                    self.logger.log_info(f"🛑 Early stopping at epoch {epoch + 1}")
                    break
            # Load best model and evaluate on all sets
            model.load_state_dict(torch.load("models/checkpoints/best_model.pt"))
            # Final evaluation on all sets
            final_train_loss, final_train_acc, final_train_roc_auc, final_train_prec, final_train_rec, final_train_f1 = self.evaluate(model, train_loader, loss_fn, use_gene_embedding)
            final_test_loss, final_test_acc, final_test_roc_auc, final_test_prec, final_test_rec, final_test_f1 = self.evaluate(model, test_loader, loss_fn, use_gene_embedding)
            final_val_loss, final_val_acc, final_val_roc_auc, final_val_prec, final_val_rec, final_val_f1 = self.evaluate(model, val_loader, loss_fn, use_gene_embedding)

            self.logger.log_info(f"🎯 Final Train Results - Loss: {final_train_loss:.4f}, Acc: {final_train_acc:.4f}, ROC_AUC: {final_train_roc_auc:.4f}, Prec: {final_train_prec:.4f}, Rec: {final_train_rec:.4f}, F1: {final_train_f1:.4f}")
            self.logger.log_info(f"🎯 Final Test Results - Loss: {final_test_loss:.4f}, Acc: {final_test_acc:.4f}, ROC_AUC: {final_test_roc_auc:.4f}, Prec: {final_test_prec:.4f}, Rec: {final_test_rec:.4f}, F1: {final_test_f1:.4f}")
            self.logger.log_info(f"🎯 Final Validation Results - Loss: {final_val_loss:.4f}, Acc: {final_val_acc:.4f}, ROC_AUC: {final_val_roc_auc:.4f}, Prec: {final_val_prec:.4f}, Rec: {final_val_rec:.4f}, F1: {final_val_f1:.4f}")

            return {
                "training_history": training_history,
                "final_train_loss": final_train_loss,
                "final_train_accuracy": final_train_acc,
                "final_train_roc_auc": final_train_roc_auc,
                "final_train_precision": final_train_prec,
                "final_train_recall": final_train_rec,
                "final_train_f1": final_train_f1,
                "final_test_loss": final_test_loss,
                "final_test_accuracy": final_test_acc,
                "final_test_roc_auc": final_test_roc_auc,
                "final_test_precision": final_test_prec,
                "final_test_recall": final_test_rec,
                "final_test_f1": final_test_f1,
                "final_val_loss": final_val_loss,
                "final_val_accuracy": final_val_acc,
                "final_val_roc_auc": final_val_roc_auc,
                "final_val_precision": final_val_prec,
                "final_val_recall": final_val_rec,
                "final_val_f1": final_val_f1,
                "best_test_loss": best_test_loss,
                "feature_engineering_summary": self.feature_engineer.get_feature_summary(),
            }


def main():
    """Main function to run the advanced training"""
    print("🚀 Starting Advanced ClinVar Training Pipeline")

    # Load data
    data_dir = Path("data/processed")
    train_data = pd.read_csv(data_dir / "train.csv")
    test_data = pd.read_csv(data_dir / "test.csv")  # Now used for per-epoch evaluation
    val_data = pd.read_csv(data_dir / "validation.csv")  # Now used for final evaluation

    print(f"📊 Data loaded - Train: {train_data.shape}, Test (per-epoch): {test_data.shape}, Validation (final): {val_data.shape}")

    # Initialize trainer
    trainer = AdvancedTrainer()

    # Run training
    results = trainer.train(train_data, test_data, val_data)

    # Save results
    results_dir = Path("results/advanced_training")
    results_dir.mkdir(parents=True, exist_ok=True)

    # Check if this was k-fold cross validation
    if "fold_results" in results:
        # K-fold cross validation results
        print("📊 Saving k-fold cross validation results...")

        # Save training history
        history_df = pd.DataFrame(results["training_history"])
        history_df.to_csv(results_dir / "cv_training_history.csv", index=False)

        # Save fold results
        fold_results_df = pd.DataFrame(results["fold_results"])
        fold_results_df.to_csv(results_dir / "fold_results.csv", index=False)

        # Save cross-validation statistics
        cv_stats = results["cv_statistics"]
        with open(results_dir / "cv_statistics.yaml", "w") as f:
            yaml.dump(cv_stats, f, default_flow_style=False)

        # Save final results (validation set results)
        final_results = {
            "final_val_loss": results["final_val_loss"],
            "final_val_accuracy": results["final_val_accuracy"],
            "final_val_roc_auc": results["final_val_roc_auc"],
            "final_val_precision": results["final_val_precision"],
            "final_val_recall": results["final_val_recall"],
            "final_val_f1": results["final_val_f1"],
            "best_fold": results["best_fold"],
            "cv_statistics": cv_stats,
            "feature_engineering_summary": results["feature_engineering_summary"],
        }

        with open(results_dir / "cv_final_results.yaml", "w") as f:
            yaml.dump(final_results, f, default_flow_style=False)

        print(f"📊 Cross-validation statistics:")
        print(f"   Mean ROC_AUC: {cv_stats['mean_test_roc_auc']:.4f} ± {cv_stats['std_test_roc_auc']:.4f}")
        print(f"   Mean Accuracy: {cv_stats['mean_test_accuracy']:.4f} ± {cv_stats['std_test_accuracy']:.4f}")
        print(f"   Mean F1: {cv_stats['mean_test_f1']:.4f} ± {cv_stats['std_test_f1']:.4f}")
        print(f"   Best fold: {results['best_fold']}")

    else:
        # Standard training results
        print("📊 Saving standard training results...")

        # Save training history
        history_df = pd.DataFrame(results["training_history"])
        history_df.to_csv(results_dir / "training_history.csv", index=False)

        # Save final results
        final_results = {
            "final_train_loss": results["final_train_loss"],
            "final_train_accuracy": results["final_train_accuracy"],
            "final_train_roc_auc": results["final_train_roc_auc"],
            "final_train_precision": results["final_train_precision"],
            "final_train_recall": results["final_train_recall"],
            "final_train_f1": results["final_train_f1"],
            "final_test_loss": results["final_test_loss"],
            "final_test_accuracy": results["final_test_accuracy"],
            "final_test_roc_auc": results["final_test_roc_auc"],
            "final_test_precision": results["final_test_precision"],
            "final_test_recall": results["final_test_recall"],
            "final_test_f1": results["final_test_f1"],
            "final_val_loss": results["final_val_loss"],
            "final_val_accuracy": results["final_val_accuracy"],
            "final_val_roc_auc": results["final_val_roc_auc"],
            "final_val_precision": results["final_val_precision"],
            "final_val_recall": results["final_val_recall"],
            "final_val_f1": results["final_val_f1"],
            "best_test_loss": results["best_test_loss"],
            "feature_engineering_summary": results["feature_engineering_summary"],
        }

        with open(results_dir / "final_results.yaml", "w") as f:
            yaml.dump(final_results, f, default_flow_style=False)

    print("✅ Training completed successfully!")
    print(f"📁 Results saved to: {results_dir}")


if __name__ == "__main__":
    main()
