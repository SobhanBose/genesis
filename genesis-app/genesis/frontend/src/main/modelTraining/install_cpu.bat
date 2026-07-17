@echo off
REM Installation script for CPU-only systems (no NVIDIA GPU) - Windows

echo ==========================================
echo Federated Learning ClinVar - CPU Setup
echo ==========================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://python.org
    pause
    exit /b 1
)

echo ✅ Python is available

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install PyTorch CPU version first
echo Installing PyTorch CPU version...
pip install torch==2.8.0+cpu torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

REM Install other dependencies
echo Installing other dependencies...
pip install -r requirements_cpu.txt

REM Verify installation
echo Verifying installation...
python -c "import torch; print(f'PyTorch version: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}')"

echo.
echo ✅ Installation completed successfully!
echo.
echo Next steps:
echo 1. Activate virtual environment: venv\Scripts\activate.bat
echo 2. Run installation test: python test_installation.py
echo 3. Prepare data: python src\data\create_federated_dataset.py
echo 4. Start federated learning: python scripts\run_federated_experiment.py 2

pause