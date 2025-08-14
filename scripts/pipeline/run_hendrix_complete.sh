#!/bin/bash
# Hendrix Complete 3-Stage Pipeline
# Runs: Video Analysis → Character-Dialogue → Comprehensive Captioning

echo "============================================="
echo "   HENDRIX COMPLETE 3-STAGE PIPELINE"
echo "============================================="
echo "Stage 1: Video Analysis (shots/scenes)"
echo "Stage 2: Character-Dialogue Matching"  
echo "Stage 3: Comprehensive Caption Generation"
echo "============================================="
echo "Started: $(date)"
echo ""

# Activate virtual environment
source hendrix_venv/bin/activate

# Get video file
VIDEO_FILE="${1:-test_video_2.mp4}"
if [ ! -f "$VIDEO_FILE" ]; then
    echo "Error: Video file not found: $VIDEO_FILE"
    echo "Usage: $0 [video_file]"
    exit 1
fi

# Show video info
echo "📹 Video: $VIDEO_FILE"
echo "   Size: $(ls -lh "$VIDEO_FILE" | awk '{print $5}')"
echo "   Duration: $(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$VIDEO_FILE" 2>/dev/null | cut -d. -f1)s"
echo ""

# Show GPU status
echo "🖥️  GPU: $(python -c "import torch; print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU only')" 2>/dev/null)"
echo ""

# Create master output directory
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="outputs/hendrix_complete_${TIMESTAMP}"
mkdir -p "$OUTPUT_DIR"

echo "📁 Output: $OUTPUT_DIR"
echo "============================================="
echo ""

# Track overall time
PIPELINE_START=$(date +%s)

# Python runner script that handles all 3 stages
cat > "$OUTPUT_DIR/run_pipeline.py" << 'EOF'
import os
import sys
import time
import json
import subprocess
from pathlib import Path
from datetime import datetime

# Setup
output_dir = Path(sys.argv[1]).resolve()
video_path = Path(sys.argv[2]).resolve()
project_root = Path(sys.argv[3]).resolve()

os.chdir(project_root)
sys.path.insert(0, str(project_root))

print("Starting Hendrix Complete Pipeline...")
print("="*60)

overall_start = time.time()
status = {"stages": {}}

# ========== STAGE 1: VIDEO ANALYSIS ==========
print("\n🎬 STAGE 1: VIDEO ANALYSIS")
print("-"*40)
stage_start = time.time()

video_output = output_dir / "video_analysis"
video_output.mkdir(exist_ok=True)

cmd = [
    sys.executable,
    "components/video_analysis/src/main.py",
    str(video_path),
    "--output-dir", str(video_output),
    "--config", "configs/optimized_pipeline.yaml"
]

print("Running shot detection and scene analysis...")
result = subprocess.run(cmd, capture_output=True, text=True)

if result.returncode == 0:
    # Count results
    shots_file = video_output / "shots.json"
    scenes_file = video_output / "scenes.json"
    
    shots_count = 0
    scenes_count = 0
    
    if shots_file.exists():
        with open(shots_file) as f:
            shots_count = len(json.load(f).get('shots', []))
    
    if scenes_file.exists():
        with open(scenes_file) as f:
            scenes_count = len(json.load(f).get('scenes', []))
    
    duration = time.time() - stage_start
    print(f"✓ Complete: {shots_count} shots, {scenes_count} scenes in {duration:.1f}s")
    status["stages"]["video_analysis"] = {
        "success": True,
        "duration": duration,
        "shots": shots_count,
        "scenes": scenes_count
    }
else:
    print(f"✗ Failed: {result.stderr}")
    status["stages"]["video_analysis"] = {"success": False}
    sys.exit(1)

# ========== STAGE 2: CHARACTER-DIALOGUE ==========
print("\n👥 STAGE 2: CHARACTER-DIALOGUE MATCHING")
print("-"*40)
stage_start = time.time()

char_output = output_dir / "character_dialogue"
char_output.mkdir(exist_ok=True)

# Run the character-dialogue pipeline
script_path = project_root / "components/character_dialogue/visual_processing_branch/scripts/run_optimized_robust_pipeline.py"

cmd = [
    sys.executable,
    str(script_path),
    str(video_path),
    "--output", str(char_output),
    "--whisper-model", "base"
]

print("Running audio transcription, face detection, and matching...")
print("This may take several minutes...")

# Run with live output
process = subprocess.Popen(
    cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    universal_newlines=True,
    bufsize=1
)

# Monitor output
output_lines = []
for line in process.stdout:
    line = line.strip()
    output_lines.append(line)
    if any(keyword in line for keyword in ["STAGE", "Success", "complete", "ERROR", "Failed"]):
        print(f"  {line}")

process.wait()

# If process failed, show last few lines
if process.returncode != 0:
    print("\nError output:")
    for line in output_lines[-10:]:
        if line:
            print(f"  {line}")

