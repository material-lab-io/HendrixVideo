# Hendrix Requirements Structure

## Overview

This document explains the modular requirements structure for the Hendrix project. The requirements have been organized to minimize conflicts, reduce redundancy, and allow for component-specific installations.

## File Structure

```
hendrix_12aug/
├── requirements-base.txt           # Common dependencies shared across components
├── requirements-captioning.txt     # Captioning component specific
├── requirements-video.txt          # Video analysis component specific
├── requirements-audio.txt          # Audio processing component specific
├── requirements-visual.txt         # Visual processing component specific
├── requirements-character-dialogue.txt  # Combined audio+visual for dialogue analysis
├── requirements-all.txt            # Complete installation (all components)
├── requirements-dev.txt            # Development tools and extras
└── requirements-minimal.txt        # Minimal dependencies for testing
```

## Installation Guide

### For specific components:

```bash
# Captioning only
pip install -r requirements-captioning.txt

# Video analysis only
pip install -r requirements-video.txt

# Audio processing only
pip install -r requirements-audio.txt

# Visual processing only
pip install -r requirements-visual.txt

# Character dialogue (audio + visual)
pip install -r requirements-character-dialogue.txt
```

### For complete installation:

```bash
# All components
pip install -r requirements-all.txt

# All components + development tools
pip install -r requirements-all.txt -r requirements-dev.txt
```

### For minimal testing:

```bash
pip install -r requirements-minimal.txt
```

## Key Decisions

1. **Base Requirements**: Common dependencies used by 3+ components are in `requirements-base.txt`
2. **Version Resolution**: All conflicts resolved by using the highest version number
3. **Python 3.12 Compatibility**: Using `numpy>=1.26.0` for Python 3.12 support
4. **Modular Structure**: Each component can be installed independently
5. **Inheritance**: Component files include base requirements using `-r requirements-base.txt`

## Version Conflicts Resolved

- **numpy**: Using `>=1.26.0` (highest, for Python 3.12)
- **transformers**: Using `>=4.36.0` for captioning, `>=4.35.0` for audio, `>=4.30.0` for video
- **accelerate**: Using `>=0.25.0` for captioning, `>=0.20.0` for video
- **requests**: Using `>=2.31.0` (highest)
- **pillow**: Using `>=10.0.0` (highest)

## Component-Specific Dependencies

### Captioning
- LLaVA-NeXT support with latest transformers
- Optional API clients for OpenAI/Google

### Video Analysis
- Shot detection with TransNetV2
- Video processing with moviepy/ffmpeg

### Audio Processing
- Whisper for transcription
- Pyannote for speaker diarization
- SpeechBrain for emotion recognition

### Visual Processing
- Face detection/recognition with multiple backends
- Scene detection and clustering
- Advanced image processing

## Migration Guide

To migrate from old structure to new:

1. Identify which components you're using
2. Install the appropriate requirements file
3. Remove old virtual environment if conflicts persist
4. Test functionality with minimal requirements first

## Maintenance

When adding new dependencies:
1. Add to the most specific component file possible
2. If used by 3+ components, add to `requirements-base.txt`
3. Always specify minimum version with `>=`
4. Test with `requirements-minimal.txt` to ensure basics work