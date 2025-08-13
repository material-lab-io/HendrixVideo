#!/bin/bash
# Setup script for Hendrix Video Analysis Pipeline

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Export environment variables for model storage (relative to project root)
export HF_HOME="$SCRIPT_DIR/cache/huggingface"
export TRANSFORMERS_CACHE="$SCRIPT_DIR/cache/transformers"
export TORCH_HOME="$SCRIPT_DIR/cache/torch"
export HF_DATASETS_CACHE="$SCRIPT_DIR/cache/datasets"

# Create cache directories if they don't exist
mkdir -p "$HF_HOME"
mkdir -p "$TRANSFORMERS_CACHE"
mkdir -p "$TORCH_HOME"
mkdir -p "$HF_DATASETS_CACHE"

# Create output directories
mkdir -p "$SCRIPT_DIR/output"
mkdir -p "$SCRIPT_DIR/temp"
mkdir -p "$SCRIPT_DIR/keyframes"

# Activate virtual environment
if [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
    source "$SCRIPT_DIR/venv/bin/activate"
else
    echo "Virtual environment not found. Creating one..."
    python3 -m venv "$SCRIPT_DIR/venv"
    source "$SCRIPT_DIR/venv/bin/activate"
    echo "Installing requirements..."
    pip install -r "$SCRIPT_DIR/requirements.txt"
fi

# Load environment variables from .env file
if [ -f "$SCRIPT_DIR/.env" ]; then
    export $(cat "$SCRIPT_DIR/.env" | grep -v '^#' | xargs)
fi

echo "Environment setup complete!"
echo "Virtual environment: $SCRIPT_DIR/venv"
echo "Model cache: $SCRIPT_DIR/cache"
echo ""
echo "To run the pipeline:"
echo "  python src/main.py <video_file>"
echo ""
echo "To run tests:"
echo "  pytest tests/"