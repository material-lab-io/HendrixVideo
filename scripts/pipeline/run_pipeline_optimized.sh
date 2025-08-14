#!/bin/bash
# Optimized Hendrix Pipeline with Progress Updates
# Uses 7B model with smart shot detection and real-time progress

echo "========================================="
echo "Hendrix Pipeline - Optimized Version"
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
echo "Duration: ${VIDEO_DURATION}s"
echo "File size: $(ls -lh $TEST_VIDEO | awk '{print $5}')"
echo ""

# Create output directory
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="outputs/test_optimized_${TIMESTAMP}"
mkdir -p "$OUTPUT_DIR"

echo "Output directory: $OUTPUT_DIR"
echo "========================================="

# Create optimized config
cat > "$OUTPUT_DIR/config_optimized.yaml" << 'EOF'
# Optimized Configuration for Speed
shot_detection:
  model_name: "transnetv2"
  min_shot_duration: 3.0  # Increase from 0.5 to reduce shots
  confidence_threshold: 0.5  # Increase from 0.3 to be more selective
  transnetv2:
    batch_size: 128  # Larger batch for faster processing
    device: "cuda"
    threshold: 0.5  # Higher threshold = fewer shots

scene_construction:
  model: "llava-hf/llava-1.5-7b-hf"  # 7B model for speed
  batch_size: 5  # Process 5 shots at once
  max_frames_per_batch: 10  # More frames per batch
  model_config:
    load_in_8bit: false  # Full precision for 7B is still fast
    torch_dtype: "float16"
    device_map: "auto"
  temperature: 0.3
  max_new_tokens: 256  # Shorter descriptions for speed

pipeline:
  use_gpu: true
  device: "cuda:0"
  log_level: "INFO"
  max_shots_to_process: 500  # Limit maximum shots
EOF

echo "Configuration optimized for:"
echo "- Minimum shot duration: 3.0s (reduces over-segmentation)"
echo "- Higher confidence threshold: 0.5"
echo "- Batch processing: 5 shots at once"
echo "- Max 500 shots (safety limit)"
echo ""

# Monitor GPU in background
(while true; do 
    nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader,nounits >> "$OUTPUT_DIR/gpu_usage.log"
    sleep 2
done) &
GPU_MONITOR_PID=$!

# Create pipeline runner with progress updates
cat > "$OUTPUT_DIR/run_pipeline_with_progress.py" << 'EOF'
import sys
import os
import time
import json
import yaml
import logging
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '/dev-work/hendrix_12aug')

# Import with progress tracking modifications
from components.pipeline import Pipeline
from components.video_analysis.src.pipeline.shot_detection import ShotDetectionPipeline
from components.video_analysis.src.pipeline.scene_construction import SceneConstructionPipeline

# Monkey patch to add progress updates
original_detect_shots = ShotDetectionPipeline.process
original_construct_scenes = SceneConstructionPipeline.process

def detect_shots_with_progress(self, video_path, output_dir, start_time=0.0, end_time=None):
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Starting shot detection...")
    print(f"  Video: {Path(video_path).name}")
    print(f"  Processing range: {start_time}s - {end_time or 'end'}s")
    
    start = time.time()
    result = original_detect_shots(self, video_path, output_dir, start_time, end_time)
    
    duration = time.time() - start
    num_shots = len(result.get('shots', []))
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ Shot detection complete!")
    print(f"  Found {num_shots} shots in {duration:.1f}s")
    print(f"  Average: {duration/num_shots:.2f}s per shot" if num_shots > 0 else "")
    
    # Limit shots if too many
    max_shots = 500
    if num_shots > max_shots:
        print(f"  ⚠️  Limiting to first {max_shots} shots (from {num_shots})")
        result['shots'] = result['shots'][:max_shots]
    
    return result

