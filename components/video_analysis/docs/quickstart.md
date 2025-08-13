# Quick Start Guide

Get up and running with the Hendrix Video Analysis Pipeline in minutes.

## Prerequisites Check

Before starting, ensure you have:
- Python 3.8 or higher
- FFmpeg installed (`ffmpeg -version` should work)
- At least 16GB RAM
- 50GB free disk space
- (Optional) NVIDIA GPU with CUDA support

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/Hendrix_Video_Analysis.git
cd Hendrix_Video_Analysis
```

### 2. Set Up Environment

```bash
# Make setup script executable
chmod +x setup_env.sh

# Run setup (creates virtual environment and installs dependencies)
./setup_env.sh
```

### 3. Verify Installation

```bash
# Activate virtual environment
source venv/bin/activate

# Run verification
python -c "import cv2, torch, transformers; print('All dependencies installed!')"
```

## Your First Analysis

### 1. Prepare a Test Video

```bash
# Create a simple test video
python tests/create_test_video.py
```

This creates `tests/sample_video.mp4` for testing.

### 2. Run Basic Analysis

```bash
python src/main.py tests/sample_video.mp4
```

### 3. Check Results

Results are saved in the `output/` directory:
- `shots.json` - Shot boundaries and keyframes
- `scenes.json` - Scene descriptions
- `keyframes/` - Extracted keyframe images

## Understanding the Output

### Shot Detection Output
```json
{
  "total_shots": 9,
  "shots": [
    {
      "shot_id": 1,
      "start": 0.0,
      "end": 2.0,
      "duration": 2.0,
      "keyframe_path": "keyframes/shot_0001.jpg",
      "confidence": 1.0,
      "transition_type": "cut"
    }
  ]
}
```

### Scene Construction Output
```json
{
  "total_scenes": 5,
  "scenes": [
    {
      "scene_id": 1,
      "summary": "Opening sequence with title card",
      "contained_shots": [1, 2],
      "mood": "introductory",
      "start_time": 0.0,
      "end_time": 5.0
    }
  ]
}
```

## Common Use Cases

### Analyze with Verbose Output
```bash
./run_verbose.sh your_video.mp4
```

### Process Multiple Videos
```bash
for video in videos/*.mp4; do
    python src/main.py "$video" --output-dir "output/$(basename $video .mp4)"
done
```

### Resume Interrupted Processing
```bash
python src/main.py video.mp4 --resume-from scene_construction
```

### Custom Configuration
```bash
# Copy default config
cp config.yaml my_config.yaml

# Edit configuration
nano my_config.yaml

# Run with custom config
python src/main.py video.mp4 --config my_config.yaml
```

## GPU vs CPU Processing

### Check GPU Availability
```python
import torch
print(f"GPU Available: {torch.cuda.is_available()}")
print(f"GPU Name: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'None'}")
```

### Force CPU Processing
Edit `config.yaml`:
```yaml
scene_construction:
  use_gpu: false
  device: "cpu"
```

## Performance Tips

1. **For Faster Processing**:
   - Use GPU (16GB+ VRAM recommended)
   - Reduce `max_frames_per_batch` in config
   - Process shorter video segments

2. **For Better Quality**:
   - Increase `keyframe_extraction.quality`
   - Use `min_shot_duration: 1.0` for less noisy shots
   - Enable all three pipeline stages

3. **For Large Videos**:
   - Use batch processing scripts
   - Enable resume capability
   - Monitor memory usage

## Next Steps

- Read the [Configuration Guide](configuration.md) to customize settings
- Check [Performance Guide](performance.md) for optimization
- See [Examples](../examples/) for advanced usage
- Review [Troubleshooting](troubleshooting.md) if you encounter issues

## Quick Commands Reference

```bash
# Basic analysis
python src/main.py video.mp4

# Verbose output
./run_verbose.sh video.mp4

# Custom output directory
python src/main.py video.mp4 --output-dir my_results

# Resume from stage
python src/main.py video.mp4 --resume-from scene_construction

# Debug mode
python src/main.py video.mp4 --debug

# Help
python src/main.py --help
```