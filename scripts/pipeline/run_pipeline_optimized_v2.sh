#!/bin/bash
# Optimized Hendrix Pipeline V2 - Simple and Fast
# Uses 7B model with smart configuration

echo "========================================="
echo "Hendrix Pipeline - Optimized V2"
echo "========================================="
echo "Model: LLaVA-7B (Fast & Efficient)"
echo "Time: $(date)"
echo "========================================="

# Activate virtual environment
source hendrix_venv/bin/activate

# Show environment info
echo "Python: $(which python)"
echo "GPU Status:"
nvidia-smi --query-gpu=name,memory.free,utilization.gpu --format=csv,noheader
echo ""

# Set test video
TEST_VIDEO="test_video_2.mp4"
if [ ! -f "$TEST_VIDEO" ]; then
    echo "Error: $TEST_VIDEO not found!"
    exit 1
fi

echo "Test video: $TEST_VIDEO"
VIDEO_DURATION=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$TEST_VIDEO" 2>/dev/null || echo "unknown")
echo "Duration: ${VIDEO_DURATION}s (~$(echo "scale=1; $VIDEO_DURATION/60" | bc) minutes)"
echo "File size: $(ls -lh $TEST_VIDEO | awk '{print $5}')"
echo ""

# Create output directory
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="outputs/test_optimized_v2_${TIMESTAMP}"
mkdir -p "$OUTPUT_DIR"

echo "Output directory: $OUTPUT_DIR"
echo "========================================="

# First, update the video analysis config to reduce shots
cat > "$OUTPUT_DIR/video_config_override.yaml" << 'EOF'
# Optimized Video Analysis Configuration
pipeline:
  batch_size: 64
  use_gpu: true
  device: "cuda:0"
  log_level: "INFO"

shot_detection:
  model_name: "transnetv2"
  min_shot_duration: 3.0  # Increase to reduce over-segmentation
  confidence_threshold: 0.5  # Higher threshold
  max_shots: 300  # Hard limit
  transnetv2:
    batch_size: 128
    device: "cuda"
    threshold: 0.5  # Higher threshold for TransNetV2

scene_construction:
  model: "llava-hf/llava-1.5-7b-hf"  # 7B for speed
  batch_size: 10  # Process more shots at once
  max_frames_per_batch: 20
  model_config:
    load_in_8bit: false
    torch_dtype: "float16"
    device_map: "auto"
    low_cpu_mem_usage: true
  temperature: 0.3
  max_new_tokens: 200  # Shorter descriptions
  progress_bar: true  # Enable progress

output:
  save_keyframes: true
  keyframe_format: "jpg"
  keyframe_quality: 85
EOF

# Copy config to video analysis directory
cp "$OUTPUT_DIR/video_config_override.yaml" components/video_analysis/config_optimized.yaml

# Monitor GPU in background
(while true; do 
    nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader,nounits >> "$OUTPUT_DIR/gpu_usage.log"
    sleep 2
done) &
GPU_MONITOR_PID=$!

# Create progress-aware pipeline runner
cat > "$OUTPUT_DIR/run_with_progress.py" << 'EOF'
import sys
import os
import time
import json
import subprocess
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '/dev-work/hendrix_12aug')

def run_component_with_progress(name, cmd, output_dir):
    """Run a component and show progress"""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Starting {name}...")
    print(f"  Command: {' '.join(cmd[:3])}...")
    
    start_time = time.time()
    
    # Run with real-time output
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )
    
    # Read output line by line
    shot_count = 0
    scene_count = 0
    for line in process.stdout:
        line = line.strip()
        if line:
            # Extract progress information
            if "Found" in line and "shots" in line:
                try:
                    shot_count = int(line.split("Found")[1].split("shots")[0].strip())
                    print(f"  ✓ Detected {shot_count} shots")
                except:
                    pass
            elif "Processing shot" in line:
                print(f"\r  {line}", end='', flush=True)
            elif "Scene" in line and "created" in line:
                scene_count += 1
                print(f"\r  Processing scenes: {scene_count} created", end='', flush=True)
            elif "ERROR" in line:
                print(f"\n  ❌ Error: {line}")
            elif "percent" in line or "%" in line:
                print(f"\r  {line}", end='', flush=True)
    
    process.wait()
    duration = time.time() - start_time
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] ✓ {name} complete in {duration:.1f}s")
    return process.returncode == 0

# Main pipeline execution
print("="*60)
print("Optimized Pipeline Execution")
print("="*60)

output_dir = Path(sys.argv[1])
video_path = sys.argv[2]

# Track overall progress
components_status = {}
overall_start = time.time()

