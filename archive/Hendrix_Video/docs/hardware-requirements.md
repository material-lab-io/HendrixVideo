# Hardware Requirements

Detailed hardware requirements and recommendations for optimal performance of the Hendrix Video Analysis Pipeline.

## Overview

The pipeline's performance varies significantly based on hardware configuration. GPU acceleration is strongly recommended for production use, while CPU-only mode is suitable for development and testing.

## Minimum Requirements

### CPU
- **Architecture**: x86_64 (Intel/AMD)
- **Cores**: 8 physical cores
- **Speed**: 2.5 GHz base clock
- **Examples**: Intel i7-8700, AMD Ryzen 7 2700

### Memory (RAM)
- **Capacity**: 16GB DDR4
- **Speed**: 2400 MHz or higher
- **Note**: May require swap space for long videos

### Storage
- **Type**: SATA SSD or better
- **Space**: 50GB free
- **Speed**: 500 MB/s sequential read

### GPU (Optional)
- **VRAM**: 8GB minimum
- **Architecture**: NVIDIA Pascal or newer
- **CUDA**: 11.7+ support
- **Examples**: GTX 1070, RTX 2060

## Recommended Requirements

### CPU
- **Architecture**: x86_64 (Intel/AMD)
- **Cores**: 16+ physical cores
- **Speed**: 3.5 GHz base clock
- **Examples**: Intel i9-12900K, AMD Ryzen 9 5900X

### Memory (RAM)
- **Capacity**: 32GB DDR4/DDR5
- **Speed**: 3200 MHz or higher
- **Channels**: Dual-channel or quad-channel

### Storage
- **Type**: NVMe SSD
- **Space**: 100GB+ free
- **Speed**: 3000+ MB/s sequential read
- **Note**: Separate drives for OS and working directory optimal

### GPU
- **VRAM**: 16GB+ recommended
- **Architecture**: NVIDIA Ampere or newer
- **CUDA**: 11.8+ support
- **Examples**: RTX 3090, RTX 4080, A5000

## Production Requirements

### High-Performance Setup
- **CPU**: AMD EPYC or Intel Xeon (32+ cores)
- **RAM**: 64GB+ ECC memory
- **GPU**: NVIDIA A100 (40GB/80GB) or RTX 4090 (24GB)
- **Storage**: RAID 0 NVMe array for working directory

### Multi-GPU Setup
```yaml
# config.yaml for multi-GPU
scene_construction:
  device: "cuda:0"  # Primary GPU
  data_parallel: true
  device_ids: [0, 1]  # Use GPUs 0 and 1
```

## Performance Benchmarks

### Processing Speed by Hardware

| Hardware Config | Shot Detection | Scene Construction | Total Time (1hr video) |
|----------------|----------------|-------------------|----------------------|
| CPU Only (16-core) | 180 fps | 0.5 shots/sec | ~2 hours |
| RTX 3060 (12GB) | 350 fps | 1.2 shots/sec | ~45 minutes |
| RTX 3090 (24GB) | 400 fps | 2.0 shots/sec | ~25 minutes |
| RTX 4090 (24GB) | 450 fps | 2.5 shots/sec | ~20 minutes |
| A100 (80GB) | 500 fps | 3.0 shots/sec | ~15 minutes |

### Memory Usage

| Video Length | Resolution | Shot Count | RAM Usage | VRAM Usage |
|-------------|------------|------------|-----------|------------|
| 5 minutes | 720p | 50 | 8GB | 6GB |
| 30 minutes | 1080p | 300 | 16GB | 10GB |
| 1 hour | 1080p | 600 | 24GB | 14GB |
| 2 hours | 4K | 1200 | 48GB | 20GB |

## Cloud Instance Recommendations

### AWS EC2

#### Development/Testing
- **Instance**: g4dn.xlarge
- **GPU**: NVIDIA T4 (16GB)
- **vCPUs**: 4
- **RAM**: 16GB
- **Cost**: ~$0.526/hour

#### Production
- **Instance**: p3.2xlarge
- **GPU**: NVIDIA V100 (16GB)
- **vCPUs**: 8
- **RAM**: 61GB
- **Cost**: ~$3.06/hour

