#!/bin/bash

# Hendrix Pipeline - Large Video Test Script
# This script runs the pipeline on test_video_2.mp4 and analyzes the results

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}HENDRIX PIPELINE - LARGE VIDEO TEST${NC}"
echo -e "${BLUE}============================================${NC}"

# Change to project directory
cd /dev-work/hendrix_12aug

# Check if virtual environment exists
if [ ! -d "hendrix_venv" ]; then
    echo -e "${RED}Error: Virtual environment not found!${NC}"
    echo "Please run: python3 -m venv hendrix_venv && source hendrix_venv/bin/activate && pip install -r requirements/all.txt"
    exit 1
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source hendrix_venv/bin/activate

# Check video file
VIDEO_FILE="test_video_2.mp4"
if [ ! -f "$VIDEO_FILE" ]; then
    echo -e "${RED}Error: $VIDEO_FILE not found!${NC}"
    exit 1
fi

# Get video info
echo -e "${BLUE}Video Information:${NC}"
VIDEO_DURATION=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$VIDEO_FILE" 2>/dev/null)
VIDEO_SIZE=$(du -h "$VIDEO_FILE" | cut -f1)
echo "  File: $VIDEO_FILE"
echo "  Size: $VIDEO_SIZE"
echo "  Duration: ${VIDEO_DURATION%.*} seconds"
echo ""

# Run the pipeline with balanced profile (better quality than fast)
echo -e "${YELLOW}Starting pipeline analysis...${NC}"
echo -e "${YELLOW}This may take several minutes for a large video.${NC}"
echo ""

START_TIME=$(date +%s)

# Run with balanced profile and verbose output
python -m hendrix_pipeline \
    --video "$VIDEO_FILE" \
    --profile balanced \
    --verbose

PIPELINE_EXIT_CODE=$?
END_TIME=$(date +%s)
ELAPSED_TIME=$((END_TIME - START_TIME))

if [ $PIPELINE_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ Pipeline completed successfully!${NC}"
    echo -e "${GREEN}Processing time: $((ELAPSED_TIME / 60)) minutes $((ELAPSED_TIME % 60)) seconds${NC}"
    
    # Find the latest output directory
    LATEST_OUTPUT=$(ls -td outputs/test_video_2_* 2>/dev/null | head -1)
    
    if [ -n "$LATEST_OUTPUT" ]; then
        echo ""
        echo -e "${BLUE}Output Analysis:${NC}"
        echo "Results saved to: $LATEST_OUTPUT"
        echo ""
        
        # List all output files
        echo -e "${BLUE}Generated files:${NC}"
        find "$LATEST_OUTPUT" -type f -name "*.json" -o -name "*.txt" -o -name "*.srt" -o -name "*.html" | sort
        
        echo ""
        echo -e "${BLUE}Quick Statistics:${NC}"
        
        # Check video analysis results
        if [ -f "$LATEST_OUTPUT/video_analysis/scenes.json" ]; then
            SCENES=$(python3 -c "import json; data=json.load(open('$LATEST_OUTPUT/video_analysis/scenes.json')); print(f\"Scenes: {data.get('total_scenes', 'N/A')}\")" 2>/dev/null || echo "Scenes: Unable to parse")
            echo "  $SCENES"
        fi
        
        # Check character dialogue results
        if [ -f "$LATEST_OUTPUT/character_dialogue/character_data.json" ]; then
            CHARS=$(python3 -c "import json; data=json.load(open('$LATEST_OUTPUT/character_dialogue/character_data.json')); print(f\"Characters: {len(data.get('characters', {}))}\")" 2>/dev/null || echo "Characters: Unable to parse")
            echo "  $CHARS"
        fi
        
        # Check caption results
        if [ -f "$LATEST_OUTPUT/comprehensive_captions/captions.json" ]; then
            CAPTIONS=$(python3 -c "import json; data=json.load(open('$LATEST_OUTPUT/comprehensive_captions/captions.json')); print(f\"Captions: {len(data.get('captions', []))}\")" 2>/dev/null || echo "Captions: Unable to parse")
            echo "  $CAPTIONS"
        fi
        
        echo ""
        echo -e "${BLUE}To view detailed results:${NC}"
        echo ""
        echo "# View pipeline summary:"
        echo "cat $LATEST_OUTPUT/pipeline_results.json | python3 -m json.tool"
        echo ""
        echo "# View scene analysis:"
        echo "cat $LATEST_OUTPUT/video_analysis/scenes.json | python3 -m json.tool | head -50"
        echo ""
        echo "# View character data:"
        echo "cat $LATEST_OUTPUT/character_dialogue/character_data.json | python3 -m json.tool | head -50"
        echo ""
        echo "# View captions (if generated):"
        echo "cat $LATEST_OUTPUT/comprehensive_captions/captions.srt 2>/dev/null | head -20"
        echo ""
        echo "# Open HTML timeline (if generated):"
        echo "open $LATEST_OUTPUT/comprehensive_captions/timeline.html 2>/dev/null"
        
        # Show first few results as preview
        echo ""
        echo -e "${BLUE}Preview of pipeline results:${NC}"
        cat "$LATEST_OUTPUT/pipeline_results.json" | python3 -m json.tool | head -30
        
    else
        echo -e "${YELLOW}Warning: Could not find output directory${NC}"
    fi
else
    echo -e "${RED}✗ Pipeline failed with exit code: $PIPELINE_EXIT_CODE${NC}"
    echo "Check the error messages above for details."
fi

echo ""
echo -e "${GREEN}Test complete!${NC}"