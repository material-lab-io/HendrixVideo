# Configuration Guide

Comprehensive guide to configuring the Hendrix Video Analysis Pipeline for your specific needs.

## Configuration Overview

The pipeline uses a hierarchical YAML configuration system with sensible defaults and extensive customization options.

## Configuration File Location

The pipeline looks for configuration in the following order:
1. Command line: `--config path/to/config.yaml`
2. Local override: `config.local.yaml` (git-ignored)
3. Default: `config.yaml`

## Complete Configuration Reference

```yaml
# Pipeline Configuration
pipeline:
  # General pipeline settings
  name: "hendrix_video_analysis"
  version: "0.1.0"
  
  # Processing settings
  batch_size: 32              # Global batch size
  num_workers: 8              # Parallel workers
  device: "auto"              # auto, cuda, cpu
  
  # Stage control
  stages:
    shot_detection: true
    scene_construction: true
    cinematic_analysis: false  # Disabled by default
  
  # Resume and checkpointing
  enable_checkpoints: true
  checkpoint_dir: "checkpoints"
  
  # Performance settings
  parallel_stages: false      # Run stages concurrently
  cleanup_intermediate: true  # Delete temp files
  
# Video Processing Configuration
video_processing:
  # FFmpeg settings
  ffmpeg_path: "ffmpeg"       # Path to ffmpeg binary
  ffprobe_path: "ffprobe"     # Path to ffprobe binary
  
  # Frame extraction
  decode_threads: 8           # FFmpeg decode threads
  hwaccel: "auto"            # Hardware acceleration
  
  # Frame processing
  resize_frames: false        # Resize for processing
  target_size: [1280, 720]   # Target resolution
  color_space: "rgb"         # rgb, bgr, gray
  
  # Memory management
  frame_buffer_size: 100     # Max frames in memory
  use_sequential_read: true  # Stream processing
  
# Shot Detection Configuration
shot_detection:
  # Detector selection
  detector: "transnetv2"     # transnetv2, autoshot, frame_diff
  
  # Common settings
  min_shot_duration: 0.5     # Minimum shot length (seconds)
  max_shot_duration: 300     # Maximum shot length (seconds)
  
  # TransNetV2 settings
  transnetv2:
    model_path: "cache/transnetv2_weights.pth"
    threshold: 0.5           # Detection threshold
    batch_size: 64          # Model batch size
    device: "cuda:0"        # Model device
    
  # Frame difference settings
  frame_diff:
    threshold: 0.3          # Difference threshold
    window_size: 5          # Comparison window
    metric: "mae"           # mae, mse, ssim
    
  # Keyframe extraction
  keyframe_extraction:
    method: "middle"        # middle, first, last, best
    quality: 90            # JPEG quality (1-100)
    format: "jpg"          # jpg, png
    
# Scene Construction Configuration  
scene_construction:
  # Model selection
  model: "llava-hf/llava-1.5-7b-hf"
  
  # Model loading settings
  model_config:
    torch_dtype: "float16"  # float32, float16, bfloat16
    device_map: "auto"      # auto, cuda:0, cpu
    low_cpu_mem_usage: true
    load_in_8bit: false     # Quantization
    load_in_4bit: false
    
  # Processing settings
  batch_size: 10           # Shots per batch
  max_frames_per_batch: 10 # Frames to process together
  use_gpu: true
  device: "cuda:0"
  
  # Inference settings
  temperature: 0.7         # Generation temperature
  max_new_tokens: 512      # Max response length
  do_sample: false         # Sampling vs greedy
  
  # Scene grouping
  scene_clustering:
    method: "temporal"     # temporal, semantic, hybrid
    min_scene_shots: 1     # Minimum shots per scene
    max_scene_duration: 180 # Maximum scene duration
    
  # Prompt configuration
  prompts:
    shot_description: "Describe this video frame..."
    scene_construction: "Group these shots into scenes..."
    
# Cinematic Analysis Configuration
cinematic_analysis:
  enabled: false           # Enable/disable stage
  
  # Analysis modules
  modules:
    shot_scale: true       # Detect shot scales
    camera_movement: true  # Detect camera motion
    color_analysis: true   # Analyze color palette
    composition: true      # Analyze composition
    
  # Model settings
  model: "cinematic-vlm-base"
  device: "cuda:0"
  batch_size: 5
  
# Output Configuration
output:
  # Output directory
  base_dir: "output"
  create_subdirs: true     # Create subdirectories
  
  # File naming
  timestamp_format: "%Y%m%d_%H%M%S"
  include_timestamp: true
  
  # Output formats
  formats:
    json: true            # JSON output
    csv: false            # CSV summaries
    html: false           # HTML reports
    
  # Result files
  shots_file: "shots.json"
  scenes_file: "scenes.json"
  analysis_file: "analysis.json"
  
  # Compression
  compress_output: false   # Gzip JSON files
  compression_level: 6     # 1-9
  
# Logging Configuration
logging:
  # Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
  level: "INFO"
  
  # Console logging
  console:
    enabled: true
    format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    colorize: true
    
  # File logging
  file:
    enabled: true
    path: "logs/pipeline.log"
    max_size: "10MB"
    backup_count: 5
    format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
  # Performance metrics
  metrics:
    enabled: true
    log_interval: 10      # Seconds
    include_memory: true
    include_gpu: true
    
# Model Management
models:
  # Cache directory
  cache_dir: "cache/models"
  
  # Model downloading
  download:
    retry_count: 3
    timeout: 3600         # 1 hour
    verify_ssl: true
    
  # Memory management
  keep_in_memory: true    # Don't unload between videos
  clear_cache_on_exit: false
  
# Advanced Settings
advanced:
  # Error handling
  error_handling:
    fail_fast: false      # Stop on first error
    retry_failed: true    # Retry failed operations
    max_retries: 3
    
  # Resource limits
  resource_limits:
    max_memory_gb: 32     # Maximum RAM usage
    max_gpu_memory_gb: 24 # Maximum VRAM usage
    
  # Profiling
  profiling:
    enabled: false
    output_dir: "profiling"
    trace_memory: true
    
  # Experimental features
  experimental:
    multi_gpu: false      # Multi-GPU support
    distributed: false    # Distributed processing
    compile_models: false # Torch compile
```

