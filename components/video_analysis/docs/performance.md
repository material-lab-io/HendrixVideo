# Performance Guide

Optimize the Hendrix Video Analysis Pipeline for maximum performance and efficiency.

## Performance Overview

The pipeline's performance depends on three main factors:
1. **Hardware capabilities** (GPU, CPU, RAM, storage)
2. **Video characteristics** (resolution, length, complexity)
3. **Configuration settings** (batch sizes, model choices)

## Quick Performance Wins

### 1. Enable GPU Acceleration
```yaml
# config.yaml
scene_construction:
  use_gpu: true
  device: "cuda:0"
  fp16: true  # Use half precision
```

### 2. Optimize Batch Sizes
```yaml
pipeline:
  batch_size: 32  # Increase for better GPU utilization

scene_construction:
  max_frames_per_batch: 10  # Adjust based on VRAM
```

### 3. Use Fast Storage
- Input videos on SSD
- Working directory on NVMe
- Separate drives for I/O parallelism

## Detailed Optimization Guide

### Shot Detection Optimization

#### TransNetV2 Settings
```yaml
shot_detection:
  detector: "transnetv2"
  batch_size: 64  # Increase for faster processing
  num_workers: 8  # Parallel frame loading
  threshold: 0.5  # Higher = fewer false positives
  min_shot_duration: 0.5  # Filter noise
```

#### Frame Difference Fallback
```yaml
shot_detection:
  frame_diff_threshold: 0.3  # Lower = more sensitive
  window_size: 5  # Frames to compare
  use_adaptive_threshold: true
```

### Scene Construction Optimization

#### Model Loading
```python
# Optimize model loading in config
scene_construction:
  model: "llava-hf/llava-1.5-7b-hf"
  load_in_8bit: false  # True for less VRAM, slower
  load_in_4bit: false  # True for minimal VRAM, slowest
  torch_dtype: "float16"  # Half precision
  low_cpu_mem_usage: true
```

#### Batch Processing
```yaml
scene_construction:
  max_frames_per_batch: 10
  prefetch_factor: 2  # Preload next batch
  pin_memory: true  # Faster GPU transfer
```

### Memory Management

#### CPU Memory
```yaml
video_processing:
  frame_buffer_size: 100  # Frames in memory
  use_sequential_read: true  # Don't load entire video
  
pipeline:
  cleanup_intermediate: true  # Delete temp files
  compress_keyframes: true  # JPEG quality 85
```

#### GPU Memory
```python
# Automatic mixed precision
scene_construction:
  use_amp: true  # Automatic mixed precision
  gradient_checkpointing: true  # Trade compute for memory
  
# Clear cache periodically
import torch
torch.cuda.empty_cache()
```

## Profiling and Benchmarking

### Built-in Profiler
```bash
python src/main.py video.mp4 --profile
```

Output:
```
Stage Timings:
- Shot Detection: 45.3s (23,000 frames @ 507 fps)
- Scene Construction: 523.2s (605 shots @ 1.16 shots/sec)
- Total Pipeline: 568.5s

Resource Usage:
- Peak RAM: 18.4 GB
- Peak VRAM: 13.2 GB
- Avg CPU: 45%
- Avg GPU: 78%
```

### Custom Profiling
```python
import time
import psutil
import GPUtil

class PerformanceMonitor:
    def __init__(self):
        self.start_time = time.time()
        self.start_memory = psutil.virtual_memory().used
        
    def checkpoint(self, name):
        elapsed = time.time() - self.start_time
        memory = psutil.virtual_memory().used
        gpu = GPUtil.getGPUs()[0] if GPUtil.getGPUs() else None
        
        print(f"{name}:")
        print(f"  Time: {elapsed:.2f}s")
        print(f"  RAM: {(memory - self.start_memory) / 1e9:.2f} GB")
        if gpu:
            print(f"  VRAM: {gpu.memoryUsed / 1024:.2f} GB")
```

## Performance Tuning by Video Type

### Short Videos (<5 minutes)
```yaml
# Optimize for quality
shot_detection:
  min_shot_duration: 0.3
  threshold: 0.4

scene_construction:
  max_frames_per_batch: 20  # Process more at once
```

### Long Videos (>30 minutes)
```yaml
# Optimize for speed
shot_detection:
  min_shot_duration: 1.0  # Skip micro-shots
  sample_rate: 2  # Process every 2nd frame

scene_construction:
  max_frames_per_batch: 5  # Smaller batches
  skip_similar_frames: true
```

