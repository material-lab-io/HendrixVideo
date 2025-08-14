#!/bin/bash
# Full Pipeline with Character-Dialogue Matching and Comprehensive Captioning
# This runs all components needed for caption generation

echo "========================================="
echo "FULL HENDRIX PIPELINE WITH CAPTIONING"
echo "========================================="
echo "This will run:"
echo "1. Video Analysis (shot/scene detection)"
echo "2. Character-Dialogue Analysis (audio + visual + fusion)"
echo "3. Comprehensive Caption Generation"
echo "========================================="
echo "Time: $(date)"
echo ""

# Activate virtual environment
source hendrix_venv/bin/activate

# Set video file
VIDEO_FILE="${1:-test_video_2.mp4}"

# Check if video exists
if [ ! -f "$VIDEO_FILE" ]; then
    echo "Error: Video file not found: $VIDEO_FILE"
    echo "Usage: $0 [video_file]"
    exit 1
fi

# Get video info
VIDEO_NAME=$(basename "$VIDEO_FILE" .mp4)
VIDEO_SIZE=$(ls -lh "$VIDEO_FILE" | awk '{print $5}')
VIDEO_DURATION=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$VIDEO_FILE" 2>/dev/null || echo "unknown")

echo "Video: $VIDEO_FILE"
echo "Size: $VIDEO_SIZE"
echo "Duration: ${VIDEO_DURATION}s (~$(echo "scale=1; $VIDEO_DURATION/60" | bc) minutes)"
echo ""

# Check GPU
echo "GPU Status:"
python -c "import torch; print(f'  CUDA Available: {torch.cuda.is_available()}'); print(f'  Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"CPU\"}')" 2>/dev/null
nvidia-smi --query-gpu=name,memory.free --format=csv,noheader 2>/dev/null | head -2
echo "========================================="

# Create output directory
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="outputs/full_pipeline_${TIMESTAMP}"
mkdir -p "$OUTPUT_DIR"

echo "Output directory: $OUTPUT_DIR"
echo ""

# Monitor GPU usage in background
(while true; do 
    nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader,nounits >> "$OUTPUT_DIR/gpu_usage.log" 2>/dev/null
    sleep 5
done) &
GPU_MONITOR_PID=$!

# Cleanup function
cleanup() {
    echo "Cleaning up..."
    kill $GPU_MONITOR_PID 2>/dev/null
}
trap cleanup EXIT

# Start pipeline
PIPELINE_START=$(date +%s)

# =============================================================================
# STAGE 1: VIDEO ANALYSIS
# =============================================================================
echo "📹 STAGE 1: VIDEO ANALYSIS"
echo "----------------------------------------"
VIDEO_START=$(date +%s)

VIDEO_OUTPUT="$OUTPUT_DIR/video_analysis"
mkdir -p "$VIDEO_OUTPUT"

echo "Running shot detection and scene analysis..."
python components/video_analysis/src/main.py "$VIDEO_FILE" \
    --output-dir "$VIDEO_OUTPUT" \
    --config configs/optimized_pipeline.yaml 2>&1 | tee "$OUTPUT_DIR/video_analysis.log" | \
    grep -E "(Processing|Detected|Complete|Saved|Error)" || true

VIDEO_END=$(date +%s)
VIDEO_DURATION=$((VIDEO_END - VIDEO_START))

# Check video results
if [ -f "$VIDEO_OUTPUT/scenes.json" ]; then
    SCENES_COUNT=$(python -c "import json; print(len(json.load(open('$VIDEO_OUTPUT/scenes.json'))['scenes']))" 2>/dev/null || echo "0")
    echo "✓ Video analysis complete: $SCENES_COUNT scenes in ${VIDEO_DURATION}s"
else
    echo "✗ Video analysis failed!"
    exit 1
fi

# =============================================================================
# STAGE 2: CHARACTER-DIALOGUE ANALYSIS (Full Pipeline)
# =============================================================================
echo ""
echo "🎭 STAGE 2: CHARACTER-DIALOGUE ANALYSIS"
echo "----------------------------------------"
echo "This includes:"
echo "  - Audio transcription with emotions"
echo "  - Speaker diarization"
echo "  - Face detection and tracking"
echo "  - Character-dialogue matching"
echo ""

CHAR_START=$(date +%s)

# Run the optimized robust pipeline for character-dialogue matching
CHAR_OUTPUT="$OUTPUT_DIR/character_dialogue"
mkdir -p "$CHAR_OUTPUT"

echo "Running full character-dialogue pipeline..."
cd components/character_dialogue/visual_processing_branch

# Run with optimized settings for better performance
python scripts/run_optimized_robust_pipeline.py "$VIDEO_FILE" \
    --output "$CHAR_OUTPUT" \
    --whisper-model base \
    --target-frames 600 2>&1 | tee "$OUTPUT_DIR/character_dialogue.log" | \
    grep -E "(STAGE|Processing|complete|Success|Error|GPU)" || true

cd - > /dev/null

CHAR_END=$(date +%s)
CHAR_DURATION=$((CHAR_END - CHAR_START))

# Find the session directory that was created
SESSION_DIR=$(find "$CHAR_OUTPUT" -name "session_*" -type d | head -1)

