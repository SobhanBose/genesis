#!/usr/bin/env python3
"""
Test script to demonstrate client sampling in federated learning.
This script shows how to run federated learning with 3 clients but sampling only 2 random clients per round.
"""

import subprocess
import time
import threading
import sys
from pathlib import Path

def start_server():
    """Start the federated learning server"""
    print("Starting federated learning server...")
    subprocess.run([
        sys.executable, "src/federated/server_new.py",
        "--port", "8080",
        "--federated_config", "configs/federated_config.yaml",
        "--data_config", "configs/data_config.yaml", 
        "--model_config", "configs/model_config.yaml"
    ])

def start_client(client_id):
    """Start a federated learning client"""
    print(f"Starting client {client_id}...")
    subprocess.run([
        sys.executable, "src/federated/client_new.py",
        "--client_id", str(client_id),
        "--federated_config", "configs/federated_config.yaml",
        "--data_config", "configs/data_config.yaml",
        "--model_config", "configs/model_config.yaml",
        "--server_address", "localhost:8080"
    ])

def main():
    """Main function to run federated learning with client sampling"""
    print("=" * 60)
    print("FEDERATED LEARNING WITH CLIENT SAMPLING")
    print("=" * 60)
    print("Configuration:")
    print("- Total clients: 3")
    print("- Clients sampled per round: 2 (random selection)")
    print("- Sampling fraction: 0.67 (2/3)")
    print("- Strategy: FedProx")
    print("=" * 60)
    
    # Check if federated data exists
    federated_data_dir = Path("federated_data/non_iid_partition/clients")
    if not federated_data_dir.exists():
        print("❌ Federated data not found!")
        print("Please run the data preparation script first:")
        print("python src/data/create_federated_dataset.py")
        return
    
    # Check if client data exists for all 3 clients
    for client_id in range(3):
        client_dir = federated_data_dir / f"client_{client_id}"
        if not client_dir.exists():
            print(f"❌ Client {client_id} data not found at {client_dir}")
            print("Please ensure all 3 clients have data prepared.")
            return
    
    print("✅ All client data found!")
    
    # Start server in a separate thread
    server_thread = threading.Thread(target=start_server)
    server_thread.daemon = True
    server_thread.start()
    
    # Wait a moment for server to start
    time.sleep(3)
    
    # Start all 3 clients in separate threads
    client_threads = []
    for client_id in range(3):
        client_thread = threading.Thread(target=start_client, args=(client_id,))
        client_thread.daemon = True
        client_thread.start()
        client_threads.append(client_thread)
        time.sleep(1)  # Small delay between client starts
    
    print("\n🚀 Federated learning started!")
    print("📊 Check the logs directory for detailed information about client sampling.")
    print("📈 The server will log which clients are sampled in each round.")
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