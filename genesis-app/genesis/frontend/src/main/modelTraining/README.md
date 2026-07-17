# Model Training (ClinVar Federated Learning)

This folder contains the federated learning model training pipeline for the ClinVar genomics project. It includes data preparation, federated dataset partitioning, client/server orchestration, model definitions, experiments, and evaluation tools.

## What this folder contains

- `configs/` - YAML configuration files for data, model, federated server, and clients.
- `data/` - Local dataset storage and processed artifacts.
- `federated_data/` - Generated federated client partitions and validation splits.
- `logs/` - Training and experiment log files.
- `models/` - Saved model checkpoints, federated client models, and global model artifacts.
- `notebooks/` - Jupyter notebooks for EDA, baseline models, and model experimentation.
- `scripts/` - High-level runner scripts for federated experiments, config generation, and evaluation.
- `src/` - Core Python implementation for data handling, federated clients/server, models, and utilities.
- `results/` - Generated metrics, plots, and reports from experiments.
- `requirements.txt` / `requirements_cpu.txt` - Dependency definitions.
- `install_cpu.sh` / `install_cpu.bat` - CPU-only installation scripts.
- `pyproject.toml` - Python project metadata and dependency list.

## Key features

- Federated learning orchestration with Flower (`flwr`).
- Configurable federated strategies: `FedAvg`, `FedProx`, and `FedAdam`.
- Client/server training with local dataset partitioning.
- Improved pathogenicity prediction models with optional gene embedding support.
- Data preprocessing and federated partition creation for IID and non-IID splits.
- Logging, checkpointing, and evaluation scaffolding.

## Recommended setup

1. Open a terminal in this folder:

   \`\`\`powershell
   cd d:\zipped\genesis\frontend\src\main\modelTraining
   \`\`\`

2. Create and activate a virtual environment.

   On Windows:
   \`\`\`powershell
   python -m venv venv
   .\venv\Scripts\activate.bat
   \`\`\`

   On macOS / Linux:
   \`\`\`bash
   python3 -m venv venv
   source venv/bin/activate
   \`\`\`

3. Install dependencies.

   For CPU-only environments:
   \`\`\`bash
   .\install_cpu.bat
   \`\`\`
   or
   \`\`\`bash
   bash install_cpu.sh
   \`\`\`

   If you want to install dependencies manually:
   \`\`\`bash
   pip install -r requirements_cpu.txt
   \`\`\`

4. Confirm the Python version is compatible. The project metadata specifies `python>=3.12`.

## Data preparation

This folder expects raw and processed data under `data/`:

- `data/raw/` - raw input files such as `train.csv`, `test.csv`, `validation.csv`, and `orthogonal.csv`.
- `data/processed/` - cleaned, preprocessed datasets used for training and validation.
- `data/gene_embeddings/` - gene embedding files used by model feature engineering.

To build federated partitions, run:

\`\`\`bash
python src/data/create_federated_dataset.py
\`\`\`

This script generates:

- `federated_data/iid_partition/clients/`
- `federated_data/non_iid_partition/clients/`
- `federated_data/non_iid_partition/validation.csv`
- `federated_data/*/metadata.pkl`

If `configs/federated_config.yaml` is missing, you can generate basic config files with:

\`\`\`bash
python scripts/create_configs.py
\`\`\`

## Configuration

The main configuration files are:

- `configs/data_config.yaml` - dataset paths and preprocessing settings.
- `configs/model_config.yaml` - model architecture, training, optimizer, and regularization settings.
- `configs/server_config.yaml` - federated server parameters and strategy configuration.
- `configs/client_config.yaml` - client-side training hyperparameters.
- `configs/strategy_examples.yaml` - example strategy settings for `FedAvg`, `FedProx`, and `FedAdam`.

### Legacy / wrapper config support

Some wrapper scripts and example command lines still reference `configs/federated_config.yaml`. If your repo does not already contain this legacy file, create it using `scripts/create_configs.py` or adapt the commands to use the new modular config files.

## Running federated experiments

### Start a federated experiment with the wrapper script

\`\`\`bash
python scripts/run_federated_experiment.py 2
\`\`\`

This script:

- starts the server on port `8080`
- launches the requested number of clients
- expects client partitions under `federated_data/non_iid_partition/clients`

### Run the server directly

\`\`\`bash
python src/federated/server.py --port 8080 --server_config configs/server_config.yaml --data_config configs/data_config.yaml --model_config configs/model_config.yaml
\`\`\`

### Run a client directly

\`\`\`bash
python src/federated/client.py --client_id 0 --client_config configs/client_config.yaml --data_config configs/data_config.yaml --model_config configs/model_config.yaml --server localhost:8080
\`\`\`

### Run the improved federated experiment

\`\`\`bash
python scripts/run_improved_federated_experiment.py --num_clients 3
\`\`\`

This wrapper launches the improved server and multiple improved clients with the default configuration files.

## Evaluation and model inspection

- `scripts/evaluate_best_model.py` - evaluate a saved model checkpoint.
- `scripts/evaluate_best_kfold_model.py` - evaluate models trained using cross-validation.
- `notebooks/` - interactive exploration and model diagnostics.

## Folder structure overview

- `src/data/` - data processing, dataset classes, and federated partition generation.
- `src/federated/` - Flower server/client implementations, config loading, and strategy factory logic.
- `src/models/` - model definitions, improved pathogenicity architecture, feature engineering, and loss utilities.
- `src/utils/` - shared utilities such as logger helpers.
- `scripts/` - high-level orchestration scripts for config generation, experiments, and validation.

## Logs and outputs

- `logs/` - runtime logs created by server and clients.
- `models/` - saved model files, checkpoints, and global / federated model artifacts.
- `results/` - generated metrics, plots, and reports.

## Notes

- The project uses Flower (`flwr`) for federated learning orchestration.
- If you are working on CPU-only hardware, prefer `requirements_cpu.txt` and the install scripts provided here.
- If you want to extend the project, use the modular configs in `configs/` and update the corresponding `server.py` / `client.py` arguments.

## Useful commands

\`\`\`bash
# Activate environment
.\venv\Scripts\activate.bat

# Generate example configs
python scripts/create_configs.py

# Prepare federated data
python src/data/create_federated_dataset.py

# Run the federated training experiment
python scripts/run_federated_experiment.py 3

# Run the improved federated experiment
python scripts/run_improved_federated_experiment.py --num_clients 3
\`\`\`

## Contact

For questions about this folder or the ClinVar federated training workflow, inspect the `src/` implementation and the `configs/` templates.
'@
