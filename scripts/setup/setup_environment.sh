#!/bin/bash

# Hendrix Environment Setup Script
# Sets up all necessary environment variables for the Hendrix pipeline

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}===== Hendrix Environment Setup =====${NC}"

# Base directory
export HENDRIX_BASE="/dev-work/hendrix_12aug"

# Python environment
export HENDRIX_VENV="$HENDRIX_BASE/hendrix_venv"

# HuggingFace token (required for speaker diarization)
if [ -z "$HF_TOKEN" ]; then
    echo -e "${YELLOW}Warning: HF_TOKEN not set${NC}"
    echo "To enable speaker diarization, set your HuggingFace token:"
    echo "  export HF_TOKEN='your_token_here'"
    echo ""
    echo "Get a token from: https://huggingface.co/settings/tokens"
    echo "Accept terms at: https://huggingface.co/pyannote/speaker-diarization-3.1"
fi

# TensorFlow/Keras compatibility
export TF_USE_LEGACY_KERAS=1

# Model cache directories for Hendrix_Video
export HF_HOME="$HENDRIX_BASE/Hendrix_Video/cache/huggingface"
export TRANSFORMERS_CACHE="$HENDRIX_BASE/Hendrix_Video/cache/transformers"
export TORCH_HOME="$HENDRIX_BASE/Hendrix_Video/cache/torch"

# CUDA settings (optional)
if command -v nvidia-smi &> /dev/null; then
    export CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-0}
    echo "GPU detected. Using CUDA device: $CUDA_VISIBLE_DEVICES"
else
    echo "No GPU detected. Will use CPU (slower processing)"
fi

# Performance settings
export OMP_NUM_THREADS=${OMP_NUM_THREADS:-8}
export TOKENIZERS_PARALLELISM=false  # Avoid warning messages

# Path additions
export PATH="$HENDRIX_VENV/bin:$PATH"

# Create necessary directories
mkdir -p "$HF_HOME" "$TRANSFORMERS_CACHE" "$TORCH_HOME"

# Function to activate Hendrix environment
hendrix_activate() {
    if [ -f "$HENDRIX_VENV/bin/activate" ]; then
        source "$HENDRIX_VENV/bin/activate"
        echo -e "${GREEN}Hendrix environment activated${NC}"
        
        # Show current settings
        echo ""
        echo "Environment Variables:"
        echo "  HENDRIX_BASE: $HENDRIX_BASE"
        echo "  HF_TOKEN: $([ -z "$HF_TOKEN" ] && echo "Not set ⚠️" || echo "Set ✓")"
        echo "  CUDA_VISIBLE_DEVICES: $CUDA_VISIBLE_DEVICES"
        echo "  Python: $(which python)"
        echo ""
    else
        echo -e "${YELLOW}Virtual environment not found. Run setup_hendrix_models.sh first${NC}"
        return 1
    fi
}

# Export the function
export -f hendrix_activate

echo ""
echo "Environment variables set. To activate the Hendrix environment:"
echo "  source $0"
echo "  hendrix_activate"
echo ""
echo "Or simply run:"
echo "  source $HENDRIX_VENV/bin/activate"

# Auto-activate if sourced
if [ "${BASH_SOURCE[0]}" != "${0}" ]; then
    hendrix_activate
fi