# Troubleshooting Guide

This guide helps you resolve common issues with the Hendrix Video Analysis Pipeline.

## Quick Diagnostics

Run the diagnostic script first:
```bash
python src/utils/diagnose.py
```

This checks:
- Python version and dependencies
- GPU availability and CUDA setup
- Model accessibility
- FFmpeg installation
- Memory availability

## Common Issues and Solutions

### Installation Issues

#### Issue: "ModuleNotFoundError: No module named 'cv2'"
**Solution**: OpenCV not installed properly
```bash
pip uninstall opencv-python opencv-python-headless
pip install opencv-python==4.8.1.78
```

#### Issue: "FFmpeg not found"
**Solution**: Install or add FFmpeg to PATH
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Check installation
ffmpeg -version
```

#### Issue: "CUDA out of memory"
**Solution**: Reduce batch sizes or use CPU
```yaml
# config.yaml
scene_construction:
  batch_size: 5  # Reduce from 10
  max_frames_per_batch: 5  # Reduce from 10
  model_config:
    load_in_8bit: true  # Enable 8-bit quantization
```

### Model Loading Issues

#### Issue: "Connection error downloading model"
**Solution**: Retry with different settings
```bash
# Use different mirror
export HF_ENDPOINT=https://hf-mirror.com

# Increase timeout
export HF_HUB_DOWNLOAD_TIMEOUT=3600

# Manual download
python -c "from transformers import AutoModel; AutoModel.from_pretrained('llava-hf/llava-1.5-7b-hf', resume_download=True)"
```

#### Issue: "Model requires more GPU memory than available"
**Solution**: Use quantization or CPU
```yaml
scene_construction:
  model_config:
    load_in_4bit: true  # Extreme quantization
    # OR
    device_map: "cpu"  # Use CPU instead
```

### Processing Errors

#### Issue: "ValueError: Shot duration is negative"
**Cause**: Corrupted video or timestamp issues
**Solution**: 
```bash
# Verify video integrity
ffmpeg -v error -i video.mp4 -f null -

# Re-encode video
ffmpeg -i corrupted.mp4 -c:v libx264 -c:a aac fixed.mp4
```

#### Issue: "JSONDecodeError in scene construction"
**Cause**: Model output parsing failed
**Solution**: Update prompt or use fallback
```yaml
scene_construction:
  prompts:
    use_simple_format: true  # Simpler output format
  fallback_on_error: true
```

#### Issue: "Pipeline hangs during processing"
**Diagnosis**:
```bash
# Check system resources
htop  # CPU/Memory
nvidia-smi  # GPU

# Enable debug logging
export HENDRIX_LOG_LEVEL=DEBUG
python src/main.py video.mp4 --debug
```

### Performance Issues

#### Issue: "Processing is extremely slow"
**Solutions**:

1. **Check GPU utilization**:
```bash
watch -n 1 nvidia-smi
# GPU-Util should be >80%
```

2. **Optimize configuration**:
```yaml
# Faster processing settings
shot_detection:
  min_shot_duration: 1.0  # Skip micro-shots
  
video_processing:
  resize_frames: true
  target_size: [854, 480]  # Lower resolution
  
scene_construction:
  batch_size: 20  # Increase if memory allows
```

3. **Use profiling**:
```bash
python src/main.py video.mp4 --profile
```

#### Issue: "Memory leak - RAM usage keeps growing"
**Solution**: Enable aggressive cleanup
```yaml
pipeline:
  cleanup_intermediate: true
  
advanced:
  memory_management:
    gc_collect_frequency: 100  # Frames
    clear_cuda_cache: true
```

### Output Issues

#### Issue: "No output files generated"
**Check**:
```bash
# Permissions
ls -la output/

# Disk space
df -h

# Process completion
tail -n 50 pipeline.log
```

#### Issue: "Keyframes are black or corrupted"
**Solution**: Check video codec compatibility
```bash
# Get video info
ffprobe -v quiet -print_format json -show_streams video.mp4

