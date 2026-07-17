import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import pandas as pd
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from sklearn.preprocessing import LabelEncoder, StandardScaler
from gensim.models import Word2Vec
import flwr as fl
from flwr.common import Parameters, FitRes, EvaluateRes, Scalar
from torch.utils.data import DataLoader, TensorDataset, WeightedRandomSampler
from torch.optim.lr_scheduler import ReduceLROnPlateau

from src.models.improved_pathogenicity_model import create_model, get_model_summary
from src.models.feature_engineering import GenomicFeatureEngineer
from src.models.loss_functions import get_loss_function
from src.utils.logger import Logger
from src.models.ref_alt_embeddings import KmerGenerator
from src.federated.config_loader import ConfigLoader


class ClinVarDataset:
    """Dataset for ClinVar data with preprocessing"""

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


class FederatedClient(fl.client.NumPyClient):
    """Simplified federated client without adaptive mu tracking or visualization components"""

    # def __init__(self, client_id: int, client_config_path: str = None, data_config_path: str = None, model_config_path: str = None, federated_config_path: str = None):
    def __init__(self, client_id: int, client_config_path: str = None, data_config_path: str = None, model_config_path: str = None):
        self.client_id = client_id

        # Load configurations with backward compatibility
        if client_config_path:
            # New modular format
            self.client_config = ConfigLoader.load_client_config(client_config_path)
            self.client_params = self.client_config["client"]
        # elif federated_config_path:
        #     # Legacy format
        #     legacy_config = ConfigLoader.load_federated_config(federated_config_path)
        #     self.client_params = legacy_config.get("client", {})
        #     # Create client_config structure for consistency
        #     self.client_config = {"client": self.client_params}
        else:
            # Try automatic loading with fallback
            try:
                configs = ConfigLoader.load_config_with_fallback()
                self.client_config = configs["client"]
                self.client_params = self.client_config["client"]
            except FileNotFoundError as e:
                raise FileNotFoundError(f"No valid client configuration found. Please provide either client_config_path (new format) or federated_config_path (legacy format), or ensure default config files exist. Error: {e}")

        # Maintain backward compatibility with federated_config
        # self.federated_config = {"client": self.client_params}

        # Load data and model configurations
        data_path = data_config_path or "configs/data_config.yaml"
        model_path = model_config_path or "configs/model_config.yaml"

        self.data_config = self._load_config(data_path)["data"]
        # Load full model config to access all sections (model, architecture, feature_engineering, etc.)
        self.model_config_full = self._load_config(model_path)
        self.model_config = self.model_config_full  # For backward compatibility, keep full config

        # Initialize logger
        self.logger = Logger(log_dir=f"logs/client_{client_id}")

        # Set device
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.logger.log_info(f"Using device: {self.device}")

        # Load client data
        self.train_data, self.test_data = self._load_client_data()

        # Initialize feature engineer
        self.feature_engineer = GenomicFeatureEngineer()

        # Setup preprocessing components (must be before model init)
        self._setup_preprocessing()

        # Initialize model (after preprocessing is ready)
        self.model = self._initialize_model().to(self.device)

        # Prepare data
        self.train_loader, self.test_loader = self._prepare_data()

        self.logger.log_info(f"Federated Client {client_id} initialized successfully")

    def _load_config(self, config_path: str) -> dict:
        """Load YAML configuration file"""
        with open(config_path, "r") as f:
            return yaml.safe_load(f)

    def _load_client_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Load client-specific training and test data"""
        # Get client data directory from client config, with fallback to default
        client_data_dir = self.client_config.get("data", {}).get("client_data_dir", "federated_data/non_iid_partition/clients")
        client_dir = Path(client_data_dir) / f"client_{self.client_id}" if self.client_id is not None else Path(client_data_dir)
        train_path = client_dir / "train.csv"
        test_path = client_dir / "test.csv"

        if not train_path.exists() or not test_path.exists():
            raise FileNotFoundError(f"Client data not found at {client_dir}")

        train_df = pd.read_csv(train_path)
        test_df = pd.read_csv(test_path)
        self.logger.log_info(f"Loaded client data - Train: {len(train_df)}, Test: {len(test_df)}")
        return train_df, test_df

    def _initialize_model(self):
        """Initialize model based on configuration"""
        input_size = self._calculate_input_size()
        output_size = self.model_config["architecture"]["output_dim"]
        model_type = self.model_config["architecture"].get("model_type", "improved")

        # Get model-specific configuration
        if model_type == "improved":
            improved_config = self.model_config["architecture"].get("improved_model", {})
            model = create_model(
                model_type="improved",
                input_size=input_size,
                output_size=output_size,
                hidden_dims=improved_config.get("hidden_dims", [512, 256, 128, 64]),
                dropout=improved_config.get("dropout", 0.3),
                gene_vocab_size=self.feature_engineer.gene_vocab_size,
                use_gene_embedding=self.model_config["feature_engineering"].get("use_gene_embedding", False),
            )
        elif model_type == "lightweight":
            lightweight_config = self.model_config["architecture"].get("lightweight_model", {})
            model = create_model(
                model_type="lightweight",
                input_size=input_size,
                output_size=output_size,
                hidden_dims=lightweight_config.get("hidden_dims", [512, 256, 128, 64, 32]),
                dropout=lightweight_config.get("dropout", 0.2),
                gene_vocab_size=self.feature_engineer.gene_vocab_size,
                use_gene_embedding=self.model_config["feature_engineering"].get("use_gene_embedding", False),
            )
        elif model_type == "ensemble":
            ensemble_config = self.model_config["architecture"].get("ensemble_model", {})
            member_type = ensemble_config.get("ensemble_member_type", "improved")
            if member_type == "improved":
                member_configs = ensemble_config.get("improved_member_settings", {})
            elif member_type == "lightweight":
                member_configs = ensemble_config.get("lightweight_member_settings", {})

            hidden_dims = member_configs.get("hidden_dims", [[512, 256, 128, 64, 32]] * ensemble_config.get("num_models", 3))

            model = create_model(
                model_type="ensemble",
                input_size=input_size,
                output_size=output_size,
                ensemble_member_type=member_type,
                num_models=ensemble_config.get("num_models", 3),
                hidden_dims=hidden_dims,
                dropout=member_configs.get("dropout", 0.3),
                gene_vocab_size=self.feature_engineer.gene_vocab_size,
                use_gene_embedding=self.model_config["feature_engineering"].get("use_gene_embedding", False),
            )
        else:
            # Fallback to improved model
            model = create_model(
                model_type="improved",
                input_size=input_size,
                output_size=output_size,
                gene_vocab_size=self.feature_engineer.gene_vocab_size,
                use_gene_embedding=self.model_config["feature_engineering"].get("use_gene_embedding", False),
            )

        # Get model summary
        model_summary = get_model_summary(model)
        self.logger.log_info(f"Initialized {model_type} model: {model_summary}")
        return model

    def _calculate_input_size(self) -> int:
        """Calculate input size for model based on preprocessed data"""
        sample_df = self.train_data.head(1).copy()
        processed_sample = self._preprocess_data(sample_df)
        use_gene_embedding = self.model_config["feature_engineering"].get("use_gene_embedding", False)
        if use_gene_embedding and "gene" in processed_sample.columns:
            return processed_sample.shape[1] - 2  # Subtract 1 for target column and 1 for gene column
        else:
            return processed_sample.shape[1] - 1  # Subtract 1 for target column

    def _setup_preprocessing(self):
        """Setup preprocessing components"""
        ref_model_path = Path("models/global_models/ref_word2vec.model")
        alt_model_path = Path("models/global_models/alt_word2vec.model")

        if not ref_model_path.exists() or not alt_model_path.exists():
            raise FileNotFoundError("Word2Vec models not found")

        self.ref_model = Word2Vec.load(str(ref_model_path))
        self.alt_model = Word2Vec.load(str(alt_model_path))
        self.label_encoder = LabelEncoder()

        # Ensure chromosome values are strings for consistent encoding
        all_chr_values = pd.concat([self.train_data["chr"].astype(str), self.test_data["chr"].astype(str)]).unique()
        self.label_encoder.fit(all_chr_values)
        self.kmer_gen = KmerGenerator(k=3)  # Default k=3, can be made configurable
        self.scaler = StandardScaler()

        # Set the chromosome encoder in feature engineer
        self.feature_engineer.label_encoders["chr"] = self.label_encoder

        self.logger.log_info("Preprocessing components initialized")

    def _preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply preprocessing and feature engineering"""
        df = df.copy()
        df = self._embed_ref_alt(df)

        # Apply feature engineering if enabled (this will handle chr encoding)
        feature_config = self.model_config["feature_engineering"]
        if feature_config.get("enabled", True):
            df = self.feature_engineer.engineer_all_features(df)
        else:
            # If feature engineering is disabled, still encode chr manually
            df["chr"] = self.label_encoder.transform(df["chr"])

        return df

    def _embed_ref_alt(self, df: pd.DataFrame) -> pd.DataFrame:
        """Embed reference and alternate sequences using Word2Vec models"""

        def embed_sequence(seq, model, k=3):
            tokens = self.kmer_gen.generate_kmers(seq)
            vectors = [model.wv[kmer] for kmer in tokens if kmer in model.wv]
            if len(vectors) == 0:
                return np.zeros(model.vector_size)
            return np.mean(vectors, axis=0)

        ref_embeddings = df["ref"].apply(lambda x: embed_sequence(x, self.ref_model))
        alt_embeddings = df["alt"].apply(lambda x: embed_sequence(x, self.alt_model))

        ref_emb_df = pd.DataFrame(ref_embeddings.tolist(), columns=pd.Index([f"ref_emb_{i}" for i in range(self.ref_model.vector_size)]), dtype=np.float32)
        alt_emb_df = pd.DataFrame(alt_embeddings.tolist(), columns=pd.Index([f"alt_emb_{i}" for i in range(self.alt_model.vector_size)]), dtype=np.float32)

        final_df = pd.concat([df.drop(columns=["ref", "alt"]), ref_emb_df, alt_emb_df], axis=1)
        return final_df

    def _prepare_data(self) -> Tuple[DataLoader, DataLoader]:
        """Prepare training and test data loaders"""
        train_processed = self._preprocess_data(self.train_data)
        test_processed = self._preprocess_data(self.test_data)

        use_gene_embedding = self.model_config["feature_engineering"].get("use_gene_embedding", False)

        # Create datasets
        train_dataset = ClinVarDataset(train_processed, use_gene_embedding=use_gene_embedding)
        test_dataset = ClinVarDataset(test_processed, use_gene_embedding=use_gene_embedding)

        # Prepare features and targets for scaling
        X_train = train_processed[train_dataset.feature_cols]
        X_test = test_processed[test_dataset.feature_cols]

        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Update the processed data with scaled features
        train_processed[train_dataset.feature_cols] = X_train_scaled
        test_processed[test_dataset.feature_cols] = X_test_scaled

        # Recreate datasets with scaled data
        train_dataset = ClinVarDataset(train_processed, use_gene_embedding=use_gene_embedding)
        test_dataset = ClinVarDataset(test_processed, use_gene_embedding=use_gene_embedding)

        # Get batch size from client config with fallback to model config for backward compatibility
        batch_size = self.client_params.get("batch_size", self.model_config.get("training", {}).get("batch_size", 32))

        # Weighted random sampler for class imbalance
        use_weighted_sampler = self.client_params.get("training", {}).get("use_weighted_sampler", self.model_config.get("training", {}).get("use_weighted_sampler", True))
        if use_weighted_sampler:
            class_sample_count = train_processed["class"].value_counts().sort_index().values
            weights = 1.0 / np.array(class_sample_count, dtype=np.float32)
            class_to_weight = {cls: w for cls, w in zip(train_processed["class"].value_counts().sort_index().index, weights)}
            sample_weights = train_processed["class"].map(lambda x: class_to_weight[x]).values
            sampler = WeightedRandomSampler(weights=sample_weights, num_samples=len(sample_weights), replacement=True)
            train_loader = DataLoader(train_dataset, batch_size=batch_size, sampler=sampler)
        else:
            train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)

        test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
        return train_loader, test_loader

    def get_parameters(self, config):
        """Get model parameters as numpy arrays"""
        return [val.cpu().numpy() for _, val in self.model.state_dict().items()]

    def set_parameters(self, parameters):
        """Set model parameters from numpy arrays"""
        params_dict = zip(self.model.state_dict().keys(), parameters)
        state_dict = {k: torch.tensor(v) for k, v in params_dict}
        self.model.load_state_dict(state_dict, strict=True)

    def fit(self, parameters, config):
        """Train the model"""
        self.set_parameters(parameters)

        # Get training configuration from client config
        epochs = int(self.client_params.get("local_epochs", 20))

        # Get learning rate from client config optimizer section
        optimizer_config = self.client_params.get("optimizer", {})
        learning_rate = float(config.get("learning_rate", optimizer_config.get("learning_rate", self.model_config.get("training", {}).get("learning_rate", 5e-4))))

        # Get weight decay from client config optimizer section
        weight_decay = float(optimizer_config.get("weight_decay", self.model_config.get("regularization", {}).get("weight_decay", 1e-3)))

        # Get federated learning strategy from training request (sent by server)
        # The server should include strategy info in the config parameter
        strategy_name = config.get("strategy", {})
        # if isinstance(strategy_info, str):
        #     strategy_name = strategy_info
        # else:
        #     strategy_name = strategy_info.get("name", "FedAvg")

        # Strategy-specific parameters
        proximal_mu = 0.0  # Default: no proximal regularization
        if strategy_name == "FedProx":
            proximal_mu = float(config.get("proximal_mu", 0.01))
            self.logger.log_info(f"FedProx training with proximal_mu={proximal_mu:.6f}")
        elif strategy_name == "FedAdam":
            self.logger.log_info(f"FedAdam training (no proximal regularization)")
        else:  # FedAvg or other strategies
            self.logger.log_info(f"{strategy_name} training (no proximal regularization)")

        # Get optimizer configuration from client config
        optimizer_config = self.client_params.get("optimizer", {})
        optimizer_name = optimizer_config.get("name", self.model_config.get("training", {}).get("optimizer", "adamw"))

        # Create optimizer based on configuration
        if optimizer_name == "adam":
            beta1 = optimizer_config.get("beta1", 0.9)
            beta2 = optimizer_config.get("beta2", 0.999)
            optimizer = torch.optim.Adam(self.model.parameters(), lr=learning_rate, weight_decay=weight_decay, betas=(beta1, beta2))
        elif optimizer_name == "adamw":
            beta1 = optimizer_config.get("beta1", 0.9)
            beta2 = optimizer_config.get("beta2", 0.999)
            optimizer = torch.optim.AdamW(self.model.parameters(), lr=learning_rate, weight_decay=weight_decay, betas=(beta1, beta2))
        elif optimizer_name == "sgd":
            momentum = optimizer_config.get("momentum", 0.9)
            optimizer = torch.optim.SGD(self.model.parameters(), lr=learning_rate, momentum=momentum, weight_decay=weight_decay)
        else:
            # Default to AdamW
            beta1 = optimizer_config.get("beta1", 0.9)
            beta2 = optimizer_config.get("beta2", 0.999)
            optimizer = torch.optim.AdamW(self.model.parameters(), lr=learning_rate, weight_decay=weight_decay, betas=(beta1, beta2))

        # Get loss function configuration from client config
        loss_config = self.client_params.get("loss", {})
        loss_type = loss_config.get("name", self.model_config.get("training", {}).get("loss_function", "cross_entropy"))

        loss_kwargs = {}
        if loss_type == "focal":
            loss_kwargs.update({"alpha": loss_config.get("focal_alpha", self.model_config.get("training", {}).get("focal_alpha", 1.0)), "gamma": loss_config.get("focal_gamma", self.model_config.get("training", {}).get("focal_gamma", 2.0))})
        elif loss_type == "label_smoothing":
            loss_kwargs.update({"smoothing": loss_config.get("label_smoothing", self.model_config.get("training", {}).get("label_smoothing", 0.1))})

        criterion = get_loss_function(loss_type, **loss_kwargs)

        # Learning rate scheduler configuration from client config
        lr_scheduler_config = self.client_params.get("lr_scheduler", {})
        scheduler_name = lr_scheduler_config.get("name", "reduce_on_plateau")

        if scheduler_name == "reduce_on_plateau":
            patience = int(lr_scheduler_config.get("patience", 3))
            factor = float(lr_scheduler_config.get("factor", 0.5))
            min_lr = float(lr_scheduler_config.get("min_lr", 1e-6))
            threshold = float(lr_scheduler_config.get("threshold", 1e-4))
            scheduler = ReduceLROnPlateau(optimizer, mode="min", factor=factor, patience=patience, min_lr=min_lr, threshold=threshold)
        else:
            # Default to ReduceLROnPlateau for backward compatibility
            scheduler = ReduceLROnPlateau(optimizer, mode="min", factor=0.5, patience=5, min_lr=1e-6, threshold=1e-3)

        self.model.train()
        total_loss = 0.0
        total_samples = 0
        best_val_loss = float("inf")
        epochs_no_improve = 0

        # Get early stopping patience from client config
        training_config = self.client_params.get("training", {})
        patience = int(training_config.get("patience", self.model_config.get("regularization", {}).get("patience", 20)))
        best_model_state = None

        # Store initial parameters for proximal term
        initial_params = {name: param.clone().detach() for name, param in self.model.named_parameters()}

        use_gene_embedding = self.model_config["feature_engineering"].get("use_gene_embedding", False)

        epoch = 0
        for epoch in range(epochs):
            epoch_loss = 0.0
            epoch_samples = 0

            for batch_idx, batch in enumerate(self.train_loader):
                if use_gene_embedding:
                    features, gene_idx, target = batch
                    features = features.to(self.device)
                    gene_idx = gene_idx.to(self.device)
                    target = target.to(self.device)
                    optimizer.zero_grad()
                    outputs = self.model(features, gene_idx=gene_idx)
                else:
                    features, target = batch
                    features = features.to(self.device)
                    target = target.to(self.device)
                    optimizer.zero_grad()
                    outputs = self.model(features)

                loss = criterion(outputs, target)

                # Add proximal term only for FedProx strategy
                if strategy_name == "FedProx" and proximal_mu > 0.0:
                    proximal_term = 0.0
                    for name, param in self.model.named_parameters():
                        if name in initial_params:
                            proximal_term += torch.norm(param - initial_params[name]) ** 2
                    proximal_term = (proximal_mu / 2) * proximal_term
                    loss += proximal_term

                loss.backward()

                # Gradient clipping from client config
                training_config = self.client_params.get("training", {})
                if training_config.get("gradient_clipping", self.model_config.get("regularization", {}).get("gradient_clipping", False)):
                    max_grad_norm = float(training_config.get("max_grad_norm", self.model_config.get("regularization", {}).get("max_grad_norm", 1.0)))
                    torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_grad_norm)

                optimizer.step()
                epoch_loss += loss.item() * features.size(0)
                epoch_samples += features.size(0)

            avg_epoch_loss = epoch_loss / epoch_samples
            total_loss += epoch_loss
            total_samples += epoch_samples

            # Validation loss for early stopping
            self.model.eval()
            with torch.no_grad():
                val_loss_epoch = 0.0
                val_samples = 0
                for batch in self.test_loader:
                    if use_gene_embedding:
                        val_features, val_gene_idx, val_target = batch
                        val_features = val_features.to(self.device)
                        val_gene_idx = val_gene_idx.to(self.device)
                        val_target = val_target.to(self.device)
                        val_outputs = self.model(val_features, gene_idx=val_gene_idx)
                    else:
                        val_features, val_target = batch
                        val_features = val_features.to(self.device)
                        val_target = val_target.to(self.device)
                        val_outputs = self.model(val_features)

                    val_loss_batch = criterion(val_outputs, val_target)
                    val_loss_epoch += val_loss_batch.item() * val_features.size(0)
                    val_samples += val_features.size(0)

                val_loss = val_loss_epoch / val_samples if val_samples > 0 else float("inf")

            self.model.train()

            scheduler.step(val_loss)

            # Log progress periodically
            if (epoch + 1) % 10 == 0 or (epoch + 1) == epochs:
                print(f"[Client {self.client_id}] Epoch {epoch + 1}/{epochs}, Loss: {avg_epoch_loss:.4f}, Val Loss: {val_loss:.4f}, LR: {optimizer.param_groups[0]['lr']:.6f}")

            # Early stopping logic
            training_config = self.client_params.get("training", {})
            min_delta = float(training_config.get("min_delta", self.model_config.get("regularization", {}).get("min_delta", 1e-4)))
            early_stopping_enabled = training_config.get("early_stopping", True)

            if val_loss < best_val_loss - min_delta:
                best_val_loss = val_loss
                epochs_no_improve = 0
                # Save best model weights
                best_model_state = {k: v.cpu().clone() for k, v in self.model.state_dict().items()}
            else:
                epochs_no_improve += 1

            if early_stopping_enabled and epochs_no_improve >= patience:
                print(f"[Client {self.client_id}] Early stopping at epoch {epoch + 1} (no improvement in validation loss for {patience} epochs)")
                break

        # Load best model weights
        if best_model_state is not None:
            self.model.load_state_dict(best_model_state)

        avg_loss = total_loss / total_samples
        updated_parameters = self.get_parameters({})

        # Return simple metrics (no complex tracking)
        metrics = {"loss": float(avg_loss), "epochs_trained": epoch + 1, "final_val_loss": float(val_loss), "final_learning_rate": float(optimizer.param_groups[0]["lr"])}

        return updated_parameters, len(self.train_data), metrics

    def evaluate(self, parameters, config):
        """Evaluate the model"""
        self.set_parameters(parameters)
        self.model.eval()

        total_loss = 0.0
        correct = 0
        total = 0

        # Get loss function from client config
        loss_config = self.client_params.get("loss", {})
        loss_type = loss_config.get("name", self.model_config.get("training", {}).get("loss_function", "cross_entropy"))
        criterion = get_loss_function(loss_type)

        use_gene_embedding = self.model_config["feature_engineering"].get("use_gene_embedding", False)

        with torch.no_grad():
            for batch in self.test_loader:
                if use_gene_embedding:
                    features, gene_idx, target = batch
                    features = features.to(self.device)
                    gene_idx = gene_idx.to(self.device)
                    target = target.to(self.device)
                    outputs = self.model(features, gene_idx=gene_idx)
                else:
                    features, target = batch
                    features = features.to(self.device)
                    target = target.to(self.device)
                    outputs = self.model(features)

                loss = criterion(outputs, target)
                total_loss += loss.item() * features.size(0)
                _, predicted = torch.max(outputs.data, 1)
                total += target.size(0)
                correct += (predicted == target).sum().item()

        avg_loss = total_loss / total
        accuracy = correct / total
        metrics = {"accuracy": accuracy, "loss": avg_loss}

        self.logger.log_info(f"Evaluation - Loss: {avg_loss:.4f}, Accuracy: {accuracy:.4f}")
        return avg_loss, len(self.test_data), metrics


