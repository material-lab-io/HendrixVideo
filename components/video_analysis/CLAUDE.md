# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Hendrix Video Analysis is a Python-based video analysis pipeline that performs sophisticated video processing through three stages:
1. **Shot Detection**: Identifies shot boundaries using TransNetV2 or frame difference method
2. **Scene Construction**: Groups shots into scenes and generates narratives using LLaVA
3. **Cinematic Analysis**: Analyzes cinematographic techniques (currently placeholder)

The pipeline uses advanced models including TransNetV2 for shot detection and LLaVA (Large Language and Vision Assistant) for visual understanding, providing detailed insights into video content structure and semantics.

## Prerequisites

- **Python**: 3.8+ required (tested with 3.12)
- **FFmpeg**: Required for video processing (`sudo apt install ffmpeg`)
- **CUDA**: Optional, for GPU acceleration (CUDA 11.8+ recommended)
- **Operating System**: Linux (Ubuntu 20.04+ recommended), macOS 10.15+, or Windows 10/11 with WSL2
- **yt-dlp**: For downloading videos from YouTube (`pip install yt-dlp`)

## Development Commands

### Environment Setup
```bash
# Initial setup (run once after cloning)
python3 init_project.py

# Create and activate virtual environment
chmod +x setup_env.sh
./setup_env.sh
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# For GPU support
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Install TransNetV2 for shot detection
pip install transnetv2-pytorch

# Verify installation
python src/utils/verify_installation.py
```

### Model Cache Setup (Important for Large Models)
```bash
# Set up local cache to avoid disk space issues
chmod +x setup_model_cache.sh
./setup_model_cache.sh
source venv/bin/activate  # Re-activate to load env vars

# Download models non-interactively
python download_models_auto.py
```

### Running the Application
```bash
# Basic usage
python src/main.py <video_file>

# With custom config
python src/main.py video.mp4 --config custom_config.yaml

# Resume from previous stage
python src/main.py video.mp4 --resume-from shots

# Enable debug logging
python src/main.py video.mp4 --debug

# Verbose mode with detailed output
./run_verbose.sh video.mp4

# Batch process multiple videos
python examples/batch_processing.py /path/to/video/directory/ --workers 4

# Batch processing with specific file patterns
python examples/batch_processing.py /videos/ --pattern "*.mp4,*.avi" --dry-run

# Analyze results after processing
python analyze_results.py

# Run with mock models for testing (no GPU required)
python src/main.py video.mp4 --config config_mock.yaml
```

### Testing
```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_integration.py

# Run specific test function
pytest tests/test_integration.py::test_full_pipeline_execution

# Run with verbose output
pytest -v tests/

# Run with coverage report
pytest --cov=src tests/

# Create test video for testing (creates tests/sample_video.mp4)
python tests/create_test_video.py

# Run tests with mock models (faster, no GPU required)
pytest tests/ --mock

# Type checking
mypy src/
```

### Code Quality
```bash
# Format code
black src/ tests/

# Check formatting
black --check src/ tests/

# Lint code
flake8 src/ tests/
```

## Architecture Overview

### Core Components

1. **Main Orchestrator** (`src/main.py`)
   - `VideoAnalysisPipeline` class coordinates all stages
   - Handles configuration, logging, and error recovery
   - Implements resume capability

2. **Pipeline Stages** (`src/pipeline/`)
   - `shot_detection.py`: Detects shot boundaries and extracts keyframes
   - `scene_construction.py`: Groups shots into scenes using LLaVA
   - `cinematic_analysis.py`: Placeholder for future cinematic analysis

3. **Model Wrappers** (`src/models/`)
   - `transnetv2.py`: TransNetV2 neural network for shot boundary detection
   - `autoshot.py`: Frame difference-based shot detection (fallback)
   - `llava.py`: Vision-language model for scene understanding
   - `cinematic_vlm.py`: Placeholder for cinematic analysis model

4. **Data Structures** (`src/schemas/`)
   - `Shot`: Video segment with timing and transition info
   - `Scene`: Grouped shots with narrative descriptions
   - `AnalysisResult`: Complete analysis output

