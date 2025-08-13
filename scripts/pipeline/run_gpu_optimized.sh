#!/bin/bash

# GPU-Optimized Hendrix Pipeline Runner
# Ensures all models use GPU where beneficial

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
BASE_DIR="/dev-work/hendrix_12aug"
PIPELINE_START=$(date +%s)

# Check if video file is provided
if [ $# -eq 0 ]; then
    echo -e "${RED}Usage: $0 <video_file>${NC}"
    exit 1
fi

VIDEO_FILE="$1"
if [[ ! "$VIDEO_FILE" = /* ]]; then
    VIDEO_FILE="$BASE_DIR/$VIDEO_FILE"
fi

if [ ! -f "$VIDEO_FILE" ]; then
    echo -e "${RED}Error: Video file not found: $VIDEO_FILE${NC}"
    exit 1
fi

VIDEO_NAME=$(basename "$VIDEO_FILE" | sed 's/\.[^.]*$//')
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="$BASE_DIR/hendrix_output/${VIDEO_NAME}_GPU_${TIMESTAMP}"

echo -e "${GREEN}===== GPU-Optimized Hendrix Pipeline =====${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📹 Video: $(basename $VIDEO_FILE)"
echo "📁 Output: $OUTPUT_DIR"
echo "🕐 Started: $(date)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Get video info
VIDEO_INFO=$(ffprobe -v quiet -print_format json -show_format -show_streams "$VIDEO_FILE" 2>/dev/null)
if [ ! -z "$VIDEO_INFO" ]; then
    DURATION=$(echo "$VIDEO_INFO" | jq -r '.format.duration // "unknown"' | awk '{printf "%.1f", $1}')
    SIZE=$(echo "$VIDEO_INFO" | jq -r '.format.size // "0"' | awk '{printf "%.1f", $1/1048576}')
    WIDTH=$(echo "$VIDEO_INFO" | jq -r '.streams[] | select(.codec_type=="video") | .width // "unknown"')
    HEIGHT=$(echo "$VIDEO_INFO" | jq -r '.streams[] | select(.codec_type=="video") | .height // "unknown"')
    FPS=$(echo "$VIDEO_INFO" | jq -r '.streams[] | select(.codec_type=="video") | .r_frame_rate // "unknown"' | head -1)
    
    echo "Video Information:"
    echo "  - Duration: ${DURATION}s ($(awk "BEGIN {printf \"%.1f\", $DURATION/60}") minutes)"
    echo "  - Size: ${SIZE} MB"
    echo "  - Resolution: ${WIDTH}x${HEIGHT}"
    echo "  - Frame rate: $FPS"
    echo ""
fi

# Check GPU availability
echo -e "${BLUE}System Configuration:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🖥️  GPUs detected:"
nvidia-smi --query-gpu=index,name,memory.total,memory.free,driver_version --format=csv,noheader | while IFS=',' read idx name total free driver; do
    echo "  GPU $idx: $name (Memory: $free MB free / $total MB total)"
done
echo "  Driver: $(nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -1)"
echo "  CUDA: $(nvcc --version 2>/dev/null | grep "release" | awk '{print $6}' || echo "Not found")"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Create output structure
mkdir -p "$OUTPUT_DIR"/{video_analysis,character_dialogue,comprehensive_captions,logs}

# Activate environment
source "$BASE_DIR/hendrix_venv/bin/activate"

# Set GPU-optimized environment variables
export HF_TOKEN=${HF_TOKEN:-""}
export TF_USE_LEGACY_KERAS=1

# Use both GPUs if available
export CUDA_VISIBLE_DEVICES=0,1

# Force GPU for PyTorch
export TORCH_CUDA_ARCH_LIST="8.9"  # Ada architecture
export PYTORCH_CUDA_ALLOC_CONF="max_split_size_mb:512"

# Set Python path
export PYTHONPATH="$BASE_DIR/Hendrix_Comprehensive_Captioning:$PYTHONPATH"

# ===== STAGE 1: Video Analysis (TransNetV2 - GPU) =====
echo -e "${BLUE}[1/3] Running Video Analysis (GPU)...${NC}"
cd "$BASE_DIR/Hendrix_Video"

echo "Starting Video Analysis with TransNetV2..."
echo "Input video: $VIDEO_FILE"
echo "Output directory: $OUTPUT_DIR/video_analysis"

START_TIME=$(date +%s)
if python src/main.py "$VIDEO_FILE" --output "$OUTPUT_DIR/video_analysis" > "$OUTPUT_DIR/logs/video_analysis.log" 2>&1; then
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    echo -e "${GREEN}✓ Video analysis complete in ${DURATION}s${NC}"
    
    if [ -f "$OUTPUT_DIR/video_analysis/scenes.json" ]; then
        SCENES=$(jq '.total_scenes' "$OUTPUT_DIR/video_analysis/scenes.json" 2>/dev/null || echo "0")
        SHOTS=$(jq '.shots | length' "$OUTPUT_DIR/video_analysis/shots.json" 2>/dev/null || echo "0")
        echo "  - Scenes detected: $SCENES"
        echo "  - Shots detected: $SHOTS"
    else
        echo -e "${YELLOW}⚠ No scenes.json found${NC}"
    fi
else
    echo -e "${RED}✗ Video analysis failed${NC}"
    echo "Error details:"
    tail -10 "$OUTPUT_DIR/logs/video_analysis.log"
    exit 1
fi

# ===== STAGE 2: Character-Dialogue Analysis (GPU-optimized) =====
echo ""
echo -e "${BLUE}[2/3] Running Character-Dialogue Analysis (GPU)...${NC}"
cd "$BASE_DIR/Hendrix_Character_Dialogue_Analysis/visual_processing_branch"

# Show current GPU usage before starting
echo "GPU status before Character-Dialogue Analysis:"
nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total --format=csv,noheader

echo ""
echo "Starting Character-Dialogue Analysis..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Configuration:"
echo "  - Whisper model: small (244MB, GPU-optimized)"
echo "  - Expected GPU memory: ~1-2GB for Whisper"
echo "  - Processing includes:"
echo "    • Audio extraction and transcription (Whisper)"
echo "    • Speaker diarization (Pyannote)"
echo "    • Face detection & recognition (InsightFace)"
echo "    • Character-dialogue matching (Fusion)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Start character-dialogue analysis with real-time progress monitoring
START_TIME=$(date +%s)
echo ""
echo "Progress:"

# Run in background and monitor log
python scripts/run_optimized_robust_pipeline.py "$VIDEO_FILE" \
    --output "$OUTPUT_DIR/character_dialogue" \
    --whisper-model small > "$OUTPUT_DIR/logs/character_dialogue.log" 2>&1 &
CDA_PID=$!

# Monitor progress
LAST_LINE=""
SPINNER=('⠋' '⠙' '⠹' '⠸' '⠼' '⠴' '⠦' '⠧' '⠇' '⠏')
SPIN_IDX=0

while kill -0 $CDA_PID 2>/dev/null; do
    # Get last meaningful line from log
    if [ -f "$OUTPUT_DIR/logs/character_dialogue.log" ]; then
        CURRENT_LINE=$(grep -E "Processing|Extracting|Detecting|Matching|complete|Stage|STAGE" "$OUTPUT_DIR/logs/character_dialogue.log" | tail -1)
        if [ "$CURRENT_LINE" != "$LAST_LINE" ] && [ ! -z "$CURRENT_LINE" ]; then
            printf "\r\033[K  ${SPINNER[$SPIN_IDX]} $CURRENT_LINE"
            LAST_LINE="$CURRENT_LINE"
        else
            printf "\r  ${SPINNER[$SPIN_IDX]} Processing..."
        fi
    fi
    SPIN_IDX=$(( (SPIN_IDX + 1) % 10 ))
    sleep 0.5
done

# Wait for process to complete
wait $CDA_PID
CDA_EXIT_CODE=$?

printf "\r\033[K"  # Clear spinner line

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

if [ $CDA_EXIT_CODE -eq 0 ]; then
    
    echo -e "${GREEN}✓ Character-dialogue analysis complete in ${DURATION}s${NC}"
    echo ""
    
    # Find output session
    CDA_SESSION=$(find "$OUTPUT_DIR/character_dialogue" -name "session_*" -type d | head -1)
    
    if [ ! -z "$CDA_SESSION" ]; then
        echo "Results Summary:"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        
        # Get detailed stats
        CHARS=$(jq '.characters | length' "$CDA_SESSION/visual_output/character_data_schemaC.json" 2>/dev/null || echo "0")
        DIALOGUES=$(jq '.[] | length' "$CDA_SESSION/fusion_output/schema_d_matches.json" 2>/dev/null || echo "0")
        TRANSCRIPTS=$(jq '.segments | length' "$CDA_SESSION/audio_output/*/schemas/schema_a_transcription.json" 2>/dev/null || echo "0")
        SPEAKERS=$(jq '.segments | map(.speaker_id) | unique | length' "$CDA_SESSION/audio_output/*/schemas/schema_b_speakers.json" 2>/dev/null || echo "0")
        
        echo "  📝 Transcription: $TRANSCRIPTS segments detected"
        echo "  🎭 Characters: $CHARS unique characters identified"
        echo "  🗣️  Speakers: $SPEAKERS speakers detected"
        echo "  🔗 Matches: $DIALOGUES dialogue-character matches"
        echo "  📁 Output: $(basename $CDA_SESSION)"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        
        # Show GPU usage after this stage
        echo ""
        echo "GPU status after Character-Dialogue Analysis:"
        nvidia-smi --query-gpu=index,utilization.gpu,memory.used --format=csv,noheader
    else
        echo -e "${YELLOW}⚠ No output session found${NC}"
    fi
else
    echo -e "${RED}✗ Character-dialogue analysis failed after ${DURATION}s${NC}"
    echo ""
    echo "Error details (last 20 lines):"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    tail -20 "$OUTPUT_DIR/logs/character_dialogue.log"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Checking for specific errors..."
    grep -i "error\|exception\|failed\|cuda\|gpu" "$OUTPUT_DIR/logs/character_dialogue.log" | tail -10 || echo "No specific errors found"
    
    # Set flag to skip or continue
    CDA_SESSION=""
fi

# ===== STAGE 3: Comprehensive Captioning (LLaVA GPU) =====
echo ""
echo -e "${BLUE}[3/3] Running Comprehensive Captioning (GPU)...${NC}"
cd "$BASE_DIR/Hendrix_Comprehensive_Captioning"

echo ""
echo "Configuration:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  - Model: LLaVA-NeXT 7B (llava-v1.6-vicuna-7b)"
echo "  - Expected GPU memory: ~14GB for model + processing"
echo "  - Processing mode: Scene-by-scene narrative generation"
echo "  - Output formats: JSON, SRT, WebVTT, HTML, TXT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo "GPU status before Captioning:"
nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total --format=csv,noheader

# Create GPU-optimized config
cat > "$OUTPUT_DIR/config_gpu.yaml" << EOF
mllm:
  provider: llava
  model: llava-hf/llava-v1.6-vicuna-7b-hf
  generation:
    temperature: 0.7
    max_tokens: 100
  device_config:
    use_gpu: true
    device: cuda:0  # Use first GPU for LLaVA
    load_in_8bit: false  # Full precision for speed
    torch_dtype: float16

fusion:
  include_emotions: true
  min_dialogue_confidence: 0.3

prompt:
  template: narrative_with_emotions
  use_improved_templates: true

output:
  formats: [json, srt, webvtt, html, txt]
  include_metadata: true

pipeline:
  use_keyframes: true
  update_context: true

advanced:
  clear_cuda_cache: true
EOF

# Find keyframes
KEYFRAMES_ARG=""
if [ -d "$OUTPUT_DIR/video_analysis/keyframes/" ]; then
    KEYFRAMES_ARG="--keyframes $OUTPUT_DIR/video_analysis/keyframes/"
fi

if [ ! -z "$CDA_SESSION" ] && [ -f "$OUTPUT_DIR/video_analysis/scenes.json" ]; then
    echo ""
    echo "Starting caption generation..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📥 Inputs:"
    echo "  - Audio analysis: $(basename $CDA_SESSION)"
    echo "  - Scene analysis: $SCENES scenes to process"
    if [ ! -z "$KEYFRAMES_ARG" ]; then
        echo "  - Keyframes: Available for visual context"
    fi
    echo "  - Config: GPU-optimized (float16, cuda:0)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Progress:"
    
    START_TIME=$(date +%s)
    
    # Run captioning in background and monitor
    python scripts/generate_comprehensive_captions.py \
        --audio-analysis "$CDA_SESSION" \
        --scene-analysis "$OUTPUT_DIR/video_analysis/scenes.json" \
        $KEYFRAMES_ARG \
        --output-dir "$OUTPUT_DIR/comprehensive_captions" \
        --config "$OUTPUT_DIR/config_gpu.yaml" > "$OUTPUT_DIR/logs/captioning.log" 2>&1 &
    CAP_PID=$!
    
    # Monitor progress
    LAST_SCENE=0
    while kill -0 $CAP_PID 2>/dev/null; do
        if [ -f "$OUTPUT_DIR/logs/captioning.log" ]; then
            # Look for scene processing progress
            CURRENT_SCENE=$(grep -oE "Processing scene [0-9]+" "$OUTPUT_DIR/logs/captioning.log" | tail -1 | grep -oE "[0-9]+" || echo "0")
            if [ "$CURRENT_SCENE" -gt "$LAST_SCENE" ]; then
                printf "\r\033[K  ⚡ Processing scene $CURRENT_SCENE/$SCENES ($(( CURRENT_SCENE * 100 / SCENES ))%%)"
                LAST_SCENE=$CURRENT_SCENE
            fi
            
            # Check if loading model
            if grep -q "Loading checkpoint shards" "$OUTPUT_DIR/logs/captioning.log" | tail -1; then
                printf "\r\033[K  ⏳ Loading LLaVA-NeXT model (this may take a minute)..."
            fi
        fi
        sleep 1
    done
    
    wait $CAP_PID
    CAP_EXIT_CODE=$?
    
    printf "\r\033[K"  # Clear progress line
    
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    
    if [ $CAP_EXIT_CODE -eq 0 ]; then
        echo -e "${GREEN}✓ Comprehensive captioning complete in ${DURATION}s${NC}"
        echo ""
        
        if [ -f "$OUTPUT_DIR/comprehensive_captions/comprehensive_captions.json" ]; then
            echo "Results Summary:"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            
            CAPTIONS=$(jq '.captions | length' "$OUTPUT_DIR/comprehensive_captions/comprehensive_captions.json" 2>/dev/null || echo "0")
            AVG_LENGTH=$(jq '.captions | map(.caption | length) | add/length' "$OUTPUT_DIR/comprehensive_captions/comprehensive_captions.json" 2>/dev/null | awk '{printf "%.0f", $1}' || echo "0")
            
            echo "  📝 Captions generated: $CAPTIONS"
            echo "  ⏱️  Average time per caption: $((DURATION / CAPTIONS))s"
            echo "  📏 Average caption length: $AVG_LENGTH characters"
            echo "  📊 Output formats created:"
            
            # Check which files were created
            for fmt in json srt vtt html txt; do
                if [ -f "$OUTPUT_DIR/comprehensive_captions/comprehensive_captions.$fmt" ]; then
                    SIZE=$(ls -lh "$OUTPUT_DIR/comprehensive_captions/comprehensive_captions.$fmt" | awk '{print $5}')
                    echo "     ✓ .$fmt ($SIZE)"
                fi
            done
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        fi
    else
        echo -e "${RED}✗ Captioning failed after ${DURATION}s${NC}"
        echo ""
        echo "Error details (last 20 lines):"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        tail -20 "$OUTPUT_DIR/logs/captioning.log"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    fi
else
    echo -e "${YELLOW}⚠ Skipping captioning due to missing inputs${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    if [ -z "$CDA_SESSION" ]; then
        echo "  ❌ Missing: Character-dialogue analysis output"
    fi
    if [ ! -f "$OUTPUT_DIR/video_analysis/scenes.json" ]; then
        echo "  ❌ Missing: Scene analysis output"
    fi
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
fi

# ===== Final Summary =====
echo ""
echo -e "${GREEN}===== Pipeline Complete =====${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Calculate total time
PIPELINE_END=$(date +%s)
TOTAL_TIME=$((PIPELINE_END - PIPELINE_START))
PIPELINE_START=$(date +%s -d "$(head -1 "$OUTPUT_DIR/logs/video_analysis.log" | cut -d' ' -f1-2)" 2>/dev/null || echo $PIPELINE_END)
TOTAL_TIME=$((PIPELINE_END - PIPELINE_START))

echo "⏱️  Total processing time: ${TOTAL_TIME}s ($(awk "BEGIN {printf \"%.1f\", $TOTAL_TIME/60}") minutes)"
echo ""

# GPU usage summary
echo "🖥️  GPU Usage Summary:"
nvidia-smi --query-gpu=index,utilization.gpu,memory.used,memory.total --format=csv,noheader | while IFS=',' read idx util mem_used mem_total; do
    MEM_PERCENT=$(awk "BEGIN {printf \"%.1f\", $mem_used/$mem_total*100}")
    echo "  GPU $idx: Utilization $util%, Memory $mem_used MB / $mem_total MB ($MEM_PERCENT%)"
done

echo ""
echo "📁 Output saved to: $OUTPUT_DIR"
echo ""
echo "📊 Results Overview:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Summary of all outputs
if [ -f "$OUTPUT_DIR/video_analysis/scenes.json" ]; then
    echo "  ✓ Video Analysis: $SCENES scenes, $SHOTS shots"
else
    echo "  ✗ Video Analysis: Failed"
fi

if [ ! -z "$CDA_SESSION" ] && [ -d "$CDA_SESSION" ]; then
    echo "  ✓ Character-Dialogue: $CHARS characters, $DIALOGUES dialogues"
else
    echo "  ✗ Character-Dialogue: Failed or incomplete"
fi

if [ -f "$OUTPUT_DIR/comprehensive_captions/comprehensive_captions.json" ]; then
    echo "  ✓ Captions: $CAPTIONS narrative captions generated"
else
    echo "  ✗ Captions: Not generated"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🔍 View results:"
echo "  - Interactive HTML: $OUTPUT_DIR/comprehensive_captions/comprehensive_captions.html"
echo "  - Raw captions: $OUTPUT_DIR/comprehensive_captions/comprehensive_captions.json"
echo "  - Subtitles: $OUTPUT_DIR/comprehensive_captions/comprehensive_captions.srt"
echo "  - Logs: $OUTPUT_DIR/logs/"
echo ""
echo "💡 Tip: To serve the HTML viewer, run:"
echo "  cd $OUTPUT_DIR && python -m http.server 8000"
echo ""
echo "🕐 Completed: $(date)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"