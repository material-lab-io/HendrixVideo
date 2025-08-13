#!/bin/bash

# Comprehensive Captioning Pipeline Runner Script

# Activate virtual environment
source venv/bin/activate

# Run the comprehensive captioning pipeline
python scripts/generate_comprehensive_captions.py \
    --audio-analysis /dev-work/audio_analysis/visual_processing_branch/output/optimized_robust/session_20250808_164327 \
    --scene-analysis /dev-work/Hendrix_Video_Analysis/output/scenes.json \
    --keyframes /dev-work/Hendrix_Video_Analysis/keyframes/ \
    --output-dir /dev-work/comprehensive_captioning/output/production \
    --log-file /dev-work/comprehensive_captioning/output/production/pipeline.log \
    --log-level INFO

echo "Pipeline completed! Check output in: /dev-work/comprehensive_captioning/output/production/"