5. **Utilities** (`src/utils/`)
   - `video_processor.py`: Video I/O operations with context manager
   - `prompt_templates.py`: Centralized prompt templates for LLMs
   - `verify_installation.py`: Check system dependencies

### Data Flow
```
Video → Shot Detection → Shots + Keyframes → Scene Construction → Scenes → Cinematic Analysis → Complete Result
```

### Key Design Patterns
- **Pipeline Pattern**: Independent stages with defined interfaces
- **Context Managers**: Resource management for video processing
- **Data Classes**: Clean serialization with `to_dict()`/`from_dict()`
- **Configuration-Driven**: YAML config controls behavior
- **Async Support**: Pipeline stages can run asynchronously for better performance
- **Error Recovery**: Automatic resume from last successful stage on failure

## Important Notes

### Model Loading
- **TransNetV2**: Neural network for accurate shot detection (~100MB)
  - Install: `pip install transnetv2-pytorch`
  - Detects both hard cuts and gradual transitions
  - GPU accelerated when available
- **LLaVA**: Real model implementation in `src/models/llava.py`
  - Model: `llava-hf/llava-1.5-7b-hf` (~13GB in float16)
  - Supports quantization (8-bit, 4-bit) for memory efficiency
- **Shot Detection Comparison**:
  - TransNetV2: ~138 shots for Tears of Steel (more accurate)
  - Frame Difference: ~293 shots for same video (over-sensitive)
  - TransNetV2 reduces false positives by 53%
  - Processing speed: 4.3x faster than real-time on GPU

### Directory Structure
- `cache/`: Model storage (huggingface, torch, transformers)
- `output/`: Analysis results (shots.json, scenes.json, etc.)
- `keyframes/`: Extracted video frames
- `temp/`: Temporary processing files
- `logs/`: Detailed pipeline logs

### Output Files
- `output/shots.json`: Detected shot boundaries with confidence scores
- `output/scenes.json`: Scene groupings with narrative descriptions
- `output/video_analysis_complete.json`: Combined analysis with metadata
- `pipeline_verbose_log.txt`: Detailed execution log (when using run_verbose.sh)

### Development Tips
- All paths are relative to project root for portability
- Use `init_project.py` after moving project to new location
- Check `config.yaml` for customizable parameters
- Models need significant disk space when fully loaded (~15GB for LLaVA-7B)
- First run will download models automatically to cache directory
- Use `run_verbose.sh` for detailed logging during development
- Use `setup_model_cache.sh` to configure local model storage

### Hardware Requirements
- **Minimum**: 16GB RAM, 8GB VRAM GPU (optional)
- **Recommended**: 32GB RAM, 16GB+ VRAM GPU
- **Disk Space**: 100GB+ for models and processing
- CPU-only mode available but significantly slower

### Memory Requirements by Model
- **LLaVA-7B Float32**: ~26GB VRAM
- **LLaVA-7B Float16**: ~13GB VRAM  
- **LLaVA-7B 8-bit**: ~7GB VRAM
- **LLaVA-7B 4-bit**: ~4GB VRAM

### Performance Benchmarks
| Video Length | Resolution | Shots | GPU Processing | CPU Processing |
|-------------|------------|-------|----------------|----------------|
| 30 seconds  | 720p       | 10    | ~15 seconds    | ~2 minutes     |
| 5 minutes   | 1080p      | 50    | ~2 minutes     | ~15 minutes    |
| 12 minutes  | 1080p      | 138   | ~8 minutes     | ~45 minutes    |

*Benchmarks on NVIDIA RTX 4500 Ada Generation (20GB) vs AMD Ryzen 9 5900X*

### Common Issues
- **OOM Errors**: Reduce `max_frames_per_batch` in config.yaml or enable quantization
- **Slow Processing**: Enable GPU in config.yaml (`use_gpu: true`)
- **Model Download Fails**: Check disk space and internet connection
- **FFmpeg Errors**: Ensure FFmpeg is installed (`sudo apt install ffmpeg`)
- **CUDA Out of Memory**: Use model quantization (`load_in_8bit: true` or `load_in_4bit: true`)
- **No Frames Extracted**: Check video integrity with `ffmpeg -v error -i video.mp4 -f null -`
- **Disk Space Error**: Use `setup_model_cache.sh` to configure local cache directory