## Common Configuration Scenarios

### Low-Memory System
```yaml
# Optimize for 8GB RAM, no GPU
pipeline:
  batch_size: 8
  cleanup_intermediate: true

video_processing:
  frame_buffer_size: 50
  resize_frames: true
  target_size: [854, 480]

scene_construction:
  batch_size: 1
  max_frames_per_batch: 1
  use_gpu: false
  device: "cpu"
  model_config:
    load_in_8bit: true
```

### High-Performance Server
```yaml
# Optimize for speed with 64GB RAM, RTX 4090
pipeline:
  batch_size: 128
  num_workers: 16
  parallel_stages: true

shot_detection:
  transnetv2:
    batch_size: 256

scene_construction:
  batch_size: 20
  max_frames_per_batch: 20
  model_config:
    torch_dtype: "float16"
```

### Quality-First Analysis
```yaml
# Maximize analysis quality
shot_detection:
  min_shot_duration: 0.3
  threshold: 0.3  # More sensitive

scene_construction:
  temperature: 0.3  # Less random
  max_new_tokens: 1024  # Longer descriptions

keyframe_extraction:
  quality: 100
  format: "png"
```

## Environment Variables

Override configuration with environment variables:

```bash
# Pipeline settings
export HENDRIX_BATCH_SIZE=64
export HENDRIX_DEVICE=cuda:1
export HENDRIX_LOG_LEVEL=DEBUG

# Model settings
export HF_HOME=/path/to/models
export TRANSFORMERS_CACHE=/path/to/cache

# Performance
export OMP_NUM_THREADS=16
export CUDA_VISIBLE_DEVICES=0,1
```

## Configuration Validation

The pipeline validates configuration on startup:

```python
# Validation checks
- Required fields present
- Valid model names
- Accessible paths
- Device availability
- Memory requirements
```

## Dynamic Configuration

### Runtime Updates
```python
# Update configuration during runtime
pipeline = VideoAnalysisPipeline(config)
pipeline.update_config({
    "scene_construction": {
        "batch_size": 20
    }
})
```

### Per-Video Configuration
```python
# Override for specific video
pipeline.analyze_video(
    "video.mp4",
    config_overrides={
        "shot_detection": {
            "min_shot_duration": 1.0
        }
    }
)
```

## Configuration Best Practices

1. **Start with Defaults**: The default configuration works well for most videos
2. **Test Incrementally**: Change one setting at a time
3. **Monitor Performance**: Use metrics to guide optimization
4. **Use Local Overrides**: Create `config.local.yaml` for machine-specific settings
5. **Document Changes**: Comment your configuration changes

## Troubleshooting Configuration

### Common Issues

**GPU Not Detected**
```yaml
# Force CPU mode
scene_construction:
  use_gpu: false
  device: "cpu"
```

**Out of Memory**
```yaml
# Reduce memory usage
pipeline:
  batch_size: 8
scene_construction:
  max_frames_per_batch: 5
  model_config:
    load_in_8bit: true
```

**Slow Processing**
```yaml
# Speed optimizations
shot_detection:
  min_shot_duration: 1.0
video_processing:
  resize_frames: true
  target_size: [640, 480]
```

## Configuration Templates

Find pre-configured templates in `config_templates/`:
- `low_memory.yaml` - For systems with <16GB RAM
- `high_performance.yaml` - For powerful GPUs
- `quality_analysis.yaml` - For detailed analysis
- `batch_processing.yaml` - For processing many videos
- `cloud_deployment.yaml` - For cloud environments