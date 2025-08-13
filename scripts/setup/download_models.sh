#!/bin/bash

# Hendrix Pipeline Model Download Script
# Downloads all required models for the three Hendrix repositories
# Total download size: ~20GB

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}===== Hendrix Pipeline Model Setup =====${NC}"
echo "This script will download all required models (~20GB total)"
echo "Make sure you have a stable internet connection"
echo ""

# Check if HF_TOKEN is set
if [ -z "$HF_TOKEN" ]; then
    echo -e "${YELLOW}Warning: HF_TOKEN not set. Required for speaker diarization.${NC}"
    echo "Please set your HuggingFace token:"
    read -p "Enter your HuggingFace token (or press Enter to skip): " hf_token
    if [ ! -z "$hf_token" ]; then
        export HF_TOKEN=$hf_token
    fi
fi

# Base directory
BASE_DIR="/dev-work/hendrix_12aug"
cd $BASE_DIR

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Python
if ! command_exists python3; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}Step 1: Setting up virtual environments${NC}"

# Create a shared virtual environment
if [ ! -d "hendrix_venv" ]; then
    echo "Creating shared virtual environment..."
    python3 -m venv hendrix_venv
fi

# Activate virtual environment
source hendrix_venv/bin/activate

# Upgrade pip
pip install --upgrade pip

echo -e "${GREEN}Step 2: Installing base dependencies${NC}"

# Install common dependencies
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install transformers accelerate datasets
pip install huggingface_hub

# Install faiss-cpu instead of faiss-gpu (works with Python 3.12)
echo -e "${YELLOW}Installing faiss-cpu instead of faiss-gpu for Python 3.12 compatibility${NC}"
pip install faiss-cpu

echo -e "${GREEN}Step 3: Setting up Hendrix_Video models${NC}"
cd $BASE_DIR/Hendrix_Video

# Install Hendrix_Video dependencies with fixes
if [ -f "requirements.txt" ]; then
    # Install requirements one by one to handle failures
    echo "Installing Hendrix_Video dependencies..."
    
    # Core dependencies
    pip install moviepy opencv-python-headless pillow
    pip install pyyaml tqdm numpy scipy
    
    # Install TransNetV2 if available
    pip install transnetv2-pytorch || echo -e "${YELLOW}TransNetV2 installation failed, will use fallback${NC}"
fi

# Set up cache directories
export HF_HOME=$BASE_DIR/Hendrix_Video/cache/huggingface
export TRANSFORMERS_CACHE=$BASE_DIR/Hendrix_Video/cache/transformers
export TORCH_HOME=$BASE_DIR/Hendrix_Video/cache/torch
mkdir -p $HF_HOME $TRANSFORMERS_CACHE $TORCH_HOME

# Download LLaVA model
echo "Downloading LLaVA-1.5-7B model..."
python3 << EOF
from transformers import AutoProcessor, LlavaForConditionalGeneration
import torch

print("Downloading LLaVA model (this may take 10-15 minutes)...")
try:
    processor = AutoProcessor.from_pretrained("llava-hf/llava-1.5-7b-hf")
    model = LlavaForConditionalGeneration.from_pretrained(
        "llava-hf/llava-1.5-7b-hf",
        torch_dtype=torch.float16,
        low_cpu_mem_usage=True
    )
    print("LLaVA model downloaded successfully!")
except Exception as e:
    print(f"Warning: Could not download LLaVA model: {e}")
    print("Model will be downloaded on first use")
EOF

echo -e "${GREEN}Step 4: Setting up Hendrix_Character_Dialogue_Analysis models${NC}"
cd $BASE_DIR/Hendrix_Character_Dialogue_Analysis/visual_processing_branch

# Install dependencies with compatibility fixes
echo "Installing Character-Dialogue Analysis dependencies..."

# Core packages
pip install opencv-python-headless numpy scikit-learn matplotlib seaborn
pip install whisper openai-whisper

# Audio processing packages
pip install librosa soundfile pydub
pip install pyannote.audio speechbrain

# Visual processing packages - with fixes
pip install deepface
pip install ultralytics  # For YOLO

# Install insightface without faiss-gpu dependency
echo -e "${YELLOW}Installing InsightFace with CPU-only support${NC}"
pip install onnxruntime  # CPU version
pip install insightface --no-deps
pip install onnx opencv-python-headless pillow numpy tqdm scikit-image

# Create .env file if it doesn't exist
if [ ! -f "$BASE_DIR/Hendrix_Character_Dialogue_Analysis/.env" ]; then
    echo "Creating .env file..."
    cat > $BASE_DIR/Hendrix_Character_Dialogue_Analysis/.env << EOF
HF_TOKEN=$HF_TOKEN
TF_USE_LEGACY_KERAS=1
EOF
fi

# Download audio models
echo "Downloading audio processing models..."
python3 << EOF
import os
os.environ['TF_USE_LEGACY_KERAS'] = '1'

# Download Whisper model
print("Downloading Whisper base model...")
try:
    import whisper
    model = whisper.load_model("base")
    print("Whisper model downloaded successfully!")
