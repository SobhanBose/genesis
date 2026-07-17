"""
Simplified federated server implementation using strategy factory.

This module provides a clean server implementation that uses Flower's built-in
strategies through the strategy factory pattern, removing complex custom
implementations while maintaining core functionality.
"""

import torch
import torch.nn as nn
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from sklearn.preprocessing import LabelEncoder, StandardScaler
from gensim.models import Word2Vec
import flwr as fl
from datetime import datetime

from src.models.improved_pathogenicity_model import create_model, get_model_summary
from src.models.feature_engineering import GenomicFeatureEngineer
from src.models.loss_functions import get_loss_function
from src.utils.logger import Logger
from src.models.ref_alt_embeddings import KmerGenerator
from src.federated.config_loader import ConfigLoader, load_yaml_config
from src.federated.strategy_factory import StrategyFactory


class SimpleClinVarDataset:
    """Simple dataset for ClinVar data with basic preprocessing"""

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


class FederatedServer:
    """
    Simplified federated server using strategy factory pattern.
    
    This server implementation removes complex custom strategy classes and uses
    Flower's built-in strategies through the strategy factory. It maintains the
    same core functionality as the backup/improved implementation while being
    much simpler and more maintainable.
    """
    
    def __init__(self, server_config_path: str = None, data_config_path: str = None, 
                 model_config_path: str = None, federated_config_path: str = None):
        """
        Initialize the federated server.
        
        Args:
            server_config_path: Path to server configuration file (new format)
            data_config_path: Path to data configuration file  
            model_config_path: Path to model configuration file
            federated_config_path: Path to federated configuration file (legacy format)
        """
        # Load configurations with backward compatibility
        if server_config_path:
            # New modular format
            self.server_config = ConfigLoader.load_server_config(server_config_path)
            # For backward compatibility, create a federated_config structure
            self.federated_config = self._convert_server_config_to_legacy_format(self.server_config)
        elif federated_config_path:
            # Legacy format
            self.federated_config = ConfigLoader.load_federated_config(federated_config_path)
            self.server_config = self.federated_config
        else:
            # Try automatic loading with fallback
            try:
                configs = ConfigLoader.load_config_with_fallback()
                self.server_config = configs['server']
                # For backward compatibility, create a federated_config structure
                self.federated_config = self._convert_server_config_to_legacy_format(self.server_config)
            except FileNotFoundError as e:
                raise FileNotFoundError(
                    "No valid server configuration found. Please provide either "
                    "server_config_path (new format) or federated_config_path (legacy format), "
                    f"or ensure default config files exist. Error: {e}"
                )
        
        # Load data and model configurations
        data_path = data_config_path or "configs/data_config.yaml"
        model_path = model_config_path or "configs/model_config.yaml"
        
        self.data_config = load_yaml_config(data_path)['data']
        self.model_config = load_yaml_config(model_path)
        
        # Initialize logger
        self.logger = Logger(log_dir='logs/server')
        self.logger.log_info("Initializing simplified federated server")
        
        # Set device
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.logger.log_info(f"Using device: {self.device}")
        
        # Load validation data
        self.validation_data = self._load_validation_data()
        self.scaler = None

        # Initialize feature engineer
        self.feature_engineer = GenomicFeatureEngineer()
        
        # Setup preprocessing components
        self._setup_preprocessing()
        
        # Initialize model
        self.model = self._initialize_model().to(self.device)
        
        # Preprocess validation data once during initialization
        self._preprocess_validation_data_once()

        self.logger.log_info("Simplified federated server initialized successfully")
    
    def _convert_server_config_to_legacy_format(self, server_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert new server configuration format to legacy format for backward compatibility.
        
        Args:
            server_config: New server configuration format
            
        Returns:
            Legacy federated configuration format
        """
        # Extract server section
        server_section = server_config.get('server', {})
        
        # Extract strategy configuration
        strategy_section = server_config.get('strategy', {})
        strategy_name = strategy_section.get('name', 'FedProx')
        
        # Build legacy format
        legacy_config = {
            'server': server_section,
            'strategy': strategy_name
        }
        
        # Add strategy-specific parameters in legacy format
        strategy_name_lower = strategy_name.lower()
        if strategy_name_lower in strategy_section:
            strategy_params = strategy_section[strategy_name_lower]
            
            # Create strategies section for legacy format
            legacy_config['strategies'] = {
                strategy_name_lower: strategy_params
            }
            
            # For FedProx, also add top-level proximal_mu for backward compatibility
            if strategy_name_lower == 'fedprox' and 'proximal_mu' in strategy_params:
                legacy_config['proximal_mu'] = strategy_params['proximal_mu']
        
        # Add evaluation section if present
        if 'evaluation' in server_config:
            legacy_config['evaluation'] = server_config['evaluation']
        
        # Add client section with defaults for backward compatibility
        legacy_config['client'] = {
            'local_epochs': 20  # Default value, will be overridden by actual client config
        }
        
        return legacy_config
    
    def create_strategy(self) -> fl.server.strategy.Strategy:
        """
        Create federated learning strategy using strategy factory.
        
        Returns:
            Strategy instance (FedAvg, FedProx, or FedAdam)
        """
        # Get strategy name from configuration
        strategy_name = ConfigLoader.get_strategy_name(self.federated_config)
        
        # Create strategy using factory
        strategy = StrategyFactory.create_strategy(strategy_name, self.federated_config, self)
        
        # Log instantiated strategy parameters
        self.logger.log_info(f"Strategy instance created: {strategy.__class__.__name__}")
        
        # Log actual strategy parameters from the instantiated object
        if strategy_name.lower() == 'fedprox' and hasattr(strategy, 'proximal_mu'):
            self.logger.log_info(f"Instantiated FedProx parameters - proximal_mu: {strategy.proximal_mu}")
            
        elif strategy_name.lower() == 'fedadam':
            # FedAdam uses different attribute names in Flower
            beta_1 = getattr(strategy, 'beta_1', 'N/A')
            beta_2 = getattr(strategy, 'beta_2', 'N/A') 
            eta = getattr(strategy, 'eta', 'N/A')
            tau = getattr(strategy, 'tau', 'N/A')
            self.logger.log_info(f"Instantiated FedAdam parameters - beta1: {beta_1}, beta2: {beta_2}, eta: {eta}, tau: {tau}")
            
        elif strategy_name.lower() == 'fedavg':
            # Log common parameters that all strategies have
            min_fit = getattr(strategy, 'min_fit_clients', 'N/A')
            min_available = getattr(strategy, 'min_available_clients', 'N/A')
            fraction_fit = getattr(strategy, 'fraction_fit', 'N/A')
            self.logger.log_info(f"Instantiated FedAvg parameters - min_fit_clients: {min_fit}, "
                               f"min_available_clients: {min_available}, fraction_fit: {fraction_fit}")
        
        return strategy
    
    def get_learning_rate(self, server_round: int) -> float:
        """
        Get learning rate for the current round with scheduling support.
        
        Args:
            server_round: Current server round
            
        Returns:
            Learning rate for the current round
        """
        try:
            # Get base learning rate from config
            training_config = self.model_config.get('training', {})
            base_lr = float(training_config.get('learning_rate', 1e-4))
            
            # Learning rate scheduling strategies
            lr_scheduler_config = self.federated_config.get('learning_rate_scheduler', {})
            lr_schedule = lr_scheduler_config.get('learning_rate_schedule', 'constant')
            
            if lr_schedule == 'step_decay':
                # Step decay: reduce learning rate every N rounds
                decay_interval = int(lr_scheduler_config.get('lr_decay_interval', 10))
                decay_factor = float(lr_scheduler_config.get('lr_decay_factor', 0.5))
                current_lr = base_lr * (decay_factor ** (server_round // decay_interval))
                
            elif lr_schedule == 'exponential_decay':
                # Exponential decay
                decay_rate = float(lr_scheduler_config.get('lr_decay_rate', 0.95))
                current_lr = base_lr * (decay_rate ** server_round)
                
            elif lr_schedule == 'cosine_annealing':
                # Cosine annealing
                total_rounds = int(self.federated_config['server']['rounds'])
                current_lr = base_lr * 0.5 * (1 + np.cos(np.pi * server_round / total_rounds))
                
            elif lr_schedule == 'warmup_then_decay':
                # Warmup for first N rounds, then decay
                warmup_rounds = int(lr_scheduler_config.get('lr_warmup_rounds', 5))
                if server_round < warmup_rounds:
                    # Linear warmup
                    current_lr = base_lr * (server_round + 1) / warmup_rounds
                else:
                    # Exponential decay after warmup
                    decay_rate = float(lr_scheduler_config.get('lr_decay_rate', 0.95))
                    current_lr = base_lr * (decay_rate ** (server_round - warmup_rounds))
            else:
                # Constant learning rate (default)
                current_lr = base_lr
            
            # Ensure learning rate doesn't go below minimum
            min_lr = float(lr_scheduler_config.get('min_learning_rate', 1e-6))
            current_lr = max(current_lr, min_lr)
            
            return current_lr
            
        except Exception as e:
            # Fallback to default learning rate if there's an error
            self.logger.log_warning(f"Error calculating learning rate: {e}. Using default.")
            return 1e-4
    
    def evaluate_global_model(self, parameters) -> Tuple[float, Dict[str, float]]:
        """
        Evaluate the global model on validation data.
        
        Args:
            parameters: Model parameters (either list of numpy arrays or Parameters object)
            
        Returns:
            Tuple of (loss, metrics_dict)
        """
        # Handle both old and new Flower API
        if hasattr(parameters, "tensors"):
            import flwr as fl
            parameters = fl.common.parameters_to_ndarrays(parameters)
        
        # Load parameters into model
        params_dict = zip(self.model.state_dict().keys(), parameters)
        state_dict = {k: torch.tensor(v) for k, v in params_dict}
        self.model.load_state_dict(state_dict, strict=True)
        
        # Get preprocessed validation data
        X_val, y_val, gene_val = self._prepare_validation_data()
        
        # Get loss function
        training_config = self.model_config.get('training', {})
        loss_type = training_config.get('loss_function', 'cross_entropy')
        criterion = get_loss_function(loss_type)
        
        use_gene_embedding = self.model_config.get('feature_engineering', {}).get('use_gene_embedding', False)
        
        # Evaluate model
        self.model.eval()
        with torch.no_grad():
            # Move data to device
            X_val = X_val.to(self.device)
            y_val = y_val.to(self.device)
            if gene_val is not None:
                gene_val = gene_val.to(self.device)
            
            if use_gene_embedding and gene_val is not None:
                outputs = self.model(X_val, gene_idx=gene_val)
            else:
                outputs = self.model(X_val)
            
            loss = criterion(outputs, y_val)
            _, predicted = torch.max(outputs.data, 1)
            accuracy = (predicted == y_val).float().mean().item()
            metrics = {'accuracy': accuracy, 'loss': loss.item()}
        
        return loss.item(), metrics
    
    def _load_validation_data(self) -> pd.DataFrame:
        """Load validation data from file."""
        # Get validation path from server config, with fallback to default
        validation_path = self.server_config.get('data', {}).get('validation_path', 
                                                                 "federated_data/non_iid_partition/validation.csv")
        validation_path = Path(validation_path)
        if not validation_path.exists():
            raise FileNotFoundError(f"Validation data not found at {validation_path}")
        validation_df = pd.read_csv(validation_path)
        self.logger.log_info(f"Loaded validation data: {len(validation_df)} samples")
        return validation_df

    def _initialize_model(self):
        """Initialize the model based on configuration."""
        # Determine input size from validation data after preprocessing
        input_size = self._calculate_input_size()
        architecture_config = self.model_config.get('architecture', {})
        output_size = architecture_config.get('output_dim', 2)
        model_type = architecture_config.get('model_type', 'improved')
        
        # Get model-specific configuration
        if model_type == "improved":
            improved_config = architecture_config.get('improved_model', {})
            model = create_model(
                model_type="improved",
                input_size=input_size,
                output_size=output_size,
                hidden_dims=improved_config.get('hidden_dims', [512, 256, 128, 64]),
                dropout=improved_config.get('dropout', 0.3),
                gene_vocab_size=self.feature_engineer.gene_vocab_size,
                use_gene_embedding=self.model_config.get('feature_engineering', {}).get('use_gene_embedding', False),
            )
        elif model_type == "lightweight":
            lightweight_config = architecture_config.get('lightweight_model', {})
            model = create_model(
                model_type="lightweight",
                input_size=input_size,
                output_size=output_size,
                hidden_dims=lightweight_config.get('hidden_dims', [512, 256, 128, 64, 32]),
                dropout=lightweight_config.get('dropout', 0.2),
                gene_vocab_size=self.feature_engineer.gene_vocab_size,
                use_gene_embedding=self.model_config.get('feature_engineering', {}).get('use_gene_embedding', False),
            )
        elif model_type == "ensemble":
            ensemble_config = architecture_config.get('ensemble_model', {})
            member_type = ensemble_config.get('ensemble_member_type', 'improved')
            if member_type == "improved":
                member_configs = ensemble_config.get('improved_member_settings', {})
            elif member_type == "lightweight":
                member_configs = ensemble_config.get('lightweight_member_settings', {})
            
            hidden_dims = member_configs.get('hidden_dims', [[512, 256, 128, 64, 32]] * ensemble_config.get('num_models', 3))
            
            model = create_model(
                model_type="ensemble",
                input_size=input_size,
                output_size=output_size,
                ensemble_member_type=member_type,
                num_models=ensemble_config.get('num_models', 3),
                hidden_dims=hidden_dims,
                dropout=member_configs.get('dropout', 0.3),
                gene_vocab_size=self.feature_engineer.gene_vocab_size,
                use_gene_embedding=self.model_config.get('feature_engineering', {}).get('use_gene_embedding', False),
            )
        else:
            # Fallback to improved model
            model = create_model(
                model_type="improved",
                input_size=input_size,
                output_size=output_size,
                gene_vocab_size=self.feature_engineer.gene_vocab_size,
                use_gene_embedding=self.model_config.get('feature_engineering', {}).get('use_gene_embedding', False),
            )
        
        # Get model summary
        model_summary = get_model_summary(model)
        self.logger.log_info(f"Initialized {model_type} model: {model_summary}")
        return model

    def _calculate_input_size(self) -> int:
        """Calculate input size from preprocessed validation data."""
        sample_df = self.validation_data.head(1).copy()
        processed_sample = self._preprocess_data(sample_df)
        use_gene_embedding = self.model_config.get('feature_engineering', {}).get('use_gene_embedding', False)
        if use_gene_embedding and 'gene' in processed_sample.columns:
            return processed_sample.shape[1] - 2  # Subtract 1 for target column and 1 for gene column
        else:
            return processed_sample.shape[1] - 1  # Subtract 1 for target column

    def _setup_preprocessing(self):
        """Setup preprocessing components."""
        # Load Word2Vec models
        ref_model_path = Path("models/global_models/ref_word2vec.model")
        alt_model_path = Path("models/global_models/alt_word2vec.model")
        if not ref_model_path.exists() or not alt_model_path.exists():
            raise FileNotFoundError("Word2Vec models not found")
        self.ref_model = Word2Vec.load(str(ref_model_path))
        self.alt_model = Word2Vec.load(str(alt_model_path))
        
        # Label encoder for chromosome
        self.label_encoder = LabelEncoder()
        # Ensure chromosome values are strings for consistent encoding
        all_chr_values = self.validation_data['chr'].astype(str).unique()
        self.label_encoder.fit(all_chr_values)
        
        # Kmer generator
        self.kmer_gen = KmerGenerator(k=3)  # Default k=3, can be made configurable
        
        # Set the chromosome encoder in feature engineer
        self.feature_engineer.label_encoders['chr'] = self.label_encoder
        
        self.logger.log_info("Preprocessing components initialized")

    def _preprocess_validation_data_once(self):
        """Preprocess validation data once during initialization to avoid repeated feature engineering."""
        self.processed_validation_data = self._preprocess_data(self.validation_data)
        
        use_gene_embedding = self.model_config.get('feature_engineering', {}).get('use_gene_embedding', False)
        val_dataset = SimpleClinVarDataset(self.processed_validation_data, use_gene_embedding=use_gene_embedding)
        
        X = self.processed_validation_data[val_dataset.feature_cols]
        y = self.processed_validation_data['class']
        
        # Initialize and fit scaler once
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # Store preprocessed tensors
        self.X_val_tensor = torch.tensor(X_scaled, dtype=torch.float32)
        self.y_val_tensor = torch.tensor(y.values, dtype=torch.long)
        
        # Store gene tensor if using gene embedding
        self.gene_val_tensor = None
        if use_gene_embedding and val_dataset.gene_col:
            self.gene_val_tensor = torch.tensor(self.processed_validation_data[val_dataset.gene_col].values, dtype=torch.long)

    def _preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply preprocessing and feature engineering."""
        df = df.copy()
        df = self._embed_ref_alt(df)
        
        # Apply feature engineering if enabled (this will handle chr encoding)
        feature_config = self.model_config.get('feature_engineering', {'enabled': True, 'use_gene_embedding': False})
        if feature_config.get('enabled', True):
            df = self.feature_engineer.engineer_all_features(df)
        else:
            # If feature engineering is disabled, still encode chr manually
            df['chr'] = self.label_encoder.transform(df['chr'])
        
        return df

    def _embed_ref_alt(self, df: pd.DataFrame) -> pd.DataFrame:
        """Embed reference and alternate sequences using Word2Vec models."""
        def embed_sequence(seq, model, k=3):
            tokens = self.kmer_gen.generate_kmers(seq)
            vectors = [model.wv[kmer] for kmer in tokens if kmer in model.wv]
            if len(vectors) == 0:
                return np.zeros(model.vector_size)
            return np.mean(vectors, axis=0)
        
        ref_embeddings = df['ref'].apply(lambda x: embed_sequence(x, self.ref_model))
        alt_embeddings = df['alt'].apply(lambda x: embed_sequence(x, self.alt_model))
        ref_emb_df = pd.DataFrame(ref_embeddings.tolist(), columns=pd.Index([f'ref_emb_{i}' for i in range(self.ref_model.vector_size)]), dtype=np.float32)
        alt_emb_df = pd.DataFrame(alt_embeddings.tolist(), columns=pd.Index([f'alt_emb_{i}' for i in range(self.alt_model.vector_size)]), dtype=np.float32)
        final_df = pd.concat([df.drop(columns=['ref', 'alt']), ref_emb_df, alt_emb_df], axis=1)
        return final_df

    def _prepare_validation_data(self) -> Tuple[torch.Tensor, torch.Tensor, Optional[torch.Tensor]]:
        """Return preprocessed validation data tensors (no repeated preprocessing)."""
        return self.X_val_tensor, self.y_val_tensor, self.gene_val_tensor


def start_server(server_config_path: str = None, data_config_path: str = None, 
                model_config_path: str = None, federated_config_path: str = None, port: int = 8080):
    """
    Start the federated server with strategy factory.
    
    This function initializes the federated server, detects the strategy from configuration
    (defaulting to FedProx for backward compatibility), logs strategy parameters, and
    ensures all three strategies (FedAvg, FedProx, FedAdam) can be instantiated correctly.
    
    Args:
        server_config_path: Path to server configuration file (new format)
        data_config_path: Path to data configuration file
        model_config_path: Path to model configuration file
        federated_config_path: Path to federated configuration file (legacy format)
        port: Port to run the server on
    """
    try:
        # Initialize server with backward compatibility
        server = FederatedServer(
            server_config_path=server_config_path,
            data_config_path=data_config_path,
            model_config_path=model_config_path,
            federated_config_path=federated_config_path
        )
        
        # Get strategy name from configuration with FedProx default
        strategy_name = ConfigLoader.get_strategy_name(server.federated_config)
        server.logger.log_info(f"Strategy detection complete: Selected '{strategy_name}' strategy")
        
        # Validate strategy is supported
        if not ConfigLoader.is_strategy_supported(strategy_name):
            supported = ConfigLoader.get_supported_strategies()
            raise ValueError(f"Unsupported strategy '{strategy_name}'. Supported strategies: {supported}")
        
        # Log strategy-specific parameters from configuration
        strategy_config = ConfigLoader.get_strategy_config(server.federated_config, strategy_name)
        server.logger.log_info(f"Strategy configuration loaded for {strategy_name}")
        
        if strategy_name.lower() == 'fedprox':
            proximal_mu = strategy_config.get('proximal_mu', server.federated_config.get('proximal_mu', 0.01))
            server.logger.log_info(f"FedProx parameters - proximal_mu: {proximal_mu}")
            
        elif strategy_name.lower() == 'fedadam':
            beta1 = strategy_config.get('beta1', 0.9)
            beta2 = strategy_config.get('beta2', 0.999)
            server_lr = strategy_config.get('server_lr', 0.001)
            epsilon = strategy_config.get('epsilon', 1e-7)
            server.logger.log_info(f"FedAdam parameters - beta1: {beta1}, beta2: {beta2}, server_lr: {server_lr}, epsilon: {epsilon}")
            
        elif strategy_name.lower() == 'fedavg':
            server.logger.log_info("FedAvg parameters - using standard weighted averaging (no additional parameters)")
        
        # Create strategy using factory with error handling
        server.logger.log_info(f"Creating {strategy_name} strategy instance using StrategyFactory...")
        try:
            strategy = StrategyFactory.create_strategy(strategy_name, server.federated_config, server)
            server.logger.log_info(f"Successfully created {strategy_name} strategy instance")
        except Exception as e:
            server.logger.log_error(f"Failed to create {strategy_name} strategy: {str(e)}")
            raise
        
        # Verify strategy was created correctly
        strategy_class_name = strategy.__class__.__name__
        server.logger.log_info(f"Strategy instantiation verified: {strategy_class_name}")
        
        # Log server configuration (handle both new and legacy formats)
        if hasattr(server, 'server_config') and 'server' in server.server_config:
            # New format: use server_config directly
            server_config = server.server_config['server']
        elif 'server' in server.federated_config:
            # Legacy format: use federated_config
            server_config = server.federated_config['server']
        else:
            # Fallback: assume federated_config is the server section
            server_config = server.federated_config
        
        server.logger.log_info(f"Server configuration - rounds: {server_config['rounds']}, "
                              f"min_fit_clients: {server_config['min_fit_clients']}, "
                              f"min_available_clients: {server_config['min_available_clients']}, "
                              f"fraction_fit: {server_config.get('fraction_fit', 1.0)}, "
                              f"fraction_evaluate: {server_config.get('fraction_evaluate', 1.0)}")
        
        # Create server configuration
        num_rounds = server_config['rounds']
        config = fl.server.ServerConfig(num_rounds=num_rounds)
        
        # Final startup logging
        server.logger.log_info(f"Starting federated server with {strategy_name} strategy on port {port}")
        server.logger.log_info(f"Server will run for {num_rounds} rounds")
        server.logger.log_info("=" * 60)
        server.logger.log_info("FEDERATED SERVER STARTUP COMPLETE")
        server.logger.log_info("=" * 60)
        
        # Start server
        fl.server.start_server(
            server_address=f"0.0.0.0:{port}",
            config=config,
            strategy=strategy,
        )
        
    except Exception as e:
        # Log startup errors
        if 'server' in locals():
            server.logger.log_error(f"Failed to start federated server: {str(e)}")
        else:
            print(f"Failed to initialize federated server: {str(e)}")
        raise


if __name__ == "__main__":
    import argparse
    from pathlib import Path
    
    parser = argparse.ArgumentParser(description="Start federated learning server")
    parser.add_argument('--port', type=int, default=8080, help='Port to run server on')
    parser.add_argument('--server_config', type=str, default="configs/server_config.yaml", 
                       help='Path to server config (new format)')
    parser.add_argument('--federated_config', type=str, default="configs/federated_config.yaml", 
                       help='Path to federated config (legacy format)')
    parser.add_argument('--data_config', type=str, default="configs/data_config.yaml", 
                       help='Path to data config')
    parser.add_argument('--model_config', type=str, default="configs/model_config.yaml", 
                       help='Path to model config')
    
    args = parser.parse_args()
    
    # Prioritize server_config if it exists, otherwise fall back to federated_config
    server_config_path = args.server_config if Path(args.server_config).exists() else None
    federated_config_path = args.federated_config if not server_config_path and Path(args.federated_config).exists() else None
    
    start_server(
        server_config_path=server_config_path,
        federated_config_path=federated_config_path,
        data_config_path=args.data_config,
        model_config_path=args.model_config,
        port=args.port
    )