## API Usage Examples

### Basic Pipeline Usage
```python
from src.main import VideoAnalysisPipeline

# Initialize pipeline
pipeline = VideoAnalysisPipeline("config.yaml")

# Analyze video
results = pipeline.analyze_video("input_video.mp4")

# Access results
shots = results['shots']
scenes = results['scenes']
print(f"Found {len(shots)} shots and {len(scenes)} scenes")
```

### Direct Model Usage
```python
from src.models.llava import LLaVAAnalyzer

# Initialize model
config = {
    "model": "llava-hf/llava-1.5-7b-hf",
    "device": "cuda:0",
    "use_gpu": True,
    "load_in_8bit": False,
    "torch_dtype": "float16"
}
analyzer = LLaVAAnalyzer(config)

# Analyze image
description = analyzer.analyze_single_image(
    "frame.jpg",
    "Describe the cinematography in this shot"
)
```

### Custom Configuration
```python
# Load and modify configuration
import yaml

with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

# Modify settings
config['scene_construction']['batch_size'] = 20
config['shot_detection']['min_shot_duration'] = 1.0

# Use custom config
pipeline = VideoAnalysisPipeline()
pipeline.update_config(config)
```

## Advanced Configuration

### Configuration Hierarchy
1. Command line: `--config path/to/config.yaml`
2. Local override: `config.local.yaml` (git-ignored)
3. Default: `config.yaml`

### Key Configuration Options
```yaml
# For low-memory systems
scene_construction:
  batch_size: 1
  max_frames_per_batch: 1
  model_config:
    load_in_8bit: true
    torch_dtype: "float16"

# For high-performance systems  
pipeline:
  batch_size: 128
  parallel_stages: true
shot_detection:
  model_name: "transnetv2"
  transnetv2:
    batch_size: 256

# For quality-first analysis
shot_detection:
  min_shot_duration: 0.3
  confidence_threshold: 0.3
scene_construction:
  temperature: 0.3
  max_new_tokens: 1024
```

### Environment Variables
```bash
# Override configuration
export HENDRIX_BATCH_SIZE=64
export HENDRIX_DEVICE=cuda:1
export HENDRIX_LOG_LEVEL=DEBUG

# Model cache (important for avoiding disk space issues)
export HF_HOME=/dev-work/Hendrix_Video_Analysis/cache/huggingface
export TRANSFORMERS_CACHE=/dev-work/Hendrix_Video_Analysis/cache/transformers
export TORCH_HOME=/dev-work/Hendrix_Video_Analysis/cache/torch

# Performance tuning
export OMP_NUM_THREADS=16
export CUDA_VISIBLE_DEVICES=0,1

# Enable mixed precision for better GPU utilization
export TORCH_ALLOW_TF32=1
```

## Model Information

### Available Models
- **TransNetV2**: State-of-the-art shot boundary detection (~100MB)
  - Detects hard cuts and gradual transitions
  - 97%+ accuracy on standard benchmarks
- **LLaVA-1.5-7B**: Vision-language understanding (~13GB in fp16)
  - Multimodal scene analysis
  - Natural language descriptions
- **LLaVA-1.5-13B**: Higher quality scene analysis (~26GB in fp16)
- **Frame Difference**: Traditional CV-based shot detection (built-in fallback)

### Model Variants and Installation
```bash
# Install TransNetV2
pip install transnetv2-pytorch

# Pre-download models (recommended)
python download_models_auto.py

# Or manually download specific models
python -c "from transformers import AutoModel; AutoModel.from_pretrained('llava-hf/llava-1.5-7b-hf')"
```

## Advanced Performance Optimization

### GPU Optimization
```bash
# Enable PyTorch compile for faster inference (requires PyTorch 2.0+)
export TORCH_COMPILE_BACKEND=inductor

# Monitor GPU usage in real-time
watch -n 0.5 nvidia-smi

# Profile GPU memory usage
python -m torch.utils.bottleneck src/main.py video.mp4
```

### Memory Optimization
```yaml
# For very large videos or limited memory
video_processing:
  sequential_read: true
  frame_buffer_size: 100
scene_construction:
  gradient_checkpointing: true
  aggressive_cleanup: true
```

