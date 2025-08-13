# Model Integration Guide

Guide for integrating and configuring models in the Hendrix Video Analysis Pipeline.

## Overview

The pipeline supports multiple models for different analysis tasks:
- **Shot Detection**: TransNetV2, AutoShot, Frame Difference
- **Scene Analysis**: LLaVA, CLIP (planned)
- **Cinematic Analysis**: CinematicVLM (planned)

## Current Models

### TransNetV2

**Purpose**: Deep learning-based shot boundary detection

**Installation**:
```bash
pip install transnetv2-pytorch
```

**Configuration**:
```yaml
shot_detection:
  detector: "transnetv2"
  transnetv2:
    model_path: "cache/transnetv2_weights.pth"
    threshold: 0.5
    batch_size: 64
    device: "cuda:0"
```

**Usage Notes**:
- Requires ~100MB for model weights
- Processes at ~400-500 fps on GPU
- Falls back to frame difference if unavailable

### LLaVA (Large Language and Vision Assistant)

**Purpose**: Vision-language understanding for scene analysis

**Model Variants**:
- `llava-hf/llava-1.5-7b-hf` (default, 13GB)
- `llava-hf/llava-1.5-13b-hf` (26GB, better quality)
- `llava-hf/llava-v1.6-vicuna-7b-hf` (newer version)

**Configuration**:
```yaml
scene_construction:
  model: "llava-hf/llava-1.5-7b-hf"
  model_config:
    torch_dtype: "float16"  # or "float32", "bfloat16"
    device_map: "auto"
    low_cpu_mem_usage: true
    load_in_8bit: false  # Enable for lower VRAM
    load_in_4bit: false  # Enable for minimal VRAM
```

**Memory Requirements**:
- Float32: ~26GB VRAM
- Float16: ~13GB VRAM
- 8-bit: ~7GB VRAM
- 4-bit: ~4GB VRAM

### AutoShot (Optional)

**Purpose**: Traditional CV-based shot detection

**Installation**:
```bash
# Clone AutoShot repository
git clone https://github.com/wanboyang/autoshot_research.git
cd autoshot_research
pip install -r requirements.txt
```

**Configuration**:
```yaml
shot_detection:
  detector: "autoshot"
  autoshot:
    model_path: "path/to/autoshot/model"
    use_color: true
    use_motion: true
    use_audio: false
```

## Adding New Models

### Step 1: Create Model Wrapper

Create a new model class in `src/models/`:

```python
# src/models/my_custom_model.py
import logging
from typing import List, Dict, Any
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class MyCustomModel:
    """Custom model for video analysis."""
    
    def __init__(self, config: dict):
        self.config = config
        self.model = None
        self.device = config.get('device', 'cpu')
        self._load_model()
    
    def _load_model(self):
        """Load model weights."""
        try:
            # Load your model here
            import torch
            from transformers import AutoModel
            
            model_name = self.config.get('model_name', 'default-model')
            self.model = AutoModel.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if self.device != 'cpu' else torch.float32
            )
            
            if self.device != 'cpu':
                self.model = self.model.to(self.device)
                
            logger.info(f"Loaded {model_name} on {self.device}")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def process(self, input_data: Any) -> Any:
        """Process input data."""
        if self.model is None:
            raise RuntimeError("Model not loaded")
            
        # Implement your processing logic
        with torch.no_grad():
            output = self.model(input_data)
            
        return output
    
    def unload(self):
        """Free model resources."""
        if self.model is not None:
            del self.model
            self.model = None
            
            if self.device != 'cpu':
                import torch
                torch.cuda.empty_cache()
```

### Step 2: Integrate into Pipeline

Update the appropriate pipeline stage:

```python
# src/pipeline/shot_detection.py
from models.my_custom_model import MyCustomModel

class ShotDetectionPipeline:
    def __init__(self, config):
        self.config = config
        detector_type = config['shot_detection']['detector']
        
        if detector_type == 'my_custom_model':
            self.detector = MyCustomModel(config['shot_detection']['my_custom_model'])
        # ... other detectors
```

### Step 3: Update Configuration

Add model configuration options:

```yaml
# config.yaml
shot_detection:
  detector: "my_custom_model"
  my_custom_model:
    model_name: "username/model-name"
    device: "cuda:0"
    batch_size: 32
    custom_param: "value"
```

### Step 4: Add Tests

Create tests for your model:

```python
# tests/test_my_custom_model.py
import pytest
from src.models.my_custom_model import MyCustomModel

def test_model_loading():
    config = {
        'model_name': 'test-model',
        'device': 'cpu'
    }
    model = MyCustomModel(config)
    assert model.model is not None

def test_model_processing():
    # Test processing logic
    pass
```

## Model Optimization

### Quantization

Reduce model size and memory usage:

