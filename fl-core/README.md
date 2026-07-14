# ClinVar Federated Learning System

This repository implements a federated learning workflow for pathogenicity prediction on ClinVar-style sequence data. The current pipeline is centered on a Flower-based federated server and client setup, uses FedProx as the default server strategy, and evaluates the global model on a centralized validation set after each round.

## What this project does

The codebase supports the following workflow:

1. Load raw or processed ClinVar-style data.
2. Create federated partitions for multiple clients.
3. Train a binary pathogenicity classifier locally on each client.
4. Aggregate client updates on a central server with FedProx regularization.
5. Evaluate the resulting global model on a held-out validation set.
6. Save logs, checkpoints, and evaluation outputs for downstream analysis.

## Repository layout

```text
clinvar/
├── configs/                     # YAML configuration files
├── data/                        # Raw and processed datasets
├── federated_data/              # Partitioned client data and validation sets
├── logs/                        # Server/client training logs
├── models/                      # Saved checkpoints and Word2Vec embedding models
├── results/                     # Metrics, plots, and reports
├── scripts/                     # Entry-point training/evaluation scripts
├── src/
│   ├── data/                    # Dataset creation and partitioning
│   ├── federated/               # Server and client training logic
│   ├── models/                  # Model definitions and feature engineering
│   └── utils/                   # Logging and helper utilities
└── pyproject.toml               # Project dependencies
```

## Requirements

The project targets Python 3.12+.

Install dependencies from the repository root:

```bash
pip install -e .
```

If you use uv, the equivalent command is:

```bash
uv sync
```

Core dependencies include:

- PyTorch
- Flower (flwr)
- scikit-learn
- pandas
- numpy
- gensim
- matplotlib

## Data requirements

The current training and evaluation workflow expects the following inputs:

- Raw and processed CSV files in `data/raw/` and `data/processed/`
- A validation CSV at `federated_data/non_iid_partition/validation.csv`
- Client-specific train/test CSV files under `federated_data/non_iid_partition/clients/client_X/`
- Word2Vec embedding models at:
  - `models/global_models/ref_word2vec.model`
  - `models/global_models/alt_word2vec.model`

If those embedding files are missing, federated training will fail before the first round can start.

## Configuration files

The main configuration files are:

- `configs/federated_config.yaml` – federated server/client behavior, client sampling, and FedProx settings
- `configs/data_config.yaml` – dataset paths and partitioning options
- `configs/model_config.yaml` – model architecture, optimization, and evaluation settings

### Federated configuration

The current default federated settings are:

```yaml
federated:
  strategy: "FedProx"
  proximal_mu: 0.01

  server:
    rounds: 50
    min_fit_clients: 2
    min_eval_clients: 0
    min_available_clients: 3
    fraction_fit: 0.67
    fraction_evaluate: 0.0
```

This means:

- The server can see up to 3 clients.
- About 2 clients are sampled per round.
- Client-side evaluation is disabled, and the server evaluates the global model centrally.

### Model configuration highlights

The model configuration currently supports multiple architecture options and training settings, including:

- `basic`, `improved`, `lightweight`, and `ensemble` model types
- binary classification output with 2 classes
- Adam/AdamW/SGD optimizers
- configurable batch size, learning rate, and weight decay
- optional regularization and early stopping

## Quick start

### 1. Prepare federated data

From the repository root:

```bash
python src/data/create_federated_dataset.py
```

This creates partitioned client data and a validation set under `federated_data/`.

### 2. Start the federated server

```bash
python src/federated/server.py --port 8080
```

The server loads the validation set, initializes the global model, and begins the training rounds.

### 3. Start one or more federated clients

Open separate terminals and run:

```bash
python src/federated/client.py --client_id 0 --server localhost:8080
```

Additional clients can be started with client IDs `1`, `2`, and so on, as long as matching client folders exist in the partitioned data directory.

## Training and evaluation scripts

### Advanced centralized training

```bash
python scripts/run_improved_training.py
```

This script trains an advanced centralized or experiment-style model workflow and writes logs and checkpoints under the `logs/` and `models/` directories.

### Model sanity checks

```bash
python scripts/test_improved_model.py
```

This validates model creation, forward passes, and architecture differences for the available model variants.

### Evaluate the best saved model

```bash
python scripts/evaluate_best_model.py
```

This script loads a saved checkpoint and reports evaluation metrics on the training, test, and validation sets.

## How client sampling works

The server uses Flower’s sampling parameters from `configs/federated_config.yaml`:

- `min_available_clients`: total clients that can register
- `min_fit_clients`: minimum number of clients required for a fit round
- `fraction_fit`: fraction of available clients to sample per round
- `fraction_evaluate`: fraction used for evaluation; set to `0.0` to rely on centralized evaluation

A typical setup with 3 available clients and 2 sampled per round is:

```yaml
federated:
  server:
    min_available_clients: 3
    min_fit_clients: 2
    fraction_fit: 0.67
    fraction_evaluate: 0.0
```

## Outputs and artifacts

The repository writes the following outputs during training and evaluation:

- `logs/server/` – server-side logs
- `logs/client_X/` – per-client logs
- `models/checkpoints/` – saved checkpoints
- `results/advanced_training/` – metrics, plots, and reports
- `federated_data/` – generated partitions and validation data

## Troubleshooting

### Common issues

- `FileNotFoundError: Client data not found`
  - Re-run `python src/data/create_federated_dataset.py`.
  - Verify that the expected client directories exist under `federated_data/non_iid_partition/clients/`.

- `FileNotFoundError: Word2Vec models not found`
  - Confirm that `models/global_models/ref_word2vec.model` and `models/global_models/alt_word2vec.model` exist.

- `Not enough clients`
  - Start additional clients or lower `min_fit_clients`.
  - Make sure the client IDs match the partition folders.

- Import or dependency errors
  - Reinstall dependencies with `pip install -e .`.

## Notes

- The default federated configuration uses a non-IID partitioning setup.
- The server performs centralized validation on the held-out validation set rather than relying on client-side evaluation.
- The advanced training workflow is intended for model experimentation and checkpointing, while the federated workflow is the primary distributed training path.

