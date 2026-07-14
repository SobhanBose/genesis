import torch
import torch.nn as nn
import numpy as np
import pandas as pd
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from sklearn.preprocessing import LabelEncoder, StandardScaler
from gensim.models import Word2Vec
import flwr as fl
from flwr.server.strategy import FedProx
from flwr.common import Metrics

from src.models.pathogenecity_model import PathogenicityClassifier
from src.utils.logger import Logger
from src.models.ref_alt_embeddings import KmerGenerator

# Utility to load YAML config
def load_yaml_config(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

class FederatedServer:
    def __init__(self, federated_config_path, data_config_path, model_config_path):
        self.federated_config = load_yaml_config(federated_config_path)['federated']
        self.data_config = load_yaml_config(data_config_path)['data']
        self.model_config = load_yaml_config(model_config_path)['model']
        self.logger = Logger(log_dir='logs/server')

        # Load validation data
        self.validation_data = self._load_validation_data()
        self.scaler = None

        # Setup preprocessing components
        self._setup_preprocessing()
        
        # Initialize model
        self.model = self._initialize_model()

        self.logger.log_info("Federated server initialized successfully")

    def _load_validation_data(self) -> pd.DataFrame:
        # Use validation.csv as per user request
        validation_path = Path("federated_data/non_iid_partition/validation.csv")
        if not validation_path.exists():
            raise FileNotFoundError(f"Validation data not found at {validation_path}")
        validation_df = pd.read_csv(validation_path)
        self.logger.log_info(f"Loaded validation data: {len(validation_df)} samples")
        return validation_df

    def _initialize_model(self) -> PathogenicityClassifier:
        # Determine input size from validation data after preprocessing
        input_size = self._calculate_input_size()
        output_size = self.model_config['architecture']['output_dim']
        model = PathogenicityClassifier(input_size=input_size, output_size=output_size)
        self.logger.log_info(f"Initialized model with input size: {input_size}")
        return model

    def _calculate_input_size(self) -> int:
        sample_df = self.validation_data.head(1).copy()
        processed_sample = self._preprocess_data(sample_df)
        return processed_sample.shape[1] - 1  # Subtract 1 for target column

    def _setup_preprocessing(self):
        # Load Word2Vec models
        ref_model_path = Path("models/global_models/ref_word2vec.model")
        alt_model_path = Path("models/global_models/alt_word2vec.model")
        if not ref_model_path.exists() or not alt_model_path.exists():
            raise FileNotFoundError("Word2Vec models not found")
        self.ref_model = Word2Vec.load(str(ref_model_path))
        self.alt_model = Word2Vec.load(str(alt_model_path))
        # Label encoder for chromosome
        self.label_encoder = LabelEncoder()
        all_chr_values = self.validation_data['chr'].unique()
        self.label_encoder.fit(all_chr_values)
        # Kmer generator
        self.kmer_gen = KmerGenerator(k=3)  # Default k=3, can be made configurable
        self.logger.log_info("Preprocessing components initialized")

    def _preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df['chr'] = self.label_encoder.transform(df['chr'])
        df = self._embed_ref_alt(df)
        return df

    def _embed_ref_alt(self, df: pd.DataFrame) -> pd.DataFrame:
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
        final_df = pd.concat([df.drop(columns=['ref', 'alt', 'gene']), ref_emb_df, alt_emb_df], axis=1)
        return final_df

    def _prepare_validation_data(self) -> Tuple[torch.Tensor, torch.Tensor]:
        processed_df = self._preprocess_data(self.validation_data)
        X = processed_df.drop(['class'], axis=1)
        y = processed_df['class']
        if self.scaler is None:
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X)
        else:
            X_scaled = self.scaler.transform(X)
        X_tensor = torch.tensor(X_scaled, dtype=torch.float32)
        y_tensor = torch.tensor(y.values, dtype=torch.long)
        return X_tensor, y_tensor

    def evaluate_global_model(self, parameters):
        # parameters may be a list of numpy arrays (old API) or a Parameters object (new API)
        if hasattr(parameters, "tensors"):
            import flwr as fl
            parameters = fl.common.parameters_to_ndarrays(parameters)
        params_dict = zip(self.model.state_dict().keys(), parameters)
        state_dict = {k: torch.tensor(v) for k, v in params_dict}
        self.model.load_state_dict(state_dict, strict=True)
        X_val, y_val = self._prepare_validation_data()
        self.model.eval()
        with torch.no_grad():
            outputs = self.model(X_val)
            loss = nn.CrossEntropyLoss()(outputs, y_val)
            _, predicted = torch.max(outputs.data, 1)
            accuracy = (predicted == y_val).float().mean().item()
            metrics = {'accuracy': accuracy, 'loss': loss.item()}
        self.logger.log_info(f"Global model evaluation - Loss: {loss.item():.4f}, Accuracy: {accuracy:.4f}")
        return loss.item(), metrics

