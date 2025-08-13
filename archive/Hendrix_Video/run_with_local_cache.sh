#!/bin/bash
# Run the Hendrix pipeline with local cache directory

# Set environment variables for local model storage
export HF_HOME="/dev-work/Hendrix_Video_Analysis/cache/huggingface"
export TRANSFORMERS_CACHE="/dev-work/Hendrix_Video_Analysis/cache/transformers"
export HUGGINGFACE_HUB_CACHE="/dev-work/Hendrix_Video_Analysis/cache/huggingface/hub"
export TORCH_HOME="/dev-work/Hendrix_Video_Analysis/cache/torch"
export HF_DATASETS_CACHE="/dev-work/Hendrix_Video_Analysis/cache/datasets"

# Show where models will be downloaded
echo "Models will be downloaded to:"
echo "  HF_HOME: $HF_HOME"
echo "  Cache dir has $(df -h /dev-work/Hendrix_Video_Analysis | tail -1 | awk '{print $4}') free space"
echo ""

# Activate virtual environment
source venv/bin/activate

# Run the pipeline
echo "Starting Hendrix Video Analysis Pipeline..."
echo "This will download the LLaVA model (~13GB) on first run"
echo "Video: $1"
echo ""

python src/main.py "$@"