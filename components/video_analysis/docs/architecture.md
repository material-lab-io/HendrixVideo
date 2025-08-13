# Architecture Overview

The Hendrix Video Analysis Pipeline is designed with modularity, scalability, and extensibility in mind. This document provides a comprehensive overview of the system architecture.

## System Design Principles

1. **Modular Pipeline**: Each stage operates independently
2. **Streaming Processing**: Handle videos of any length without loading entirely into memory
3. **Fail-Safe Design**: Graceful degradation and resume capability
4. **Configuration-Driven**: Behavior controlled through YAML configuration
5. **Model Agnostic**: Easy to swap or add new models

## High-Level Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Input Video   │────▶│  Video Processor │────▶│ Frame Extractor │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Pipeline Orchestrator                     │
├─────────────────┬─────────────────┬─────────────────────────────┤
│ Shot Detection  │Scene Construction│   Cinematic Analysis        │
│   (Stage 1)     │    (Stage 2)     │      (Stage 3)             │
└─────────────────┴─────────────────┴─────────────────────────────┘
         │                  │                      │
         ▼                  ▼                      ▼
┌─────────────────┐ ┌──────────────┐    ┌─────────────────┐
│   Shot List     │ │ Scene Graph  │    │ Style Analysis  │
│   + Keyframes   │ │ + Narratives │    │   + Metrics     │
└─────────────────┘ └──────────────┘    └─────────────────┘
```

## Component Architecture

### 1. Core Components

#### VideoProcessor (`src/utils/video_processor.py`)
- Handles video file I/O using MoviePy and OpenCV
- Provides frame extraction and metadata
- Implements streaming frame access
- Memory-efficient video handling

```python
class VideoProcessor:
    def __init__(self, video_path: str):
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)
        
    def get_frame(self, frame_number: int) -> np.ndarray:
        """Extract specific frame without loading entire video"""
        
    def extract_frames(self, indices: List[int]) -> List[np.ndarray]:
        """Batch frame extraction"""
```

#### Pipeline Orchestrator (`src/main.py`)
- Coordinates execution of pipeline stages
- Manages configuration and state
- Implements resume functionality
- Handles error recovery

```python
class VideoAnalysisPipeline:
    def __init__(self, config_path: str):
        self.config = load_config(config_path)
        self.shot_detector = ShotDetectionPipeline(self.config)
        self.scene_constructor = SceneConstructionPipeline(self.config)
        self.cinematic_analyzer = CinematicAnalysisPipeline(self.config)
```

### 2. Pipeline Stages

#### Stage 1: Shot Detection (`src/pipeline/shot_detection.py`)

**Purpose**: Identify shot boundaries and extract representative keyframes

**Components**:
- Shot boundary detectors (TransNetV2, AutoShot)
- Keyframe extraction strategies
- Shot filtering and validation

**Data Flow**:
```
Video → Frame Extraction → Shot Detection → Shot Filtering → Keyframe Extraction
```

#### Stage 2: Scene Construction (`src/pipeline/scene_construction.py`)

**Purpose**: Group shots into semantic scenes with descriptions

**Components**:
- Vision-Language models (LLaVA)
- Scene clustering algorithms
- Narrative generation

**Data Flow**:
```
Shots + Keyframes → Visual Analysis → Semantic Grouping → Scene Description
```

#### Stage 3: Cinematic Analysis (`src/pipeline/cinematic_analysis.py`)

**Purpose**: Analyze cinematographic style and techniques

**Components**:
- Style classifiers
- Motion analysis
- Composition metrics

**Data Flow**:
```
Scenes + Metadata → Style Analysis → Technique Detection → Report Generation
```

### 3. Model Layer

#### Model Abstraction
Each model implements a common interface:

```python
class BaseModel(ABC):
    @abstractmethod
    def load_model(self):
        """Load model weights and initialize"""
        
    @abstractmethod
    def process(self, input_data):
        """Process input and return results"""
        
    @abstractmethod
    def unload(self):
        """Clean up resources"""
```

#### Supported Models

**Shot Detection**:
- TransNetV2: Deep learning-based shot boundary detection
- AutoShot: Traditional CV methods with motion analysis
- FrameDiff: Fallback using frame differences

**Scene Analysis**:
- LLaVA-1.5-7B: Vision-language understanding
- CLIP: Visual-semantic similarity (planned)

**Cinematic Analysis**:
- CinematicVLM: Cinematography-specific model (planned)

### 4. Data Models

#### Shot Schema (`src/schemas/shot.py`)
```python
@dataclass
class Shot:
    shot_id: int
    start: float  # seconds
    end: float
    keyframe_path: str
    confidence: float
    transition_type: str
