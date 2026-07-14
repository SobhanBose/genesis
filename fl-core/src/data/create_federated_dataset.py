import os
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
from typing import Dict, List, Tuple, Optional
import numpy as np
from sklearn.model_selection import train_test_split
import pickle
from src.utils.logger import Logger
from pathlib import Path

# Configure logging
logger = Logger(log_dir='logs/data')

class PathogenicityDataset(Dataset):
    """Custom Dataset for pathogenicity prediction"""
    
    def __init__(self, data: pd.DataFrame, feature_cols: List[str], target_col: str = 'label'):
        self.data = data.reset_index(drop=True)
        self.feature_cols = feature_cols
        self.target_col = target_col
        
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        # Extract features and target
        features = torch.tensor(self.data.iloc[idx][self.feature_cols].values, dtype=torch.float32)
        target = torch.tensor(self.data.iloc[idx][self.target_col], dtype=torch.long)
        return features, target

class FederatedDatasetManager:
    """Manages federated dataset creation and distribution"""
    
    def __init__(self, data_dir: str, output_dir: str):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load datasets
        self.train_df = pd.read_csv(self.data_dir / "train.csv")
        self.test_df = pd.read_csv(self.data_dir / "test.csv")
        self.validation_df = pd.read_csv(self.data_dir / "validation.csv")
        
        logger.log_info(f"Loaded datasets - Train: {len(self.train_df)}, Test: {len(self.test_df)}, Validation: {len(self.validation_df)}")
    
    def create_iid_partition(self, n_clients: int, seed: int = 42) -> Dict[int, Dict[str, pd.DataFrame]]:
        """Create IID (Independent and Identically Distributed) partitions"""
        np.random.seed(seed)
        
        # Combine train and test for partitioning
        combined_df = pd.concat([self.train_df, self.test_df], ignore_index=True)
        
        # Shuffle the data
        combined_df = combined_df.sample(frac=1, random_state=seed).reset_index(drop=True)
        
        # Calculate partition sizes
        total_samples = len(combined_df)
        base_size = total_samples // n_clients
        remainder = total_samples % n_clients
        
        client_data = {}
        start_idx = 0
        
        for client_id in range(n_clients):
            # Add one extra sample to first 'remainder' clients
            size = base_size + (1 if client_id < remainder else 0)
            end_idx = start_idx + size
            
            client_df = combined_df.iloc[start_idx:end_idx].copy()
            
            # Split client data into train/test (80/20)
            train_data, test_data = train_test_split(
                client_df, test_size=0.2, random_state=seed, stratify=client_df.get('label')
            )
            
            client_data[client_id] = {
                'train': train_data,
                'test': test_data
            }
            
            start_idx = end_idx
            logger.log_info(f"Client {client_id}: Train={len(train_data)}, Test={len(test_data)}")
        
        return client_data
    
    def create_non_iid_partition(self, n_clients: int, alpha: float = 0.5, seed: int = 42) -> Dict[int, Dict[str, pd.DataFrame]]:
        """Create Non-IID partitions using Dirichlet distribution"""
        np.random.seed(seed)
        
        # Combine train and test
        combined_df = pd.concat([self.train_df, self.test_df], ignore_index=True)
        
        # Get unique labels
        labels = combined_df['class'].unique()
        n_labels = len(labels)
        
        # Create label-wise data indices
        label_indices = {}
        for label in labels:
            label_indices[label] = combined_df[combined_df['class'] == label].index.tolist()
            np.random.shuffle(label_indices[label])
        
        # Generate Dirichlet distribution for each label
        client_data = {i: {'train': [], 'test': []} for i in range(n_clients)}
        
        for label in labels:
            # Sample proportions from Dirichlet distribution
            proportions = np.random.dirichlet([alpha] * n_clients)
            proportions = proportions / proportions.sum()  # Normalize
            
            # Distribute indices based on proportions
            indices = label_indices[label]
            start_idx = 0
            
            for client_id in range(n_clients):
                end_idx = start_idx + int(len(indices) * proportions[client_id])
                if client_id == n_clients - 1:  # Last client gets remaining indices
                    end_idx = len(indices)
                
                client_indices = indices[start_idx:end_idx]
                if client_indices:  # Only add if there are indices
                    client_data[client_id]['train'].extend(client_indices)
                
                start_idx = end_idx
        
        # Convert indices to DataFrames and split train/test
        final_client_data = {}
        for client_id in range(n_clients):
            if client_data[client_id]['train']:
                client_df = combined_df.iloc[client_data[client_id]['train']].copy()
                
                # Split into train/test (80/20)
                if len(client_df) > 1:
                    try:
                        train_data, test_data = train_test_split(
                            client_df, test_size=0.2, random_state=seed, 
                            stratify=client_df['class']
                        )
                    except ValueError:  # If stratification fails due to class imbalance
                        split_idx = int(0.8 * len(client_df))
                        train_data = client_df.iloc[:split_idx]
                        test_data = client_df.iloc[split_idx:]
                else:
                    train_data = client_df
                    test_data = pd.DataFrame()
                
                final_client_data[client_id] = {
                    'train': train_data,
                    'test': test_data
                }
                
                logger.log_info(f"Client {client_id}: Train={len(train_data)}, Test={len(test_data)}")
        
        return final_client_data
    
    def save_client_data(self, client_data: Dict[int, Dict[str, pd.DataFrame]], partition_type: str):
        """Save client data to files"""
        partition_dir = self.output_dir / f"{partition_type}_partition"
        partition_dir.mkdir(exist_ok=True)
        
        # Save validation data (same for all clients)
        self.validation_df.to_csv(partition_dir / "validation.csv", index=False)
        
        # Save client-specific data
        clients_dir = partition_dir / "clients"
        clients_dir.mkdir(exist_ok=True)
        
        for client_id, data in client_data.items():
            client_dir = clients_dir / f"client_{client_id}"
            client_dir.mkdir(exist_ok=True)
            
            data['train'].to_csv(client_dir / "train.csv", index=False)
            data['test'].to_csv(client_dir / "test.csv", index=False)
        
        # Save metadata
        metadata = {
            'n_clients': len(client_data),
            'partition_type': partition_type,
            'total_train_samples': sum(len(data['train']) for data in client_data.values()),
            'total_test_samples': sum(len(data['test']) for data in client_data.values()),
            'validation_samples': len(self.validation_df)
        }
        
        with open(partition_dir / "metadata.pkl", 'wb') as f:
            pickle.dump(metadata, f)
        
        logger.log_info(f"Saved {partition_type} partition data to {partition_dir}")
        return partition_dir
    
    def create_pytorch_datasets(self, client_data: Dict[int, Dict[str, pd.DataFrame]], 
                              feature_cols: List[str]) -> Dict[int, Dict[str, PathogenicityDataset]]:
        """Convert pandas DataFrames to PyTorch Datasets"""
        pytorch_datasets = {}
        
        for client_id, data in client_data.items():
            pytorch_datasets[client_id] = {
                'train': PathogenicityDataset(data['train'], feature_cols),
                'test': PathogenicityDataset(data['test'], feature_cols)
            }
        
        # Add validation dataset (same for all)
        validation_dataset = PathogenicityDataset(self.validation_df, feature_cols)
        
        return pytorch_datasets, validation_dataset
    
    def get_data_statistics(self, client_data: Dict[int, Dict[str, pd.DataFrame]]) -> Dict:
        """Calculate statistics about the federated data distribution"""
        stats = {
            'clients': {},
            'overall': {}
        }
        
        all_train_labels = []
        all_test_labels = []
        
        for client_id, data in client_data.items():
            train_labels = data['train']['class'].value_counts().to_dict()
            test_labels = data['test']['class'].value_counts().to_dict()
            
            stats['clients'][client_id] = {
                'train_samples': len(data['train']),
                'test_samples': len(data['test']),
                'train_label_dist': train_labels,
                'test_label_dist': test_labels
            }
            
            all_train_labels.extend(data['train']['class'].tolist())
            all_test_labels.extend(data['test']['class'].tolist())
        
        stats['overall'] = {
            'total_clients': len(client_data),
            'total_train_samples': len(all_train_labels),
            'total_test_samples': len(all_test_labels),
            'train_label_dist': pd.Series(all_train_labels).value_counts().to_dict(),
            'test_label_dist': pd.Series(all_test_labels).value_counts().to_dict()
        }
        
        return stats

