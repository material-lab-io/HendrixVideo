#!/bin/bash

# Comprehensive Captioning Pipeline Runner Script with Improvements

# Create output directory
mkdir -p /dev-work/comprehensive_captioning/output/production_improved

# Activate virtual environment
source venv/bin/activate

# Run the comprehensive captioning pipeline with improvements
python scripts/generate_comprehensive_captions.py \
    --audio-analysis /dev-work/audio_analysis/visual_processing_branch/output/optimized_robust/session_20250808_164327 \
    --scene-analysis /dev-work/Hendrix_Video_Analysis/output/scenes.json \
    --keyframes /dev-work/Hendrix_Video_Analysis/keyframes/ \
    --output-dir /dev-work/comprehensive_captioning/output/production_improved \
    --log-file /dev-work/comprehensive_captioning/output/production_improved/pipeline.log \
    --log-level INFO

echo "Pipeline completed! Check output in: /dev-work/comprehensive_captioning/output/production_improved/"