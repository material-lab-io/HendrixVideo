# Hendrix Video Analysis Pipeline - Usage Guide

## Table of Contents

1. [Overview](#overview)
2. [Basic Usage](#basic-usage)
3. [Advanced Usage](#advanced-usage)
4. [Configuration Options](#configuration-options)
5. [Output Formats](#output-formats)
6. [Performance Optimization](#performance-optimization)
7. [API Usage](#api-usage)
8. [Troubleshooting](#troubleshooting)
9. [Examples](#examples)

## Overview

The Hendrix Video Analysis Pipeline provides comprehensive video analysis through three main components:
- **Video Analysis**: Shot detection, scene construction, keyframe extraction
- **Character & Dialogue**: Speech transcription, speaker diarization, face detection
- **Captioning**: AI-powered caption generation with multiple output formats

## Basic Usage

### Command Line Interface

The primary way to use Hendrix is through the command line interface:

```bash
# Basic usage with default settings
python -m hendrix_pipeline --video input.mp4

# Specify output directory
python -m hendrix_pipeline --video input.mp4 --output-dir ./my_results

# Use a specific profile
python -m hendrix_pipeline --video input.mp4 --profile fast
```

### Available Profiles

Hendrix comes with pre-configured profiles for different use cases:

| Profile | Description | Use Case |
|---------|-------------|----------|
| `fast` | Speed-optimized, reduced features | Quick previews, testing |
| `balanced` | Default, good balance | Most use cases |
| `quality` | Maximum quality, all features | Final production |
| `test` | Development with mock models | Development/debugging |

### Shell Script Wrappers

For convenience, several shell scripts are provided:

```bash
# Run complete pipeline
bash scripts/pipeline/run_hendrix_complete.sh video.mp4

# GPU-optimized version
bash scripts/pipeline/run_pipeline_optimized_v2.sh video.mp4

# Simple interface with menu
bash scripts/pipeline/run_pipeline_simple.sh
```

## Advanced Usage

### Component Selection

Run specific components only:

```bash
# Video analysis only
python -m hendrix_pipeline --video input.mp4 --components video

# Audio processing only
python -m hendrix_pipeline --video input.mp4 --components audio

# Multiple components
python -m hendrix_pipeline --video input.mp4 --components video,audio

# Skip specific components
python -m hendrix_pipeline --video input.mp4 --skip-components captioning
```

### Model Selection

Choose specific models for each component:

```bash
# Use larger Whisper model for better transcription
python -m hendrix_pipeline --video input.mp4 --whisper-model large

# Use different vision-language model
python -m hendrix_pipeline --video input.mp4 --vlm-model llava_13b

# Combine multiple model options
python -m hendrix_pipeline --video input.mp4 \
    --whisper-model large \
    --vlm-model llava_13b \
    --diarization-model pyannote_3.0
```

### Output Format Selection

Control which output formats are generated:

```bash
# Generate only SRT subtitles
python -m hendrix_pipeline --video input.mp4 --output-formats srt

# Multiple formats
python -m hendrix_pipeline --video input.mp4 --output-formats srt,vtt,json

# All formats (default)
python -m hendrix_pipeline --video input.mp4 --output-formats all
```

### Batch Processing

Process multiple videos efficiently:

```bash
# Using bash loop
for video in videos/*.mp4; do
    python -m hendrix_pipeline --video "$video" --profile balanced
done

# Parallel processing
find videos/ -name "*.mp4" | parallel -j 4 \
    python -m hendrix_pipeline --video {} --output-dir outputs/{}
```

## Configuration Options

### Configuration File Structure

Hendrix uses YAML configuration files located in `configs/`:

```yaml
# configs/base_config.yaml
components:
  video_analysis:
    shot_detection:
      model: "transnetv2"
      threshold: 0.5
      min_shot_duration: 1.0
    
  character_dialogue:
    whisper:
      model_size: "base"
      language: "auto"
      
  captioning:
    vision_language_model:
      active_model: "llava_7b"
      temperature: 0.7
      max_tokens: 150
```

### Custom Configuration

Create and use custom configurations:

```bash
# Copy and modify base config
cp configs/base_config.yaml configs/my_config.yaml
# Edit my_config.yaml as needed

# Use custom config
python -m hendrix_pipeline --video input.mp4 --config configs/my_config.yaml
```

### Environment Variables

Configure behavior through environment variables:

```bash
# Set model cache directory
export HENDRIX_MODEL_PATH="/path/to/models"

# Set output directory
export HENDRIX_OUTPUT_PATH="/path/to/outputs"

# Configure GPU usage
export CUDA_VISIBLE_DEVICES="0,1"  # Use specific GPUs
export CUDA_VISIBLE_DEVICES="-1"   # Force CPU mode

# Set API keys for cloud models
export OPENAI_API_KEY="your-key"
export HF_TOKEN="your-huggingface-token"

# Control logging
export HENDRIX_LOG_LEVEL="DEBUG"
export HENDRIX_LOG_FILE="/path/to/logfile.log"
```

### Runtime Overrides

Override configuration options at runtime:

```bash
# Override specific settings
python -m hendrix_pipeline --video input.mp4 \
    --set components.captioning.vision_language_model.temperature=0.3 \
    --set components.video_analysis.shot_detection.threshold=0.7

# Disable specific features
python -m hendrix_pipeline --video input.mp4 \
    --disable-emotion-detection \
    --disable-scene-construction
```

## Output Formats

### JSON Output

Complete analysis data in structured format:

```json
{
  "video_metadata": {
    "filename": "input.mp4",
    "duration": 120.5,
    "fps": 30.0,
    "resolution": [1920, 1080]
  },
  "scenes": [
    {
      "scene_id": 1,
      "start_time": 0.0,
      "end_time": 15.3,
      "shots": [1, 2, 3],
      "summary": "Opening scene with characters introducing themselves",
      "characters": ["speaker_1", "speaker_2"],
      "emotions": ["neutral", "happy"]
    }
  ],
  "captions": [
    {
      "start": 0.0,
      "end": 2.5,
      "text": "[Speaker 1] Hello, welcome to our presentation",
      "speaker": "speaker_1",
      "confidence": 0.95
    }
  ]
}
```

### SRT Subtitles

Standard subtitle format compatible with most video players:

```srt
1
00:00:00,000 --> 00:00:02,500
[Speaker 1] Hello, welcome to our presentation

2
00:00:02,500 --> 00:00:05,000
[Speaker 2] Today we'll be discussing video analysis
```

### WebVTT Subtitles

Modern subtitle format with styling support:

```vtt
WEBVTT

NOTE
Generated by Hendrix Video Analysis Pipeline

00:00:00.000 --> 00:00:02.500
<v Speaker 1>Hello, welcome to our presentation

00:00:02.500 --> 00:00:05.000
<v Speaker 2>Today we'll be discussing video analysis
```

### HTML Timeline

Interactive visualization of the video analysis:

- Scene boundaries with thumbnails
- Character appearance timeline
- Emotion visualization
- Searchable transcript
- Click-to-navigate interface

## Performance Optimization

### GPU Optimization

```bash
# Enable mixed precision for faster processing
python -m hendrix_pipeline --video input.mp4 --mixed-precision

# Use model quantization
python -m hendrix_pipeline --video input.mp4 --quantize 8bit

# Batch processing for efficiency
python -m hendrix_pipeline --video input.mp4 --batch-size 32
```

### Memory Management

```bash
# Limit GPU memory usage
python -m hendrix_pipeline --video input.mp4 --gpu-memory-fraction 0.8

# Enable gradient checkpointing
python -m hendrix_pipeline --video input.mp4 --gradient-checkpointing

# Process in chunks for long videos
python -m hendrix_pipeline --video input.mp4 --chunk-duration 300
```

### CPU Optimization

```bash
# Set number of threads
export OMP_NUM_THREADS=8
python -m hendrix_pipeline --video input.mp4 --device cpu

# Use smaller models for CPU
python -m hendrix_pipeline --video input.mp4 \
    --profile fast \
    --whisper-model tiny
```

## API Usage

### Python API

Use Hendrix programmatically in your Python applications:

```python
from hendrix_pipeline import Pipeline
from components.config_manager import ConfigManager

# Initialize pipeline
config = ConfigManager(config_path="configs/base_config.yaml")
pipeline = Pipeline(config)

# Process video
results = pipeline.process_video(
    video_path="input.mp4",
    output_dir="outputs/",
    components=["video", "audio", "captioning"]
)

# Access results
scenes = results["scenes"]
captions = results["captions"]
metadata = results["metadata"]
```

### Async Processing

```python
import asyncio
from hendrix_pipeline import AsyncPipeline

async def process_videos(video_list):
    pipeline = AsyncPipeline()
    
    tasks = []
    for video in video_list:
        task = pipeline.process_video_async(video)
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    return results

# Run async processing
video_list = ["video1.mp4", "video2.mp4", "video3.mp4"]
results = asyncio.run(process_videos(video_list))
```

### Custom Components

Extend the pipeline with custom processors:

```python
from hendrix_pipeline import Pipeline, BaseComponent

class CustomProcessor(BaseComponent):
    def process(self, video_path, **kwargs):
        # Your custom processing logic
        results = {"custom_data": "processed"}
        return results

# Register and use custom component
pipeline = Pipeline()
pipeline.register_component("custom", CustomProcessor())
pipeline.process_video("input.mp4", components=["video", "custom"])
```

## Troubleshooting

### Common Issues

1. **Out of Memory Error**
   ```bash
   # Solution: Use smaller models or quantization
   python -m hendrix_pipeline --video input.mp4 --profile fast --quantize 8bit
   ```

2. **CUDA Not Available**
   ```bash
   # Check CUDA installation
   python -c "import torch; print(torch.cuda.is_available())"
   
   # Force CPU mode
   python -m hendrix_pipeline --video input.mp4 --device cpu
   ```

3. **Model Download Fails**
   ```bash
   # Manual download with retry
   python scripts/setup/download_models.py --retry 5
   
   # Use different model source
   export HF_ENDPOINT="https://hf-mirror.com"
   ```

4. **Slow Processing**
   ```bash
   # Enable performance profiling
   python -m hendrix_pipeline --video input.mp4 --profile-performance
   
   # Check GPU utilization
   nvidia-smi -l 1
   ```

### Debug Mode

Enable detailed debugging information:

```bash
# Verbose logging
python -m hendrix_pipeline --video input.mp4 --verbose --log-level DEBUG

# Save intermediate outputs
python -m hendrix_pipeline --video input.mp4 --save-intermediate

# Dry run to check configuration
python -m hendrix_pipeline --video input.mp4 --dry-run
```

## Examples

### Example 1: Conference Video Analysis

```bash
# Optimize for speech and multiple speakers
python -m hendrix_pipeline \
    --video conference_recording.mp4 \
    --whisper-model medium \
    --diarization-speakers 5 \
    --skip-emotion-detection \
    --output-formats srt,json
```

### Example 2: Movie Scene Analysis

```bash
# Full analysis with high quality
python -m hendrix_pipeline \
    --video movie_scene.mp4 \
    --profile quality \
    --vlm-model llava_13b \
    --enable-scene-description \
    --output-formats all
```

### Example 3: Quick Preview

```bash
# Fast processing for preview
python -m hendrix_pipeline \
    --video test_video.mp4 \
    --profile fast \
    --max-duration 60 \
    --output-formats srt
```

### Example 4: Batch Processing with Custom Settings

```python
# batch_process.py
import os
from hendrix_pipeline import Pipeline
from pathlib import Path

# Configure pipeline
pipeline = Pipeline(profile="balanced")

# Process all videos in directory
video_dir = Path("videos/")
output_dir = Path("outputs/")

for video_file in video_dir.glob("*.mp4"):
    print(f"Processing {video_file.name}...")
    
    # Custom output path
    video_output = output_dir / video_file.stem
    video_output.mkdir(exist_ok=True)
    
    # Process with custom settings
    results = pipeline.process_video(
        video_path=str(video_file),
        output_dir=str(video_output),
        whisper_model="base",
        output_formats=["srt", "json", "html"]
    )
    
    print(f"Completed {video_file.name}")
    print(f"  Scenes: {len(results['scenes'])}")
    print(f"  Captions: {len(results['captions'])}")
```

### Example 5: Integration with Video Editing

```python
# Generate EDL (Edit Decision List) from analysis
from hendrix_pipeline import Pipeline
import json

def generate_edl(analysis_results, output_path):
    """Generate EDL file from Hendrix analysis"""
    with open(output_path, 'w') as f:
        f.write("TITLE: Hendrix Analysis EDL\n")
        f.write("FCM: NON-DROP FRAME\n\n")
        
        for idx, scene in enumerate(analysis_results['scenes']):
            start_tc = frames_to_timecode(scene['start_frame'])
            end_tc = frames_to_timecode(scene['end_frame'])
            
            f.write(f"{idx+1:03d}  AX  V  C  ")
            f.write(f"{start_tc} {end_tc} ")
            f.write(f"{start_tc} {end_tc}\n")
            f.write(f"* FROM CLIP NAME: {scene.get('description', 'Scene ' + str(idx+1))}\n")

# Process video and generate EDL
pipeline = Pipeline()
results = pipeline.process_video("input.mp4")
generate_edl(results, "output.edl")
```

---

For more information and updates, visit the [Hendrix GitHub repository](https://github.com/yourusername/hendrix_12aug).