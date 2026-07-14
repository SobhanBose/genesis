#!/usr/bin/env python3
"""
Analyze global model performance metrics from federated learning results.
"""

import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Tuple

def parse_metrics_from_log(log_text: str) -> Dict[str, List[Tuple[int, float]]]:
    """
    Parse global metrics from the log output.
    
    Args:
        log_text: The log output containing metrics
        
    Returns:
        Dictionary with global_accuracy and global_loss data
    """
    metrics = {}
    
    # Extract global_accuracy data
    if 'global_accuracy' in log_text:
        acc_start = log_text.find("'global_accuracy': [")
        acc_end = log_text.find("]", acc_start)
        acc_data = log_text[acc_start:acc_end]
        
        # Parse the tuples
        acc_tuples = []
        for line in acc_data.split('\n'):
            if '(' in line and ')' in line:
                # Extract round and value
                parts = line.strip().strip(',').strip('(').strip(')').split(',')
                if len(parts) == 2:
                    round_num = int(parts[0])
                    value = float(parts[1])
                    acc_tuples.append((round_num, value))
        
        metrics['global_accuracy'] = acc_tuples
    
    # Extract global_loss data
    if 'global_loss' in log_text:
        loss_start = log_text.find("'global_loss': [")
        loss_end = log_text.find("]", loss_start)
        loss_data = log_text[loss_start:loss_end]
        
        # Parse the tuples
        loss_tuples = []
        for line in loss_data.split('\n'):
            if '(' in line and ')' in line:
                # Extract round and value
                parts = line.strip().strip(',').strip('(').strip(')').split(',')
                if len(parts) == 2:
                    round_num = int(parts[0])
                    value = float(parts[1])
                    loss_tuples.append((round_num, value))
        
        metrics['global_loss'] = loss_tuples
    
    return metrics

def analyze_global_performance(metrics: Dict[str, List[Tuple[int, float]]]):
    """
    Analyze global model performance.
    
    Args:
        metrics: Dictionary containing global_accuracy and global_loss data
    """
    print("=" * 60)
    print("GLOBAL MODEL PERFORMANCE ANALYSIS")
    print("=" * 60)
    
    if 'global_accuracy' in metrics:
        acc_data = metrics['global_accuracy']
        rounds, accuracies = zip(*acc_data)
        
        print(f"\n📊 GLOBAL ACCURACY (Validation Set)")
        print(f"   Rounds: {len(rounds)}")
        print(f"   Best Accuracy: {max(accuracies):.4f} (Round {rounds[accuracies.index(max(accuracies))]})")
        print(f"   Final Accuracy: {accuracies[-1]:.4f} (Round {rounds[-1]})")
        print(f"   Average Accuracy: {np.mean(accuracies):.4f}")
        print(f"   Accuracy Range: {min(accuracies):.4f} - {max(accuracies):.4f}")
        print(f"   Standard Deviation: {np.std(accuracies):.4f}")
        
        # Trend analysis
        if len(accuracies) > 1:
            trend = "↗️ Improving" if accuracies[-1] > accuracies[0] else "↘️ Declining"
            print(f"   Overall Trend: {trend}")
    
    if 'global_loss' in metrics:
        loss_data = metrics['global_loss']
        rounds, losses = zip(*loss_data)
        
        print(f"\n📉 GLOBAL LOSS (Validation Set)")
        print(f"   Rounds: {len(rounds)}")
        print(f"   Best Loss: {min(losses):.4f} (Round {rounds[losses.index(min(losses))]})")
        print(f"   Final Loss: {losses[-1]:.4f} (Round {rounds[-1]})")
        print(f"   Average Loss: {np.mean(losses):.4f}")
        print(f"   Loss Range: {min(losses):.4f} - {max(losses):.4f}")
        print(f"   Standard Deviation: {np.std(losses):.4f}")
        
        # Trend analysis
        if len(losses) > 1:
            trend = "↘️ Improving" if losses[-1] < losses[0] else "↗️ Declining"
            print(f"   Overall Trend: {trend}")
    
    # Combined analysis
    if 'global_accuracy' in metrics and 'global_loss' in metrics:
        print(f"\n🎯 COMBINED ANALYSIS")
        acc_data = metrics['global_accuracy']
        loss_data = metrics['global_loss']
        
        # Find best round (highest accuracy, lowest loss)
        best_acc_round = max(acc_data, key=lambda x: x[1])
        best_loss_round = min(loss_data, key=lambda x: x[1])
        
        print(f"   Best Accuracy Round: {best_acc_round[0]} (Acc: {best_acc_round[1]:.4f})")
        print(f"   Best Loss Round: {best_loss_round[0]} (Loss: {best_loss_round[1]:.4f})")
        
        # Check if they coincide
        if best_acc_round[0] == best_loss_round[0]:
            print(f"   ✅ Best accuracy and loss occurred in the same round!")
        else:
            print(f"   ⚠️  Best accuracy and loss occurred in different rounds")

