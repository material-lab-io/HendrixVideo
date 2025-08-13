# Hendrix Pipeline Requirements Structure

This directory contains a modular requirements system for the Hendrix Video Analysis Pipeline. The structure allows you to install only the components you need, reducing installation time and avoiding unnecessary dependencies.

## Requirements Files

### Core Requirements

- **`base.txt`** - Common dependencies shared across all components
  - ML frameworks (PyTorch, etc.)
  - Basic computer vision libraries
  - Data science tools
  - Utility libraries

### Component-Specific Requirements

- **`video.txt`** - Video analysis component
  - Includes: base.txt
  - Video processing (MoviePy, FFmpeg)
  - Shot detection tools
  
- **`audio.txt`** - Audio processing component
  - Includes: base.txt
  - Speech recognition (Whisper)
  - Speaker diarization (pyannote)
  - Audio analysis tools
  
- **`visual.txt`** - Visual processing component
  - Includes: base.txt
  - Face detection/recognition
  - Emotion detection
  - Object tracking
  
- **`captioning.txt`** - Caption generation component
  - Includes: base.txt
  - Transformers and LLMs
  - Text processing tools
  - Caption format libraries

### Combined Requirements

- **`all.txt`** - Complete installation with all components
- **`minimal.txt`** - Minimal dependencies for testing/development
- **`dev.txt`** - Development tools (testing, linting, documentation)

## Installation Guide

### Quick Start

```bash
# For complete installation
pip install -r requirements/all.txt

# For development
pip install -r requirements/all.txt -r requirements/dev.txt

# For minimal testing setup
pip install -r requirements/minimal.txt
```

### Component-Specific Installation

```bash
# Only video analysis
pip install -r requirements/video.txt

# Only audio processing
pip install -r requirements/audio.txt

# Only captioning
pip install -r requirements/captioning.txt

# Audio + Visual (for character-dialogue analysis)
pip install -r requirements/audio.txt -r requirements/visual.txt
```

### GPU Support

Most components support GPU acceleration. For GPU support:

```bash
# Install PyTorch with CUDA support (adjust CUDA version as needed)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Then install other requirements
pip install -r requirements/all.txt
```

### Special Requirements

#### Pyannote Audio
Requires HuggingFace authentication:
```bash
# Set your HuggingFace token
export HUGGING_FACE_HUB_TOKEN="your_token_here"
```

#### TransNetV2
Optional, requires TensorFlow:
```bash
pip install tensorflow>=2.13.0
```

## Version Compatibility

- **Python**: 3.8+ required, tested with 3.12
- **CUDA**: 11.8 or 12.1 recommended for GPU support
- **Operating Systems**: Linux, macOS, Windows (WSL2 recommended)

## Troubleshooting

### Common Issues

1. **CUDA/GPU errors**: Ensure PyTorch is installed with correct CUDA version
2. **Memory errors**: Use quantization options in config or reduce batch size
3. **Missing system dependencies**: 
   - Linux: `sudo apt-get install ffmpeg libsm6 libxext6`
   - macOS: `brew install ffmpeg`
   - Windows: Install ffmpeg manually

### Conflicting Dependencies

If you encounter dependency conflicts:

1. Create a fresh virtual environment
2. Install base requirements first
3. Install component-specific requirements
4. Report persistent conflicts as issues

## Updating Requirements

When updating dependencies:

1. Test changes in isolated environment
2. Ensure compatibility across all components
3. Update version constraints conservatively
4. Document any breaking changes

## Contributing

When adding new dependencies:

1. Add to appropriate component file
2. Avoid duplicating base dependencies
3. Pin versions for stability
4. Test with minimal and full installations