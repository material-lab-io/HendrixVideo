# Installation Guide

Comprehensive installation instructions for the Hendrix Video Analysis Pipeline.

## System Requirements

### Operating System
- **Linux**: Ubuntu 20.04+ (recommended), CentOS 8+, Debian 10+
- **macOS**: 10.15+ (Catalina or later)
- **Windows**: 10/11 with WSL2 (limited support)

### Hardware Requirements

#### Minimum
- CPU: 8-core x86_64 processor
- RAM: 16GB
- Storage: 50GB free space
- GPU: Optional (CPU mode available)

#### Recommended
- CPU: 16+ core processor
- RAM: 32GB
- Storage: 100GB+ SSD
- GPU: NVIDIA GPU with 16GB+ VRAM

## Prerequisites

### 1. Python Installation

Ensure Python 3.8+ is installed:

```bash
python3 --version
# Should output: Python 3.8.x or higher
```

If not installed:
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.8 python3.8-venv python3.8-dev

# macOS (using Homebrew)
brew install python@3.8

# CentOS/RHEL
sudo yum install python38 python38-devel
```

### 2. FFmpeg Installation

FFmpeg is required for video processing:

```bash
# Check if installed
ffmpeg -version

# Ubuntu/Debian
sudo apt update
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# CentOS/RHEL
sudo yum install epel-release
sudo yum install ffmpeg ffmpeg-devel
```

### 3. CUDA Installation (Optional, for GPU)

For NVIDIA GPU support:

```bash
# Check CUDA version
nvidia-smi

# Install CUDA 11.8+ (Ubuntu example)
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-keyring_1.0-1_all.deb
sudo dpkg -i cuda-keyring_1.0-1_all.deb
sudo apt-get update
sudo apt-get -y install cuda
```

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/Hendrix_Video_Analysis.git
cd Hendrix_Video_Analysis
```

### 2. Create Virtual Environment

```bash
# Using the provided script
chmod +x setup_env.sh
./setup_env.sh

# Or manually
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# For GPU support
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 4. Download Models

Models are downloaded automatically on first use, or manually:

```bash
python init_project.py
```

This downloads:
- TransNetV2 weights (~100MB)
- LLaVA-1.5-7B model (~13GB)

### 5. Verify Installation

```bash
python src/utils/verify_installation.py
```

Expected output:
```
✓ Python version: 3.8.10
✓ FFmpeg installed: 4.4.2
✓ PyTorch installed: 2.0.1
✓ CUDA available: Yes (or No)
✓ Transformers installed: 4.36.0
✓ All dependencies satisfied!
```

## Platform-Specific Instructions

### Ubuntu/Debian

```bash
# Install system dependencies
sudo apt update
sudo apt install -y python3-pip python3-venv python3-dev \
    ffmpeg libsm6 libxext6 libxrender-dev libgomp1 \
    libglib2.0-0 libsm6 libxrender1 libxext6 libgl1

# Clone and setup
git clone https://github.com/yourusername/Hendrix_Video_Analysis.git
cd Hendrix_Video_Analysis
./setup_env.sh
```

### macOS

```bash
# Install Homebrew if not installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python@3.8 ffmpeg

# Clone and setup
git clone https://github.com/yourusername/Hendrix_Video_Analysis.git
cd Hendrix_Video_Analysis
./setup_env.sh
```

### Windows (WSL2)

```bash
# In WSL2 terminal
sudo apt update
sudo apt install python3.8 python3.8-venv python3-pip ffmpeg

# Clone and setup
git clone https://github.com/yourusername/Hendrix_Video_Analysis.git
cd Hendrix_Video_Analysis
./setup_env.sh
```

## Docker Installation (Alternative)

```bash
# Build Docker image
docker build -t hendrix-video-analysis .

# Run container
docker run --gpus all -v $(pwd)/videos:/app/videos \
    -v $(pwd)/output:/app/output \
    hendrix-video-analysis video.mp4
```

## Troubleshooting Installation

### Common Issues

#### 1. CUDA/GPU Not Detected
```bash
# Check PyTorch CUDA
python -c "import torch; print(torch.cuda.is_available())"

# If False, reinstall PyTorch with CUDA
pip uninstall torch torchvision torchaudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

#### 2. FFmpeg Not Found
```bash
# Add FFmpeg to PATH
export PATH=$PATH:/usr/local/bin/ffmpeg

# Or specify in config.yaml
video_processing:
  ffmpeg_path: "/usr/local/bin/ffmpeg"
```

#### 3. Memory Errors
```bash
# Reduce batch size in config.yaml
scene_construction:
  batch_size: 4  # Reduce from 10
  max_frames_per_batch: 5  # Reduce from 10
```

#### 4. Model Download Fails
```bash
# Manual download with resume
export HF_HUB_ENABLE_HF_TRANSFER=1
python -c "from transformers import AutoModel; AutoModel.from_pretrained('llava-hf/llava-1.5-7b-hf')"
```

## Environment Variables

Optional environment variables:

```bash
# Model cache directory
export HF_HOME=/path/to/model/cache

# CUDA settings
export CUDA_VISIBLE_DEVICES=0  # Use specific GPU

# Logging
export HENDRIX_LOG_LEVEL=DEBUG

# FFmpeg path
export FFMPEG_PATH=/usr/local/bin/ffmpeg
```

## Post-Installation

### 1. Run Test Suite
```bash
pytest tests/
```

### 2. Process Test Video
```bash
python tests/create_test_video.py
python src/main.py tests/sample_video.mp4
```

### 3. Configure Settings
```bash
cp config.yaml config.local.yaml
# Edit config.local.yaml with your preferences
```

## Updating

To update the pipeline:

```bash
git pull origin main
pip install -r requirements.txt --upgrade
```

## Uninstallation

```bash
# Remove virtual environment
rm -rf venv/

# Remove cached models (optional)
rm -rf cache/ ~/.cache/huggingface/

# Remove the directory
cd ..
rm -rf Hendrix_Video_Analysis/
```

## Next Steps

- Follow the [Quick Start Guide](quickstart.md)
- Configure settings in [Configuration Guide](configuration.md)
- Check [Hardware Requirements](hardware-requirements.md) for optimization