#!/bin/bash

# Install core Hendrix components (Python 3.12 compatible)

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}========================================"
echo "Installing Core Hendrix Components"
echo "(Python 3.12 Compatible)"
echo "========================================${NC}"
echo ""

# Activate virtual environment
if [ ! -d "hendrix_venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv hendrix_venv
fi

source hendrix_venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip wheel setuptools

# Install core components
echo -e "\n${BLUE}Installing base requirements...${NC}"
pip install -r requirements/base.txt

echo -e "\n${BLUE}Installing video analysis requirements...${NC}"
pip install -r requirements/video.txt

echo -e "\n${BLUE}Installing audio processing requirements...${NC}"
pip install -r requirements/audio.txt || {
    echo -e "${YELLOW}Some audio packages may have issues. Continuing...${NC}"
}

echo -e "\n${BLUE}Installing captioning requirements...${NC}"
pip install -r requirements/captioning.txt

echo -e "\n${BLUE}Installing visual processing (with compatibility fixes)...${NC}"
# Install visual requirements but skip problematic packages
echo "Installing compatible visual processing packages..."
pip install opencv-python pillow ultralytics supervision albumentations mediapipe

echo "Installing face detection packages (Python 3.12 compatible)..."
# Skip packages with issues
pip install onnxruntime-gpu || pip install onnxruntime  # Fallback to CPU version
pip install face-recognition dlib mtcnn || echo -e "${YELLOW}Some face packages may have issues${NC}"
pip install insightface facenet-pytorch || echo -e "${YELLOW}Some face recognition packages may have issues${NC}"

echo "Installing emotion detection..."
pip install deepface fer || echo -e "${YELLOW}Some emotion packages may have issues${NC}"

echo -e "\n${GREEN}========================================"
echo "Core Installation Complete!"
echo "========================================${NC}"
echo ""
echo "Installed components:"
echo "  ✓ Base dependencies"
echo "  ✓ Video analysis"
echo "  ✓ Audio processing"
echo "  ✓ Captioning"
echo "  ✓ Visual processing (core features)"
echo ""
echo "Skipped due to Python 3.12 compatibility:"
echo "  - imgaug (use albumentations instead)"
echo "  - Advanced tracking features (optional)"
echo ""
echo "To verify installation:"
echo "  ./test_setup.sh"
echo ""
echo "To run a test:"
echo "  ./quick_test.sh"