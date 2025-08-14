#!/bin/bash
# Simple Pipeline Runner - Direct Command Line Usage
# Usage: ./run_pipeline_simple.sh [video_file] [mode] [options]

# Default values
VIDEO_FILE="${1:-test_video_2.mp4}"
MODE="${2:-complete}"  # complete, video, audio, fast
WHISPER_MODEL="${3:-base}"

# Activate virtual environment
source hendrix_venv/bin/activate

# Create timestamp for output directory
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Show system info
echo "========================================="
echo "Hendrix Pipeline Runner"
echo "========================================="
echo "Video: $VIDEO_FILE"
echo "Mode: $MODE"
echo "Time: $(date)"
echo ""

# Check if video exists
if [ ! -f "$VIDEO_FILE" ]; then
    echo "Error: Video file not found: $VIDEO_FILE"
    exit 1
fi

# Show GPU status
echo "GPU Status:"
python -c "import torch; print(f'  CUDA: {torch.cuda.is_available()}'); print(f'  Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"CPU\"}')" 2>/dev/null
echo "========================================="
echo ""

case $MODE in
    "complete"|"full")
        echo "Running COMPLETE PIPELINE (Video + Audio + Captions)"
        OUTPUT_DIR="outputs/complete_${TIMESTAMP}"
        
        # Run the fixed pipeline script
        bash run_pipeline_final.sh
        ;;
        
    "video"|"v")
        echo "Running VIDEO ANALYSIS ONLY"
        OUTPUT_DIR="outputs/video_${TIMESTAMP}"
        mkdir -p "$OUTPUT_DIR"
        
        python components/video_analysis/src/main.py "$VIDEO_FILE" \
            --output-dir "$OUTPUT_DIR" \
            --config configs/optimized_pipeline.yaml
        
        echo ""
        echo "Video analysis complete!"
        echo "Results saved to: $OUTPUT_DIR"
        
        # Show summary
        if [ -f "$OUTPUT_DIR/shots.json" ]; then
            python -c "
import json
with open('$OUTPUT_DIR/shots.json') as f:
    data = json.load(f)
    print(f\"  Shots detected: {len(data['shots'])}\")
"
        fi
        
        if [ -f "$OUTPUT_DIR/scenes.json" ]; then
            python -c "
import json
with open('$OUTPUT_DIR/scenes.json') as f:
    data = json.load(f)
    print(f\"  Scenes created: {len(data['scenes'])}\")
"
        fi
        ;;
        
    "audio"|"a")
        echo "Running AUDIO PROCESSING ONLY (GPU Optimized)"
        echo "Whisper Model: $WHISPER_MODEL"
        OUTPUT_DIR="outputs/audio_${TIMESTAMP}"
        mkdir -p "$OUTPUT_DIR"
        
        python components/character_dialogue/audio_processing_branch/scripts/complete_audio_pipeline_gpu.py \
            "$VIDEO_FILE" \
            --whisper-model "$WHISPER_MODEL" \
            --output "$OUTPUT_DIR"
        
        echo ""
        echo "Audio processing complete!"
        echo "Results saved to: $OUTPUT_DIR"
        ;;
        
    "fast"|"quick")
        echo "Running FAST TEST (Reduced Quality)"
        OUTPUT_DIR="outputs/fast_${TIMESTAMP}"
        mkdir -p "$OUTPUT_DIR"
        
        # Create fast config
        cat > "$OUTPUT_DIR/fast_config.yaml" << 'EOF'
shot_detection:
  model_name: "transnetv2"
  min_shot_duration: 5.0
  confidence_threshold: 0.7
  max_shots: 30
  transnetv2:
    batch_size: 256
    threshold: 0.7

scene_construction:
  model: "llava-hf/llava-1.5-7b-hf"
  batch_size: 20
  max_frames_per_batch: 30
  temperature: 0.3
  max_new_tokens: 150
  model_config:
    load_in_8bit: true
    torch_dtype: "float16"

pipeline:
  batch_size: 64
  use_gpu: true
  save_keyframes: true

output:
  shots_file: "./shots.json"
  scenes_file: "./scenes.json"
  combined_output: "./video_analysis_complete.json"
EOF
        
        echo "Using fast configuration (fewer shots, 8-bit model)..."
        
        python components/video_analysis/src/main.py "$VIDEO_FILE" \
            --output-dir "$OUTPUT_DIR" \
            --config "$OUTPUT_DIR/fast_config.yaml"
        
        echo ""
        echo "Fast test complete!"
        echo "Results saved to: $OUTPUT_DIR"
        ;;
        
    "custom")
        echo "Running with CUSTOM CONFIGURATION"
        echo "Place your config.yaml in the current directory"
        
        if [ ! -f "config.yaml" ]; then
            echo "Error: config.yaml not found in current directory"
            exit 1
        fi
        
        OUTPUT_DIR="outputs/custom_${TIMESTAMP}"
        mkdir -p "$OUTPUT_DIR"
        
        python components/video_analysis/src/main.py "$VIDEO_FILE" \
            --output-dir "$OUTPUT_DIR" \
            --config config.yaml
        ;;
        
    *)
        echo "Usage: $0 [video_file] [mode] [whisper_model]"
        echo ""
        echo "Modes:"
        echo "  complete - Run full pipeline (default)"
        echo "  video    - Run video analysis only"
        echo "  audio    - Run audio processing only"
        echo "  fast     - Quick test with reduced quality"
        echo "  custom   - Use custom config.yaml"
        echo ""
        echo "Whisper Models (for audio mode):"
        echo "  tiny, base, small, medium, large"
        echo ""
        echo "Examples:"
        echo "  $0                              # Run complete pipeline on test_video_2.mp4"
        echo "  $0 myvideo.mp4 complete         # Run complete pipeline on custom video"
        echo "  $0 myvideo.mp4 video            # Run video analysis only"
        echo "  $0 myvideo.mp4 audio small      # Run audio with 'small' model"
        echo "  $0 myvideo.mp4 fast             # Quick test"
        exit 1
        ;;
esac

# Show final summary
echo ""
echo "========================================="
echo "Pipeline execution finished!"
echo "Output directory: $OUTPUT_DIR"
echo ""

# List generated files
if [ -d "$OUTPUT_DIR" ]; then
    echo "Generated files:"
    find "$OUTPUT_DIR" -type f \( -name "*.json" -o -name "*.srt" -o -name "*.vtt" \) | while read -r file; do
        SIZE=$(ls -lh "$file" | awk '{print $5}')
        echo "  - $(basename "$file") ($SIZE)"
    done
fi

echo "========================================="