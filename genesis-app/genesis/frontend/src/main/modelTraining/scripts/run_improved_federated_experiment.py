#!/usr/bin/env python3
"""
Script to run improved federated learning experiment with enhanced pathogenicity models
"""

import subprocess
import time
import sys
import argparse
from pathlib import Path

def run_improved_federated_experiment(
    num_clients=3,
    server_port=8080,
    federated_config="configs/federated_config.yaml",
    data_config="configs/data_config.yaml", 
    model_config="configs/model_config.yaml"
):
    """
    Run improved federated learning experiment
    """
    print("🚀 Starting Improved Federated Learning Experiment")
    print(f"📊 Configuration:")
    print(f"   - Number of clients: {num_clients}")
    print(f"   - Server port: {server_port}")
    print(f"   - Federated config: {federated_config}")
    print(f"   - Data config: {data_config}")
    print(f"   - Model config: {model_config}")
    
    # Start server
    print("\n🖥️  Starting improved federated server...")
    server_cmd = [
        sys.executable, "-m", "src.federated.improved_server",
        "--port", str(server_port),
        "--federated_config", federated_config,
        "--data_config", data_config,
        "--model_config", model_config
    ]
    
    server_process = subprocess.Popen(server_cmd)
    
    # Wait for server to start
    print("⏳ Waiting for server to start...")
    time.sleep(10)
    
    # Start clients
    client_processes = []
    for client_id in range(num_clients):
        print(f"👤 Starting improved client {client_id}...")
        client_cmd = [
            sys.executable, "-m", "src.federated.improved_client",
            "--client_id", str(client_id),
            "--federated_config", federated_config,
            "--data_config", data_config,
            "--model_config", model_config,
            "--server", f"localhost:{server_port}"
        ]
        
        client_process = subprocess.Popen(client_cmd)
        client_processes.append(client_process)
        time.sleep(2)  # Stagger client starts
    
    print(f"\n✅ All {num_clients} improved clients started")
    print("🔄 Federated learning in progress...")
    print("📊 Check logs/server/ and logs/client_*/ for detailed logs")
    
    try:
        # Wait for server to complete
        server_process.wait()
        print("\n🎉 Improved federated learning experiment completed!")
        
    except KeyboardInterrupt:
        print("\n⚠️  Experiment interrupted by user")
        
    finally:
        # Clean up processes
        print("🧹 Cleaning up processes...")
        server_process.terminate()
        for client_process in client_processes:
            client_process.terminate()
        
        # Wait for processes to terminate
        server_process.wait()
        for client_process in client_processes:
            client_process.wait()
        
        print("✅ All processes terminated")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run Improved Federated Learning Experiment')
    parser.add_argument('--num_clients', type=int, default=3, help='Number of clients')
    parser.add_argument('--server_port', type=int, default=8080, help='Server port')
    parser.add_argument('--federated_config', type=str, default="configs/federated_config.yaml", help='Federated config path')
    parser.add_argument('--data_config', type=str, default="configs/data_config.yaml", help='Data config path')
    parser.add_argument('--model_config', type=str, default="configs/model_config.yaml", help='Model config path')
    
    args = parser.parse_args()
    
    run_improved_federated_experiment(
        num_clients=args.num_clients,
        server_port=args.server_port,
        federated_config=args.federated_config,
        data_config=args.data_config,
        model_config=args.model_config
    )