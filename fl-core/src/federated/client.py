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
from torch.utils.data import DataLoader, TensorDataset
from torch.optim.lr_scheduler import ReduceLROnPlateau

from src.models.pathogenecity_model import PathogenicityClassifier
from src.utils.logger import Logger
from src.models.ref_alt_embeddings import KmerGenerator

# Utility to load YAML config
def load_yaml_config(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

class FederatedClient(fl.client.NumPyClient):
    def __init__(self, client_id: int, federated_config_path, data_config_path, model_config_path):
        self.client_id = client_id
        self.federated_config = load_yaml_config(federated_config_path)['federated']
        self.data_config = load_yaml_config(data_config_path)['data']
        self.model_config = load_yaml_config(model_config_path)['model']
        self.logger = Logger(log_dir=f'logs/client_{client_id}')
        # Set device
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.logger.log_info(f"Using device: {self.device}")
        # Load client data
        self.train_data, self.test_data = self._load_client_data()
        # Setup preprocessing components (must be before model init)
        self._setup_preprocessing()
        # Initialize model (after preprocessing is ready)
        self.model = self._initialize_model().to(self.device)
        # Prepare data
        self.train_loader, self.test_loader = self._prepare_data()

        self.logger.log_info(f"Client {client_id} initialized successfully")

    def _load_client_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        client_dir = Path("federated_data/non_iid_partition/clients") / f"client_{self.client_id}"
        train_path = client_dir / "train.csv"
        test_path = client_dir / "test.csv"
        if not train_path.exists() or not test_path.exists():
            raise FileNotFoundError(f"Client data not found at {client_dir}")
        train_df = pd.read_csv(train_path)
        test_df = pd.read_csv(test_path)
        self.logger.log_info(f"Loaded client data - Train: {len(train_df)}, Test: {len(test_df)}")
        return train_df, test_df

    def _initialize_model(self) -> PathogenicityClassifier:
        input_size = self._calculate_input_size()
        output_size = self.model_config['architecture']['output_dim']
        model = PathogenicityClassifier(input_size=input_size, output_size=output_size)
        self.logger.log_info(f"Initialized model with input size: {input_size}")
        return model

    def _calculate_input_size(self) -> int:
        sample_df = self.train_data.head(1).copy()
        processed_sample = self._preprocess_data(sample_df)
        return processed_sample.shape[1] - 1  # Subtract 1 for target column

    def _setup_preprocessing(self):
        ref_model_path = Path("models/global_models/ref_word2vec.model")
        alt_model_path = Path("models/global_models/alt_word2vec.model")
        if not ref_model_path.exists() or not alt_model_path.exists():
            raise FileNotFoundError("Word2Vec models not found")
        self.ref_model = Word2Vec.load(str(ref_model_path))
        self.alt_model = Word2Vec.load(str(alt_model_path))
        self.label_encoder = LabelEncoder()
        all_chr_values = pd.concat([self.train_data['chr'], self.test_data['chr']]).unique()
        self.label_encoder.fit(all_chr_values)
        self.kmer_gen = KmerGenerator(k=3)  # Default k=3, can be made configurable
        self.scaler = StandardScaler()
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

    def _prepare_data(self) -> Tuple[DataLoader, DataLoader]:
        train_processed = self._preprocess_data(self.train_data)
        test_processed = self._preprocess_data(self.test_data)
        X_train = train_processed.drop(['class'], axis=1)
        y_train = train_processed['class']
        X_test = test_processed.drop(['class'], axis=1)
        y_test = test_processed['class']
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        X_train_tensor = torch.tensor(X_train_scaled, dtype=torch.float32)
        y_train_tensor = torch.tensor(y_train.values, dtype=torch.long)
        X_test_tensor = torch.tensor(X_test_scaled, dtype=torch.float32)
        y_test_tensor = torch.tensor(y_test.values, dtype=torch.long)
        train_dataset = TensorDataset(X_train_tensor, y_train_tensor)
        test_dataset = TensorDataset(X_test_tensor, y_test_tensor)
        batch_size = self.model_config['training']['batch_size'] if 'training' in self.model_config else 32
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
        return train_loader, test_loader

    def get_parameters(self, config):
        return [val.cpu().numpy() for _, val in self.model.state_dict().items()]

    def set_parameters(self, parameters):
        params_dict = zip(self.model.state_dict().keys(), parameters)
        state_dict = {k: torch.tensor(v) for k, v in params_dict}
        self.model.load_state_dict(state_dict, strict=True)

    def fit(self, parameters, config):
        self.set_parameters(parameters)
        epochs = int(config.get("epochs", self.federated_config["client"]["local_epochs"]))
        learning_rate = float(config.get("learning_rate", self.model_config['training']['learning_rate']))
        weight_decay = float(self.model_config['regularization']['weight_decay']) if 'regularization' in self.model_config and 'weight_decay' in self.model_config['regularization'] else 1e-4
        
        # FedProx: Get proximal_mu from config
        proximal_mu = float(config.get("proximal_mu", 0.01))
        self.logger.log_info(f"FedProx training with proximal_mu={proximal_mu}")
        
        optimizer = torch.optim.Adam(self.model.parameters(), lr=learning_rate, weight_decay=weight_decay)
        criterion = nn.CrossEntropyLoss()
        scheduler = ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5, min_lr=1e-6, threshold=1e-3)
        self.model.train()
        total_loss = 0.0
        total_samples = 0
        best_val_loss = float('inf')
        epochs_no_improve = 0
        patience = self.model_config['regularization']['patience'] if 'regularization' in self.model_config and 'patience' in self.model_config['regularization'] else 10
        early_stop = False
        best_model_state = None
        # Store initial parameters for proximal term
        initial_params = {name: param.clone().detach() for name, param in self.model.named_parameters()}
        
        for epoch in range(epochs):
            epoch_loss = 0.0
            epoch_samples = 0
            for batch_idx, (data, target) in enumerate(self.train_loader):
                data = data.to(self.device)
                target = target.to(self.device)
                optimizer.zero_grad()
                outputs = self.model(data)
                loss = criterion(outputs, target)
                
                # FedProx: Add proximal term to loss
                proximal_term = 0.0
                for name, param in self.model.named_parameters():
                    if name in initial_params:
                        proximal_term += torch.norm(param - initial_params[name]) ** 2
                proximal_term = (proximal_mu / 2) * proximal_term
                loss += proximal_term
                
                loss.backward()
                optimizer.step()
                epoch_loss += loss.item() * data.size(0)
                epoch_samples += data.size(0)
            avg_epoch_loss = epoch_loss / epoch_samples
            total_loss += epoch_loss
            total_samples += epoch_samples
            # Validation loss for early stopping
            val_loss = None
            self.model.eval()
            with torch.no_grad():
                val_loss_epoch = 0.0
                val_samples = 0
                for val_data, val_target in self.test_loader:
                    val_data = val_data.to(self.device)
                    val_target = val_target.to(self.device)
                    val_outputs = self.model(val_data)
                    val_loss_batch = criterion(val_outputs, val_target)
                    val_loss_epoch += val_loss_batch.item() * val_data.size(0)
                    val_samples += val_data.size(0)
                avg_loss_val = val_loss_epoch / val_samples if val_samples > 0 else float('inf')
                val_loss = avg_loss_val
            self.model.train()
            scheduler.step(val_loss)
            if (epoch + 1) % 10 == 0 or (epoch + 1) == epochs:
                print(f"[Client {self.client_id}] Epoch {epoch+1}/{epochs}, Loss: {avg_epoch_loss:.4f}, Val Loss: {val_loss:.4f}; ; learning_rate: {optimizer.param_groups[0]['lr']:.6f}")
            # Early stopping logic
            if val_loss < best_val_loss - 1e-4:
                best_val_loss = val_loss
                epochs_no_improve = 0
                # Save best model weights
                best_model_state = {k: v.cpu().clone() for k, v in self.model.state_dict().items()}
            else:
                epochs_no_improve += 1
            if epochs_no_improve >= patience:
                print(f"[Client {self.client_id}] Early stopping at epoch {epoch+1} (no improvement in validation loss for {patience} epochs)")
                break
        # At end of training, load best model weights
        if best_model_state is not None:
            self.model.load_state_dict(best_model_state)
        avg_loss = total_loss / total_samples
        updated_parameters = self.get_parameters({})
        return updated_parameters, len(self.train_data), {"loss": avg_loss}

    def evaluate(self, parameters, config):
        self.set_parameters(parameters)
        self.model.eval()
        total_loss = 0.0
        correct = 0
        total = 0
        all_predictions = []
        all_targets = []
        criterion = nn.CrossEntropyLoss()
        with torch.no_grad():
            for data, target in self.test_loader:
                data = data.to(self.device)
                target = target.to(self.device)
                outputs = self.model(data)
                loss = criterion(outputs, target)
                total_loss += loss.item() * data.size(0)
                _, predicted = torch.max(outputs.data, 1)
                total += target.size(0)
                correct += (predicted == target).sum().item()
                all_predictions.extend(predicted.cpu().numpy())
                all_targets.extend(target.cpu().numpy())
        avg_loss = total_loss / total
        accuracy = correct / total
        metrics = {'accuracy': accuracy, 'loss': avg_loss}
        self.logger.log_info(f"Evaluation - Loss: {avg_loss:.4f}, Accuracy: {accuracy:.4f}")
        return avg_loss, len(self.test_data), metrics