# Find session directory
import glob
session_dirs = glob.glob(str(char_output / "session_*"))
if session_dirs:
    session_dir = Path(session_dirs[0])
    duration = time.time() - stage_start
    print(f"✓ Complete: Session {session_dir.name} in {duration:.1f}s")
    status["stages"]["character_dialogue"] = {
        "success": True,
        "duration": duration,
        "session": session_dir.name
    }
else:
    print("✗ Failed: No session directory created")
    status["stages"]["character_dialogue"] = {"success": False}
    sys.exit(1)

# No need to change directories

# ========== STAGE 3: CAPTION GENERATION ==========
print("\n💬 STAGE 3: COMPREHENSIVE CAPTION GENERATION")
print("-"*40)
stage_start = time.time()

caption_output = output_dir / "captions"
caption_output.mkdir(exist_ok=True)

# Check for keyframes
keyframes_dir = video_output / "keyframes"
keyframe_args = []
if keyframes_dir.exists() and list(keyframes_dir.glob("*.jpg")):
    keyframe_args = ["--keyframes", str(keyframes_dir)]
    print("Using keyframes for enhanced captions")

cmd = [
    sys.executable,
    "components/captioning/scripts/generate_comprehensive_captions.py",
    "--scene-analysis", str(scenes_file),
    "--audio-analysis", str(session_dir),
    "--output-dir", str(caption_output),
    "--max-scenes", "200"
] + keyframe_args

print("Generating narrative captions...")
result = subprocess.run(cmd, capture_output=True, text=True)

if result.returncode == 0:
    # Check outputs
    formats_found = []
    for fmt in ['srt', 'vtt', 'json', 'html']:
        if (caption_output / f"comprehensive_captions.{fmt}").exists():
            formats_found.append(fmt.upper())
    
    duration = time.time() - stage_start
    print(f"✓ Complete: Generated {', '.join(formats_found)} in {duration:.1f}s")
    status["stages"]["caption_generation"] = {
        "success": True,
        "duration": duration,
        "formats": formats_found
    }
else:
    print(f"✗ Failed: Check logs for details")
    status["stages"]["caption_generation"] = {"success": False}

# ========== FINAL SUMMARY ==========
total_time = time.time() - overall_start
print("\n" + "="*60)
print("PIPELINE COMPLETE")
print("="*60)
print(f"Total Time: {total_time:.1f}s ({total_time/60:.1f} minutes)")
print("\nStage Results:")

success_count = 0
for stage, info in status["stages"].items():
    if info.get("success"):
        success_count += 1
        print(f"  ✓ {stage}: {info.get('duration', 0):.1f}s")
    else:
        print(f"  ✗ {stage}: Failed")

print(f"\nSuccess: {success_count}/3 stages completed")

# Save status
with open(output_dir / "pipeline_status.json", "w") as f:
    json.dump(status, f, indent=2)

print(f"\nAll outputs saved to: {output_dir}")

# List key files
print("\nKey Output Files:")
key_files = [
    "video_analysis/scenes.json",
    "video_analysis/shots.json",
    f"character_dialogue/{status['stages'].get('character_dialogue', {}).get('session', 'session_*')}/fusion_output/schema_d_matches.json",
    "captions/comprehensive_captions.srt",
    "captions/comprehensive_captions.html"
]

for file_path in key_files:
    full_path = output_dir / file_path
    if full_path.exists():
        size = full_path.stat().st_size
        print(f"  ✓ {file_path} ({size:,} bytes)")
    elif "*" not in file_path:
        print(f"  ✗ {file_path} (not found)")

print("="*60)
EOF

# Run the pipeline
echo "Executing 3-stage pipeline..."
python "$OUTPUT_DIR/run_pipeline.py" "$OUTPUT_DIR" "$VIDEO_FILE" "$(pwd)" 2>&1 | tee "$OUTPUT_DIR/pipeline.log"

PIPELINE_END=$(date +%s)
TOTAL_TIME=$((PIPELINE_END - PIPELINE_START))

# Final summary
echo ""
echo "============================================="
echo "Pipeline finished in $TOTAL_TIME seconds"
echo ""

# Check if captions were generated
if [ -f "$OUTPUT_DIR/captions/comprehensive_captions.srt" ]; then
    echo "✅ SUCCESS: All stages completed!"
    echo ""
    echo "📺 To use the captions:"
    echo "   SRT file: $OUTPUT_DIR/captions/comprehensive_captions.srt"
    echo "   VTT file: $OUTPUT_DIR/captions/comprehensive_captions.vtt"
    
    if [ -f "$OUTPUT_DIR/captions/comprehensive_captions.html" ]; then
        echo ""
        echo "🌐 To view interactive captions:"
        echo "   Open in browser: $OUTPUT_DIR/captions/comprehensive_captions.html"
    fi
else
    echo "⚠️  Pipeline completed with errors. Check logs:"
    echo "   $OUTPUT_DIR/pipeline.log"
fi

echo ""
echo "📁 Full output directory: $OUTPUT_DIR"
echo "============================================="