#!/usr/bin/env python3
"""
Federated Learning Experiment Runner
Usage: python scripts/run_federated_experiment.py [num_clients]
"""

import subprocess
import time
import threading
import sys
import signal
import os
from pathlib import Path

def start_server(port=8080):
    """Start the federated learning server"""
    print(f"Starting federated learning server on port {port}...")
    try:
        subprocess.run([
            sys.executable, "src/federated/server.py",
            "--port", str(port),
            "--federated_config", "configs/federated_config.yaml",
            "--data_config", "configs/data_config.yaml", 
            "--model_config", "configs/model_config.yaml"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Server failed to start: {e}")
        return False
    return True

def start_client(client_id, server_address="localhost:8080"):
    """Start a federated learning client"""
    print(f"Starting client {client_id}...")
    try:
        subprocess.run([
            sys.executable, "src/federated/client.py",
            "--client_id", str(client_id),
            "--federated_config", "configs/federated_config.yaml",
            "--data_config", "configs/data_config.yaml",
            "--model_config", "configs/model_config.yaml",
            "--server", server_address
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Client {client_id} failed to start: {e}")
        return False
    return True

def main():
    """Main function to run federated learning experiment"""
    # Get number of clients from command line argument
    num_clients = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    
    print("=" * 60)
    print("FEDERATED LEARNING EXPERIMENT")
    print("=" * 60)
    print(f"Configuration:")
    print(f"- Number of clients: {num_clients}")
    print(f"- Server port: 8080")
    print(f"- Strategy: FedProx")
    print("=" * 60)
    
    # Check if federated data exists
    federated_data_dir = Path("federated_data/non_iid_partition/clients")
    if not federated_data_dir.exists():
        print("❌ Federated data not found!")
        print("Please run the data preparation script first:")
        print("python src/data/create_federated_dataset.py")
        return
    
    # Check if client data exists for all clients
    for client_id in range(num_clients):
        client_dir = federated_data_dir / f"client_{client_id}"
        if not client_dir.exists():
            print(f"❌ Client {client_id} data not found at {client_dir}")
            print("Please ensure all clients have data prepared.")
            return
    
    print("✅ All client data found!")
    
    # Start server in a separate thread
    server_thread = threading.Thread(target=start_server)
    server_thread.daemon = True
    server_thread.start()
    
    # Wait a moment for server to start
    time.sleep(3)
    
    # Start all clients in separate threads
    client_threads = []
    for client_id in range(num_clients):
        client_thread = threading.Thread(target=start_client, args=(client_id,))
        client_thread.daemon = True
        client_thread.start()
        client_threads.append(client_thread)
        time.sleep(1)  # Small delay between client starts
    
    print("\n🚀 Federated learning started!")
    print("📊 Check the logs directory for detailed information.")
    print("📈 The server will log training progress and client sampling.")
    print("\nPress Ctrl+C to stop all processes...")
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping federated learning...")
        print("✅ All processes stopped.")

if __name__ == "__main__":
    main() 