#!/bin/bash

# Hendrix Pipeline Test Script
# This script runs a quick test of the Hendrix video analysis pipeline

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}HENDRIX PIPELINE TEST${NC}"
echo -e "${BLUE}========================================${NC}"

# Change to project directory
cd /dev-work/hendrix_12aug

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source hendrix_venv/bin/activate

# Run the pipeline with fast profile
echo -e "${YELLOW}Running pipeline with fast profile...${NC}"
python -m hendrix_pipeline --video test_video.mp4 --profile fast

# Check if successful
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Pipeline completed successfully!${NC}"
    
    # Find the latest output directory
    LATEST_OUTPUT=$(ls -td outputs/test_video_* 2>/dev/null | head -1)
    
    if [ -n "$LATEST_OUTPUT" ]; then
        echo -e "${GREEN}Results saved to: $LATEST_OUTPUT${NC}"
        echo ""
        echo -e "${BLUE}Output files:${NC}"
        ls -la "$LATEST_OUTPUT/"
        
        echo ""
        echo -e "${BLUE}To view the results:${NC}"
        echo "  - JSON data: cat $LATEST_OUTPUT/*.json"
        echo "  - If HTML timeline exists: open $LATEST_OUTPUT/timeline.html"
    fi
else
    echo -e "${RED}✗ Pipeline failed. Check the error messages above.${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}Test complete!${NC}"