def create_federated_datasets(data_dir: str, output_dir: str, n_clients: int, 
                            partition_type: str = 'non_iid', alpha: float = 0.5, 
                            feature_cols: Optional[List[str]] = None, seed: int = 42):
    """
    Main function to create federated datasets
    
    Args:
        data_dir: Directory containing train.csv, test.csv, orthogonal.csv
        output_dir: Directory to save federated datasets
        n_clients: Number of federated clients
        partition_type: 'iid' or 'non_iid'
        alpha: Dirichlet alpha parameter for non-IID (lower = more heterogeneous)
        feature_cols: List of feature column names
        seed: Random seed for reproducibility
    """
    
    # Initialize manager
    manager = FederatedDatasetManager(data_dir, output_dir)
    
    # Create partitions
    if partition_type == 'iid':
        client_data = manager.create_iid_partition(n_clients, seed)
    elif partition_type == 'non_iid':
        client_data = manager.create_non_iid_partition(n_clients, alpha, seed)
    else:
        raise ValueError("partition_type must be 'iid' or 'non_iid'")
    
    # Save data
    partition_dir = manager.save_client_data(client_data, partition_type)
    
    # Calculate and save statistics
    stats = manager.get_data_statistics(client_data)
    with open(partition_dir / "statistics.pkl", 'wb') as f:
        pickle.dump(stats, f)
    
    # Create PyTorch datasets if feature columns provided
    pytorch_datasets = None
    validation_dataset = None
    if feature_cols:
        pytorch_datasets, validation_dataset = manager.create_pytorch_datasets(client_data, feature_cols)
    
    logger.log_info(f"Federated dataset creation completed!")
    logger.log_info(f"Partition type: {partition_type}")
    logger.log_info(f"Number of clients: {n_clients}")
    logger.log_info(f"Data saved to: {partition_dir}")
    
    return {
        'client_data': client_data,
        'pytorch_datasets': pytorch_datasets,
        'validation_dataset': validation_dataset,
        'statistics': stats,
        'partition_dir': partition_dir
    }

# Usage example
if __name__ == "__main__":
    # Example usage
    data_dir = "data/processed"
    output_dir = "federated_data"
    n_clients = 10
    
    # Assuming your feature columns (adjust based on your actual data)
    # You'll need to specify the actual feature column names from your dataset
    feature_cols = [col for col in pd.read_csv(os.path.join(data_dir, "train.csv")).columns if col != 'class']
    target_col = 'class'
    
    # Create IID partition
    # iid_result = create_federated_datasets(
    #     data_dir=data_dir,
    #     output_dir=output_dir,
    #     n_clients=n_clients,
    #     partition_type='iid',
    #     feature_cols=feature_cols,
    #     seed=42
    # )
    
    # Create Non-IID partition
    non_iid_result = create_federated_datasets(
        data_dir=data_dir,
        output_dir=output_dir,
        n_clients=n_clients,
        partition_type='non_iid',
        alpha=5,  # Lower alpha = more heterogeneous
        feature_cols=feature_cols,
        seed=42
    )