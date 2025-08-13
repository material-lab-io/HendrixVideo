# Hendrix Video Analysis Pipeline

A sophisticated three-stage video analysis pipeline that leverages state-of-the-art computer vision and language models to perform comprehensive video understanding, shot detection, scene construction, and cinematic analysis.

## Overview

Hendrix Video Analysis Pipeline automatically processes videos through three distinct stages:

1. **Shot Detection** - Identifies shot boundaries and extracts keyframes
2. **Scene Construction** - Groups shots into semantic scenes with narrative descriptions
3. **Cinematic Analysis** - Analyzes cinematographic techniques and style (optional)

The pipeline uses advanced models including TransNetV2 for shot detection and LLaVA (Large Language and Vision Assistant) for visual understanding, providing detailed insights into video content structure and semantics.

## Key Features

- **Automatic Shot Detection**: Uses TransNetV2 with intelligent fallback to frame difference methods
- **Semantic Scene Understanding**: Leverages LLaVA-1.5-7B for detailed frame analysis
- **Flexible Configuration**: YAML-based configuration for easy customization
- **Resume Capability**: Can resume interrupted processing from any stage
- **GPU Acceleration**: Optimized for NVIDIA GPUs with automatic CPU fallback
- **Comprehensive Logging**: Detailed logging for debugging and monitoring
- **Modular Architecture**: Easy to extend with new models and analysis stages

## Quick Start

### Prerequisites

- Python 3.8+
- CUDA-capable GPU (recommended) with 16GB+ VRAM
- FFmpeg installed
- 32GB+ RAM recommended
- 100GB+ free disk space

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Hendrix_Video_Analysis.git
cd Hendrix_Video_Analysis
```

2. Set up the environment:
```bash
chmod +x setup_env.sh
./setup_env.sh
```

3. Download models (first run will download automatically):
```bash
python init_project.py
```

### Basic Usage

Analyze a video with default settings:
```bash
python src/main.py path/to/your/video.mp4
```

Analyze with verbose output:
```bash
./run_verbose.sh path/to/your/video.mp4
```

Resume from a specific stage:
```bash
python src/main.py path/to/video.mp4 --resume-from scene_construction
```

### Example Output

The pipeline generates structured JSON outputs for each stage:

```json
{
  "shots": [
    {
      "shot_id": 1,
      "start": 0.0,
      "end": 2.5,
      "keyframe_path": "keyframes/shot_0001.jpg",
      "confidence": 0.95
    }
  ],
  "scenes": [
    {
      "scene_id": 1,
      "summary": "A bustling city street with heavy traffic",
      "mood": "energetic",
      "contained_shots": [1, 2, 3]
    }
  ]
}
```

## Hardware Requirements

### Minimum Requirements
- **CPU**: 8-core processor
- **RAM**: 16GB
- **GPU**: NVIDIA GPU with 8GB VRAM (optional)
- **Storage**: 50GB free space

### Recommended Requirements
- **CPU**: 16+ core processor
- **RAM**: 32GB
- **GPU**: NVIDIA GPU with 16GB+ VRAM
- **Storage**: 100GB+ free space (SSD preferred)

### Cloud Deployment
- **AWS**: p3.2xlarge or g4dn.xlarge instances
- **Google Cloud**: T4 or V100 instances
- **Azure**: NC6 or NC12 instances

## Performance Benchmarks

| Video Length | Resolution | Shots | GPU Processing | CPU Processing |
|-------------|------------|-------|----------------|----------------|
| 30 seconds  | 720p       | 10    | ~15 seconds    | ~2 minutes     |
| 5 minutes   | 1080p      | 50    | ~2 minutes     | ~15 minutes    |
| 1 hour      | 1080p      | 600   | ~20 minutes    | ~2 hours       |

*Benchmarks on NVIDIA RTX 3090 (24GB) vs AMD Ryzen 9 5900X*

## Architecture

The pipeline follows a modular architecture with three main stages:

```
Input Video → Shot Detection → Scene Construction → Cinematic Analysis → Output
                    ↓                    ↓                    ↓
                Keyframes          Scene Graphs        Style Report
```

Each stage can be run independently and produces intermediate outputs that can be reused.

## Configuration

Edit `config.yaml` to customize the pipeline:

```yaml
shot_detection:
  detector: "transnetv2"  # or "autoshot"
  min_shot_duration: 0.5
  threshold: 0.3

scene_construction:
  model: "llava-hf/llava-1.5-7b-hf"
  batch_size: 10
  use_gpu: true
```

## Documentation

- [Quick Start Guide](docs/quickstart.md)
- [Installation Guide](docs/installation.md)
- [API Reference](docs/api-reference.md)
- [Architecture Overview](docs/architecture.md)
- [Configuration Guide](docs/configuration.md)
- [Troubleshooting](docs/troubleshooting.md)

## Examples

Check the `examples/` directory for:
- Basic video analysis script
- Batch processing multiple videos
- Custom prompt templates
- Performance benchmarking

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Citation

If you use this pipeline in your research, please cite:

```bibtex
@software{hendrix_video_analysis,
  title = {Hendrix Video Analysis Pipeline},
  year = {2024},
  url = {https://github.com/yourusername/Hendrix_Video_Analysis}
}
```

## Acknowledgments

- TransNetV2 for shot boundary detection
- LLaVA team for the vision-language model
- OpenCV and MoviePy communities

## Contact

For questions and support, please open an issue on GitHub or contact the maintainers.

---

**Note**: This project requires significant computational resources. For production use, we recommend using a dedicated GPU server or cloud instance.