if [ -z "$SESSION_DIR" ]; then
    echo "✗ Character-dialogue analysis failed - no session directory found"
    exit 1
fi

echo "✓ Character-dialogue analysis complete in ${CHAR_DURATION}s"
echo "  Session: $(basename $SESSION_DIR)"

# Check what was generated
echo ""
echo "Checking generated schemas:"
[ -f "$SESSION_DIR/audio_output/"*/schemas/schema_a_transcription.json ] && echo "  ✓ Schema A (transcriptions)"
[ -f "$SESSION_DIR/audio_output/"*/schemas/schema_b_speakers.json ] && echo "  ✓ Schema B (speakers)"
[ -f "$SESSION_DIR/visual_output/character_data_schemaC.json" ] && echo "  ✓ Schema C (characters)"
[ -f "$SESSION_DIR/fusion_output/schema_d_matches.json" ] && echo "  ✓ Schema D (matches)"

# =============================================================================
# STAGE 3: COMPREHENSIVE CAPTION GENERATION
# =============================================================================
echo ""
echo "📝 STAGE 3: COMPREHENSIVE CAPTION GENERATION"
echo "--------------------------------------------"
CAPTION_START=$(date +%s)

CAPTION_OUTPUT="$OUTPUT_DIR/captions"
mkdir -p "$CAPTION_OUTPUT"

# Check if we have keyframes
KEYFRAMES_DIR="$VIDEO_OUTPUT/keyframes"
KEYFRAME_ARG=""
if [ -d "$KEYFRAMES_DIR" ] && [ "$(ls -A $KEYFRAMES_DIR)" ]; then
    KEYFRAME_ARG="--keyframes $KEYFRAMES_DIR"
    echo "Using keyframes for enhanced caption generation"
fi

echo "Generating comprehensive captions..."
python components/captioning/scripts/generate_comprehensive_captions.py \
    --scene-analysis "$VIDEO_OUTPUT/scenes.json" \
    --audio-analysis "$SESSION_DIR" \
    --output-dir "$CAPTION_OUTPUT" \
    $KEYFRAME_ARG \
    --max-scenes 100 2>&1 | tee "$OUTPUT_DIR/caption_generation.log" | \
    grep -E "(Processing|Generated|complete|Error|scenes)" || true

CAPTION_END=$(date +%s)
CAPTION_DURATION=$((CAPTION_END - CAPTION_START))

# Check caption results
if [ -f "$CAPTION_OUTPUT/captions.srt" ]; then
    echo "✓ Caption generation complete in ${CAPTION_DURATION}s"
    echo ""
    echo "Generated caption files:"
    for file in "$CAPTION_OUTPUT"/*; do
        if [ -f "$file" ]; then
            echo "  - $(basename $file) ($(ls -lh $file | awk '{print $5}'))"
        fi
    done
else
    echo "✗ Caption generation failed!"
fi

# =============================================================================
# SUMMARY
# =============================================================================
PIPELINE_END=$(date +%s)
TOTAL_DURATION=$((PIPELINE_END - PIPELINE_START))

echo ""
echo "========================================="
echo "PIPELINE SUMMARY"
echo "========================================="
echo "Total Duration: ${TOTAL_DURATION}s ($(echo "scale=1; $TOTAL_DURATION/60" | bc) minutes)"
echo ""
echo "Stage Timings:"
echo "  1. Video Analysis: ${VIDEO_DURATION}s"
echo "  2. Character-Dialogue: ${CHAR_DURATION}s"
echo "  3. Caption Generation: ${CAPTION_DURATION}s"
echo ""

# GPU usage summary
if [ -f "$OUTPUT_DIR/gpu_usage.log" ] && [ -s "$OUTPUT_DIR/gpu_usage.log" ]; then
    echo "GPU Performance:"
    awk -F, 'NF==2 && $2>100 {
        gpu+=$1; mem+=$2; count++
    } END {
        if(count>0) {
            print "  Average GPU Utilization: " gpu/count "%"
            print "  Average Memory Usage: " mem/count " MB"
        }
    }' "$OUTPUT_DIR/gpu_usage.log"
fi

echo ""
echo "Output Structure:"
echo "$OUTPUT_DIR/"
echo "├── video_analysis/"
echo "│   ├── shots.json"
echo "│   ├── scenes.json"
echo "│   ├── video_analysis_complete.json"
echo "│   └── keyframes/"
echo "├── character_dialogue/"
echo "│   └── $SESSION_DIR/"
echo "│       ├── audio_output/     (transcripts + emotions)"
echo "│       ├── visual_output/    (character detections)"
echo "│       └── fusion_output/    (character-dialogue matches)"
echo "└── captions/"
echo "    ├── captions.srt"
echo "    ├── captions.vtt"
echo "    ├── captions.json"
echo "    └── captions_report.txt"
echo ""
echo "========================================="
echo "✓ Full pipeline complete!"
echo "All outputs saved to: $OUTPUT_DIR"
echo "========================================="

# Optional: Open the caption viewer if generated
if [ -f "$CAPTION_OUTPUT/captions_viewer.html" ]; then
    echo ""
    echo "To view interactive captions:"
    echo "  Open: $CAPTION_OUTPUT/captions_viewer.html"
fi