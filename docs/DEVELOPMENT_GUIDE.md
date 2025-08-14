# Hendrix Video Analysis Pipeline - Development Guide

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Development Setup](#development-setup)
3. [Component Development](#component-development)
4. [Adding New Models](#adding-new-models)
5. [Testing Strategy](#testing-strategy)
6. [Debugging Techniques](#debugging-techniques)
7. [Code Style Guidelines](#code-style-guidelines)
8. [Performance Profiling](#performance-profiling)
9. [Contributing Workflow](#contributing-workflow)

## Architecture Overview

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Input Video                           │
└────────────────────────────┬────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Pipeline Manager                          │
│                 (components/pipeline.py)                     │
└────────────┬──────────────┬──────────────┬──────────────────┘
            │              │              │
            ▼              ▼              ▼
    ┌───────────┐  ┌───────────────┐  ┌──────────────┐
    │   Video   │  │  Character &  │  │  Captioning  │
    │ Analysis  │  │   Dialogue    │  │  Generation  │
    └─────┬─────┘  └───────┬───────┘  └──────┬───────┘
          │                │                  │
          ▼                ▼                  ▼
    ┌───────────┐  ┌───────────────┐  ┌──────────────┐
    │   JSON    │  │     JSON      │  │ Multiple     │
    │  Output   │  │    Output     │  │  Formats     │
    └───────────┘  └───────────────┘  └──────────────┘
```

### Component Architecture

Each component follows a standard structure:

```
component/
├── __init__.py          # Package initialization
├── main.py              # CLI entry point
├── processor.py         # Core processing logic
├── models.py            # Model loading and inference
├── schemas.py           # Data schemas (Pydantic)
├── utils.py             # Helper functions
├── config/              # Component-specific configs
│   └── config.yaml
└── tests/               # Component tests
    ├── test_processor.py
    └── test_models.py
```

### Data Flow

1. **Input Stage**: Video file → Validation → Metadata extraction
2. **Processing Stage**: Parallel component execution → Result aggregation
3. **Output Stage**: Format conversion → File writing → Cleanup

## Development Setup

### Prerequisites

```bash
# System requirements
- Python 3.8+ (3.12 recommended)
- CUDA 11.8+ (for GPU support)
- FFmpeg
- Git

# Development tools
- Docker (optional)
- VS Code or PyCharm
- NVIDIA Docker runtime (for GPU in Docker)
```

### Environment Setup

1. **Clone and Setup Virtual Environment**
   ```bash
   git clone https://github.com/yourusername/hendrix_12aug.git
   cd hendrix_12aug
   python3 -m venv hendrix_dev
   source hendrix_dev/bin/activate
   ```

2. **Install Development Dependencies**
   ```bash
   pip install -r requirements/all.txt
   pip install -r requirements/dev.txt
   ```

3. **Setup Pre-commit Hooks**
   ```bash
   pre-commit install
   pre-commit run --all-files  # Test the setup
   ```

4. **Configure IDE**
   ```bash
   # VS Code
   cp .vscode/settings.example.json .vscode/settings.json
   
   # PyCharm
   # Mark 'hendrix_12aug' as Sources Root
   # Configure Python interpreter to use hendrix_dev
   ```

### Docker Development

```dockerfile
# Dockerfile.dev
FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04

# Install Python and dependencies
RUN apt-get update && apt-get install -y \
    python3.12 python3.12-dev python3-pip \
    ffmpeg git curl

# Setup workspace
WORKDIR /workspace
COPY requirements/ requirements/
RUN pip3 install -r requirements/all.txt -r requirements/dev.txt

# Mount code as volume for development
VOLUME ["/workspace"]

CMD ["/bin/bash"]
```

Build and run:
```bash
docker build -f Dockerfile.dev -t hendrix-dev .
docker run --gpus all -it -v $(pwd):/workspace hendrix-dev
```

## Component Development

### Creating a New Component

1. **Component Structure**
   ```bash
   mkdir -p components/my_component/{config,tests}
   touch components/my_component/{__init__.py,main.py,processor.py,schemas.py}
   ```

2. **Base Component Class**
   ```python
   # components/my_component/processor.py
   from typing import Dict, Any, Optional
   from pathlib import Path
   import logging
   
   from components.base import BaseComponent
   
   class MyComponentProcessor(BaseComponent):
       """Your component description"""
       
       def __init__(self, config: Dict[str, Any]):
           super().__init__(config)
           self.logger = logging.getLogger(__name__)
           
       def process(self, input_path: Path, **kwargs) -> Dict[str, Any]:
           """Main processing method"""
           self.logger.info(f"Processing {input_path}")
           
           # Your processing logic here
           results = {
               "status": "success",
               "data": {}
           }
           
           return results
           
       def validate_input(self, input_path: Path) -> bool:
           """Validate input before processing"""
           return input_path.exists() and input_path.suffix in ['.mp4', '.avi']
   ```

3. **Data Schemas**
   ```python
   # components/my_component/schemas.py
   from pydantic import BaseModel, Field
   from typing import List, Optional
   from datetime import datetime
   
   class ProcessingResult(BaseModel):
       """Schema for processing results"""
       timestamp: datetime = Field(default_factory=datetime.now)
       status: str
       data: Dict[str, Any]
       errors: Optional[List[str]] = None
       
       class Config:
           json_encoders = {
               datetime: lambda v: v.isoformat()
           }
   ```

4. **CLI Entry Point**
   ```python
   # components/my_component/main.py
   import argparse
   import json
   from pathlib import Path
   
   from .processor import MyComponentProcessor
   from components.config_manager import ConfigManager
   
   def main():
       parser = argparse.ArgumentParser(description="My Component")
       parser.add_argument("--input", required=True, help="Input file")
       parser.add_argument("--output", required=True, help="Output directory")
       parser.add_argument("--config", help="Config file path")
       
       args = parser.parse_args()
       
       # Load configuration
       config = ConfigManager(args.config).get_component_config("my_component")
       
       # Process
       processor = MyComponentProcessor(config)
       results = processor.process(Path(args.input))
       
       # Save results
       output_path = Path(args.output) / "results.json"
       output_path.write_text(json.dumps(results, indent=2))
       
   if __name__ == "__main__":
       main()
   ```

### Integrating with Pipeline

1. **Register Component**
   ```python
   # components/pipeline.py
   from components.my_component.processor import MyComponentProcessor
   
   class Pipeline:
       def __init__(self, config):
           self.components = {
               "video": VideoAnalysisProcessor(config),
               "audio": AudioProcessor(config),
               "my_component": MyComponentProcessor(config),  # Add here
           }
   ```

2. **Update Configuration**
   ```yaml
   # configs/base_config.yaml
   components:
     my_component:
       enabled: true
       settings:
         param1: value1
         param2: value2
   ```

## Adding New Models

### Model Integration Steps

1. **Define Model Configuration**
   ```yaml
   # configs/models.yaml
   models:
     my_new_model:
       name: "My New Model"
       type: "vision_language"
       source: "huggingface"
       model_id: "organization/model-name"
       revision: "main"
       requirements:
         gpu_memory: 8  # GB
         quantizable: true
       configs:
         default:
           temperature: 0.7
           max_tokens: 150
   ```

2. **Create Model Loader**
   ```python
   # components/captioning/models/my_model.py
   from typing import Optional, Dict, Any
   import torch
   from transformers import AutoModelForCausalLM, AutoTokenizer
   
   class MyModelLoader:
       """Loader for My New Model"""
       
       def __init__(self, model_config: Dict[str, Any]):
           self.config = model_config
           self.model = None
           self.tokenizer = None
           
       def load(self, device: str = "cuda", quantize: Optional[str] = None):
           """Load model with optional quantization"""
           model_id = self.config["model_id"]
           
           # Load tokenizer
           self.tokenizer = AutoTokenizer.from_pretrained(model_id)
           
           # Load model with quantization if specified
           if quantize == "8bit":
               self.model = AutoModelForCausalLM.from_pretrained(
                   model_id,
                   load_in_8bit=True,
                   device_map="auto"
               )
           else:
               self.model = AutoModelForCausalLM.from_pretrained(
                   model_id,
                   torch_dtype=torch.float16,
                   device_map="auto"
               )
               
       def generate(self, prompt: str, **kwargs) -> str:
           """Generate text from prompt"""
           inputs = self.tokenizer(prompt, return_tensors="pt")
           outputs = self.model.generate(
               **inputs,
               max_new_tokens=kwargs.get("max_tokens", 150),
               temperature=kwargs.get("temperature", 0.7)
           )
           return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
   ```

3. **Register Model**
   ```python
   # components/captioning/model_registry.py
   from .models.my_model import MyModelLoader
   
   MODEL_REGISTRY = {
       "llava_7b": LLaVALoader,
       "my_new_model": MyModelLoader,  # Add here
   }
   ```

### Model Testing

```python
# tests/test_my_model.py
import pytest
from components.captioning.models.my_model import MyModelLoader

@pytest.fixture
def model_config():
    return {
        "model_id": "test/model",
        "temperature": 0.7
    }

def test_model_loading(model_config):
    """Test model loads correctly"""
    loader = MyModelLoader(model_config)
    loader.load(device="cpu")
    assert loader.model is not None
    assert loader.tokenizer is not None

def test_model_generation(model_config):
    """Test model generates output"""
    loader = MyModelLoader(model_config)
    loader.load(device="cpu")
    
    output = loader.generate("Test prompt")
    assert isinstance(output, str)
    assert len(output) > 0
```

## Testing Strategy

### Test Structure

```
tests/
├── unit/                 # Unit tests
│   ├── test_config_manager.py
│   ├── test_video_utils.py
│   └── test_schemas.py
├── integration/          # Integration tests
│   ├── test_pipeline.py
│   └── test_components.py
├── fixtures/             # Test data
│   ├── sample_video.mp4
│   └── expected_outputs/
└── conftest.py          # Pytest configuration
```

### Writing Tests

1. **Unit Tests**
   ```python
   # tests/unit/test_config_manager.py
   import pytest
   from components.config_manager import ConfigManager
   
   def test_config_loading():
       """Test configuration loads correctly"""
       config = ConfigManager("configs/test_config.yaml")
       assert config.get("components") is not None
       
   def test_config_override():
       """Test configuration override works"""
       config = ConfigManager()
       config.set("test.value", 42)
       assert config.get("test.value") == 42
   ```

2. **Integration Tests**
   ```python
   # tests/integration/test_pipeline.py
   import pytest
   from pathlib import Path
   from hendrix_pipeline import Pipeline
   
   @pytest.fixture
   def sample_video():
       return Path("tests/fixtures/sample_video.mp4")
       
   def test_pipeline_execution(sample_video, tmp_path):
       """Test full pipeline execution"""
       pipeline = Pipeline(profile="test")
       results = pipeline.process_video(
           video_path=sample_video,
           output_dir=tmp_path
       )
       
       assert results["status"] == "success"
       assert (tmp_path / "captions.srt").exists()
   ```

3. **Mocking External Services**
   ```python
   # tests/unit/test_api_calls.py
   from unittest.mock import patch, MagicMock
   
   @patch("openai.Completion.create")
   def test_openai_captioning(mock_openai):
       """Test OpenAI API integration"""
       mock_openai.return_value = MagicMock(
           choices=[{"text": "Generated caption"}]
       )
       
       from components.captioning.openai_client import generate_caption
       result = generate_caption("test prompt")
       
       assert result == "Generated caption"
       mock_openai.assert_called_once()
   ```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=components --cov-report=html

# Run specific test file
pytest tests/unit/test_config_manager.py

# Run with markers
pytest -m "not slow"  # Skip slow tests
pytest -m integration  # Only integration tests

# Parallel execution
pytest -n auto  # Use all CPU cores
```

## Debugging Techniques

### Logging Configuration

```python
# components/utils/logging.py
import logging
import sys
from pathlib import Path

def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    component: str = "hendrix"
):
    """Setup structured logging"""
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # File handler if specified
    handlers = [console_handler]
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        handlers=handlers
    )
    
    # Component-specific logger
    logger = logging.getLogger(component)
    return logger
```

### Debug Mode

```python
# components/base.py
class BaseComponent:
    def __init__(self, config: Dict[str, Any], debug: bool = False):
        self.config = config
        self.debug = debug
        
        if self.debug:
            self._setup_debug()
            
    def _setup_debug(self):
        """Enable debug features"""
        # Save intermediate outputs
        self.save_intermediate = True
        
        # Enable profiling
        self.profiler = cProfile.Profile()
        
        # Verbose logging
        self.logger.setLevel(logging.DEBUG)
        
    def _debug_checkpoint(self, data: Any, name: str):
        """Save debug checkpoint"""
        if self.debug and self.save_intermediate:
            debug_path = Path(f"debug/{name}_{timestamp()}.pkl")
            debug_path.parent.mkdir(exist_ok=True)
            
            with open(debug_path, 'wb') as f:
                pickle.dump(data, f)
                
            self.logger.debug(f"Saved debug checkpoint: {debug_path}")
```

### Memory Profiling

```python
# tools/memory_profiler.py
import tracemalloc
import psutil
import GPUtil

class MemoryProfiler:
    """Profile memory usage during execution"""
    
    def __init__(self):
        self.snapshots = []
        
    def start(self):
        """Start memory profiling"""
        tracemalloc.start()
        self.start_snapshot = tracemalloc.take_snapshot()
        
    def checkpoint(self, label: str):
        """Take memory snapshot"""
        snapshot = tracemalloc.take_snapshot()
        stats = snapshot.compare_to(self.start_snapshot, 'lineno')
        
        # System memory
        process = psutil.Process()
        system_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # GPU memory if available
        gpu_memory = 0
        if GPUtil.getGPUs():
            gpu = GPUtil.getGPUs()[0]
            gpu_memory = gpu.memoryUsed
            
        self.snapshots.append({
            "label": label,
            "system_memory_mb": system_memory,
            "gpu_memory_mb": gpu_memory,
            "top_allocations": stats[:10]
        })
        
    def report(self):
        """Generate memory report"""
        for snapshot in self.snapshots:
            print(f"\n=== {snapshot['label']} ===")
            print(f"System Memory: {snapshot['system_memory_mb']:.1f} MB")
            print(f"GPU Memory: {snapshot['gpu_memory_mb']:.1f} MB")
            print("\nTop allocations:")
            for stat in snapshot['top_allocations']:
                print(stat)
```

### Interactive Debugging

```python
# Enable interactive debugging
import pdb

def process_video(video_path):
    # ... some code ...
    
    if DEBUG:
        pdb.set_trace()  # Breakpoint
        
    # Or use breakpoint() in Python 3.7+
    if suspicious_condition:
        breakpoint()
```

## Code Style Guidelines

### Python Style Guide

Follow PEP 8 with these additions:

1. **Line Length**: 120 characters maximum
2. **Imports**: Group in order: stdlib, third-party, local
3. **Docstrings**: Use Google style
4. **Type Hints**: Required for public APIs

```python
# Example of proper style
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path

import numpy as np
import torch
from transformers import AutoModel

from components.base import BaseComponent
from components.utils import timer_decorator


class VideoProcessor(BaseComponent):
    """Process video frames for analysis.
    
    This class handles video loading, frame extraction, and preprocessing
    for downstream analysis tasks.
    
    Args:
        config: Configuration dictionary
        device: Device to use for processing ('cuda' or 'cpu')
        
    Attributes:
        model: The loaded video processing model
        fps: Frames per second of the video
        
    Example:
        >>> processor = VideoProcessor(config, device='cuda')
        >>> frames = processor.extract_frames('video.mp4')
    """
    
    def __init__(
        self,
        config: Dict[str, Any],
        device: str = "cuda"
    ) -> None:
        super().__init__(config)
        self.device = device
        self.model = self._load_model()
        
    @timer_decorator
    def extract_frames(
        self,
        video_path: Path,
        sample_rate: int = 1
    ) -> List[np.ndarray]:
        """Extract frames from video at specified sample rate.
        
        Args:
            video_path: Path to the video file
            sample_rate: Extract every nth frame
            
        Returns:
            List of frames as numpy arrays
            
        Raises:
            ValueError: If video_path doesn't exist
            RuntimeError: If video cannot be decoded
        """
        if not video_path.exists():
            raise ValueError(f"Video not found: {video_path}")
            
        # Implementation here
        frames = []
        return frames
```

### Code Formatting

Use Black formatter with configuration:

```toml
# pyproject.toml
[tool.black]
line-length = 120
target-version = ['py38', 'py39', 'py310', 'py311', 'py312']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
  | archive
)/
'''
```

### Linting Configuration

```ini
# .flake8
[flake8]
max-line-length = 120
exclude = 
    .git,
    __pycache__,
    build,
    dist,
    archive,
    venv
ignore = 
    E203,  # whitespace before ':'
    W503,  # line break before binary operator
per-file-ignores =
    __init__.py:F401
```

## Performance Profiling

### CPU Profiling

```python
# tools/profile_pipeline.py
import cProfile
import pstats
from pstats import SortKey

def profile_pipeline(video_path: str, output_file: str = "profile_stats"):
    """Profile pipeline execution"""
    
    profiler = cProfile.Profile()
    
    # Start profiling
    profiler.enable()
    
    # Run pipeline
    from hendrix_pipeline import Pipeline
    pipeline = Pipeline()
    pipeline.process_video(video_path)
    
    # Stop profiling
    profiler.disable()
    
    # Save stats
    profiler.dump_stats(f"{output_file}.prof")
    
    # Print summary
    stats = pstats.Stats(profiler)
    stats.sort_stats(SortKey.CUMULATIVE)
    stats.print_stats(20)  # Top 20 functions
    
    # Generate call graph (requires gprof2dot)
    import subprocess
    subprocess.run([
        "gprof2dot", "-f", "pstats", f"{output_file}.prof",
        "-o", f"{output_file}.dot"
    ])
    subprocess.run([
        "dot", "-Tpng", f"{output_file}.dot",
        "-o", f"{output_file}.png"
    ])
```

### GPU Profiling

```python
# tools/gpu_profiler.py
import torch
from torch.profiler import profile, ProfilerActivity

def profile_gpu_operations(model, input_data):
    """Profile GPU operations"""
    
    with profile(
        activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA],
        record_shapes=True,
        profile_memory=True,
        with_stack=True
    ) as prof:
        with torch.no_grad():
            for _ in range(10):  # Warm up
                model(input_data)
                
            for _ in range(100):  # Profile
                model(input_data)
                
    # Print summary
    print(prof.key_averages().table(sort_by="cuda_time_total", row_limit=10))
    
    # Export to Chrome tracing format
    prof.export_chrome_trace("gpu_trace.json")
    
    # Export to TensorBoard
    prof.export_stacks("profiler_stacks.txt", "self_cuda_time_total")
```

### Benchmarking

```python
# benchmarks/benchmark_pipeline.py
import time
import statistics
from pathlib import Path
import pandas as pd

def benchmark_pipeline(video_files: List[Path], iterations: int = 3):
    """Benchmark pipeline performance"""
    
    results = []
    
    for video in video_files:
        video_times = []
        
        for i in range(iterations):
            start_time = time.time()
            
            # Run pipeline
            pipeline = Pipeline(profile="fast")
            pipeline.process_video(video)
            
            elapsed = time.time() - start_time
            video_times.append(elapsed)
            
        # Calculate statistics
        results.append({
            "video": video.name,
            "size_mb": video.stat().st_size / 1024 / 1024,
            "mean_time": statistics.mean(video_times),
            "std_time": statistics.stdev(video_times) if len(video_times) > 1 else 0,
            "min_time": min(video_times),
            "max_time": max(video_times)
        })
        
    # Create report
    df = pd.DataFrame(results)
    df.to_csv("benchmark_results.csv", index=False)
    
    print("\n=== Benchmark Results ===")
    print(df.to_string())
    
    # Performance metrics
    print(f"\nAverage processing speed: {df['size_mb'].sum() / df['mean_time'].sum():.2f} MB/s")
```

## Contributing Workflow

### Development Process

1. **Fork and Clone**
   ```bash
   # Fork on GitHub, then:
   git clone https://github.com/yourusername/hendrix_12aug.git
   cd hendrix_12aug
   git remote add upstream https://github.com/original/hendrix_12aug.git
   ```

2. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   # Or for bugfix:
   git checkout -b fix/issue-description
   ```

3. **Development Cycle**
   ```bash
   # Make changes
   vim components/your_file.py
   
   # Run tests
   pytest tests/unit/test_your_feature.py
   
   # Format code
   black components/
   flake8 components/
   
   # Commit with conventional commits
   git add -A
   git commit -m "feat: add new video filter capability"
   ```

4. **Stay Updated**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

5. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   # Create PR on GitHub
   ```

### Pull Request Guidelines

1. **PR Title**: Use conventional commit format
   - `feat: add new feature`
   - `fix: resolve issue with X`
   - `docs: update development guide`
   - `refactor: improve performance of Y`

2. **PR Description Template**
   ```markdown
   ## Description
   Brief description of changes
   
   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Breaking change
   - [ ] Documentation update
   
   ## Testing
   - [ ] Unit tests pass
   - [ ] Integration tests pass
   - [ ] Manual testing completed
   
   ## Checklist
   - [ ] Code follows style guidelines
   - [ ] Self-review completed
   - [ ] Comments added for complex code
   - [ ] Documentation updated
   - [ ] No new warnings
   ```

3. **Code Review Process**
   - Respond to feedback promptly
   - Use "resolve conversation" when addressed
   - Request re-review after changes
   - Squash commits before merge if requested

### Release Process

1. **Version Bumping**
   ```bash
   # Update version in setup.py, __init__.py
   bump2version minor  # or major, patch
   ```

2. **Create Release Notes**
   ```markdown
   # Release v2.1.0
   
   ## Features
   - Added GPU memory profiling
   - New model: GPT-4 Vision support
   
   ## Fixes
   - Fixed memory leak in video processing
   - Resolved CUDA compatibility issues
   
   ## Breaking Changes
   - None
   
   ## Contributors
   - @username1
   - @username2
   ```

3. **Tag and Release**
   ```bash
   git tag -a v2.1.0 -m "Release version 2.1.0"
   git push origin v2.1.0
   # Create release on GitHub
   ```

---

For questions or support, join our [Discord community](https://discord.gg/hendrix) or open an issue on GitHub.