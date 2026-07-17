def create_config_files():
    """Create configuration files"""
    
    # Data configuration
    data_config = """
# Data Configuration
data:
  raw_dir: "data/raw"
  processed_dir: "data/processed"
  gene_embeddings_dir: "data/gene_embeddings"
  
  files:
    train: "train.csv"
    test: "test.csv"
    validation: "orthogonal.csv"
    gene_embeddings: "gene2vec_dim_200_iter_9_w2v.tsv"

preprocessing:
  normalize: true
  handle_missing: "drop"  # or "impute"
  feature_selection: false

federated:
  output_dir: "federated_data"
  partitions:
    - type: "iid"
      n_clients: 5
    - type: "non_iid" 
      n_clients: 5
      alpha: 0.5
"""
    
    # Model configuration
    model_config = """
# Model Configuration
model:
  name: "PathogenicityPredictor"
  type: "deep_learning"
  
  architecture:
    input_dim: null  # Will be set based on data
    hidden_dims: [512, 256, 128]
    output_dim: 2  # Binary classification
    dropout: 0.3
    activation: "relu"
    
  training:
    batch_size: 32
    learning_rate: 0.001
    epochs: 100
    optimizer: "adam"
    loss_function: "cross_entropy"
    
  regularization:
    weight_decay: 1e-4
    early_stopping: true
    patience: 10
"""
    
    # Federated learning configuration
    federated_config = """
# Federated Learning Configuration
federated:
  strategy: "FedAvg"  # FedAvg, FedProx, FedNova, etc.
  
  server:
    rounds: 50
    min_fit_clients: 3
    min_eval_clients: 3
    min_available_clients: 5
    
  client:
    local_epochs: 5
    batch_size: 32
    learning_rate: 0.001
    
  aggregation:
    weighted: true  # Weight by number of samples
    
  evaluation:
    server_validation: true
    client_validation: true
    metrics: ["accuracy", "f1_score", "auc"]
    
  privacy:
    differential_privacy: false
    secure_aggregation: false
"""
    
    configs = {
        "configs/data_config.yaml": data_config,
        "configs/model_config.yaml": model_config,
        "configs/federated_config.yaml": federated_config
    }
    
    for config_path, config_content in configs.items():
        with open(config_path, 'w') as f:
            f.write(config_content)

if __name__ == "__main__":
    create_config_files()