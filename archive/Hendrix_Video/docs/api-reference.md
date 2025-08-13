# API Reference

Complete API documentation for the Hendrix Video Analysis Pipeline.

## Core Classes

### VideoAnalysisPipeline

Main orchestrator class that coordinates the entire analysis pipeline.

```python
class VideoAnalysisPipeline:
    """
    Main pipeline for video analysis.
    
    Attributes:
        config (dict): Pipeline configuration
        shot_detector (ShotDetectionPipeline): Shot detection stage
        scene_constructor (SceneConstructionPipeline): Scene construction stage
        cinematic_analyzer (CinematicAnalysisPipeline): Cinematic analysis stage
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize the pipeline with configuration.
        
        Args:
            config_path: Path to YAML configuration file
            
        Raises:
            FileNotFoundError: If config file not found
            ValueError: If config is invalid
        """
    
    def analyze_video(
        self, 
        video_path: str, 
        resume_from: Optional[str] = None,
        output_dir: Optional[str] = None
    ) -> dict:
        """
        Analyze a video through all pipeline stages.
        
        Args:
            video_path: Path to input video file
            resume_from: Stage to resume from ('shot_detection', 'scene_construction')
            output_dir: Override output directory from config
            
        Returns:
            Dictionary containing analysis results:
            {
                'shots': List[Shot],
                'scenes': List[Scene],
                'analysis': dict,
                'metadata': dict
            }
            
        Raises:
            FileNotFoundError: If video file not found
            RuntimeError: If pipeline fails
        """
```

## Pipeline Stages

### ShotDetectionPipeline

Handles shot boundary detection and keyframe extraction.

```python
class ShotDetectionPipeline:
    """Stage 1: Shot boundary detection."""
    
    def __init__(self, config: dict):
        """
        Initialize with configuration.
        
        Args:
            config: Pipeline configuration dictionary
        """
    
    def detect_shots(
        self, 
        video_path: str,
        save_keyframes: bool = True
    ) -> List[Shot]:
        """
        Detect shot boundaries in video.
        
        Args:
            video_path: Path to video file
            save_keyframes: Whether to extract and save keyframes
            
        Returns:
            List of Shot objects with boundaries and keyframes
            
        Example:
            shots = detector.detect_shots("video.mp4")
            print(f"Found {len(shots)} shots")
        """
    
    def extract_keyframes(
        self,
        video_processor: VideoProcessor,
        shots: List[Shot],
        method: str = "middle"
    ) -> None:
        """
        Extract keyframe for each shot.
        
        Args:
            video_processor: Video processor instance
            shots: List of shots to extract keyframes for
            method: Extraction method ('middle', 'first', 'last', 'best')
        """
```

### SceneConstructionPipeline

Groups shots into semantic scenes with descriptions.

```python
class SceneConstructionPipeline:
    """Stage 2: Semantic scene construction."""
    
    def __init__(self, config: dict):
        """Initialize with configuration."""
    
    def process_shots(
        self,
        shots: List[Shot],
        save_intermediate: bool = True,
        individual_mode: bool = False
    ) -> List[Scene]:
        """
        Process shots to construct semantic scenes.
        
        Args:
            shots: List of Shot objects from Stage 1
            save_intermediate: Save intermediate results
            individual_mode: Process each shot individually
            
        Returns:
            List of Scene objects with descriptions
            
        Example:
            scenes = constructor.process_shots(shots, individual_mode=True)
            for scene in scenes:
                print(f"Scene {scene.scene_id}: {scene.summary}")
        """
    
    def refine_scene(
        self,
        scene: Scene,
        shots: List[Shot],
        custom_prompt: Optional[str] = None
    ) -> Scene:
        """
        Refine a single scene with additional analysis.
        
        Args:
            scene: Scene to refine
            shots: All shots in the video
            custom_prompt: Custom refinement prompt
            
        Returns:
            Refined Scene object
        """
```

## Data Models

### Shot

Represents a single shot in the video.

```python
@dataclass
class Shot:
    """
    Video shot with temporal boundaries.
    
    Attributes:
        shot_id: Unique identifier
        start: Start time in seconds
        end: End time in seconds
        duration: Shot duration in seconds
        keyframe_path: Path to extracted keyframe
        confidence: Detection confidence (0-1)
        transition_type: Type of transition (cut, dissolve, fade)
    """
    
    shot_id: int
    start: float
    end: float
    duration: float = field(init=False)
    keyframe_path: Optional[str] = None
    confidence: float = 1.0
    transition_type: str = "cut"
    
    def __post_init__(self):
        """Calculate duration from start and end."""
        self.duration = self.end - self.start
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Shot':
        """Create Shot from dictionary."""
```

### Scene

Represents a semantic scene composed of multiple shots.

```python
@dataclass
class Scene:
    """
    Semantic scene containing multiple shots.
    
    Attributes:
        scene_id: Unique identifier
        summary: Text description of the scene
        contained_shots: List of shot IDs in this scene
        setting: Scene setting/location
        mood: Emotional tone of the scene
        start_time: Scene start time in seconds
        end_time: Scene end time in seconds
    """
    
    scene_id: int
    summary: str
    contained_shots: List[int]
    setting: Optional[str] = None
    mood: Optional[str] = None
    start_time: float = 0.0
    end_time: float = 0.0
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Scene':
        """Create Scene from dictionary."""
```

## Models

### TransNetV2

Shot boundary detection using TransNetV2.

```python
class TransNetV2Detector:
    """TransNetV2 shot boundary detector."""
    
    def __init__(self, config: dict):
        """
        Initialize TransNetV2 model.
        
        Args:
            config: Model configuration
        """
    
    def detect_shots(
        self,
        video_processor: VideoProcessor
    ) -> List[Dict[str, Any]]:
        """
        Detect shot boundaries in video.
        
        Args:
            video_processor: Video processor instance
            
        Returns:
            List of shot dictionaries with boundaries
        """
```