### High Resolution (4K+)
```yaml
video_processing:
  resize_frames: true
  target_size: [1920, 1080]  # Downscale for processing
  
keyframe_extraction:
  quality: 85  # Lower quality for smaller files
```

## Parallel Processing

### Multi-Video Processing
```python
from concurrent.futures import ProcessPoolExecutor
import subprocess

def process_video(video_path):
    cmd = f"python src/main.py {video_path}"
    subprocess.run(cmd, shell=True)

# Process 4 videos in parallel
videos = ["video1.mp4", "video2.mp4", "video3.mp4", "video4.mp4"]
with ProcessPoolExecutor(max_workers=4) as executor:
    executor.map(process_video, videos)
```

### Pipeline Parallelism
```yaml
# Enable pipeline parallelism
pipeline:
  parallel_stages: true  # Run stages concurrently
  stage_buffer_size: 50  # Shots to buffer between stages
```

## Caching Strategies

### Model Caching
```yaml
models:
  cache_dir: "/fast/ssd/model_cache"
  keep_in_memory: true  # Don't unload between videos
```

### Result Caching
```python
# Enable result caching
pipeline:
  enable_cache: true
  cache_dir: "cache/results"
  cache_ttl: 86400  # 24 hours
```

## Network and I/O Optimization

### Video Loading
```yaml
video_processing:
  decode_threads: 8  # FFmpeg threads
  input_buffer_size: 32768  # 32MB buffer
  hwaccel: "auto"  # Hardware decoding
```

### Output Writing
```yaml
output:
  compression: "gzip"  # Compress JSON
  async_write: true  # Non-blocking writes
  buffer_size: 1048576  # 1MB write buffer
```

## Common Performance Issues

### Issue: Slow Model Loading
**Solution**: Keep models in memory between runs
```python
# In main.py
MODEL_CACHE = {}

def get_model(model_name):
    if model_name not in MODEL_CACHE:
        MODEL_CACHE[model_name] = load_model(model_name)
    return MODEL_CACHE[model_name]
```

### Issue: GPU Underutilization
**Solution**: Increase batch sizes and enable prefetching
```yaml
scene_construction:
  max_frames_per_batch: 20  # Increase
  num_workers: 4  # Data loading threads
  prefetch_factor: 2
```

### Issue: Memory Leaks
**Solution**: Enable aggressive cleanup
```python
import gc
import torch

# After each video
gc.collect()
torch.cuda.empty_cache()
```

## Performance Monitoring

### Real-time Monitoring
```bash
# Terminal 1: Run pipeline
python src/main.py video.mp4

# Terminal 2: Monitor GPU
watch -n 1 nvidia-smi

# Terminal 3: Monitor system
htop
```

### Logging Performance Metrics
```yaml
logging:
  performance_metrics: true
  metric_interval: 10  # Log every 10 seconds
  include_gpu_stats: true
```

## Optimization Checklist

- [ ] GPU enabled and detected
- [ ] Appropriate batch sizes for hardware
- [ ] Fast storage for working directory
- [ ] Models cached in memory
- [ ] Parallel processing enabled where possible
- [ ] Monitoring enabled for bottleneck detection
- [ ] Configuration tuned for video characteristics

## Expected Performance

### By Hardware Tier

| Hardware | 1min Video | 10min Video | 1hr Video |
|----------|------------|-------------|-----------|
| CPU Only | 2-3 min | 20-30 min | 2-3 hrs |
| RTX 3060 | 30-45 sec | 5-8 min | 30-45 min |
| RTX 3090 | 20-30 sec | 3-5 min | 20-30 min |
| A100 | 15-20 sec | 2-3 min | 15-20 min |

### By Video Complexity

| Complexity | Shot Count | Processing Time |
|------------|------------|-----------------|
| Simple (static) | 10-50 | 5-10 min/hour |
| Medium (normal) | 200-400 | 15-25 min/hour |
| Complex (action) | 600-1000 | 30-45 min/hour |

## Advanced Techniques

### Custom Model Optimization
```python
# Compile model for faster inference (PyTorch 2.0+)
import torch
model = torch.compile(model)

# Quantization for faster inference
model = torch.quantization.quantize_dynamic(
    model, {torch.nn.Linear}, dtype=torch.qint8
)
```

### Distributed Processing
```python
# Using Ray for distributed processing
import ray

@ray.remote
def process_video_segment(video_path, start, end):
    # Process video segment
    pass

# Process in parallel
futures = []
for i in range(0, duration, segment_length):
    future = process_video_segment.remote(video, i, i + segment_length)
    futures.append(future)

results = ray.get(futures)
```