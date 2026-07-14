#!/usr/bin/env python3
"""
Test script for weighted average metrics aggregation function.
"""

from typing import List, Tuple, Dict
from flwr.common import Metrics

def weighted_average_metrics(metrics: List[Tuple[int, Metrics]]) -> Metrics:
    """
    Aggregate evaluation metrics using weighted average based on number of examples.
    
    Args:
        metrics: List of tuples containing (num_examples, metrics_dict)
    
    Returns:
        Aggregated metrics dictionary
    """
    if not metrics:
        return {}
    
    # Get all unique metric keys
    all_keys = set()
    for _, metric_dict in metrics:
        all_keys.update(metric_dict.keys())
    
    aggregated_metrics = {}
    
    for key in all_keys:
        # Calculate weighted average for each metric
        weighted_sum = 0.0
        total_examples = 0
        
        for num_examples, metric_dict in metrics:
            if key in metric_dict:
                weighted_sum += num_examples * float(metric_dict[key])
                total_examples += num_examples
        
        if total_examples > 0:
            aggregated_metrics[key] = weighted_sum / total_examples
    
    return aggregated_metrics

def test_weighted_average():
    """Test the weighted average function with sample data."""
    
    # Sample metrics from different clients
    client_metrics = [
        (100, {"accuracy": 0.85, "loss": 0.15, "f1_score": 0.82}),  # Client 1: 100 samples
        (50, {"accuracy": 0.90, "loss": 0.10, "f1_score": 0.88}),   # Client 2: 50 samples
        (75, {"accuracy": 0.78, "loss": 0.22, "f1_score": 0.75}),   # Client 3: 75 samples
    ]
    
    # Calculate expected results manually
    # accuracy: (100*0.85 + 50*0.90 + 75*0.78) / (100 + 50 + 75) = 84.5 / 225 = 0.3756
    # loss: (100*0.15 + 50*0.10 + 75*0.22) / 225 = 30.5 / 225 = 0.1356
    # f1_score: (100*0.82 + 50*0.88 + 75*0.75) / 225 = 182.5 / 225 = 0.8111
    
    expected_accuracy = (100*0.85 + 50*0.90 + 75*0.78) / 225
    expected_loss = (100*0.15 + 50*0.10 + 75*0.22) / 225
    expected_f1_score = (100*0.82 + 50*0.88 + 75*0.75) / 225
    
    # Test the function
    result = weighted_average_metrics(client_metrics)
    
    print("Test Results:")
    print(f"Expected accuracy: {expected_accuracy:.4f}")
    print(f"Actual accuracy: {result['accuracy']:.4f}")
    print(f"Expected loss: {expected_loss:.4f}")
    print(f"Actual loss: {result['loss']:.4f}")
    print(f"Expected f1_score: {expected_f1_score:.4f}")
    print(f"Actual f1_score: {result['f1_score']:.4f}")
    
    # Verify results
    assert abs(result['accuracy'] - expected_accuracy) < 1e-4, f"Accuracy mismatch: {result['accuracy']} vs {expected_accuracy}"
    assert abs(result['loss'] - expected_loss) < 1e-4, f"Loss mismatch: {result['loss']} vs {expected_loss}"
    assert abs(result['f1_score'] - expected_f1_score) < 1e-4, f"F1 score mismatch: {result['f1_score']} vs {expected_f1_score}"
    
    print("\n✅ All tests passed! Weighted average function is working correctly.")
    
    # Test edge case: empty metrics
    empty_result = weighted_average_metrics([])
    assert empty_result == {}, f"Empty metrics should return empty dict, got {empty_result}"
    print("✅ Empty metrics test passed!")
    
    # Test edge case: single client
    single_client = [(100, {"accuracy": 0.85})]
    single_result = weighted_average_metrics(single_client)
    assert single_result["accuracy"] == 0.85, f"Single client should return original value, got {single_result}"
    print("✅ Single client test passed!")

if __name__ == "__main__":
    test_weighted_average() 