```

#### Scene Schema (`src/schemas/scene.py`)
```python
@dataclass
class Scene:
    scene_id: int
    summary: str
    contained_shots: List[int]
    setting: Optional[str]
    mood: Optional[str]
    start_time: float
    end_time: float
```

## System Interactions

### Sequence Diagram: Video Processing

```
User            Pipeline         ShotDetector      SceneConstructor    Output
 │                 │                  │                    │              │
 ├──analyze(video)─▶                 │                    │              │
 │                 ├──load_video()───▶                    │              │
 │                 │                  │                    │              │
 │                 ├──detect_shots()─▶                    │              │
 │                 │                  ├──process_frames()─▶              │
 │                 │                  │◀─────shots────────┤              │
 │                 │◀────shot_list────┤                    │              │
 │                 │                  │                    │              │
 │                 ├──construct_scenes()──────────────────▶              │
 │                 │                  │                    ├──analyze()──▶
 │                 │                  │                    │◀───scenes───┤
 │                 │◀─────────────────scene_list──────────┤              │
 │                 │                  │                    │              │
 │                 ├──save_results()──────────────────────────────────▶  │
 │◀────complete────┤                  │                    │              │
```

### State Management

The pipeline maintains state for:
1. **Progress Tracking**: Current stage and processed items
2. **Intermediate Results**: Shots, keyframes, partial scenes
3. **Resource Management**: Loaded models and cached data

```python
class PipelineState:
    def __init__(self):
        self.current_stage = None
        self.completed_stages = set()
        self.shots = []
        self.scenes = []
        self.checkpoints = {}
```

## Extensibility

### Adding New Models

1. Implement the model interface:
```python
class MyCustomModel(BaseModel):
    def load_model(self):
        self.model = load_pretrained_model("my-model")
        
    def process(self, frames):
        return self.model.predict(frames)
```

2. Register in configuration:
```yaml
shot_detection:
  detector: "my_custom_model"
  model_config:
    weights: "path/to/weights"
```

### Adding New Pipeline Stages

1. Create stage class:
```python
class CustomAnalysisPipeline:
    def __init__(self, config):
        self.config = config
        
    def process(self, input_data):
        # Implement processing logic
        return results
```

2. Integrate into main pipeline:
```python
self.custom_analyzer = CustomAnalysisPipeline(config)
results = self.custom_analyzer.process(scenes)
```

## Performance Considerations

### Memory Management
- Streaming video processing (never load entire video)
- Batch processing with configurable sizes
- Automatic garbage collection between stages
- GPU memory monitoring and management

### Parallel Processing
- Multi-threaded frame extraction
- GPU-accelerated model inference
- Asynchronous I/O operations
- Optional multi-GPU support

### Caching Strategy
- Model weight caching
- Intermediate result caching
- Keyframe caching with TTL
- Configuration-based cache control

## Error Handling

### Fault Tolerance
```python
try:
    result = stage.process(data)
except ModelError as e:
    logger.error(f"Model failed: {e}")
    result = fallback_method(data)
except Exception as e:
    logger.error(f"Stage failed: {e}")
    if self.config.get("fail_fast"):
        raise
    else:
        return partial_results
```

### Resume Capability
- Checkpoint after each stage
- Atomic writes for results
- Stage-level recovery
- Configurable retry logic

## Configuration System

### Hierarchical Configuration
```yaml
# Global settings
pipeline:
  batch_size: 32
  num_workers: 8

# Stage-specific settings
shot_detection:
  detector: "transnetv2"
  threshold: 0.5
  
# Model-specific settings
models:
  llava:
    model_id: "llava-hf/llava-1.5-7b-hf"
    device: "cuda:0"
```

### Environment Variable Override
```bash
HENDRIX_BATCH_SIZE=64 python src/main.py video.mp4
```

## Deployment Architecture

### Docker Deployment
```dockerfile
FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04

# Install dependencies
RUN apt-get update && apt-get install -y \
    python3.8 ffmpeg

# Copy application
COPY . /app
WORKDIR /app

# Install Python packages
RUN pip install -r requirements.txt

ENTRYPOINT ["python", "src/main.py"]
```

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hendrix-video-analysis
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: hendrix
        image: hendrix-video-analysis:latest
        resources:
          limits:
            nvidia.com/gpu: 1
```

## Future Architecture Enhancements

1. **Microservices Architecture**: Separate services for each stage
2. **Message Queue Integration**: RabbitMQ/Kafka for job distribution
3. **REST API**: HTTP endpoints for video submission
4. **WebSocket Support**: Real-time progress updates
5. **Cloud Storage Integration**: S3/GCS for video and result storage