def plot_global_metrics(metrics: Dict[str, List[Tuple[int, float]]], save_path: str = "global_metrics.png"):
    """
    Plot global accuracy and loss over rounds.
    
    Args:
        metrics: Dictionary containing global_accuracy and global_loss data
        save_path: Path to save the plot
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    
    if 'global_accuracy' in metrics:
        acc_data = metrics['global_accuracy']
        rounds, accuracies = zip(*acc_data)
        
        ax1.plot(rounds, accuracies, 'b-o', linewidth=2, markersize=6, label='Global Accuracy')
        ax1.set_ylabel('Accuracy')
        ax1.set_title('Global Model Accuracy (Validation Set)')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Add best accuracy marker
        best_acc_idx = np.argmax(accuracies)
        ax1.plot(rounds[best_acc_idx], accuracies[best_acc_idx], 'ro', markersize=10, label=f'Best: {accuracies[best_acc_idx]:.4f}')
        ax1.legend()
    
    if 'global_loss' in metrics:
        loss_data = metrics['global_loss']
        rounds, losses = zip(*loss_data)
        
        ax2.plot(rounds, losses, 'r-o', linewidth=2, markersize=6, label='Global Loss')
        ax2.set_xlabel('Federated Round')
        ax2.set_ylabel('Loss')
        ax2.set_title('Global Model Loss (Validation Set)')
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        
        # Add best loss marker
        best_loss_idx = np.argmin(losses)
        ax2.plot(rounds[best_loss_idx], losses[best_loss_idx], 'go', markersize=10, label=f'Best: {losses[best_loss_idx]:.4f}')
        ax2.legend()
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"\n📈 Plot saved as: {save_path}")

def main():
    """Main function to analyze the provided log data."""
    
    # Your log data
    log_data = """
INFO :          History (metrics, distributed, evaluate):
INFO :          {'accuracy': [(1, 0.9241902538663554),
INFO :                        (2, 0.9311934636708491),
INFO :                        (3, 0.9320105048147067),
INFO :                        (4, 0.9278085789320105),
INFO :                        (5, 0.9317187044061862),
INFO :                        (6, 0.9269915377881529),
INFO :                        (7, 0.9255325357455501),
INFO :                        (8, 0.9297344616282462),
INFO :                        (9, 0.9245404143565801),
INFO :                        (10, 0.9245404143565801),
INFO :                        (11, 0.9360957105339948),
INFO :                        (12, 0.9289757805660928),
INFO :                        (13, 0.9283921797490516),
INFO :                        (14, 0.9298511817916545),
INFO :                        (15, 0.9341114677560548),
INFO :                        (16, 0.9282170995039393),
INFO :                        (17, 0.914269039976656),
INFO :                        (18, 0.9273416982783775),
INFO :                        (19, 0.9205135687189963),
INFO :                        (20, 0.9252407353370294)],
INFO :           'global_accuracy': [(1, 0.7534932494163513),
INFO :                               (2, 0.8182021975517273),
INFO :                               (3, 0.8306807279586792),
INFO :                               (4, 0.8201449513435364),
INFO :                               (5, 0.8516027927398682),
INFO :                               (6, 0.8356123566627502),
INFO :                               (7, 0.8258985280990601),
INFO :                               (8, 0.8134947419166565),
INFO :                               (9, 0.7928715348243713),
INFO :                               (10, 0.8178285956382751),
INFO :                               (11, 0.8349398374557495),
INFO :                               (12, 0.8311290740966797),
INFO :                               (13, 0.8235821723937988),
INFO :                               (14, 0.8270193338394165),
INFO :                               (15, 0.8004931807518005),
INFO :                               (16, 0.8082641959190369),
INFO :                               (17, 0.7915265560150146),
INFO :                               (18, 0.8084136843681335),
INFO :                               (19, 0.8026601076126099),
INFO :                               (20, 0.7655234336853027)],
INFO :           'global_loss': [(1, 0.5468737483024597),
INFO :                           (2, 0.4451076090335846),
INFO :                           (3, 0.4227033853530884),
INFO :                           (4, 0.4482681155204773),
INFO :                           (5, 0.37880876660346985),
INFO :                           (6, 0.41575920581817627),
INFO :                           (7, 0.4174973964691162),
INFO :                           (8, 0.4481009542942047),
INFO :                           (9, 0.48967665433883667),
INFO :                           (10, 0.4574154019355774),
INFO :                           (11, 0.42920053005218506),
INFO :                           (12, 0.41087058186531067),
INFO :                           (13, 0.43575581908226013),
INFO :                           (14, 0.4320477545261383),
INFO :                           (15, 0.4749756455421448),
INFO :                           (16, 0.47364604473114014),
INFO :                           (17, 0.5071578621864319),
INFO :                           (18, 0.473300576210022),
INFO :                           (19, 0.48286640644073486),
INFO :                           (20, 0.5484695434570312)]}
    """
    
    # Parse metrics
    metrics = parse_metrics_from_log(log_data)
    
    # Analyze performance
    analyze_global_performance(metrics)
    
    # Create visualization
    try:
        plot_global_metrics(metrics)
    except ImportError:
        print("\n⚠️  matplotlib not available, skipping plot generation")

if __name__ == "__main__":
    main() 