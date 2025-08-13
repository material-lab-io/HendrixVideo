# Model Swapping Guide

This guide explains how to easily swap models in the Hendrix pipeline for different use cases, performance requirements, or quality needs.

## Table of Contents

1. [Overview](#overview)
2. [Quick Model Swapping](#quick-model-swapping)
3. [Available Models](#available-models)
4. [Model Profiles](#model-profiles)
5. [Advanced Configuration](#advanced-configuration)
6. [Performance Considerations](#performance-considerations)
7. [Adding New Models](#adding-new-models)

## Overview

Hendrix supports multiple models for each component:
- **Vision-Language Models**: For caption generation
- **Audio Models**: For speech recognition
- **Diarization Models**: For speaker identification  
- **Video Analysis Models**: For shot detection and face recognition

All models can be swapped through configuration without code changes.

## Quick Model Swapping

### Method 1: Configuration File

Edit `configs/base_config.yaml`:

```yaml
# Change the active vision-language model
active_model: llava_13b  # Options: llava_7b, llava_13b, openai_gpt4, mock

# Change audio model
audio_models:
  whisper:
    model: large  # Options: tiny, base, small, medium, large
```

### Method 2: Command Line

```bash
# Use specific models
python -m hendrix_pipeline --video input.mp4 \
    --vlm-model llava_13b \
    --whisper-model large \
    --diarization-model pyannote_3_1

# Use model preset
python -m hendrix_pipeline --video input.mp4 --model-preset quality
```

### Method 3: Python API

```python
from components.config_manager import ConfigManager

# Load configuration
config = ConfigManager()

# Swap vision-language model
config.set_active_model("llava_13b")

# Change audio model
config.set("audio_models.whisper.model", "large")

# Change multiple models at once
config.apply_profile("quality")
```

### Method 4: Environment Variables

```bash
# Set model preferences via environment
export HENDRIX_VLM_MODEL=llava_13b
export HENDRIX_WHISPER_MODEL=large
export HENDRIX_USE_8BIT=true

python -m hendrix_pipeline --video input.mp4
```

## Available Models

### Vision-Language Models

| Model | Size | VRAM | Speed | Quality | Use Case |
|-------|------|------|-------|---------|----------|
| `llava_7b` | 14GB | 16GB | Fast | Good | Default, balanced |
| `llava_13b` | 26GB | 24GB | Medium | Better | Higher quality captions |
| `llava_next_mistral_7b` | 14GB | 16GB | Fast | Good | Efficient, newer |
| `openai_gpt4` | API | N/A | Slow | Best | Highest quality |
| `mock` | 0MB | 0GB | Instant | N/A | Testing only |

### Audio Models (Whisper)

| Model | Size | Speed | Quality | Use Case |
|-------|------|-------|---------|----------|
| `tiny` | 39MB | 39x | Basic | Quick tests |
| `base` | 74MB | 16x | Good | Default |
| `small` | 244MB | 6x | Better | Better accuracy |
| `medium` | 769MB | 2x | High | Professional |
| `large` | 1.5GB | 1x | Best | Maximum accuracy |

### Speaker Diarization

| Model | Features | Requirements |
|-------|----------|--------------|
| `pyannote_3_1` | Latest, most accurate | HF token required |
| `pyannote_3_0` | Stable, good accuracy | HF token required |
| `none` | Disabled | No requirements |

### Video Analysis

| Component | Models | Notes |
|-----------|--------|-------|
| Shot Detection | `transnetv2`, `pyscenedetect` | TransNet more accurate |
| Face Detection | `retinaface`, `mtcnn`, `yolov8` | RetinaFace recommended |
| Emotion | `fer`, `deepface` | FER is faster |

## Model Profiles

Pre-configured model combinations for common use cases:

### Minimal Profile
```yaml
profile: minimal
# Uses smallest models for testing
# - llava_7b with 8-bit quantization
# - whisper tiny
# - basic shot detection
# - no face/emotion detection
```

### Balanced Profile (Default)
```yaml
profile: balanced
# Good balance of speed and quality
# - llava_7b
# - whisper base
# - transnetv2 shot detection
# - retinaface + fer
```

### Quality Profile
```yaml
profile: quality
# Maximum quality, slower processing
# - llava_13b
# - whisper large
# - all features enabled
# - higher token limits
```

### Fast Profile
```yaml
profile: fast
# Optimized for speed
# - llava_7b with optimization
# - whisper tiny
# - minimal processing
# - reduced features
```

## Advanced Configuration

### Custom Model Combinations

Create your own model profile in `configs/custom_profile.yaml`:

```yaml
extends: base_config.yaml

# Custom model selection
active_model: llava_13b
audio_models:
  whisper:
    model: medium
    
# Optimize for specific use case
components:
  video_analysis:
    shot_detection:
      model: transnetv2
      confidence_threshold: 0.7  # Higher threshold
      
  captioning:
    generation:
      temperature: 0.3  # More focused captions
      max_tokens: 200   # Longer descriptions
      
# Resource optimization
resources:
  memory:
    max_gpu_memory_fraction: 0.95  # Use more VRAM
    enable_gradient_checkpointing: true
```

### Quantization Options

Reduce memory usage with quantization:

```python
# 8-bit quantization
config.set("models.llava_13b.device_config.load_in_8bit", True)

# 4-bit quantization (for very large models)
config.set("models.llava_13b.device_config.load_in_4bit", True)
```

### API Model Configuration

For cloud-based models:

```yaml
models:
  openai_gpt4:
    provider: openai
    model: gpt-4-vision-preview
    api_key: ${OPENAI_API_KEY}
    max_retries: 3
    timeout: 30
    generation:
      temperature: 0.7
      max_tokens: 150
```

## Performance Considerations

### Memory Requirements

| Configuration | VRAM Usage | RAM Usage | Processing Speed |
|--------------|------------|-----------|------------------|
| Minimal | 4-6GB | 8GB | Fast |
| Balanced | 8-12GB | 16GB | Medium |
| Quality | 16-24GB | 32GB | Slow |
| 8-bit Quantized | 50% less | Same | 10-20% slower |

### Model Loading Times

```python
# Pre-load models to avoid reload delays
from hendrix import preload_models

# Load all models at startup
preload_models(["llava_7b", "whisper_base", "retinaface"])

# Or load on-demand with caching
config.set("pipeline.use_cache", True)
```

### Batch Processing

```yaml
# Optimize for batch processing
pipeline:
  batch_size: 4  # Process 4 scenes at once
  prefetch_frames: true
  
components:
  captioning:
    batch_inference: true
    max_batch_size: 8
```

## Adding New Models

### Step 1: Add to Model Registry

Edit `configs/models.yaml`:

```yaml
vision_language_models:
  my_custom_model:
    name: "My Custom VLM"
    model_id: "org/model-name"
    size_gb: 20
    recommended_vram_gb: 24
    features:
      - custom_feature
```

### Step 2: Add to Base Config

Edit `configs/base_config.yaml`:

```yaml
models:
  my_custom_model:
    provider: huggingface  # or custom
    model: "org/model-name"
    device_config:
      device_map: auto
      torch_dtype: float16
```

### Step 3: Implement Loader (if needed)

```python
# components/models/custom_loader.py
from hendrix.models.base import BaseModelLoader

class CustomModelLoader(BaseModelLoader):
    def load_model(self, config):
        # Custom loading logic
        return model
        
    def generate(self, inputs, **kwargs):
        # Custom generation logic
        return outputs
```

### Step 4: Register and Use

```python
# Register the model
from hendrix.models import register_model
register_model("my_custom_model", CustomModelLoader)

# Use it
config.set_active_model("my_custom_model")
```

## Best Practices

### 1. Choose Models Based on Hardware

```python
from hendrix.utils import detect_hardware

hw = detect_hardware()
if hw.gpu_memory < 8:
    config.apply_profile("minimal")
elif hw.gpu_memory < 16:
    config.apply_profile("balanced")
else:
    config.apply_profile("quality")
```

### 2. Progressive Quality Enhancement

```python
# Start with fast processing
results_fast = pipeline.process(video, profile="fast")

# Enhance specific scenes with better models
important_scenes = identify_important_scenes(results_fast)
results_hq = pipeline.process_scenes(
    video, 
    scenes=important_scenes,
    profile="quality"
)
```

### 3. Model-Specific Optimization

```yaml
# Optimize for specific models
profiles:
  llava_optimized:
    active_model: llava_7b
    overrides:
      models:
        llava_7b:
          device_config:
            use_flash_attention_2: true
            load_in_8bit: true
      generation:
        do_sample: false  # Deterministic output
        num_beams: 1      # Faster generation
```

## Troubleshooting

### Model Won't Load

```bash
# Clear model cache
rm -rf ~/.cache/huggingface/hub/models--*

# Re-download
python scripts/setup/download_models.py --model llava_7b --force
```

### Out of Memory

```python
# Use smaller model
config.set_active_model("llava_7b")

# Enable quantization
config.set("models.llava_7b.device_config.load_in_8bit", True)

# Reduce batch size
config.set("pipeline.batch_size", 1)
```

### Slow Performance

```bash
# Check model is using GPU
python -c "from hendrix import check_gpu_usage; check_gpu_usage()"

# Use faster models
python -m hendrix_pipeline --video input.mp4 \
    --vlm-model llava_7b \
    --whisper-model tiny \
    --skip-diarization
```

## Summary

Model swapping in Hendrix is designed to be flexible and easy:

1. **Simple swapping** via configuration or command line
2. **Pre-configured profiles** for common use cases
3. **Fine-grained control** over individual components
4. **Extensible system** for adding new models

Choose models based on your:
- Hardware capabilities
- Quality requirements
- Processing time constraints
- Specific use case needs

Start with the balanced profile and adjust based on your results!