```python
# 8-bit quantization
from transformers import BitsAndBytesConfig

quantization_config = BitsAndBytesConfig(
    load_in_8bit=True,
    bnb_8bit_compute_dtype=torch.float16
)

model = AutoModel.from_pretrained(
    model_name,
    quantization_config=quantization_config
)
```

### Mixed Precision

Use automatic mixed precision for faster inference:

```python
from torch.cuda.amp import autocast

with autocast():
    output = model(input_data)
```

### Model Compilation (PyTorch 2.0+)

```python
import torch

# Compile model for faster inference
model = torch.compile(model, mode="reduce-overhead")
```

## Model Management

### Caching Models

Configure model caching:

```yaml
models:
  cache_dir: "/path/to/model/cache"
  keep_in_memory: true  # Don't unload between videos
  
  # Hugging Face specific
  hf_cache_dir: "~/.cache/huggingface"
  use_auth_token: false  # For private models
```

### Downloading Models

Pre-download models:

```python
# download_models.py
from transformers import AutoModel, AutoProcessor

models = [
    "llava-hf/llava-1.5-7b-hf",
    "openai/clip-vit-base-patch32"
]

for model_name in models:
    print(f"Downloading {model_name}...")
    AutoModel.from_pretrained(model_name)
    AutoProcessor.from_pretrained(model_name)
```

### Model Versioning

Track model versions:

```yaml
models:
  versions:
    llava: "v1.5-7b"
    transnetv2: "v1.0"
  
  # Revision/commit hash for reproducibility
  revisions:
    llava: "b234b804b114d9e37bb655e11cbbb5f5e971b7a9"
```

## Custom Prompts

### Configuring Prompts

```yaml
scene_construction:
  prompts:
    shot_description: |
      Analyze this video frame and describe:
      1. The main action or event
      2. The setting or location
      3. The mood or atmosphere
      4. Any notable cinematographic techniques
    
    scene_construction: |
      Group these shots into coherent scenes based on:
      - Temporal continuity
      - Spatial continuity
      - Narrative continuity
      Output as JSON with scene boundaries and descriptions.
```

### Dynamic Prompts

```python
def create_custom_prompt(video_metadata, shot_info):
    """Create context-aware prompts."""
    
    genre = video_metadata.get('genre', 'unknown')
    duration = shot_info['duration']
    
    if genre == 'action':
        return "Describe the action sequence, focusing on movement and energy..."
    elif duration < 1.0:
        return "This is a quick shot. Identify the key visual element..."
    else:
        return "Describe the scene comprehensively..."
```

## Performance Tuning

### Batch Processing

Configure optimal batch sizes:

```python
def get_optimal_batch_size(model_name, device):
    """Determine optimal batch size based on model and device."""
    
    if 'cuda' in device:
        vram = torch.cuda.get_device_properties(0).total_memory
        
        if '13b' in model_name:
            return min(4, int(vram / 8e9))  # 8GB per sample
        elif '7b' in model_name:
            return min(8, int(vram / 4e9))  # 4GB per sample
        else:
            return 16
    else:
        return 1  # CPU processing
```

### Memory Management

```python
class ModelManager:
    """Manage model lifecycle and memory."""
    
    def __init__(self):
        self.loaded_models = {}
        
    def get_model(self, model_name, config):
        """Load or retrieve cached model."""
        if model_name not in self.loaded_models:
            self.loaded_models[model_name] = self._load_model(model_name, config)
        return self.loaded_models[model_name]
    
    def clear_unused(self, keep_models=None):
        """Clear unused models from memory."""
        keep_models = keep_models or []
        
        for name, model in list(self.loaded_models.items()):
            if name not in keep_models:
                model.unload()
                del self.loaded_models[name]
```

## Troubleshooting Models

### Common Issues

**Issue**: "Could not find a version that satisfies the requirement"
```bash
# Update transformers
pip install transformers --upgrade

# Or install from source
pip install git+https://github.com/huggingface/transformers
```

**Issue**: "CUDA out of memory"
```python
# Enable gradient checkpointing
model.gradient_checkpointing_enable()

# Use smaller batch size
config['batch_size'] = 1

# Clear cache
torch.cuda.empty_cache()
```

**Issue**: "Model not found"
```python
# Check model name
from huggingface_hub import list_models
models = list(list_models(filter="llava"))
print([m.modelId for m in models])
```

## Future Models

### Planned Integrations

1. **CLIP** - For semantic similarity
2. **VideoMAE** - For temporal understanding  
3. **X-CLIP** - For video-text alignment
4. **CogVideo** - For video understanding

### Model Roadmap

- Q1 2024: CLIP integration for scene similarity
- Q2 2024: VideoMAE for temporal analysis
- Q3 2024: Custom fine-tuned models
- Q4 2024: Multi-modal ensemble methods