try:
    # 1. Video Analysis with optimized config
    print("\n📹 STAGE 1: Video Analysis (Shot Detection + Scene Construction)")
    video_cmd = [
        sys.executable,
        "components/video_analysis/src/main.py",
        str(video_path),
        "--output", str(output_dir / "video_analysis"),
        "--config", "components/video_analysis/config_optimized.yaml",
        "--debug"
    ]
    
    # Set environment for progress
    env = os.environ.copy()
    env['PYTHONUNBUFFERED'] = '1'
    
    success = run_component_with_progress("Video Analysis", video_cmd, output_dir)
    components_status['video'] = success
    
    if success:
        # Check results
        shots_file = output_dir / "video_analysis" / "shots.json"
        scenes_file = output_dir / "video_analysis" / "scenes.json"
        
        if shots_file.exists():
            with open(shots_file) as f:
                shots_data = json.load(f)
                num_shots = len(shots_data.get('shots', []))
                print(f"  📊 Results: {num_shots} shots detected")
                
                if num_shots > 500:
                    print(f"  ⚠️  Warning: Too many shots ({num_shots}), consider adjusting thresholds")
    
    # 2. Audio Analysis
    print("\n🎤 STAGE 2: Character & Dialogue Analysis")
    audio_cmd = [
        sys.executable,
        "components/character_dialogue/visual_processing_branch/scripts/run_optimized_robust_pipeline.py",
        str(video_path),
        "--output", str(output_dir / "character_dialogue"),
        "--whisper-model", "base"
    ]
    
    # Change to correct directory
    original_dir = os.getcwd()
    os.chdir("components/character_dialogue/visual_processing_branch")
    
    success = run_component_with_progress("Audio Analysis", 
        ["python", "scripts/run_optimized_robust_pipeline.py", 
         str(video_path), "--output", str(output_dir / "character_dialogue"),
         "--whisper-model", "base"], 
        output_dir)
    components_status['audio'] = success
    
    os.chdir(original_dir)
    
    # 3. Caption Generation
    if components_status.get('video', False):
        print("\n📝 STAGE 3: Caption Generation")
        caption_cmd = [
            sys.executable,
            "components/captioning/scripts/generate_comprehensive_captions.py",
            "--scene-analysis", str(output_dir / "video_analysis/scenes.json"),
            "--audio-analysis", str(output_dir / "character_dialogue"),
            "--output-dir", str(output_dir / "comprehensive_captions"),
            "--max-scenes", "50"  # Limit for speed
        ]
        
        success = run_component_with_progress("Caption Generation", caption_cmd, output_dir)
        components_status['caption'] = success
    
    # Summary
    total_time = time.time() - overall_start
    print("\n" + "="*60)
    print(f"Pipeline Completed in {total_time:.1f}s ({total_time/60:.1f} minutes)")
    print("="*60)
    
    print("\nComponent Status:")
    for comp, status in components_status.items():
        print(f"  - {comp}: {'✓ Success' if status else '✗ Failed'}")
    
    # Save summary
    summary = {
        'timestamp': datetime.now().isoformat(),
        'duration': total_time,
        'components_status': components_status,
        'video_path': str(video_path),
        'output_dir': str(output_dir)
    }
    
    with open(output_dir / 'pipeline_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
        
except KeyboardInterrupt:
    print("\n\n⚠️  Pipeline interrupted by user")
    print(f"Partial results available in: {output_dir}")
except Exception as e:
    print(f"\n❌ Pipeline error: {str(e)}")
    import traceback
    traceback.print_exc()
EOF

# Run the pipeline
echo "Starting optimized pipeline..."
echo "This will show real-time progress for each stage"
echo ""

START_TIME=$(date +%s)

python "$OUTPUT_DIR/run_with_progress.py" "$OUTPUT_DIR" "$TEST_VIDEO" 2>&1 | tee "$OUTPUT_DIR/pipeline_output.log"

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# Stop GPU monitoring
kill $GPU_MONITOR_PID 2>/dev/null

# Clean up temp config
rm -f components/video_analysis/config_optimized.yaml

echo ""
echo "========================================="
echo "Performance Summary"
echo "========================================="
echo "Total Duration: $DURATION seconds (~$(($DURATION / 60)) minutes)"

# GPU usage analysis
if [ -f "$OUTPUT_DIR/gpu_usage.log" ] && [ -s "$OUTPUT_DIR/gpu_usage.log" ]; then
    echo ""
    echo "GPU Performance:"
    awk -F, 'NF==2 && $2>10 {
        gpu+=$1; mem+=$2; count++
    } END {
        if(count>0) {
            print "  Average GPU Utilization: " gpu/count "%"
            print "  Average Memory Used: " mem/count " MB"
        } else {
            print "  No significant GPU activity detected"
        }
    }' "$OUTPUT_DIR/gpu_usage.log"
fi

# Results summary
echo ""
echo "Output Summary:"
if [ -f "$OUTPUT_DIR/video_analysis/shots.json" ]; then
    SHOT_COUNT=$(grep -o '"shot_id"' "$OUTPUT_DIR/video_analysis/shots.json" | wc -l)
    echo "  - Shots detected: $SHOT_COUNT"
fi

if [ -f "$OUTPUT_DIR/video_analysis/scenes.json" ]; then
    SCENE_COUNT=$(grep -o '"scene_id"' "$OUTPUT_DIR/video_analysis/scenes.json" | wc -l)
    echo "  - Scenes created: $SCENE_COUNT"
fi

if [ -d "$OUTPUT_DIR/comprehensive_captions" ]; then
    echo "  - Caption files:"
    ls "$OUTPUT_DIR/comprehensive_captions/"*.{srt,vtt,json} 2>/dev/null | head -5
fi

echo ""
echo "========================================="
echo "✓ Pipeline complete!"
echo "Results saved to: $OUTPUT_DIR"
echo ""
echo "Tips for faster processing:"
echo "- Increase min_shot_duration (current: 3.0s)"
echo "- Increase confidence_threshold (current: 0.5)"
echo "- Use smaller whisper model (current: base)"
echo "========================================="