# Convert to compatible format
ffmpeg -i input.mp4 -c:v libx264 -pix_fmt yuv420p output.mp4
```

## Platform-Specific Issues

### Linux

#### Issue: "libGL.so.1: cannot open shared object file"
```bash
# Install OpenGL libraries
sudo apt-get update
sudo apt-get install libgl1-mesa-glx
```

#### Issue: "Permission denied accessing GPU"
```bash
# Add user to video group
sudo usermod -a -G video $USER
# Logout and login again
```

### macOS

#### Issue: "Illegal hardware instruction"
**Solution**: Incompatible PyTorch version
```bash
# Install macOS-specific PyTorch
pip uninstall torch torchvision
pip install torch torchvision
```

#### Issue: "VideoCapture not working"
**Solution**: Grant camera permissions or use different backend
```python
# In video_processor.py
cv2.VideoCapture(video_path, cv2.CAP_AVFOUNDATION)
```

### Windows (WSL2)

#### Issue: "Cannot access GPU in WSL2"
**Solution**: Ensure WSL2 GPU support
```bash
# Check WSL version
wsl --version
# Should be 2.0.0 or higher

# Install CUDA in WSL2
wget https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-keyring_1.0-1_all.deb
sudo dpkg -i cuda-keyring_1.0-1_all.deb
sudo apt-get update
sudo apt-get -y install cuda
```

## Error Messages Reference

### "RuntimeError: CUDA error: out of memory"
- Reduce batch sizes
- Enable model quantization
- Use gradient checkpointing
- Clear CUDA cache between videos

### "AssertionError: No frames extracted"
- Check video file integrity
- Verify FFmpeg can read the video
- Check start/end timestamps
- Try different decoder settings

### "HTTPError: 503 Service Unavailable"
- Model hosting service is down
- Use local model cache
- Try alternative model sources
- Check internet connectivity

### "ValueError: Expected 4D tensor, got 3D"
- Frame preprocessing issue
- Check color channel order (RGB vs BGR)
- Verify frame dimensions
- Check batch dimension

## Advanced Debugging

### Enable Verbose Logging
```python
# In your script
import logging
logging.basicConfig(level=logging.DEBUG)

# Or via environment
export PYTHONLOGGING=DEBUG
```

### Memory Profiling
```python
# Add to main.py
import tracemalloc
tracemalloc.start()

# After processing
current, peak = tracemalloc.get_traced_memory()
print(f"Current memory usage: {current / 10**6:.1f} MB")
print(f"Peak memory usage: {peak / 10**6:.1f} MB")
```

### GPU Debugging
```python
# Monitor GPU memory
import torch
print(f"Allocated: {torch.cuda.memory_allocated() / 1e9:.2f} GB")
print(f"Reserved: {torch.cuda.memory_reserved() / 1e9:.2f} GB")

# Force synchronization
torch.cuda.synchronize()
```

### Process Monitoring
```bash
# Monitor system resources
pip install gpustat
gpustat -i 1

# Profile specific function
python -m cProfile -s cumulative src/main.py video.mp4
```

## Getting Help

If you can't resolve your issue:

1. **Check existing issues**: [GitHub Issues](https://github.com/yourusername/Hendrix_Video_Analysis/issues)

2. **Create detailed bug report**:
```bash
python src/utils/create_bug_report.py
```

This generates `bug_report.txt` with:
- System information
- Configuration
- Error logs
- Environment details

3. **Ask for help**:
- Include the bug report
- Provide sample video (if possible)
- Describe expected vs actual behavior
- List steps to reproduce

## Common Warnings (Safe to Ignore)

These warnings are typically harmless:

- `UserWarning: The given NumPy array is not writeable` - PyTorch optimization
- `FutureWarning: Passing (type, 1) or '1type'` - NumPy deprecation
- `Some weights of the model checkpoint were not used` - Normal for fine-tuned models

## Health Check Script

Create a health check script:

```python
#!/usr/bin/env python3
# health_check.py

import sys
import torch
import cv2
import transformers

print("System Health Check")
print("=" * 50)

# Check Python
print(f"Python: {sys.version}")

# Check GPU
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

# Check dependencies
print(f"PyTorch: {torch.__version__}")
print(f"Transformers: {transformers.__version__}")
print(f"OpenCV: {cv2.__version__}")

print("=" * 50)
print("Health check complete!")
```

Run regularly to ensure system readiness:
```bash
python health_check.py
```