def construct_scenes_with_progress(self, shots, keyframes_dir, output_dir):
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Starting scene construction...")
    print(f"  Processing {len(shots)} shots with LLaVA-7B")
    print(f"  Batch size: {getattr(self, 'batch_size', 1)}")
    
    # Add progress tracking
    total_shots = len(shots)
    processed = 0
    start = time.time()
    
    # Process in smaller chunks with updates
    batch_size = getattr(self, 'batch_size', 5)
    scenes = []
    
    for i in range(0, total_shots, batch_size):
        batch_end = min(i + batch_size, total_shots)
        batch_shots = shots[i:batch_end]
        
        print(f"\r  Progress: {i}/{total_shots} shots ({i/total_shots*100:.1f}%) - "
              f"Time: {time.time()-start:.1f}s - "
              f"Est. remaining: {(time.time()-start)/(i+1)*(total_shots-i):.1f}s" if i > 0 else "...", 
              end='', flush=True)
        
        # Process batch
        batch_scenes = original_construct_scenes(self, batch_shots, keyframes_dir, output_dir)
        scenes.extend(batch_scenes.get('scenes', []))
    
    duration = time.time() - start
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] ✓ Scene construction complete!")
    print(f"  Created {len(scenes)} scenes in {duration:.1f}s")
    print(f"  Average: {duration/len(scenes):.2f}s per scene" if scenes else "")
    
    return {'scenes': scenes}

# Apply patches
ShotDetectionPipeline.process = detect_shots_with_progress
SceneConstructionPipeline.process = construct_scenes_with_progress

# Load custom config
with open('$OUTPUT_DIR/config_optimized.yaml', 'r') as f:
    custom_config = yaml.safe_load(f)

print("Initializing pipeline with optimized settings...")
pipeline = Pipeline()

# Override config
if hasattr(pipeline, 'config'):
    pipeline.config.update(custom_config)

# Process video
print("\n" + "="*60)
print("Starting optimized pipeline processing...")
print("="*60)

try:
    start_time = time.time()
    
    results = pipeline.process_video(
        video_path='$TEST_VIDEO',
        output_dir='$OUTPUT_DIR',
        components=["video", "audio", "caption"],
        verbose=True
    )
    
    total_time = time.time() - start_time
    
    # Save results
    with open(Path('$OUTPUT_DIR') / 'pipeline_summary.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "="*60)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Pipeline completed successfully!")
    print("="*60)
    print(f"Total time: {total_time:.1f}s ({total_time/60:.1f} minutes)")
    print(f"Status: {results.get('status', 'unknown')}")
    print(f"Components run: {results.get('components_run', [])}")
    
    if 'video_analysis' in results:
        va = results['video_analysis']
        print(f"\nVideo Analysis:")
        print(f"  - Shots: {va.get('total_shots', 0)}")
        print(f"  - Scenes: {va.get('total_scenes', 0)}")
    
    if 'audio_analysis' in results:
        aa = results['audio_analysis']
        print(f"\nAudio Analysis:")
        print(f"  - Transcripts: {len(aa.get('transcripts', []))}")
        print(f"  - Speakers: {len(aa.get('speakers', []))}")
        
except KeyboardInterrupt:
    print("\n\n⚠️  Pipeline interrupted by user")
    print("Partial results may be available in:", '$OUTPUT_DIR')
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
finally:
    print(f"\nOutput directory: $OUTPUT_DIR")
EOF

# Run pipeline
START_TIME=$(date +%s)

python "$OUTPUT_DIR/run_pipeline_with_progress.py" 2>&1 | tee "$OUTPUT_DIR/pipeline_output.log"

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# Stop GPU monitoring
kill $GPU_MONITOR_PID 2>/dev/null

echo ""
echo "========================================="
echo "Performance Summary"
echo "========================================="
echo "Duration: $DURATION seconds"

# GPU usage summary
if [ -f "$OUTPUT_DIR/gpu_usage.log" ]; then
    echo ""
    echo "GPU Performance:"
    awk -F, '{gpu+=$1; mem+=$2; count++} END {
        print "  Average GPU: " gpu/count "%"
        print "  Average Memory: " mem/count " MB"
        print "  Peak Memory: " max " MB"
    } {if($2>max) max=$2}' "$OUTPUT_DIR/gpu_usage.log"
fi

# Check outputs
echo ""
echo "Output Files:"
find "$OUTPUT_DIR" -name "*.json" -o -name "*.srt" -o -name "*.vtt" | head -10

echo ""
echo "========================================="
echo "Pipeline complete! Results in: $OUTPUT_DIR"
echo "========================================="