#### High Performance
- **Instance**: p4d.24xlarge
- **GPU**: 8x NVIDIA A100 (40GB)
- **vCPUs**: 96
- **RAM**: 1152GB
- **Cost**: ~$32.77/hour

### Google Cloud Platform

#### Development/Testing
- **Machine Type**: n1-standard-4
- **GPU**: NVIDIA T4
- **vCPUs**: 4
- **RAM**: 15GB
- **Cost**: ~$0.45/hour

#### Production
- **Machine Type**: n1-standard-8
- **GPU**: NVIDIA V100
- **vCPUs**: 8
- **RAM**: 30GB
- **Cost**: ~$2.48/hour

### Azure

#### Development/Testing
- **Size**: NC6s_v3
- **GPU**: NVIDIA V100 (16GB)
- **vCPUs**: 6
- **RAM**: 112GB
- **Cost**: ~$3.06/hour

## Hardware Optimization Tips

### CPU Optimization
```bash
# Set CPU affinity for better performance
taskset -c 0-15 python src/main.py video.mp4

# Enable performance governor
sudo cpupower frequency-set -g performance
```

### GPU Optimization
```bash
# Set GPU to persistence mode
sudo nvidia-smi -pm 1

# Set maximum performance
sudo nvidia-smi -ac 5001,1590  # For RTX 3090

# Monitor GPU usage
watch -n 1 nvidia-smi
```

### Memory Optimization
```yaml
# config.yaml adjustments
pipeline:
  batch_size: 16  # Reduce if OOM
  prefetch_frames: 100  # Reduce for less RAM

scene_construction:
  max_frames_per_batch: 5  # Reduce for less VRAM
  fp16: true  # Use half precision
```

### Storage Optimization
- Use separate drives for:
  - Input videos
  - Working directory (keyframes)
  - Model cache
  - Output files

```bash
# Example mount configuration
/dev/nvme0n1 → /mnt/input     # Input videos
/dev/nvme1n1 → /mnt/work      # Working directory
/dev/nvme2n1 → /mnt/output    # Results
```

## System Monitoring

### Monitor Resource Usage
```bash
# CPU and Memory
htop

# GPU
nvidia-smi dmon -s um

# Disk I/O
iotop

# Combined monitoring
python src/utils/monitor_resources.py
```

### Performance Profiling
```bash
# Profile pipeline execution
python -m cProfile -o profile.stats src/main.py video.mp4

# Analyze profile
python -m pstats profile.stats
```

## Scaling Considerations

### Horizontal Scaling
- Process multiple videos in parallel
- Distribute across multiple machines
- Use job queue systems (Celery, RQ)

### Vertical Scaling
- Upgrade to higher VRAM GPUs
- Add more system RAM
- Use faster NVMe drives

### Batch Processing
```python
# Example batch processing script
import multiprocessing as mp

def process_video(video_path):
    os.system(f"python src/main.py {video_path}")

# Process 4 videos in parallel
with mp.Pool(4) as pool:
    pool.map(process_video, video_list)
```

## Cost-Performance Analysis

| Setup | Performance | Cost/Hour | Cost per 1hr Video |
|-------|-------------|-----------|-------------------|
| Local RTX 3060 | Medium | $0 (owned) | $0 |
| AWS g4dn.xlarge | Medium | $0.526 | $0.40 |
| AWS p3.2xlarge | High | $3.06 | $1.28 |
| Local RTX 4090 | Very High | $0 (owned) | $0 |

## Recommendations by Use Case

### Personal/Research Use
- RTX 3060 Ti or better
- 32GB RAM
- 500GB NVMe SSD

### Small Production
- RTX 3090 or RTX 4080
- 64GB RAM
- 1TB NVMe SSD

### Enterprise/Cloud
- Multiple A100 GPUs
- 128GB+ RAM
- Distributed storage

## Future Hardware Support

The pipeline is designed to support:
- Apple Silicon (M1/M2) with MPS backend
- AMD GPUs via ROCm (experimental)
- Intel GPUs via OneAPI (planned)
- TPU support for cloud deployment (planned)