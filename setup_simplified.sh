#!/bin/bash

# Hendrix Video Analysis Pipeline - Simplified Setup
# One-click installer for the unified Hendrix pipeline

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}===== Hendrix Video Pipeline Setup =====${NC}"
echo "One-click installer for video analysis pipeline"
echo ""

# Auto-detect base directory
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Installing in: $BASE_DIR"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Python
if ! command_exists python3; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Python version: $PYTHON_VERSION"

# Check FFmpeg
if ! command_exists ffmpeg; then
    echo -e "${YELLOW}Warning: FFmpeg not found. Installing...${NC}"
    if command_exists apt-get; then
        sudo apt-get update && sudo apt-get install -y ffmpeg
    elif command_exists brew; then
        brew install ffmpeg
    else
        echo -e "${RED}Please install FFmpeg manually${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}Step 1: Creating virtual environment${NC}"
if [ ! -d "hendrix_venv" ]; then
    python3 -m venv hendrix_venv
    echo "Virtual environment created"
else
    echo "Virtual environment already exists"
fi

# Activate virtual environment
source hendrix_venv/bin/activate
pip install --upgrade pip

echo -e "${GREEN}Step 2: Installing core dependencies${NC}"
pip install -r requirements/minimal.txt
pip install torchvision pandas moviepy scikit-learn

echo -e "${GREEN}Step 3: Installing component dependencies (essential only)${NC}"
# Install video processing essentials
if [ -f "requirements/video.txt" ]; then
    echo "Installing video processing dependencies..."
    # Skip audio libraries that need system dependencies
    pip install -r requirements/video.txt || echo -e "${YELLOW}Some video dependencies failed (continuing)${NC}"
fi

# Install core captioning dependencies only
echo "Installing essential transformers and ML libraries..."
pip install accelerate sentence-transformers || echo -e "${YELLOW}Some ML dependencies failed (continuing)${NC}"

echo -e "${GREEN}Step 4: Verifying installation${NC}"
python -m hendrix_pipeline --verify

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Installation successful!${NC}"
    echo ""
    echo "🎬 Testing with sample video (if available)..."
    if [ -f "test_video.mp4" ]; then
        echo "Running quick test with test_video.mp4..."
        python -m hendrix_pipeline --video test_video.mp4 --profile test --dry-run
        echo ""
        echo "To run actual processing:"
        echo "  python -m hendrix_pipeline --video test_video.mp4 --profile test"
    else
        echo "No test video found. Place a video file and run:"
        echo "  python -m hendrix_pipeline --video YOUR_VIDEO.mp4 --profile test"
    fi
    echo ""
    echo "Available commands:"
    echo "  python -m hendrix_pipeline --help          # Show all options"
    echo "  python -m hendrix_pipeline --list-models   # Show available models" 
    echo "  python -m hendrix_pipeline --verify        # Verify installation"
    echo ""
    echo "For development:"
    echo "  source hendrix_venv/bin/activate           # Activate environment"
else
    echo -e "${RED}❌ Installation verification failed${NC}"
    echo "Please check the error messages above and install missing dependencies"
    exit 1
fi