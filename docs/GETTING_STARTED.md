# Getting Started with Hendrix Video Analysis Pipeline

This guide will walk you through setting up and running your first video analysis with Hendrix.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation](#installation)
3. [First Run](#first-run)
4. [Understanding the Output](#understanding-the-output)
5. [Common Workflows](#common-workflows)
6. [Customization](#customization)
7. [Next Steps](#next-steps)

## System Requirements

### Minimum Requirements
- **OS**: Linux (Ubuntu 20.04+), macOS 11+, Windows 10+ (WSL2)
- **Python**: 3.8 or higher
- **RAM**: 8GB minimum
- **Storage**: 20GB free space
- **CPU**: 4+ cores recommended

### Recommended Requirements
- **GPU**: NVIDIA GPU with 8GB+ VRAM
- **CUDA**: 11.8 or 12.1
- **RAM**: 16GB or more
- **Storage**: 50GB+ for models and outputs
- **CPU**: 8+ cores

### Software Dependencies
- FFmpeg (for video processing)
- Git (for cloning repository)
- CUDA Toolkit (for GPU support)

## Installation

### Step 1: Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg git python3-pip python3-venv
```

**macOS:**
```bash
brew install ffmpeg git python
```

**Windows:**
- Install [WSL2](https://docs.microsoft.com/en-us/windows/wsl/install)
- Follow Ubuntu instructions in WSL2

### Step 2: Clone Repository

```bash
git clone https://github.com/material-lab-io/HendrixVideo.git
cd HendrixVideo
```

### Step 3: Create Virtual Environment

```bash
python3 -m venv hendrix_venv
source hendrix_venv/bin/activate  # On Windows: hendrix_venv\Scripts\activate
```

### Step 4: Install Hendrix

**Option A: Complete Installation (Recommended)**
```bash
pip install --upgrade pip
pip install -r requirements/all.txt
```

**Option B: Minimal Installation (For Testing)**
```bash
pip install --upgrade pip
pip install -r requirements/minimal.txt
```

**Option C: Custom Installation**
```bash
# Choose components you need
pip install -r requirements/base.txt
pip install -r requirements/video.txt     # For video analysis
pip install -r requirements/audio.txt     # For audio processing
pip install -r requirements/captioning.txt # For caption generation
```

**Option D: Development Mode (Recommended for Contributors)**
```bash
# Install in editable mode to allow code changes without reinstallation
pip install -e .
pip install -r requirements/dev.txt  # Development dependencies

# This allows you to modify the code and test immediately
# Changes to Python files will be reflected without reinstalling
```

### Step 5: Download Models

```bash
# Automatic download script
bash scripts/setup/download_models.sh

# Or manually specify models
python scripts/setup/download_models.py --models llava_7b whisper_base
```

### Step 6: Verify Installation

```bash
# Run verification script
python -m hendrix_pipeline --verify

# Or test with sample video
python -m hendrix_pipeline --video examples/sample_video.mp4 --profile test
```

## First Run

### Basic Pipeline Execution

1. **Prepare your video file**
   ```bash
   # Supported formats: MP4, AVI, MOV, MKV, WEBM
   ls ~/Videos/my_video.mp4
   ```

2. **Run the pipeline**
   ```bash
   # Using the wrapper script (recommended)
   bash scripts/pipeline/run_complete.sh ~/Videos/my_video.mp4
   
   # Or using Python directly
   python -m hendrix_pipeline --video ~/Videos/my_video.mp4
   ```

3. **Monitor progress**
   - The pipeline will show progress bars for each stage
   - Logs are saved to `logs/hendrix_pipeline.log`
   - Use `--verbose` for detailed output

### Quick Test Run

For a quick test with minimal processing:

```bash
# Option 1: Use test videos already in the repository
# test_video.mp4 and test_video_2.mp4 are included

# Option 2: Download from YouTube using yt-dlp
pip install yt-dlp
yt-dlp -f "best[height<=720]" -o "test_video.mp4" "https://www.youtube.com/watch?v=VIDEO_ID"

# Option 3: Use any local video file
# Supported formats: MP4, AVI, MOV, MKV, WEBM

# Run with fast profile
python -m hendrix_pipeline --video test_video.mp4 --profile fast --output-dir test_output
```

## Understanding the Output

After processing, you'll find results in the `outputs/` directory:

```
outputs/
└── my_video_20240812_143022/
    ├── analysis_results.json      # Complete analysis data
    ├── my_video_captions.srt      # Standard subtitle file
    ├── my_video_captions.vtt      # WebVTT subtitle file
    ├── my_video_timeline.html     # Interactive visualization
    ├── my_video_transcript.txt    # Plain text transcript
    └── metadata.json              # Processing metadata
```

### Output Files Explained

1. **analysis_results.json**
   - Complete scene-by-scene analysis
   - Character appearances and emotions
   - Shot boundaries and keyframes
   - Full transcript with speaker labels

2. **Subtitle Files (SRT/VTT)**
   - Ready to use with video players
   - Include speaker labels and emotions
   - Properly timed captions

3. **timeline.html**
   - Visual timeline of the video
   - Interactive scene navigation
   - Character appearance tracking
   - Emotion visualization

## Common Workflows

### 1. Process Multiple Videos

```bash
# Create a batch script
for video in ~/Videos/*.mp4; do
    python -m hendrix_pipeline --video "$video" --profile balanced
done
```

### 2. Extract Only Transcripts

```bash
python -m hendrix_pipeline --video input.mp4 \
    --components audio \
    --output-formats txt,json
```

### 3. Generate Captions for Existing Analysis

```bash
# If you already have analysis_results.json
python -m hendrix_caption --input analysis_results.json \
    --output-formats srt,vtt,html
```

### 4. Use Different Models

```bash
# Use larger Whisper model for better transcription
python -m hendrix_pipeline --video input.mp4 \
    --whisper-model large \
    --llm-model llava_13b
```

## Customization

### Configuration Options

1. **Edit default configuration**
   ```bash
   nano configs/base_config.yaml
   ```

2. **Common customizations:**
   ```yaml
   # Change caption style
   components:
     captioning:
       prompt:
         template: descriptive  # or narrative, minimal
   
   # Adjust quality vs speed
   generation:
     temperature: 0.3  # Lower = more consistent
     max_tokens: 100   # Shorter captions
   
   # GPU memory management
   resources:
     memory:
       max_gpu_memory_fraction: 0.8  # Use 80% of VRAM
   ```

### Command Line Options

```bash
python -m hendrix_pipeline --help

# Common options:
--video PATH           # Input video file
--output-dir PATH      # Output directory
--profile NAME         # Use preset profile (fast/balanced/quality)
--config PATH          # Custom config file
--components LIST      # Run specific components
--output-formats LIST  # Choose output formats
--device DEVICE        # Force CPU/GPU (cuda:0, cpu)
--verbose              # Detailed logging
--dry-run              # Preview without processing
```

### Environment Variables

```bash
# Set API keys
export OPENAI_API_KEY="your-key-here"
export HF_TOKEN="your-huggingface-token"

# Set paths
export HENDRIX_MODEL_PATH="/path/to/models"
export HENDRIX_OUTPUT_PATH="/path/to/outputs"

# Performance settings
export CUDA_VISIBLE_DEVICES="0,1"  # Use specific GPUs
export OMP_NUM_THREADS="8"         # CPU threads
```

## Next Steps

### 1. Explore Advanced Features

- [Model Configuration Guide](MODEL_CONFIG.md)
- [GPU Optimization Guide](GPU_OPTIMIZATION.md)
- [API Usage](API_USAGE.md)

### 2. Integrate with Your Workflow

```python
# Use as a Python library
from hendrix import Pipeline

pipeline = Pipeline(config_path="configs/base_config.yaml")
results = pipeline.process_video("input.mp4")
```

### 3. Contribute

- Report issues on GitHub
- Submit pull requests
- Share your use cases

## Troubleshooting

### Installation Issues

**Problem**: `pip install` fails with dependency conflicts
```bash
# Solution: Use a fresh virtual environment
deactivate
rm -rf hendrix_venv
python3 -m venv hendrix_venv
source hendrix_venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements/all.txt
```

**Problem**: CUDA not detected
```bash
# Check CUDA installation
nvidia-smi
python -c "import torch; print(torch.cuda.is_available())"

# Reinstall PyTorch with correct CUDA version
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Runtime Issues

**Problem**: Out of memory errors
```bash
# Use smaller models
python -m hendrix_pipeline --video input.mp4 --profile fast

# Or enable 8-bit quantization
python -m hendrix_pipeline --video input.mp4 --quantize 8bit
```

**Problem**: Slow processing
```bash
# Check GPU usage
nvidia-smi -l 1

# Use faster models
python -m hendrix_pipeline --video input.mp4 \
    --whisper-model tiny \
    --skip-emotion-detection
```

### Getting Help

1. Check the [FAQ](FAQ.md)
2. Search [existing issues](https://github.com/material-lab-io/HendrixVideo/issues)
3. Create a new issue with:
   - System information
   - Error messages
   - Steps to reproduce

## Congratulations!

You've successfully set up Hendrix Video Analysis Pipeline. Start processing your videos and explore the powerful features available. Happy analyzing!