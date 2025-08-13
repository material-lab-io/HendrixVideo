#!/bin/bash

# Set up environment variables for model caching in dev-work directory
export HF_HOME="/dev-work/Hendrix_Video_Analysis/cache/huggingface"
export TRANSFORMERS_CACHE="/dev-work/Hendrix_Video_Analysis/cache/transformers"
export TORCH_HOME="/dev-work/Hendrix_Video_Analysis/cache/torch"
export HF_DATASETS_CACHE="/dev-work/Hendrix_Video_Analysis/cache/huggingface/datasets"

# Create directories if they don't exist
mkdir -p "$HF_HOME"
mkdir -p "$TRANSFORMERS_CACHE"
mkdir -p "$TORCH_HOME"
mkdir -p "$HF_DATASETS_CACHE"

echo "Model cache directories configured:"
echo "HF_HOME: $HF_HOME"
echo "TRANSFORMERS_CACHE: $TRANSFORMERS_CACHE"
echo "TORCH_HOME: $TORCH_HOME"
echo "HF_DATASETS_CACHE: $HF_DATASETS_CACHE"