### LLaVAAnalyzer

Vision-language analysis using LLaVA.

```python
class LLaVAAnalyzer:
    """LLaVA vision-language analyzer."""
    
    def __init__(self, config: dict):
        """
        Initialize LLaVA model.
        
        Args:
            config: Model configuration including model_id, device, etc.
        """
    
    def analyze_single_image(
        self,
        image_path: str,
        prompt: str
    ) -> str:
        """
        Analyze single image with prompt.
        
        Args:
            image_path: Path to image file
            prompt: Analysis prompt
            
        Returns:
            Model response text
            
        Example:
            description = analyzer.analyze_single_image(
                "frame.jpg",
                "Describe the scene in this image"
            )
        """
    
    def analyze_shot_sequence(
        self,
        image_paths: List[str],
        shot_ids: List[int],
        prompt: str
    ) -> List[dict]:
        """
        Analyze sequence of shots for scene construction.
        
        Args:
            image_paths: List of keyframe paths
            shot_ids: Corresponding shot IDs
            prompt: Scene construction prompt
            
        Returns:
            List of scene dictionaries
        """
```

## Utilities

### VideoProcessor

Handles video file operations and frame extraction.

```python
class VideoProcessor:
    """Video file processor and frame extractor."""
    
    def __init__(self, video_path: str):
        """
        Initialize video processor.
        
        Args:
            video_path: Path to video file
            
        Raises:
            FileNotFoundError: If video not found
            ValueError: If video cannot be opened
        """
    
    def get_metadata(self) -> dict:
        """
        Get video metadata.
        
        Returns:
            Dictionary with video properties:
            {
                'filename': str,
                'duration': float,
                'fps': float,
                'width': int,
                'height': int,
                'total_frames': int,
                'codec': str,
                'format': str
            }
        """
    
    def get_frame(self, frame_number: int) -> np.ndarray:
        """
        Extract single frame.
        
        Args:
            frame_number: Frame index (0-based)
            
        Returns:
            Frame as numpy array (H, W, C) in RGB format
            
        Raises:
            ValueError: If frame number out of range
        """
    
    def extract_frames(
        self,
        frame_indices: List[int],
        resize: Optional[Tuple[int, int]] = None
    ) -> List[np.ndarray]:
        """
        Extract multiple frames efficiently.
        
        Args:
            frame_indices: List of frame numbers to extract
            resize: Optional (width, height) to resize frames
            
        Returns:
            List of frames as numpy arrays
        """
    
    def save_frame(
        self,
        frame: np.ndarray,
        output_path: str,
        quality: int = 90
    ) -> None:
        """
        Save frame to file.
        
        Args:
            frame: Frame array
            output_path: Output file path
            quality: JPEG quality (1-100)
        """
```

### Configuration Utilities

```python
def load_config(config_path: str) -> dict:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to config file
        
    Returns:
        Configuration dictionary
        
    Raises:
        FileNotFoundError: If config not found
        yaml.YAMLError: If config invalid
    """

def merge_configs(base: dict, override: dict) -> dict:
    """
    Merge configuration dictionaries.
    
    Args:
        base: Base configuration
        override: Override values
        
    Returns:
        Merged configuration
    """

def validate_config(config: dict) -> None:
    """
    Validate configuration.
    
    Args:
        config: Configuration to validate
        
    Raises:
        ValueError: If configuration invalid
    """
```

## Example Usage

### Basic Pipeline Usage

```python
from src.main import VideoAnalysisPipeline

# Initialize pipeline
pipeline = VideoAnalysisPipeline("config.yaml")

# Analyze video
results = pipeline.analyze_video("input_video.mp4")

# Access results
shots = results['shots']
scenes = results['scenes']

print(f"Found {len(shots)} shots and {len(scenes)} scenes")
```

### Custom Configuration

```python
# Load and modify configuration
import yaml

with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

# Modify settings
config['scene_construction']['batch_size'] = 20
config['shot_detection']['min_shot_duration'] = 1.0

# Save custom config
with open("custom_config.yaml", "w") as f:
    yaml.dump(config, f)

# Use custom config
pipeline = VideoAnalysisPipeline("custom_config.yaml")
```

### Direct Model Usage

```python
from src.models.llava import LLaVAAnalyzer

# Initialize model
config = {
    "model": "llava-hf/llava-1.5-7b-hf",
    "device": "cuda:0",
    "use_gpu": True
}
analyzer = LLaVAAnalyzer(config)

# Analyze image
description = analyzer.analyze_single_image(
    "frame.jpg",
    "Describe the cinematography in this shot"
)
print(description)
```

### Batch Processing

```python
import glob
from concurrent.futures import ProcessPoolExecutor

def process_video(video_path):
    pipeline = VideoAnalysisPipeline()
    return pipeline.analyze_video(video_path)

# Process multiple videos
video_files = glob.glob("videos/*.mp4")
with ProcessPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(process_video, video_files))
```

## Error Handling

All methods may raise the following exceptions:

- `FileNotFoundError`: Input files not found
- `ValueError`: Invalid parameters or data
- `RuntimeError`: Processing errors
- `MemoryError`: Insufficient memory
- `torch.cuda.OutOfMemoryError`: GPU memory exhausted

Example error handling:

```python
try:
    results = pipeline.analyze_video("video.mp4")
except FileNotFoundError:
    print("Video file not found")
except torch.cuda.OutOfMemoryError:
    print("GPU out of memory, try reducing batch size")
except Exception as e:
    print(f"Analysis failed: {e}")
```