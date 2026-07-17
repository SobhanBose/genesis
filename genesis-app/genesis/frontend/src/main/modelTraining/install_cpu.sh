#!/bin/bash
# Installation script for CPU-only systems (no NVIDIA GPU)

set -e  # Exit on any error

echo "=========================================="
echo "Federated Learning ClinVar - CPU Setup"
echo "=========================================="

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "Python version: $python_version"

if [[ $(echo "$python_version < 3.8" | bc -l) -eq 1 ]]; then
    echo "❌ Python 3.8 or higher is required"
    exit 1
fi

echo "✅ Python version is compatible"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install PyTorch CPU version first
echo "Installing PyTorch CPU version..."
pip install torch==2.8.0+cpu torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install other dependencies
echo "Installing other dependencies..."
pip install -r requirements_cpu.txt

# Verify installation
echo "Verifying installation..."
python -c "import torch; print(f'PyTorch version: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}')"

echo ""
echo "✅ Installation completed successfully!"
echo ""
echo "Next steps:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Run installation test: python test_installation.py"
echo "3. Prepare data: python src/data/create_federated_dataset.py"
echo "4. Start federated learning: python scripts/run_federated_experiment.py 2"