def start_client(client_id: int, federated_config_path: str = "configs/federated_config.yaml", data_config_path: str = "configs/data_config.yaml", model_config_path: str = "configs/model_config.yaml", server_address: str = "localhost:8080"):
    client = FederatedClient(client_id, federated_config_path, data_config_path, model_config_path)
    client.logger.log_info(f"Starting client {client_id}")
    client.logger.log_info(f"Connecting to server at {server_address}")
    client.logger.log_info(f"Training data: {len(client.train_data)} samples")
    client.logger.log_info(f"Test data: {len(client.test_data)} samples")
    fl.client.start_numpy_client(
        server_address=server_address,
        client=client
    )

# Optional: main() for CLI usage
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Federated Learning Client')
    parser.add_argument('--client_id', type=int, required=True, help='Client ID')
    parser.add_argument('--federated_config', type=str, default="configs/federated_config.yaml", help='Path to federated config')
    parser.add_argument('--data_config', type=str, default="configs/data_config.yaml", help='Path to data config')
    parser.add_argument('--model_config', type=str, default="configs/model_config.yaml", help='Path to model config')
    parser.add_argument('--server', type=str, default="localhost:8080", help='Server address')
    args = parser.parse_args()
    start_client(args.client_id, args.federated_config, args.data_config, args.model_config, args.server)