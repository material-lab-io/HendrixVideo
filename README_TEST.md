# Hendrix Pipeline Testing Guide

This guide will help you set up and test the complete Hendrix video analysis pipeline.

## Overview

The Hendrix pipeline consists of three components that work together:
1. **Hendrix_Video**: Analyzes video structure (shots/scenes)
2. **Hendrix_Character_Dialogue_Analysis**: Matches dialogue to characters
3. **Hendrix_Comprehensive_Captioning**: Generates rich narrative captions

## Prerequisites

- **System Requirements**:
  - Ubuntu 20.04+ (or compatible Linux distribution)
  - Python 3.8 or higher
  - FFmpeg installed (`sudo apt install ffmpeg`)
  - 32GB RAM recommended (16GB minimum)
  - NVIDIA GPU with 8GB+ VRAM (optional but recommended)
  - 25GB free disk space for models

- **HuggingFace Account** (optional - for enhanced speaker diarization):
  1. Create account at https://huggingface.co
  2. Get token from https://huggingface.co/settings/tokens
  3. Accept terms at https://huggingface.co/pyannote/speaker-diarization-3.1
  
  **Note**: The pipeline works without a HuggingFace token, but speaker diarization improves accuracy

## Quick Start

### Step 1: Download Models

Run the setup script to download all required models (~20GB):

```bash
cd /dev-work/hendrix_12aug
./setup_hendrix_models.sh
```

**Optional**: When prompted, enter your HuggingFace token for enhanced speaker diarization.
The pipeline will work without it, using alternative methods or skipping speaker analysis.

This script will:
- Create a shared virtual environment
- Install all dependencies
- Download all AI models
- Set up cache directories

Expected download times:
- Fast connection (100 Mbps): ~30 minutes
- Average connection (25 Mbps): ~2 hours

### Step 2: Test the Pipeline

Run the test script with your video:

```bash
# Basic usage
./test_hendrix_pipeline.sh /path/to/your/video.mp4

# Quick mode (faster, lower quality)
./test_hendrix_pipeline.sh /path/to/your/video.mp4 --quick

# Custom output directory
./test_hendrix_pipeline.sh /path/to/your/video.mp4 --output my_results
```

### Step 3: View Results

After processing completes, view your results:

```bash
cd hendrix_output/[video_name]_[timestamp]
./view_results.sh
```

## What the Pipeline Does

1. **Video Analysis Stage**:
   - Detects shot boundaries (scene changes)
   - Extracts keyframes from each shot
   - Groups shots into semantic scenes
   - Generates scene descriptions

2. **Character-Dialogue Analysis Stage**:
   - Transcribes all dialogue with timestamps
   - Detects emotions in speech (happy, sad, angry, etc.)
   - Identifies different speakers
   - Detects and tracks faces/characters
   - Matches dialogue to characters

3. **Comprehensive Captioning Stage**:
   - Combines all previous analyses
   - Generates narrative captions like:
     ```
     [0:00-0:08] In a dimly lit room, Character_1, 
     filled with anger, shouts "Where is the evidence?" 
     while Character_2 nervously backs away.
     ```

## Output Files

The pipeline creates a structured output directory:

```
hendrix_output/video_name_timestamp/
├── pipeline_summary.txt          # Overview of results
├── view_results.sh              # Script to view results
├── video_analysis/              # Hendrix_Video output
│   ├── shots.json              # Shot boundaries
│   ├── scenes.json             # Scene descriptions
│   └── keyframes/              # Extracted frames
├── character_dialogue/          # Character-Dialogue output
│   └── optimized_robust/
│       └── session_*/
│           ├── audio_output/   # Transcriptions
│           ├── visual_output/  # Character data
│           └── fusion_output/  # Character-dialogue matches
└── comprehensive_captions/      # Final captions
    ├── captions.json           # Structured captions
    ├── captions.srt            # Subtitle file
    ├── captions.vtt            # WebVTT format
    ├── captions.html           # Interactive viewer
    └── captions_report.txt     # Human-readable report
```

## Using the Results

### View Captions with Your Video

Use the generated SRT file with any video player:
```bash
# VLC
vlc your_video.mp4 --sub-file hendrix_output/*/comprehensive_captions/captions.srt

# mpv
mpv your_video.mp4 --sub-file=hendrix_output/*/comprehensive_captions/captions.srt
```

### Interactive HTML Viewer

Open the HTML file in a web browser:
```bash
firefox hendrix_output/*/comprehensive_captions/captions.html
```

## Environment Setup

To manually set up the environment for development:

```bash
# Set up environment variables
source hendrix_env_setup.sh

# Activate virtual environment
hendrix_activate

# Your environment is now ready
```

## Processing Times

Estimated processing times (on NVIDIA GPU):
- 1-minute video: ~2-3 minutes
- 5-minute video: ~8-10 minutes
- 30-minute video: ~45-60 minutes

CPU-only processing is 5-10x slower.

## Troubleshooting

### Common Issues

1. **"HF_TOKEN not set" warning**:
   ```bash
   export HF_TOKEN="your_huggingface_token"
   ```

2. **CUDA/GPU errors**:
   ```bash
   # Force CPU mode
   export CUDA_VISIBLE_DEVICES=""
   ./test_hendrix_pipeline.sh video.mp4
   ```

3. **Out of memory errors**:
   ```bash
   # Use quick mode for lower memory usage
   ./test_hendrix_pipeline.sh video.mp4 --quick
   ```

4. **Model download failures**:
   - Check internet connection
   - Ensure 25GB free disk space
   - Re-run setup_hendrix_models.sh

5. **FFmpeg not found**:
   ```bash
   sudo apt update
   sudo apt install ffmpeg
   ```

### Checking Logs

Each stage creates detailed logs:
```bash
# View all logs
cd hendrix_output/[video_name]_[timestamp]
cat hendrix_video.log
cat hendrix_character_dialogue.log
cat hendrix_captioning.log
```

## Advanced Usage

### Custom Model Selection

Edit the test script to use different models:
- Whisper models: tiny, base, small, medium, large
- LLaVA quantization: 8-bit, 4-bit for lower memory

### Batch Processing

Process multiple videos:
```bash
for video in /path/to/videos/*.mp4; do
    ./test_hendrix_pipeline.sh "$video"
done
```

### Using Pre-existing Analysis

If you already have outputs from individual pipelines:
```bash
# Just run comprehensive captioning
cd Hendrix_Comprehensive_Captioning
python scripts/generate_comprehensive_captions.py \
    --audio-analysis /path/to/character_dialogue_output \
    --scene-analysis /path/to/scenes.json \
    --output-dir /path/to/output
```

## Performance Tips

1. **Use GPU acceleration** (10x faster):
   - Ensure NVIDIA drivers installed
   - CUDA toolkit not required (PyTorch includes it)

2. **Quick mode** for testing:
   - Uses smaller models
   - Processes fewer frames
   - Good for initial testing

3. **Memory management**:
   - Close other applications
   - Use 8-bit quantization if needed
   - Process shorter video clips

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review log files for detailed error messages
3. Ensure all prerequisites are met
4. Try with a shorter test video first

## Next Steps

After successful testing:
1. Process your full video library
2. Integrate captions into your workflow
3. Customize the pipeline configuration
4. Explore individual components for specific needs

---

Happy video analysis with Hendrix!