class FederatedStrategy(FedProx):
    def __init__(self, server, proximal_mu=0.01, **kwargs):
        # Use weighted average for evaluation metrics aggregation
        kwargs['evaluate_metrics_aggregation_fn'] = self.weighted_average_metrics
        kwargs['on_fit_config_fn'] = self.on_fit_config_fn
        kwargs['evaluate_fn'] = self.evaluate_fn  # Add centralized evaluation
        super().__init__(proximal_mu=proximal_mu, **kwargs)
        self.server = server
        self.parameters = None
    
    def configure_fit(self, server_round: int, parameters, client_manager):
        """Configure the next round of training with client sampling logging."""
        # Get the configuration from parent class
        config = super().configure_fit(server_round, parameters, client_manager)
        
        # Log client sampling information
        sample_size = len(config)
        total_clients = len(client_manager.all())
        self.server.logger.log_info(
            f"Round {server_round}: Sampled {sample_size} clients out of {total_clients} available clients "
            f"(fraction_fit={self.fraction_fit:.2f})"
        )
        
        # Log which clients were sampled
        # config is a list of tuples (client_proxy, fit_config)
        sampled_client_ids = [client_proxy.cid for client_proxy, _ in config]
        self.server.logger.log_info(f"Round {server_round}: Sampled clients: {sampled_client_ids}")
        
        return config
    
    def on_fit_config_fn(self, server_round: int) -> Dict[str, float]:
        try:
            # Get base learning rate from config and ensure it's a float
            base_lr_raw = self.server.model_config['training']['learning_rate']
            base_lr = float(base_lr_raw)
            
            # Log the base learning rate for debugging
            self.server.logger.log_info(f"Base learning rate: {base_lr_raw} (type: {type(base_lr_raw)}) -> {base_lr}")
            
            # Learning rate scheduling strategies
            lr_scheduler_config = self.server.federated_config.get('learning_rate_scheduler', {})
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
                total_rounds = int(self.server.federated_config['server']['rounds'])
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
            min_lr_raw = lr_scheduler_config.get('min_learning_rate', 1e-6)
            min_lr = float(min_lr_raw)
            current_lr = max(current_lr, min_lr)
            
            # Log learning rate for current round
            self.server.logger.log_info(f"Round {server_round}: Learning rate = {current_lr:.6f}")
            
            return {
                "learning_rate": current_lr,
                "epochs": int(self.server.federated_config['client']['local_epochs']),
                "batch_size": int(self.server.model_config['training']['batch_size']),
                "server_round": server_round,
                "proximal_mu": float(self.server.federated_config.get('proximal_mu', 0.01))
            }
            
        except Exception as e:
            # Fallback to default values if there's an error
            self.server.logger.log_info(f"Error in on_fit_config_fn: {e}. Using default values.")
            return {
                "learning_rate": 1e-4,  # Default learning rate
                "epochs": 5,
                "batch_size": 32,
                "server_round": server_round
            }
    
    def weighted_average_metrics(self, metrics: List[Tuple[int, Metrics]]) -> Metrics:
        if not metrics:
            return {}
        
        # Get all unique metric keys
        all_keys = set()
        for _, metric_dict in metrics:
            all_keys.update(metric_dict.keys())
        
        aggregated_metrics = {}
        
        for key in all_keys:
            # Calculate weighted average for each metric
            weighted_sum = 0.0
            total_examples = 0
            
            for num_examples, metric_dict in metrics:
                if key in metric_dict:
                    weighted_sum += num_examples * float(metric_dict[key])
                    total_examples += num_examples
            
            if total_examples > 0:
                aggregated_metrics[key] = weighted_sum / total_examples
        
        return aggregated_metrics
    
    def evaluate_fn(self, server_round: int, parameters, config):
        try:
            # Evaluate global model on validation set
            loss, metrics = self.server.evaluate_global_model(parameters)
            
            # Return only loss and accuracy metrics
            evaluation_metrics = {
                "accuracy": metrics.get("accuracy", 0.0),
                "loss": loss
            }
            
            # Log the evaluation results
            self.server.logger.log_info(
                f"Centralized evaluation (Round {server_round}): "
                f"Loss={loss:.4f}, Accuracy={evaluation_metrics['accuracy']:.4f}"
            )
            
            # Return (loss, metrics) - Flower expects only 2 values
            return loss, evaluation_metrics
            
        except Exception as e:
            self.server.logger.log_info(f"Error in centralized evaluation: {e}")
            # Return default values on error
            return 1.0, {"accuracy": 0.0, "loss": 1.0}
    
    def aggregate_evaluate(self, server_round, results, failures):
        aggregated_loss, aggregated_metrics = super().aggregate_evaluate(server_round, results, failures)
        if self.parameters is not None:
            global_loss, global_metrics = self.server.evaluate_global_model(self.parameters)
            for key, value in global_metrics.items():
                aggregated_metrics[f"global_{key}"] = value
        return aggregated_loss, aggregated_metrics
    
    def aggregate_fit(self, server_round, results, failures):
        aggregated_parameters, aggregated_metrics = super().aggregate_fit(server_round, results, failures)
        if aggregated_parameters is not None:
            self.parameters = aggregated_parameters
        return aggregated_parameters, aggregated_metrics

