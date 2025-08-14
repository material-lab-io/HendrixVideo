#!/bin/bash
# Hendrix Unified Installation Script
# Installs all dependencies with GPU optimization

set -e  # Exit on error

echo "========================================="
echo "Hendrix Pipeline Unified Installation"
echo "========================================="

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "Python version: $PYTHON_VERSION"

# Check CUDA availability
if command -v nvidia-smi &> /dev/null; then
    echo "NVIDIA GPU detected:"
    nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
    CUDA_AVAILABLE=true
else
    echo "No NVIDIA GPU detected. Installing CPU-only versions."
    CUDA_AVAILABLE=false
fi

# Create virtual environment if not exists
if [ ! -d "hendrix_venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv hendrix_venv
fi

# Activate virtual environment
source hendrix_venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip wheel setuptools

# Install NumPy first (critical for compatibility)
echo "Installing NumPy..."
pip install numpy==1.26.4

# Install PyTorch with CUDA support
if [ "$CUDA_AVAILABLE" = true ]; then
    echo "Installing PyTorch with CUDA 11.8 support..."
    pip install torch==2.2.2+cu118 torchvision==0.17.2+cu118 torchaudio==2.2.2+cu118 --index-url https://download.pytorch.org/whl/cu118
else
    echo "Installing PyTorch CPU-only..."
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
fi

# Install core requirements
echo "Installing unified requirements..."
pip install -r requirements-unified.txt

# Verify GPU installation
echo "Verifying installation..."
python3 -c "
import torch
print(f'PyTorch version: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'CUDA version: {torch.version.cuda}')
    print(f'GPU: {torch.cuda.get_device_name(0)}')
"

# Download models
echo "Would you like to download models now? (y/n)"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    python scripts/setup/download_models.sh
fi

echo "========================================="
echo "Installation complete!"
echo "Activate environment with: source hendrix_venv/bin/activate"
echo "========================================="