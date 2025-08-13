#!/bin/bash

# Quick script to run test mode 3 directly

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
echo "Running Test Mode 3 - Quality Test"
echo "========================================${NC}"

# Activate virtual environment
source hendrix_venv/bin/activate

# Download test video if needed
if [ ! -f "test_video.mp4" ]; then
    echo "Downloading test video..."
    curl -L -o test_video.mp4 "https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/720/Big_Buck_Bunny_720_10s_1MB.mp4"
fi

# Set Python path
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"

# Create output directory
OUTPUT_DIR="outputs/test_quality_$(date +%Y%m%d_%H%M%S)"

echo -e "\n${YELLOW}Running quality test...${NC}"
echo "Note: Using 'test' profile for Python 3.12 compatibility"
echo "Output will be saved to: $OUTPUT_DIR"
echo ""

# Run the pipeline with test profile (works with mock implementation)
python hendrix_pipeline.py \
    --video test_video.mp4 \
    --profile test \
    --output-dir "$OUTPUT_DIR" \
    --verbose

echo -e "\n${GREEN}✓ Test completed!${NC}"
echo "Results saved to: $OUTPUT_DIR"
echo ""
echo "Check the output files:"
ls -la "$OUTPUT_DIR"/*/*.*