except Exception as e:
    print(f"Warning: Could not download Whisper model: {e}")

# Download emotion recognition model
print("Downloading emotion recognition model...")
try:
    from transformers import pipeline
    # Use a different emotion model that's compatible
    classifier = pipeline("audio-classification", model="superb/hubert-base-superb-er")
    print("Emotion model downloaded successfully!")
except Exception as e:
    print(f"Warning: Could not download emotion model: {e}")

# Download speaker diarization
if os.environ.get('HF_TOKEN'):
    print("Downloading speaker diarization model...")
    try:
        from pyannote.audio import Pipeline
        pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", use_auth_token=os.environ['HF_TOKEN'])
        print("Speaker diarization model downloaded successfully!")
    except Exception as e:
        print(f"Warning: Could not download speaker diarization: {e}")
        print("Make sure you have accepted the model terms at: https://huggingface.co/pyannote/speaker-diarization-3.1")
else:
    print("Skipping speaker diarization (no HF_TOKEN)")
EOF

# Download visual models with CPU support
echo "Downloading visual processing models (CPU mode)..."
python3 << EOF
import os
os.environ['TF_USE_LEGACY_KERAS'] = '1'

# Download InsightFace models with CPU support
print("Downloading InsightFace models...")
try:
    from insightface.app import FaceAnalysis
    # Use CPU provider explicitly
    app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
    app.prepare(ctx_id=-1, det_size=(640, 640))
    print("InsightFace models downloaded successfully!")
except Exception as e:
    print(f"Warning: Could not download InsightFace models: {e}")
    print("Models will be downloaded on first use")
EOF

echo -e "${GREEN}Step 5: Setting up Hendrix_Comprehensive_Captioning models${NC}"
cd $BASE_DIR/Hendrix_Comprehensive_Captioning

# Install dependencies
if [ -f "requirements.txt" ]; then
    # Install core requirements
    pip install pyyaml tqdm pillow
    pip install jsonschema pydantic
fi

# Download LLaVA-NeXT model
echo "Downloading LLaVA-NeXT (LLaVA 1.6) model..."
python3 << EOF
from transformers import LlavaNextProcessor, LlavaNextForConditionalGeneration
import torch

print("Downloading LLaVA-NeXT model (this may take 10-15 minutes)...")
try:
    processor = LlavaNextProcessor.from_pretrained("llava-hf/llava-v1.6-vicuna-7b-hf")
    model = LlavaNextForConditionalGeneration.from_pretrained(
        "llava-hf/llava-v1.6-vicuna-7b-hf", 
        torch_dtype=torch.float16,
        low_cpu_mem_usage=True
    )
    print("LLaVA-NeXT model downloaded successfully!")
except Exception as e:
    print(f"Warning: Could not download LLaVA-NeXT model: {e}")
    print("Model will be downloaded on first use")
EOF

echo -e "${GREEN}Step 6: Installing additional compatibility packages${NC}"

# Install additional packages that might be needed
pip install sortedcontainers filterpy lap
pip install scenedetect[opencv] --no-deps
pip install av

echo -e "${GREEN}Step 7: Verifying installations${NC}"

# Quick verification
python3 << EOF
import sys
print("\nVerifying key packages:")
packages = [
    ("torch", "PyTorch"),
    ("transformers", "Transformers"),
    ("whisper", "Whisper"),
    ("cv2", "OpenCV"),
    ("moviepy", "MoviePy"),
    ("faiss", "FAISS (CPU)"),
    ("insightface", "InsightFace"),
]

for pkg, name in packages:
    try:
        if pkg == "cv2":
            import cv2
        elif pkg == "faiss":
            import faiss
        else:
            __import__(pkg)
        print(f"✓ {name}")
    except ImportError:
        print(f"✗ {name} (will be installed on first use)")

# Check CUDA availability
try:
    import torch
    if torch.cuda.is_available():
        print(f"\n✓ CUDA available: {torch.cuda.get_device_name(0)}")
    else:
        print("\n⚠ CUDA not available - will use CPU (slower)")
except:
    pass
EOF

echo ""
echo -e "${GREEN}===== Model Setup Complete =====${NC}"
echo ""
echo "Summary:"
echo "- Virtual environment created at: $BASE_DIR/hendrix_venv"
echo "- Using faiss-cpu for Python 3.12 compatibility"
echo "- Models downloaded to respective cache directories"
echo "- Dependencies installed for all three repositories"
echo ""
echo "Important notes:"
echo "1. Using CPU version of FAISS due to Python 3.12"
echo "2. If you didn't provide HF_TOKEN, speaker diarization won't work"
echo "3. Some models may download on first use if the download failed"
echo "4. Total disk usage: ~20GB for all models"
echo ""
echo "To activate the environment for future use:"
echo "  source $BASE_DIR/hendrix_venv/bin/activate"
echo ""
echo "Next step: Run test_hendrix_pipeline.sh to test the pipeline"