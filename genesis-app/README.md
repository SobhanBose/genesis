# GENESIS Project

GENESIS is a full-stack federated learning platform that combines a Python-based federated learning server, a Node.js backend, and React-based web and desktop clients. The project is designed to orchestrate training runs, manage experiment metadata, and provide a user-facing interface for monitoring and controlling federated learning workflows.

## Overview

This repository contains four related components:

- [fl_server](fl_server): a FastAPI + Flower (FLWR) service for managing federated learning runs and exposing training APIs
- [genesis/backend](genesis/backend): a Node.js/Express backend service
- [genesis/frontend](genesis/frontend): an Electron desktop application built with React and Vite
- [GenesisWeb](GenesisWeb): a browser-based React web application

The platform is intended for training and evaluating federated learning experiments on biological or genomics-related data, with support for logging, metrics, run persistence, and run lifecycle management.

## Project Structure

```text
.
├── fl_server/              # Python federated learning server and API
├── genesis/                # Desktop app stack
│   ├── backend/            # Express API service
│   └── frontend/           # Electron + React client
├── GenesisWeb/             # Web client (React + Vite)
├── README.md               # Project overview and setup guide
└── Doc.txt, tree.txt       # Additional project notes
```

## Key Features

- Start, stop, and monitor federated learning training runs
- Expose REST endpoints for run status, logs, errors, and metrics
- Persist run metadata and results to disk
- Support multiple frontend clients (desktop and web)
- Provide an API documentation experience through Swagger/ReDoc
- Include Docker-based deployment support for the FL server

## Prerequisites

Before starting, make sure you have the following installed:

- Python 3.12 or newer
- Node.js 18+ and npm
- A terminal with PowerShell or Bash support
- Optional: Docker and Docker Compose for containerized deployment

## 1. FL Server Setup

The federated learning server lives in [fl_server](fl_server).

### Create a Python environment

On Windows PowerShell:

```powershell
cd fl_server
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

On macOS/Linux:

```bash
cd fl_server
python3 -m venv .venv
source .venv/bin/activate
```

### Install Python dependencies

```bash
pip install -r requirements.txt
```

### Run the API server

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Once running, the service will be available at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health endpoint: http://localhost:8000/api/v1/health

### FL Server API highlights

The API exposes endpoints under the /api/v1/training namespace, including:

- POST /api/v1/training/start: start a new training run
- POST /api/v1/training/stop: stop the active run
- GET /api/v1/training/status: get current status
- GET /api/v1/training/runs: list previous runs
- GET /api/v1/training/runs/{run_id}: inspect run metadata
- GET /api/v1/training/metrics: fetch current metrics
- GET /api/v1/training/logs: retrieve logs

## 2. Node Backend Setup

The backend service is located in [genesis/backend](genesis/backend).

```bash
cd genesis/backend
npm install
```

This service is intended to support the broader application backend and can be extended for additional APIs and integrations.

## 3. Electron Frontend Setup

The desktop client is located in [genesis/frontend](genesis/frontend).

```bash
cd genesis/frontend
npm install
npm run dev
```

The frontend also contains model training assets under its source tree. The project notes indicate that the following step may be needed in some setups:

```bash
cd src/main/modelTraining
./install_cpu.bat
```

If you are on Windows, run the batch script from the appropriate location before launching the app.

## 4. Web Frontend Setup

The browser-based client is located in [GenesisWeb](GenesisWeb).

```bash
cd GenesisWeb
npm install
npm run dev
```

This will start the Vite development server for the web application.

## 5. Docker Usage

The FL server also includes Docker configuration in [fl_server](fl_server).

### Build the image

```bash
cd fl_server
./build.sh
```

### Run with Docker Compose

```bash
docker-compose up -d
```

For more details, see [fl_server/DOCKER.md](fl_server/DOCKER.md).

## Configuration and Data

The FL server uses YAML configuration files in [fl_server/configs](fl_server/configs) and writes output artifacts to directories such as:

- [fl_server/logs](fl_server/logs)
- [fl_server/results](fl_server/results)
- [fl_server/models](fl_server/models)
- [fl_server/data](fl_server/data)

These directories hold run metadata, logs, checkpoints, metrics, and model artifacts.

## Development Notes

- The FL server is the core orchestration layer for training lifecycle and run management.
- The frontend applications are client interfaces that depend on the backend services and training APIs.
- The repository is organized around modular components, so changes to training logic, API routes, or UI components can be made independently.
- The Python server uses FastAPI, Pydantic, and Flower, while the web and desktop clients use React and Vite.

## Recommended Development Workflow

1. Start the FL server.
2. Launch the backend service.
3. Start the desktop or web client.
4. Use the Swagger UI to explore endpoints and test training operations.
5. Review logs and metrics in the generated output directories.

## Troubleshooting

If you encounter setup issues:

- Confirm that Python and Node.js versions meet the stated requirements.
- Reinstall dependencies if package versions or environment state are inconsistent.
- Ensure the virtual environment is activated before running the Python server.
- If the FL server cannot find files or model assets, verify that the expected directories exist under [fl_server](fl_server).
- For Windows-specific setup, use the appropriate PowerShell commands and ensure scripts are run from the correct folder.

## License

This project does not currently define a public license in the repository metadata. Please check with the project owners before redistribution or commercial use.
