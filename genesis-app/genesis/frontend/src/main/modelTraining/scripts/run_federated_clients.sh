#!/bin/bash

# Simple Federated Learning Runner for WSL2
# Usage: ./scripts/run_federated_experiment.sh [num_clients]

set -e

# Default number of clients
NUM_CLIENTS=${1:-2}
SERVER_PORT=8080

echo "Starting federated learning experiment with $NUM_CLIENTS clients..."

# Start server in background
# echo "Starting server on port $SERVER_PORT..."
# uv run -m src.federated.server --port $SERVER_PORT &
# SERVER_PID=$!

# Wait for server to start
# sleep 3

# Start clients
echo "Starting $NUM_CLIENTS clients..."
for ((i=0; i<NUM_CLIENTS; i++)); do
    echo "Starting client $i..."
    uv run -m src.federated.client --client_id $i --server localhost:$SERVER_PORT > /dev/null 2>&1 &
    sleep 1
done

echo "All processes started!"
# echo "Server PID: $SERVER_PID"
echo "Press Ctrl+C to stop all processes"

# Wait for user interrupt
trap 'echo "\nStopping all processes..."; pkill -f "uv run.*client"; pkill -f "gnome-terminal.*client"; pkill -f "xterm.*client"; exit' INT
wait 