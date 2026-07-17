# Genesis

A multi-part project containing:
- `backend/` — Node.js backend API and WebSocket server for client management, authentication, and training orchestration.
- `frontend/` — Electron + React desktop application for interacting with the system.
- `model/` — Python package implementing the ClinVar federated learning system, data preparation, and model training.

## Overview

This repository is organized as a polyglot workspace with three main components:

1. **Backend**: A CommonJS Express application with MongoDB persistence and WebSocket support.
2. **Frontend**: An Electron application built with React and Vite for desktop UI.
3. **Model**: A Python-based federated learning package for pathogenicity prediction using ClinVar.

Each component is largely independent and has its own dependencies and runtime instructions.

---

## Repository Structure

```text
genesis/
├── backend/        # Node.js API, WebSocket server, client/auth/web routing
├── frontend/       # Electron + React desktop application
├── model/          # Python package for federated learning
├── .gitignore
└── README.md       # This file
```

### backend/

- `index.js` — Main Express server entrypoint.
- `routers/` — Route definitions for `/client`, `/auth`, and `/web` endpoints.
- `controllers/` — Controller implementations for client management, authentication, and web actions.
- `.env` — Environment variables used by the backend.
- `package.json` — Backend package manifest.

### frontend/

- `src/` — React source code for the Electron UI.
- `build/` — Compiled application output.
- `electron.vite.config.mjs` — Electron Vite configuration.
- `package.json` — Frontend package manifest.
- `README.md` — Frontend-specific setup instructions.

### model/

- `pyproject.toml` — Python package configuration and dependencies.
- `configs/` — Configuration YAML files for data, model, and federated learning setup.
- `data/` — Raw, processed, and federated dataset files.
- `src/` — Python source code for federation, data creation, and models.
- `federated_data/` — Partitioned dataset for federated experiments.
- `results/`, `logs/`, `models/` — Outputs, log files, and saved models.

---

## Backend

### What it does

The backend is an Express app that provides:
- REST APIs for client management (`/client`)
- User authentication (`/auth`)
- Web control endpoints (`/web`)
- WebSocket communication for connected clients

It also exposes a basic root route at `/` that returns `Hello World!`.

### Important endpoints

- `GET /client/clients` — List all clients.
- `GET /client/clients/:userid` — Get client details.
- `PUT /client/clients/:userid` — Update a client.
- `DELETE /client/clients/:userid` — Delete a client.
- `POST /client/clients/increment-inference/:userid` — Increment inference count.
- `POST /client/clients/increment-contribution/:userid` — Increment contribution count.
- `POST /client/clients/add-activity/:userid` — Add client activity.
- `POST /client/clients/update-data-rows-and-size/:userid` — Update client data statistics.
- `POST /auth/register` — Register a new user.
- `POST /auth/login` — Login.
- `POST /web/startServer` — Start the backend web server.
- `POST /web/stopServer` — Stop the backend web server.

### WebSocket behavior

A WebSocket server is attached to the same HTTP server. It:
- accepts connections from clients using a URL like `/ws/:clientId`
- tracks connected clients in memory
- sends commands like `start_training` and `stop_training`
- logs connection and disconnection activity

### Install and run

```bash
cd genesis/backend
npm install
node index.js
```

The service listens on port `3000` by default.

### Environment

The backend uses `dotenv` to load environment variables. At minimum, provide:

```env
MONGODB=<your-mongodb-connection-string>
```

The connection string is used in `index.js` to connect to MongoDB.

---

## Frontend

### What it does

The frontend is an Electron desktop app built with React and Vite. It is intended to provide a local UI for interacting with the backend and the federated learning workflow.

### Key scripts

- `npm install` — Install dependencies.
- `npm run dev` — Start the Electron app in development mode.
- `npm run build` — Build the Electron application.
- `npm run build:win` — Build a Windows distributable.
- `npm run build:mac` — Build a macOS distributable.
- `npm run build:linux` — Build a Linux distributable.
- `npm run lint` — Run ESLint.
- `npm run format` — Run Prettier.

### Install and run

```bash
cd genesis/frontend
npm install
npm run dev
```

### Notes

This app uses:
- Electron
- React
- Tailwind CSS
- React Router
- WebSocket support via `ws`

---

## Model

### What it does

The `model/` package is a Python project for ClinVar pathogenicity prediction with federated learning support.

It includes:
- Federated server and client logic
- Data creation and partitioning scripts
- Model definitions and embeddings
- Configuration files for data, model, and federation
- Saved models, logs, results, and notebooks

### Dependencies

The package requires Python 3.12 or later. Key dependencies are:
- `flwr` (Flower federated learning)
- `gensim`
- `lightgbm`
- `matplotlib`
- `pandas`
- `pytest`
- `scikit-learn`
- `torch`
- `torchinfo`
- `tqdm`
- `pyyaml`
- `pydantic`

### Install and run

The `model/` package is configured with `pyproject.toml`.

```bash
cd genesis/model
python -m pip install -e .
```

Or, if you use Poetry:

```bash
cd genesis/model
poetry install
```

### Important files and folders

- `configs/` — YAML settings for data, model architecture, and federated learning behavior.
- `data/raw/` — Raw dataset CSV files.
- `data/processed/` — Cleaned and preprocessed train/validation/test splits.
- `federated_data/` — Client-partitioned federated datasets.
- `src/` — Python source code for federated training, data transformation, and models.
- `results/` — Metrics, plots, and reports from experiments.
- `logs/` — Training and execution logs.
- `models/` — Saved model checkpoints and federated models.
- `notebooks/` — Analysis and model exploration notebooks.

---

## Usage Recommendations

Use this repository as a workspace rather than a single deployable application. Each subfolder is a self-contained project:

- `backend/` for API/WebSocket services
- `frontend/` for the Electron desktop client
- `model/` for Python model training and federated experiments

If you want to run the full stack, start each component in its own terminal.

### Suggested order

1. Start MongoDB and set `backend/.env`.
2. Run `backend/index.js`.
3. Run `frontend` in development mode.
4. Use the frontend to interact with the backend and any federated learning orchestration.

### Full stack example

```bash
# Terminal 1: backend
cd genesis/backend
npm install
node index.js

# Terminal 2: frontend
cd genesis/frontend
npm install
npm run dev

# Terminal 3: model (optional for local federated learning experiments)
cd genesis/model
python -m pip install -e .
# or use Poetry if preferred
# poetry install
```

If the frontend connects to the backend, the UI can use backend APIs and the WebSocket server to manage clients and training.

---

## Notes and caveats

- The backend currently uses an online MongoDB connection URL in `index.js` and expects a valid `MONGODB` environment variable.
- The frontend README in `frontend/README.md` contains the basic Electron app setup.
- The Python `model/` package is configured via `pyproject.toml` and appears to target Python 3.12.

---

## Contribution

If you add features, keep each component isolated and document the new behavior in the corresponding subfolder.

- Update `backend/` docs for API or WebSocket changes.
- Update `frontend/README.md` for UI and Electron workflow changes.
- Update `model/README.md` for federated training experiments and dataset changes.