### Distributed Processing
```python
# Using Ray for distributed processing (requires ray installation)
from examples.distributed_processing import DistributedPipeline

pipeline = DistributedPipeline(num_workers=4)
results = pipeline.process_videos_parallel(video_list)
```

## Docker Support
```bash
# Build Docker image
docker build -t hendrix-video-analysis .

# Run container with GPU support
docker run --gpus all -v $(pwd)/videos:/app/videos \
    -v $(pwd)/output:/app/output \
    hendrix-video-analysis video.mp4
```

## Example Usage Patterns

### Download and Analyze YouTube Videos
```bash
# Download video
yt-dlp -f "best[height<=1080]" -o "videos/%(title)s.%(ext)s" "https://www.youtube.com/watch?v=VIDEO_ID"

# Analyze downloaded video
python src/main.py "videos/video_title.mp4"
```

### Batch Processing Multiple Videos
```python
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

def process_video(video_path):
    pipeline = VideoAnalysisPipeline()
    return pipeline.analyze_video(video_path)

# Process videos in parallel
video_files = Path("videos/").glob("*.mp4")
with ProcessPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(process_video, video_files))
```

### Custom Prompts for Scene Analysis
```python
# Override default prompts
from src.utils.prompt_templates import SCENE_CONSTRUCTION_PROMPT

custom_prompts = {
    "shot_description": "Analyze this frame for action movie elements...",
    "scene_construction": SCENE_CONSTRUCTION_PROMPT.format(shot_range="1-50")
}

pipeline = VideoAnalysisPipeline()
pipeline.config['scene_construction']['prompts'] = custom_prompts
```

### Performance Monitoring
```python
import time
import psutil

# Monitor resource usage during processing
start_time = time.time()
start_memory = psutil.Process().memory_info().rss / 1e9

results = pipeline.analyze_video("video.mp4")

end_time = time.time()
end_memory = psutil.Process().memory_info().rss / 1e9

print(f"Processing time: {end_time - start_time:.2f}s")
print(f"Memory used: {end_memory - start_memory:.2f}GB")
```

## Troubleshooting Quick Reference

### Diagnostic Commands
```bash
# Verify video integrity
ffmpeg -v error -i video.mp4 -f null -

# Monitor GPU usage
watch -n 1 nvidia-smi

# Check available disk space
df -h output/ cache/

# View detailed logs
tail -f pipeline_verbose_log.txt

# Analyze results after processing
python analyze_results.py
```

### Common Fixes
```yaml
# Fix CUDA OOM errors
scene_construction:
  model_config:
    load_in_8bit: true
  batch_size: 1

# Fix slow CPU processing  
video_processing:
  resize_frames: true
  target_size: [640, 480]

# Fix model download issues
models:
  download:
    retry_count: 5
    timeout: 7200
```

## Utility Scripts

### Model Management
- `setup_model_cache.sh`: Configure local model cache directories
- `download_models_auto.py`: Download models non-interactively
- `download_models.py`: Interactive model download with prompts

### Analysis Tools
- `analyze_results.py`: Summarize pipeline output with statistics
- `run_verbose.sh`: Run pipeline with detailed logging

### Development Tools
- `init_project.py`: Initialize project after cloning/moving
- `setup_env.sh`: Create and configure virtual environment
- `src/utils/verify_installation.py`: Check all dependencies
- `tests/create_test_video.py`: Generate synthetic test videos with multiple shots

## Contributing

### Development Setup
```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run pre-commit on all files
pre-commit run --all-files
```

### Commit Convention
Use conventional commits format:
- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `test:` Test additions/changes
- `perf:` Performance improvements
- `refactor:` Code refactoring

### Testing Requirements
- All new features must include tests
- Maintain test coverage above 80%
- Use pytest fixtures for reusable test components
- Mock external API calls and model inference

## Recent Updates

- **TransNetV2 Integration**: Now using neural network-based shot detection for better accuracy
- **Local Model Caching**: Models stored in project directory to avoid disk space issues
- **Improved LLaVA Support**: Full model configuration with quantization options
- **Performance Monitoring**: Added detailed logging and resource tracking
- **YouTube Support**: Can download and analyze videos directly from YouTube URLs