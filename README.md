# Hendrix Video Analysis Pipeline

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A comprehensive AI-powered video analysis pipeline that combines computer vision, speech recognition, and natural language processing to generate detailed video captions and analysis. Hendrix provides a modular, extensible framework for understanding video content at multiple levels - from shot detection to emotion analysis.

## 📋 Table of Contents

- [Key Features](#-key-features)
- [Quick Start](#-quick-start)
- [Project Structure](#-project-structure)
- [Configuration](#️-configuration)
- [Advanced Usage](#-advanced-usage)
- [Output Formats](#-output-formats)
- [Model Information](#-model-information)
- [Documentation](#-documentation)
- [Contributing](#-contributing)
- [License](#-license)

## 🎯 Key Features

- **🎬 Shot Detection & Scene Analysis**: Automatically detect shot boundaries and group them into coherent scenes using TransNetV2
- **🎤 Speech Recognition & Speaker Diarization**: Transcribe dialogue with Whisper and identify different speakers using Pyannote
- **😊 Face Detection & Emotion Analysis**: Track characters throughout the video and analyze their emotional states
- **🤖 AI-Powered Caption Generation**: Generate context-aware captions using state-of-the-art vision-language models (LLaVA, GPT-4V)
- **📄 Multiple Output Formats**: Export to SRT, WebVTT, JSON, and interactive HTML timeline
- **🔧 Modular Architecture**: Use individual components or the complete pipeline
- **⚡ GPU Optimization**: Efficient processing with automatic GPU/CPU fallback and quantization support

## 🚀 Quick Start

### Prerequisites

- Python 3.8+ (tested with 3.12)
- CUDA-capable GPU (optional but recommended)
- FFmpeg installed on your system
- 16GB+ RAM recommended
- 50GB+ free disk space for models

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/material-lab-io/HendrixVideo.git
cd HendrixVideo
```

2. **Create virtual environment**
```bash
python -m venv hendrix_venv
source hendrix_venv/bin/activate  # On Windows: hendrix_venv\Scripts\activate
```

3. **Install dependencies**
```bash
# For complete installation
pip install -r requirements/all.txt

# For minimal installation (testing only)
pip install -r requirements/minimal.txt

# For specific components
pip install -r requirements/video.txt      # Video analysis only
pip install -r requirements/audio.txt      # Audio processing only
pip install -r requirements/captioning.txt # Caption generation only
```

4. **Download required models**
```bash
bash scripts/setup/download_models.sh
```

### Basic Usage

```bash
# Run the complete pipeline on a video
bash scripts/pipeline/run_complete.sh path/to/your/video.mp4

# Run with GPU optimization
bash scripts/pipeline/run_gpu_optimized.sh path/to/your/video.mp4

# Run with a specific profile
python -m hendrix_pipeline --video path/to/video.mp4 --profile fast
```

## 📁 Project Structure

```
hendrix_12aug/
├── components/           # Core pipeline components
│   ├── video_analysis/   # Shot detection and scene analysis
│   ├── character_dialogue/ # Audio transcription and face detection
│   └── captioning/       # AI-powered caption generation
├── configs/              # Configuration files
│   ├── base_config.yaml  # Main configuration
│   ├── models.yaml       # Model registry
│   └── pipeline/         # Pipeline-specific configs
├── scripts/              # Executable scripts
│   ├── setup/            # Setup and installation
│   ├── pipeline/         # Pipeline runners
│   └── utils/            # Utility scripts
├── requirements/         # Modular requirements
├── models/               # Model storage
├── outputs/              # Pipeline outputs
├── docs/                 # Documentation
└── examples/             # Example videos and usage
```

## ⚙️ Configuration

### Easy Model Swapping

Edit `configs/base_config.yaml` to change models:

```yaml
# Change the active model
active_model: llava_13b  # Options: llava_7b, llava_13b, openai_gpt4, mock

# Or use Python
from components.config_manager import ConfigManager
config = ConfigManager()
config.set_active_model("llava_13b")
```

### Available Profiles

- **fast**: Optimized for speed, reduced quality
- **balanced**: Good balance of speed and quality (default)
- **quality**: Maximum quality, all features enabled
- **test**: For development with mock models

```bash
# Use a profile
python -m hendrix_pipeline --video video.mp4 --profile fast
```

## 🔧 Advanced Usage

### Component-Specific Processing

```python
# Video analysis only
from components.video_analysis import VideoAnalyzer
analyzer = VideoAnalyzer(config)
scenes = analyzer.process_video("video.mp4")

# Audio processing only
from components.character_dialogue import AudioProcessor
processor = AudioProcessor(config)
transcript = processor.process_audio("video.mp4")

# Caption generation with existing analysis
from components.captioning import CaptionGenerator
generator = CaptionGenerator(config)
captions = generator.generate_captions(scenes, transcript)
```

### Custom Configuration

```python
from components.config_manager import ConfigManager

# Load with custom profile
config = ConfigManager(profile="quality")

# Override specific settings
config.set("generation.temperature", 0.8)
config.set("pipeline.batch_size", 4)

# Use different models for different components
config.set("audio_models.whisper.model", "large")
config.set("active_model", "llava_13b")
```

## 📊 Output Formats

The pipeline generates multiple output formats in the `outputs/` directory:

- **JSON**: Complete analysis data with timestamps, transcripts, and metadata
- **SRT/WebVTT**: Standard subtitle formats for video players
- **HTML**: Interactive timeline visualization
- **TXT**: Plain text transcripts and summaries

## 🔍 Model Information

### Vision-Language Models
- **LLaVA 7B**: Fast and efficient (14GB VRAM)
- **LLaVA 13B**: Better quality (24GB VRAM)
- **GPT-4 Vision**: Best quality (requires API key)

### Audio Models
- **Whisper**: tiny, base, small, medium, large
- **Pyannote**: Speaker diarization (requires HuggingFace token)

### Video Analysis
- **TransNetV2**: Accurate shot detection
- **RetinaFace**: High-quality face detection
- **FER**: Facial emotion recognition

## 🐛 Troubleshooting

### Common Issues

1. **CUDA out of memory**
   - Use a smaller model or enable 8-bit quantization
   - Reduce batch size in configuration
   - Use the `fast` profile

2. **Models not downloading**
   - Check internet connection
   - Manually download from HuggingFace
   - Set HF_TOKEN for gated models

3. **FFmpeg errors**
   - Ensure FFmpeg is installed: `ffmpeg -version`
   - Install: `sudo apt-get install ffmpeg` (Linux) or `brew install ffmpeg` (macOS)

## 📈 Performance Tips

- Use GPU acceleration when available
- Enable 8-bit quantization for large models
- Process videos in batches for efficiency
- Use the `fast` profile for quick previews
- Clear cache periodically with `--clear-cache`

## 📚 Documentation

- **[Getting Started Guide](docs/GETTING_STARTED.md)** - Detailed installation and setup instructions
- **[Usage Guide](docs/USAGE_GUIDE.md)** - Comprehensive usage examples and API reference
- **[Development Guide](docs/DEVELOPMENT_GUIDE.md)** - Architecture, development setup, and best practices
- **[Model Swapping Guide](docs/MODEL_SWAPPING_GUIDE.md)** - How to use different AI models
- **[API Reference](docs/API_REFERENCE.md)** - Detailed API documentation

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- TransNetV2 for shot detection
- OpenAI Whisper for speech recognition
- Pyannote for speaker diarization
- LLaVA for vision-language understanding
- All other open-source contributors

## 📞 Support

- Documentation: [docs/](docs/)
- Issues: [GitHub Issues](https://github.com/material-lab-io/HendrixVideo/issues)
- Discussions: [GitHub Discussions](https://github.com/material-lab-io/HendrixVideo/discussions)