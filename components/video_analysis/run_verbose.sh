#!/bin/bash

# Verbose run script for Hendrix Video Analysis Pipeline
# This script runs the pipeline with full logging to help monitor progress

echo "=============================================="
echo "Hendrix Video Analysis Pipeline - Verbose Mode"
echo "=============================================="
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Set environment variables for better output
export PYTHONUNBUFFERED=1

# Clear previous output
echo "Clearing previous output..."
rm -rf verbose_output/*

# Run the pipeline with debug logging
echo "Starting pipeline with verbose logging..."
echo "Output will be saved to: verbose_output/"
echo "Log will be saved to: pipeline_verbose_log.txt"
echo ""
echo "Processing will show detailed information for each shot..."
echo "=============================================="
echo ""

# Get video file from command line or use default
VIDEO_FILE=${1:-"tests/sample_video.mp4"}

# Run with tee to both display and save output
python src/main.py "$VIDEO_FILE" \
    --output-dir verbose_output \
    --debug \
    2>&1 | tee pipeline_verbose_log.txt

echo ""
echo "=============================================="
echo "Pipeline completed!"
echo "Check verbose_output/ for results"
echo "Check pipeline_verbose_log.txt for full log"
echo "=============================================="