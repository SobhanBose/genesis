# Federated Learning Configuration Examples

This directory contains example configurations for different federated learning strategies and scenarios. These examples demonstrate best practices and recommended parameter settings.

## Available Examples

### Strategy-Specific Examples

1. **`fedavg_example.yaml`** - FedAvg (Federated Averaging)
   - Standard federated learning baseline
   - Best for homogeneous (IID) data
   - Minimal configuration required

2. **`fedprox_example.yaml`** - FedProx (Federated Proximal)
   - Handles heterogeneous (non-IID) data
   - Includes proximal regularization
   - Recommended for most real-world scenarios

3. **`fedadam_example.yaml`** - FedAdam (Federated Adam)
   - Server-side adaptive optimization
   - Fastest convergence
   - Best for complex optimization landscapes

## How to Use These Examples

### Quick Start

1. **Copy an example configuration**:
   ```bash
   cp configs/examples/fedprox_example.yaml configs/my_config.yaml
   ```

2. **Modify parameters as needed**:
   ```yaml
   # Edit configs/my_config.yaml
   federated:
     strategy: "FedProx"
     strategies:
       fedprox:
         proximal_mu: 0.1  # Adjust based on your data
   ```

3. **Run federated training**:
   ```bash
   python scripts/run_federated_experiment.py --config configs/my_config.yaml
   ```

### Choosing the Right Strategy

#### Use FedAvg when:
- You have homogeneous (IID) data across clients
- You want a simple baseline for comparison
- You need minimal computational overhead
- You're doing proof-of-concept work

#### Use FedProx when:
- You have heterogeneous (non-IID) data across clients
- You need robustness to client dropout
- You want to control client drift
- You're deploying in production (recommended default)

#### Use FedAdam when:
- You need fast convergence
- You have complex optimization landscapes
- You can afford higher memory usage
- You want adaptive learning rates

## Configuration Structure

All examples follow this structure:

```yaml
federated:
  # Strategy selection (required)
  strategy: "FedProx"
  
  # Strategy-specific parameters
  strategies:
    fedprox:
      proximal_mu: 0.075
    
    fedadam:
      beta1: 0.9
      beta2: 0.999
      server_lr: 0.001
      epsilon: 1e-7
    
    fedavg: {}
  
  # Server configuration
  server:
    rounds: 50
    min_fit_clients: 3
    min_available_clients: 3
    fraction_fit: 1.0
    fraction_evaluate: 1.0
  
  # Client configuration
  client:
    local_epochs: 5
  
  # Evaluation configuration
  evaluation:
    centralized_evaluation: true
```

## Parameter Tuning Guidelines

### Start with Defaults
Each example provides sensible defaults. Start with these and adjust based on your specific needs:

- **FedAvg**: No strategy-specific parameters to tune
- **FedProx**: Start with `proximal_mu: 0.075`
- **FedAdam**: Start with `beta1: 0.9, beta2: 0.999, server_lr: 0.001`

### Common Adjustments

#### For Faster Convergence
```yaml
# FedAdam with aggressive settings
strategies:
  fedadam:
    beta1: 0.8          # More responsive
    server_lr: 0.01     # Higher learning rate

client:
  local_epochs: 3       # More frequent communication
```

#### For More Stability
```yaml
# FedProx with conservative settings
strategies:
  fedprox:
    proximal_mu: 0.05   # Less regularization

server:
  fraction_fit: 0.8     # Use subset of clients
```

#### For Heterogeneous Data
```yaml
# FedProx with strong regularization
strategies:
  fedprox:
    proximal_mu: 0.15   # Higher regularization

client:
  local_epochs: 3       # Limit client drift
```

## Scenario-Based Examples

### Research Experiment
```yaml
federated:
  strategy: "FedAdam"
  strategies:
    fedadam:
      beta1: 0.9
      beta2: 0.999
      server_lr: 0.001
      epsilon: 1e-8       # Higher precision
  
  server:
    rounds: 100          # More rounds for analysis
    fraction_fit: 1.0    # Use all clients
```

### Production Deployment
```yaml
federated:
  strategy: "FedProx"
  strategies:
    fedprox:
      proximal_mu: 0.075
  
  server:
    rounds: 50
    min_fit_clients: 5   # Require more clients
    fraction_fit: 0.8    # Robust to client dropout
  
  client:
    local_epochs: 5
```

### Resource-Constrained Environment
```yaml
federated:
  strategy: "FedAvg"     # Minimal overhead
  strategies:
    fedavg: {}
  
  server:
    rounds: 100          # More rounds, less computation per round
    fraction_fit: 0.5    # Use fewer clients
  
  client:
    local_epochs: 3      # Reduce local computation
```

## Validation and Testing

### Test Your Configuration
Before running full experiments, validate your configuration:

```bash
# Test configuration loading
python -c "
import yaml
with open('configs/my_config.yaml', 'r') as f:
    config = yaml.safe_load(f)
print('Configuration loaded successfully')
print(f'Strategy: {config[\"federated\"][\"strategy\"]}')
"

# Test strategy creation
python -c "
from src.federated.strategy_factory import StrategyFactory
# ... test strategy creation
"
```

### Compare Strategies
Run the same experiment with different strategies to compare:

```bash
# Test all three strategies
python scripts/run_federated_experiment.py --config configs/examples/fedavg_example.yaml
python scripts/run_federated_experiment.py --config configs/examples/fedprox_example.yaml
python scripts/run_federated_experiment.py --config configs/examples/fedadam_example.yaml
```

## Troubleshooting

### Common Issues

1. **"Unknown strategy" error**: Check strategy name spelling and case
2. **Parameter validation errors**: Verify parameter ranges (see parameter reference)
3. **Slow convergence**: Try FedAdam or adjust learning rates
4. **Poor accuracy**: Try FedProx with higher proximal_mu
5. **Training instability**: Reduce learning rates or increase regularization

### Getting Help

- **Parameter Reference**: See `docs/federated_strategy_parameters.md`
- **Troubleshooting Guide**: See `docs/federated_strategy_troubleshooting.md`
- **Migration Guide**: See `docs/federated_strategy_migration_guide.md`
- **Configuration Guide**: See `docs/federated_strategy_configuration_guide.md`

## Best Practices

1. **Start Simple**: Begin with FedProx defaults, then optimize
2. **One Change at a Time**: Modify one parameter at a time for systematic tuning
3. **Monitor Training**: Watch for convergence, stability, and accuracy
4. **Document Changes**: Keep track of what works for your specific use case
5. **Test Thoroughly**: Validate configurations before production deployment

## Contributing

When adding new examples:

1. Follow the existing naming convention: `[strategy]_[scenario]_example.yaml`
2. Include comprehensive comments explaining parameter choices
3. Provide use case description and tuning guidelines
4. Test the configuration thoroughly
5. Update this README with the new example

For questions or suggestions, refer to the main documentation or create an issue.