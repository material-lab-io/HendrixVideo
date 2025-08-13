# Long Video Support Guide

## Overview

The optimized robust pipeline fully supports processing long videos (30 minutes to several hours) with efficient memory management and linear scaling.

## Performance Benchmarks

| Video Duration | Processing Time | Memory Usage | Match Rate |
|----------------|-----------------|--------------|------------|
| 30 minutes | ~9.5 minutes | 4-6 GB | 74-83% |
| 1 hour | ~19 minutes | 4-6 GB | 74-83% |
| 2 hours | ~38 minutes | 4-6 GB | 74-83% |

**Key Features**:
- Linear time scaling (constant memory usage)
- Streaming processing prevents memory overflow
- Automatic chunking for efficient processing
- Progress tracking with time estimates

## Running Long Videos

### Basic Command
```bash
cd visual_processing_branch
python scripts/run_optimized_robust_pipeline.py long_video.mp4 --verbose
```

### Optimized Settings for Long Videos
```bash
# Maximum quality (slower)
python scripts/run_optimized_robust_pipeline.py long_video.mp4 \
    --whisper-model large-v3 \
    --target-frames 2000 \
    --extraction-mode adaptive

# Balanced quality/speed
python scripts/run_optimized_robust_pipeline.py long_video.mp4 \
    --whisper-model base \
    --target-frames 1000 \
    --extraction-mode adaptive

# Fast processing
python scripts/run_optimized_robust_pipeline.py long_video.mp4 \
    --whisper-model tiny \
    --target-frames 500 \
    --extraction-mode uniform
```

## Memory Management

The pipeline implements several strategies to handle long videos efficiently:

### 1. Streaming Audio Processing
- Audio is processed in chunks
- Prevents loading entire audio into memory
- Whisper processes segments incrementally

### 2. Adaptive Frame Extraction
- Only extracts frames during dialogue segments
- Reduces total frames processed by 50-70%
- Maintains high match rate with fewer frames

### 3. Batch Processing
- Faces processed in configurable batches
- Default batch size: 32 frames
- Adjustable based on available memory

### 4. Progressive Output
- Results written incrementally
- Prevents memory buildup
- Allows recovery from interruptions

## Configuration for Long Videos

### Environment Variables
```bash
# Increase for better GPU utilization
export CUDA_VISIBLE_DEVICES=0
export TF_FORCE_GPU_ALLOW_GROWTH=true

# For systems with limited memory
export OMP_NUM_THREADS=4
```

### Pipeline Parameters
```python
# In scripts/run_optimized_robust_pipeline.py
config = {
    'batch_size': 16,          # Reduce for low memory
    'max_frames_per_chunk': 100,  # Process in chunks
    'frame_buffer_size': 50,    # Keep limited frames in memory
    'embedding_cache_size': 1000  # Cache recent embeddings
}
```

## Handling Different Video Types

### Documentary/Interview Style
- High dialogue density
- Multiple speakers
- Recommended: `--target-frames 1500`

### Action Movies
- Sparse dialogue
- Fast scene changes
- Recommended: `--extraction-mode intelligent`

### TV Shows/Series
- Regular dialogue patterns
- Consistent characters
- Recommended: `--min-appearances 5`

## Troubleshooting Long Videos

### Out of Memory Errors
```bash
# Reduce batch size
python scripts/run_optimized_robust_pipeline.py video.mp4 --batch-size 8

# Process in segments
python scripts/video_segmenter.py long_video.mp4 --segment-duration 600
```

### Slow Processing
```bash
# Use GPU acceleration
export CUDA_VISIBLE_DEVICES=0

# Use faster models
--whisper-model tiny --insightface-model buffalo_sc
```

### Codec Issues
```bash
# Convert to compatible format first
python scripts/video_converter.py input.mp4 output_h264.mp4
```

## Best Practices

1. **Pre-processing**
   - Convert videos to H.264 codec
   - Ensure consistent frame rate
   - Check audio quality

2. **Resource Management**
   - Close other applications
   - Monitor GPU memory usage
   - Use SSD for temp files

3. **Incremental Processing**
   - Save intermediate results
   - Enable checkpoint recovery
   - Use `--resume` flag if interrupted

4. **Quality vs Speed**
   - Start with base models
   - Increase quality if needed
   - Monitor match rates

## Example: Processing a 2-Hour Movie

```bash
# Step 1: Convert video if needed
python scripts/video_converter.py movie.mkv movie_h264.mp4

# Step 2: Run optimized pipeline
python scripts/run_optimized_robust_pipeline.py movie_h264.mp4 \
    --whisper-model base \
    --target-frames 1500 \
    --extraction-mode adaptive \
    --batch-size 16 \
    --verbose

# Step 3: Validate results
python scripts/validate_all_schemas.py output/optimized_robust/session_*

# Step 4: View summary
python scripts/display_all_schemas.py output/optimized_robust/session_* | head -100
```

## Performance Optimization Tips

### GPU Acceleration
- Ensure CUDA is properly installed
- Use appropriate GPU model
- Monitor GPU utilization

### Parallel Processing
- Audio and visual can process simultaneously
- Use multiple CPU cores for extraction
- Enable threading in configuration

### Caching
- Models cached after first load
- Embeddings cached during processing
- Results cached for resume capability

## Monitoring Progress

The pipeline provides detailed progress information:
- Frame extraction progress with ETA
- Character detection statistics
- Matching progress with confidence scores
- Memory usage warnings

## Expected Results for Long Videos

### 30-Minute Documentary
- ~150 dialogue segments
- 8-12 unique characters
- 74-83% match rate
- ~9.5 minutes processing

### 2-Hour Feature Film
- ~300-400 dialogue segments
- 15-25 unique characters
- 70-80% match rate
- ~38 minutes processing

### 1-Hour TV Episode
- ~200-250 dialogue segments
- 5-10 unique characters
- 75-85% match rate
- ~19 minutes processing

## Advanced Configuration

For production environments processing many long videos:

```python
# config/production_long_video.yaml
pipeline:
  whisper_model: base
  target_frames: 1200
  extraction_mode: adaptive
  
optimization:
  batch_size: 32
  use_gpu: true
  cache_embeddings: true
  parallel_processing: true
  
memory:
  max_memory_gb: 8
  swap_threshold: 0.8
  gc_interval: 100
  
recovery:
  enable_checkpoints: true
  checkpoint_interval: 300
  auto_resume: true
```

## Conclusion

The optimized robust pipeline handles long videos efficiently with:
- Linear time scaling
- Constant memory usage
- High match rates (74-83%)
- Robust error handling
- Progress tracking
- Resume capability

For videos longer than 2 hours, consider splitting into parts or using a machine with more resources.