def start_client(
    client_id: int,
    client_config_path: str = "configs/client_config.yaml",
    data_config_path: str = "configs/data_config.yaml",
    model_config_path: str = "configs/model_config.yaml",
    federated_config_path: str = None,  # For backward compatibility
    server_address: str = "localhost:8080",
):
    """Start a federated client"""
    # Support both new and legacy config paths
    # if federated_config_path:
    # Legacy mode
    # client = FederatedClient(client_id, client_config_path=None, data_config_path=data_config_path, model_config_path=model_config_path, federated_config_path=federated_config_path)
    # else:
    # New modular mode
    client = FederatedClient(client_id, client_config_path=client_config_path, data_config_path=data_config_path, model_config_path=model_config_path)
    client.logger.log_info(f"Starting federated client {client_id}")
    client.logger.log_info(f"Connecting to server at {server_address}")
    client.logger.log_info(f"Training data: {len(client.train_data)} samples")
    client.logger.log_info(f"Test data: {len(client.test_data)} samples")

    fl.client.start_client(server_address=server_address, client=client.to_client())


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Federated Learning Client")
    parser.add_argument("--client_id", type=int, required=False, help="Client ID", default=None)
    parser.add_argument("--client_config", type=str, default="configs/client_config.yaml", help="Path to client config (new format)")
    # parser.add_argument("--federated_config", type=str, default=None, help="Path to federated config (legacy format)")
    parser.add_argument("--data_config", type=str, default="configs/data_config.yaml", help="Path to data config")
    parser.add_argument("--model_config", type=str, default="configs/model_config.yaml", help="Path to model config")
    parser.add_argument("--server", type=str, default="localhost:8080", help="Server address")
    args = parser.parse_args()

    # start_client(args.client_id, client_config_path=args.client_config, data_config_path=args.data_config, model_config_path=args.model_config, federated_config_path=args.federated_config, server_address=args.server)
    start_client(args.client_id, client_config_path=args.client_config, data_config_path=args.data_config, model_config_path=args.model_config, server_address=args.server)
