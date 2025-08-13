#!/bin/bash

# Hendrix Pipeline - Complete Pipeline Runner
# Runs all components of the Hendrix video analysis pipeline with the new structure

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Set script directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

# Parse arguments
if [ $# -eq 0 ]; then
    echo "Usage: $0 <video_path> [options]"
    echo ""
    echo "Options:"
    echo "  --profile PROFILE    Use configuration profile (fast, balanced, quality, test)"
    echo "  --output-dir DIR     Custom output directory"
    echo "  --config FILE        Custom configuration file"
    echo "  --gpu-device DEVICE  GPU device (cuda:0, cuda:1, cpu, auto)"
    echo "  --skip-component     Skip a component (video, audio, caption)"
    echo "  --verbose           Enable verbose logging"
    echo ""
    echo "Examples:"
    echo "  $0 video.mp4"
    echo "  $0 video.mp4 --profile fast"
    echo "  $0 video.mp4 --output-dir /custom/path --gpu-device cuda:1"
    exit 1
fi

# Default values
VIDEO_PATH="$1"
shift
PROFILE="balanced"
CUSTOM_OUTPUT=""
CUSTOM_CONFIG=""
GPU_DEVICE="auto"
SKIP_COMPONENTS=""
VERBOSE=false

# Parse optional arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --profile)
            PROFILE="$2"
            shift 2
            ;;
        --output-dir)
            CUSTOM_OUTPUT="$2"
            shift 2
            ;;
        --config)
            CUSTOM_CONFIG="$2"
            shift 2
            ;;
        --gpu-device)
            GPU_DEVICE="$2"
            shift 2
            ;;
        --skip-component)
            SKIP_COMPONENTS="$SKIP_COMPONENTS $2"
            shift 2
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Convert to absolute path if relative
if [[ ! "$VIDEO_PATH" = /* ]]; then
    VIDEO_PATH="$(pwd)/$VIDEO_PATH"
fi

# Check if video exists
if [ ! -f "$VIDEO_PATH" ]; then
    echo -e "${RED}Error: Video file not found: $VIDEO_PATH${NC}"
    exit 1
fi

# Setup paths
VIDEO_NAME=$(basename "$VIDEO_PATH" | sed 's/\.[^.]*$//')
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

if [ -z "$CUSTOM_OUTPUT" ]; then
    OUTPUT_DIR="$PROJECT_ROOT/outputs/${VIDEO_NAME}_${TIMESTAMP}"
else
    OUTPUT_DIR="$CUSTOM_OUTPUT"
fi

# Configuration file
if [ -z "$CUSTOM_CONFIG" ]; then
    CONFIG_FILE="$PROJECT_ROOT/configs/base_config.yaml"
else
    CONFIG_FILE="$CUSTOM_CONFIG"
fi

echo -e "${GREEN}========================================"
echo "HENDRIX VIDEO ANALYSIS PIPELINE v2.0"
echo "========================================${NC}"
echo "Video: $(basename $VIDEO_PATH)"
echo "Profile: $PROFILE"
echo "Output: $OUTPUT_DIR"
echo "Config: $CONFIG_FILE"
echo "GPU Device: $GPU_DEVICE"
echo "Started: $(date)"
echo ""

# Create output structure
mkdir -p "$OUTPUT_DIR"/{video_analysis,character_dialogue,comprehensive_captions,logs}

# Activate virtual environment if it exists
if [ -d "$PROJECT_ROOT/hendrix_venv" ]; then
    source "$PROJECT_ROOT/hendrix_venv/bin/activate"
fi

# Set environment variables
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
export HF_TOKEN=${HF_TOKEN:-""}
export TF_USE_LEGACY_KERAS=1

# Set GPU device if specified
if [ "$GPU_DEVICE" != "auto" ]; then
    if [ "$GPU_DEVICE" == "cpu" ]; then
        export CUDA_VISIBLE_DEVICES=""
    else
        export CUDA_VISIBLE_DEVICES="${GPU_DEVICE#cuda:}"
    fi
fi

# Logging setup
if [ "$VERBOSE" = true ]; then
    LOG_LEVEL="DEBUG"
    REDIRECT=""
else
    LOG_LEVEL="INFO"
    REDIRECT="2>&1"
fi

# ===== STAGE 1: Video Analysis =====
if [[ ! " $SKIP_COMPONENTS " =~ " video " ]]; then
    echo -e "${BLUE}[1/3] Running Video Analysis...${NC}"
    
    if [ "$VERBOSE" = true ]; then
        python -m components.video_analysis.main \
            "$VIDEO_PATH" \
            --output "$OUTPUT_DIR/video_analysis" \
            --config "$CONFIG_FILE" \
            --profile "$PROFILE" \
            --log-level "$LOG_LEVEL" \
            | tee "$OUTPUT_DIR/logs/video_analysis.log"
    else
        python -m components.video_analysis.main \
            "$VIDEO_PATH" \
            --output "$OUTPUT_DIR/video_analysis" \
            --config "$CONFIG_FILE" \
            --profile "$PROFILE" \
            --log-level "$LOG_LEVEL" \
            > "$OUTPUT_DIR/logs/video_analysis.log" 2>&1
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Video analysis complete${NC}"
        
        # Check outputs
        if [ -f "$OUTPUT_DIR/video_analysis/scenes.json" ]; then
            SCENES=$(python -c "import json; print(json.load(open('$OUTPUT_DIR/video_analysis/scenes.json'))['total_scenes'])" 2>/dev/null || echo "0")
            echo "  - Scenes detected: $SCENES"
        fi
    else
        echo -e "${RED}✗ Video analysis failed${NC}"
        tail -20 "$OUTPUT_DIR/logs/video_analysis.log"
        exit 1
    fi
else
    echo -e "${YELLOW}[1/3] Skipping Video Analysis${NC}"
fi

# ===== STAGE 2: Character-Dialogue Analysis =====
if [[ ! " $SKIP_COMPONENTS " =~ " audio " ]]; then
    echo ""
    echo -e "${BLUE}[2/3] Running Character-Dialogue Analysis...${NC}"
    
    if [ "$VERBOSE" = true ]; then
        python -m components.character_dialogue.main \
            "$VIDEO_PATH" \
            --output "$OUTPUT_DIR/character_dialogue" \
            --config "$CONFIG_FILE" \
            --profile "$PROFILE" \
            --log-level "$LOG_LEVEL" \
            | tee "$OUTPUT_DIR/logs/character_dialogue.log"
    else
        python -m components.character_dialogue.main \
            "$VIDEO_PATH" \
            --output "$OUTPUT_DIR/character_dialogue" \
            --config "$CONFIG_FILE" \
            --profile "$PROFILE" \
            --log-level "$LOG_LEVEL" \
            > "$OUTPUT_DIR/logs/character_dialogue.log" 2>&1
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Character-dialogue analysis complete${NC}"
        
        # Check outputs
        if [ -f "$OUTPUT_DIR/character_dialogue/character_data.json" ]; then
            CHARS=$(python -c "import json; print(len(json.load(open('$OUTPUT_DIR/character_dialogue/character_data.json'))['characters']))" 2>/dev/null || echo "0")
            echo "  - Characters detected: $CHARS"
        fi
    else
        echo -e "${YELLOW}⚠ Character-dialogue analysis had issues${NC}"
        # Create minimal output for caption generation to continue
        mkdir -p "$OUTPUT_DIR/character_dialogue"
        echo '{"characters": {}, "transcripts": []}' > "$OUTPUT_DIR/character_dialogue/character_data.json"
    fi
else
    echo -e "${YELLOW}[2/3] Skipping Character-Dialogue Analysis${NC}"
fi

# ===== STAGE 3: Comprehensive Captioning =====
if [[ ! " $SKIP_COMPONENTS " =~ " caption " ]]; then
    echo ""
    echo -e "${BLUE}[3/3] Running Comprehensive Captioning...${NC}"
    
    # Check if we have required inputs
    if [ -f "$OUTPUT_DIR/video_analysis/scenes.json" ]; then
        
        if [ "$VERBOSE" = true ]; then
            python -m components.captioning.main \
                --scene-analysis "$OUTPUT_DIR/video_analysis/scenes.json" \
                --character-analysis "$OUTPUT_DIR/character_dialogue/character_data.json" \
                --output-dir "$OUTPUT_DIR/comprehensive_captions" \
                --config "$CONFIG_FILE" \
                --profile "$PROFILE" \
                --log-level "$LOG_LEVEL" \
                | tee "$OUTPUT_DIR/logs/captioning.log"
        else
            python -m components.captioning.main \
                --scene-analysis "$OUTPUT_DIR/video_analysis/scenes.json" \
                --character-analysis "$OUTPUT_DIR/character_dialogue/character_data.json" \
                --output-dir "$OUTPUT_DIR/comprehensive_captions" \
                --config "$CONFIG_FILE" \
                --profile "$PROFILE" \
                --log-level "$LOG_LEVEL" \
                > "$OUTPUT_DIR/logs/captioning.log" 2>&1
        fi
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Comprehensive captioning complete${NC}"
            
            # Check outputs
            if [ -f "$OUTPUT_DIR/comprehensive_captions/captions.json" ]; then
                CAPTIONS=$(python -c "import json; print(len(json.load(open('$OUTPUT_DIR/comprehensive_captions/captions.json'))['captions']))" 2>/dev/null || echo "0")
                echo "  - Captions generated: $CAPTIONS"
            fi
        else
            echo -e "${RED}✗ Captioning failed${NC}"
            tail -20 "$OUTPUT_DIR/logs/captioning.log"
        fi
    else
        echo -e "${YELLOW}⚠ Skipping captioning due to missing scene analysis${NC}"
    fi
else
    echo -e "${YELLOW}[3/3] Skipping Comprehensive Captioning${NC}"
fi

# ===== SUMMARY =====
echo ""
echo -e "${GREEN}========================================"
echo "PIPELINE SUMMARY"
echo "========================================${NC}"
echo "Output directory: $OUTPUT_DIR"
echo ""

# Check what was generated
echo "Generated files:"
if [ -f "$OUTPUT_DIR/video_analysis/scenes.json" ]; then
    echo "  ✓ Scene analysis: $OUTPUT_DIR/video_analysis/scenes.json"
fi
if [ -f "$OUTPUT_DIR/character_dialogue/character_data.json" ]; then
    echo "  ✓ Character data: $OUTPUT_DIR/character_dialogue/character_data.json"
fi
if [ -f "$OUTPUT_DIR/comprehensive_captions/captions.srt" ]; then
    echo "  ✓ SRT captions: $OUTPUT_DIR/comprehensive_captions/captions.srt"
fi
if [ -f "$OUTPUT_DIR/comprehensive_captions/captions.vtt" ]; then
    echo "  ✓ WebVTT captions: $OUTPUT_DIR/comprehensive_captions/captions.vtt"
fi
if [ -f "$OUTPUT_DIR/comprehensive_captions/timeline.html" ]; then
    echo "  ✓ Timeline viewer: $OUTPUT_DIR/comprehensive_captions/timeline.html"
fi

echo ""
echo "To view results:"
echo "  - Timeline: open $OUTPUT_DIR/comprehensive_captions/timeline.html"
echo "  - Captions: $OUTPUT_DIR/comprehensive_captions/captions.srt"
echo "  - Full data: $OUTPUT_DIR/comprehensive_captions/captions.json"
echo ""
echo "Finished: $(date)"