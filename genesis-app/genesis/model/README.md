# ClinVar Federated Learning System

A federated learning system for pathogenicity prediction using the ClinVar dataset, featuring client sampling capabilities.

## Features

- **Federated Learning**: Distributed training across multiple clients
- **Client Sampling**: Random sampling of clients in each round
- **FedProx Strategy**: Robust federated averaging with proximal terms
- **Centralized Evaluation**: Global model evaluation on validation data
- **Learning Rate Scheduling**: Multiple scheduling strategies (step decay, exponential, cosine annealing)
- **Non-IID Data Partitioning**: Realistic data distribution across clients

## Client Sampling Configuration

The system supports configurable client sampling where you can specify:
- Total number of available clients
- Number of clients to sample per round
- Sampling fraction (ratio of clients to sample)

### Example: 3 Clients, 2 Sampled Per Round

```yaml
# configs/federated_config.yaml
federated:
  server:
    min_available_clients: 3    # Total clients available
    min_fit_clients: 2          # Minimum clients required per round
    fraction_fit: 0.67          # Sample 2 out of 3 clients (2/3 = 0.67)
    fraction_evaluate: 0.0      # No client evaluation (use centralized)
```

This configuration will:
- Have 3 total clients available
- Randomly sample 2 clients in each round
- Ensure at least 2 clients participate per round
- Use centralized evaluation instead of client evaluation

## Quick Start

### 1. Validate Configuration

```bash
python validate_client_sampling.py
```

This will show your current configuration and validate the client sampling setup.

### 2. Prepare Data (if not already done)

```bash
python src/data/create_federated_dataset.py
```

### 3. Run Federated Learning with Client Sampling

```bash
python test_client_sampling.py
```

This will start:
- 1 federated learning server
- 3 clients (but only 2 will be sampled per round)

## Configuration Files

### Federated Configuration (`configs/federated_config.yaml`)

```yaml
federated:
  strategy: "FedProx"
  proximal_mu: 0.01
  
  server:
    rounds: 30
    min_fit_clients: 2
    min_available_clients: 3
    fraction_fit: 0.67          # Key parameter for client sampling
    fraction_evaluate: 0.0
    
  client:
    local_epochs: 5
    batch_size: 32
    learning_rate: 1e-4
```

### Data Configuration (`configs/data_config.yaml`)

```yaml
data:
  raw_dir: "data/raw"
  processed_dir: "data/processed"
  federated_dir: "federated_data"
```

### Model Configuration (`configs/model_config.yaml`)

```yaml
model:
  architecture:
    input_dim: null  # Auto-determined
    hidden_dims: [512, 256, 128]
    output_dim: 2
    dropout: 0.3
```

## Client Sampling Details

### How It Works

1. **Client Registration**: All 3 clients register with the server
2. **Round Start**: Server begins a new training round
3. **Random Sampling**: Server randomly selects 2 out of 3 clients
4. **Training**: Selected clients train on their local data
5. **Aggregation**: Server aggregates model updates from participating clients
6. **Evaluation**: Global model is evaluated on validation data
7. **Repeat**: Process continues for specified number of rounds

### Sampling Patterns

With 3 clients and 2 sampled per round, you might see patterns like:
- Round 1: Clients [0, 1] participate
- Round 2: Clients [1, 2] participate
- Round 3: Clients [0, 2] participate
- Round 4: Clients [0, 1] participate
- ... and so on

### Logging

The server logs detailed information about client sampling:
```
Round 1: Sampled 2 clients out of 3 available clients (fraction_fit=0.67)
Round 1: Sampled clients: [0, 1]
```

## Customizing Client Sampling

### Different Sampling Ratios

To change the sampling ratio, modify `fraction_fit` in the configuration:

```yaml
# Sample 1 out of 3 clients (33%)
fraction_fit: 0.33

# Sample all 3 clients (100%)
fraction_fit: 1.0

# Sample 2 out of 5 clients (40%)
min_available_clients: 5
fraction_fit: 0.4
```

### Minimum Client Requirements

Ensure `min_fit_clients` is set appropriately:
- Should be ≤ `min_available_clients * fraction_fit`
- Represents the minimum clients needed for training to proceed

## Running Individual Components

### Start Server Only

```bash
python src/federated/server_new.py --port 8080
```

### Start Individual Client

```bash
python src/federated/client_new.py --client_id 0 --server_address localhost:8080
```

## Monitoring and Logs

- **Server logs**: `logs/server/`
- **Client logs**: `logs/client_X/` (where X is client ID)
- **Results**: `results/` directory

## Requirements

- Python 3.8+
- PyTorch
- Flower (flwr)
- scikit-learn
- pandas
- numpy
- gensim

## Project Structure

```
clinvar/
├── configs/                 # Configuration files
├── src/
│   ├── federated/          # Federated learning components
│   ├── models/             # Model definitions
│   ├── data/               # Data processing
│   └── utils/              # Utilities
├── federated_data/         # Partitioned client data
├── logs/                   # Training logs
├── results/                # Results and metrics
├── test_client_sampling.py # Main execution script
└── validate_client_sampling.py # Configuration validation
```

## Troubleshooting

### Common Issues

1. **"Client data not found"**: Run data preparation script first
2. **"Not enough clients"**: Ensure all clients are started and connected
3. **"Configuration validation failed"**: Check your YAML configuration syntax

### Validation

Always run the validation script before starting training:
```bash
python validate_client_sampling.py
```

This will check:
- Configuration syntax
- Client data availability
- Sampling parameter consistency
