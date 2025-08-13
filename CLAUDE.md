# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

The Hendrix Video Analysis Pipeline is a comprehensive AI-powered system for analyzing video content. It consists of three interconnected components:

1. **Video Analysis**: Shot detection, scene construction, keyframe extraction
2. **Character & Dialogue**: Speech transcription, speaker diarization, face detection, emotion analysis
3. **Captioning**: AI-powered caption generation using vision-language models

## Project Structure (v2.0 - Reorganized)

```
hendrix_12aug/
├── components/           # Core pipeline components
│   ├── video_analysis/   # Video structure analysis
│   ├── character_dialogue/ # Audio/visual processing
│   ├── captioning/       # Caption generation
│   └── config_manager.py # Configuration management
├── configs/              # All configuration files
│   ├── base_config.yaml  # Main configuration
│   ├── models.yaml       # Model registry
│   └── pipeline/         # Pipeline configs
├── scripts/              # Executable scripts
│   ├── setup/            # Setup and installation
│   ├── pipeline/         # Pipeline runners
│   └── utils/            # Utilities
├── requirements/         # Modular requirements
├── docs/                 # Documentation
├── outputs/              # Pipeline outputs
├── models/               # Model storage
└── archive/              # Old/obsolete files
```

## Key Commands

### Quick Start
```bash
# Run complete pipeline
bash scripts/pipeline/run_complete.sh video.mp4

# Run with Python entry point
python -m hendrix_pipeline --video video.mp4

# Run with specific profile
python -m hendrix_pipeline --video video.mp4 --profile fast

# List available models
python -m hendrix_pipeline --list-models

# Verify installation
python -m hendrix_pipeline --verify
```

### Development
```bash
# Install all dependencies
pip install -r requirements/all.txt -r requirements/dev.txt

# Run tests
pytest tests/

# Format code
black components/ --line-length 120

# Lint code
flake8 components/ --max-line-length=120
```

### Model Management
```bash
# Download models
bash scripts/setup/download_models.sh

# Swap models via command line
python -m hendrix_pipeline --video video.mp4 --vlm-model llava_13b --whisper-model large
```

## Configuration System

### Model Swapping
Models can be easily swapped by editing `configs/base_config.yaml`:
```yaml
active_model: llava_7b  # Change to: llava_13b, openai_gpt4, etc.
```

Or programmatically:
```python
from components.config_manager import ConfigManager
config = ConfigManager()
config.set_active_model("llava_13b")
```

### Available Profiles
- **fast**: Speed-optimized, reduced features
- **balanced**: Default, good balance
- **quality**: Maximum quality, all features
- **test**: Development with mock models

### Key Configuration Sections
- `models`: Vision-language model definitions
- `audio_models`: Whisper, diarization settings
- `video_models`: Shot detection, face detection
- `pipeline`: Processing settings, device config
- `output`: Format and naming settings

## Architecture Notes

### Pipeline Flow
1. Video → Video Analysis → Shots, Scenes, Keyframes
2. Video → Character & Dialogue → Transcripts, Speakers, Faces
3. Results → Captioning → SRT, VTT, HTML, JSON outputs

### Component Communication
- Components communicate via JSON files
- Each component can run independently
- Results are aggregated in the captioning stage

### GPU/Memory Management
- Automatic GPU detection with CPU fallback
- Configurable memory limits
- Support for 8-bit and 4-bit quantization
- Batch processing for efficiency

## Important Files

### Entry Points
- `hendrix_pipeline.py`: Main Python entry point
- `scripts/pipeline/run_complete.sh`: Bash pipeline runner
- `components/config_manager.py`: Configuration management

### Configuration
- `configs/base_config.yaml`: Main configuration
- `configs/models.yaml`: Available models registry
- `configs/pipeline/default.yaml`: Pipeline settings

### Documentation
- `README.md`: Project overview
- `docs/GETTING_STARTED.md`: Setup guide
- `docs/MODEL_SWAPPING_GUIDE.md`: Model management
- `REORGANIZATION_SUMMARY.md`: Recent changes

## Development Guidelines

### Adding New Models
1. Add to `configs/models.yaml`
2. Add to `configs/base_config.yaml`
3. Implement loader if needed
4. Update documentation

### Code Style
- Use Black formatter (120 char lines)
- Follow existing patterns
- Add type hints where possible
- Document complex functions

### Testing
- Unit tests in `tests/unit/`
- Integration tests in `tests/integration/`
- Use pytest fixtures
- Mock external APIs

## Common Tasks

### Process Multiple Videos
```bash
for video in *.mp4; do
    python -m hendrix_pipeline --video "$video" --profile balanced
done
```

### Extract Only Transcripts
```bash
python -m hendrix_pipeline --video input.mp4 \
    --components audio \
    --output-formats txt,json
```

### Debug Issues
```bash
# Run with verbose output
python -m hendrix_pipeline --video input.mp4 --verbose

# Check specific component
python -m components.video_analysis.main --video input.mp4 --debug
```

## Troubleshooting

### Memory Issues
- Use smaller models or quantization
- Reduce batch size in config
- Use the `fast` profile

### Model Loading
- Check model files in `~/.cache/huggingface/`
- Verify HF_TOKEN for gated models
- Clear cache if corrupted

### Performance
- Ensure CUDA is properly installed
- Check GPU usage with `nvidia-smi`
- Use appropriate profile for hardware

## Recent Changes (v2.0)

1. Reorganized directory structure
2. Centralized configuration system
3. Modular requirements
4. Easy model swapping
5. Improved documentation
6. Unified pipeline scripts

See `REORGANIZATION_SUMMARY.md` for details.