def start_server(federated_config_path: str = "configs/federated_config.yaml", data_config_path: str = "configs/data_config.yaml", model_config_path: str = "configs/model_config.yaml", port: int = 8080):
    server = FederatedServer(federated_config_path, data_config_path, model_config_path)
    
    # Get proximal_mu from config or use default
    proximal_mu = server.federated_config.get('proximal_mu', 0.01)
    
    strategy = FederatedStrategy(
        server=server,
        proximal_mu=proximal_mu,
        min_fit_clients=server.federated_config['server']['min_fit_clients'],
        min_evaluate_clients=server.federated_config['server']['min_eval_clients'],
        min_available_clients=server.federated_config['server']['min_available_clients'],
        fraction_fit=server.federated_config['server'].get('fraction_fit', 1.0),  # Use configurable fraction
        fraction_evaluate=server.federated_config['server'].get('fraction_evaluate', 1.0),  # Use configurable fraction
    )
    config = fl.server.ServerConfig(num_rounds=server.federated_config['server']['rounds'])
    server.logger.log_info(f"Starting federated server on port {port}")
    server.logger.log_info(f"Using FedProx strategy with proximal_mu={proximal_mu}")
    fl.server.start_server(
        server_address=f"0.0.0.0:{port}",
        config=config,
        strategy=strategy,
    )

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Federated Learning Server')
    parser.add_argument('--port', type=int, default=8080, help='Server port')
    parser.add_argument('--federated_config', type=str, default="configs/federated_config.yaml", help='Path to federated config')
    parser.add_argument('--data_config', type=str, default="configs/data_config.yaml", help='Path to data config')
    parser.add_argument('--model_config', type=str, default="configs/model_config.yaml", help='Path to model config')
    args = parser.parse_args()
    start_server(
        federated_config_path=args.federated_config,
        data_config_path=args.data_config,
        model_config_path=args.model_config,
        port=args.port
    )