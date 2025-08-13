# Hendrix Video Analysis Pipeline - Technical Overview

## Executive Summary

Hendrix Video Analysis is a sophisticated multi-stage video processing pipeline that automatically analyzes video content through shot detection, scene construction, and cinematic analysis. The system leverages state-of-the-art deep learning models to transform raw video into structured, semantically-rich data about visual content, narrative flow, and cinematographic techniques.

## System Architecture

### Pipeline Overview
```
Input Video → Shot Detection → Scene Construction → Cinematic Analysis → Structured Output
    │              │                  │                     │                    │
    │         TransNetV2/        LLaVA-7B VLM         Future VLM          JSON/HTML
    │         AutoShot           (Visual-Language)     (Placeholder)       Reports
    │                                                                           
    └─────────────── Keyframe Extraction & Storage ──────────────────────────┘
```

### Core Technologies
- **Language**: Python 3.8+
- **Deep Learning Framework**: PyTorch 2.0+
- **Computer Vision**: OpenCV, MoviePy
- **Vision-Language Models**: LLaVA (Large Language and Vision Assistant)
- **Shot Detection**: TransNetV2 (CNN-based shot boundary detection)
- **ML Libraries**: Transformers (Hugging Face), scikit-learn
- **Processing**: CUDA GPU acceleration, async pipeline stages

## Stage 1: Shot Detection

### Purpose
Identifies visual discontinuities in video to segment it into individual shots (continuous camera takes).

### Technical Implementation
```python
# Models Available:
1. TransNetV2: Deep learning model using 3D CNN architecture
   - Detects both hard cuts and gradual transitions
   - Confidence scores for each boundary
   
2. AutoShot: Classical CV approach (fallback)
   - Frame difference calculation
   - Histogram comparison
   - Motion vector analysis
```

### Processing Flow
1. Load video metadata (fps, resolution, duration)
2. Process frames in batches (configurable batch_size)
3. Apply shot detection algorithm
4. Filter by confidence threshold and minimum duration
5. Extract keyframe from each shot (middle/first/last/best)

### Output Schema
```json
{
  "shots": [
    {
      "shot_id": 1,
      "start": 0.0,           // Start time in seconds
      "end": 3.57,            // End time in seconds
      "duration": 3.57,       // Duration in seconds
      "start_frame": 0,       // Frame number
      "end_frame": 107,
      "keyframe_path": "keyframes/shot_0001.jpg",
      "confidence": 0.95,     // Detection confidence [0-1]
      "transition_type": "cut" // cut/fade/dissolve/wipe
    }
  ],
  "metadata": {
    "total_shots": 315,
    "average_shot_duration": 2.01,
    "video_duration": 634.57
  }
}
```

## Stage 2: Scene Construction

### Purpose
Groups semantically related shots into scenes and generates natural language descriptions using vision-language models.

### Technical Implementation
```python
# Vision-Language Model: LLaVA-1.5-7B
- Architecture: CLIP vision encoder + Vicuna-7B language model
- Input: Keyframes from shots
- Output: Natural language descriptions

# Processing Modes:
1. Individual: Each shot analyzed separately
2. Grouped: Multiple shots analyzed together
3. Hierarchical: Shots grouped by visual similarity first
```

### Scene Grouping Algorithm
1. Visual similarity clustering (optional)
   - Feature extraction using CLIP embeddings
   - Temporal proximity weighting
   - Agglomerative clustering
   
2. Narrative coherence analysis
   - LLaVA analyzes keyframe sequences
   - Identifies narrative boundaries
   - Generates scene-level descriptions

### Output Schema
```json
{
  "scenes": [
    {
      "scene_id": 1,
      "shot_ids": [1, 2, 3],    // Constituent shots
      "start": 0.0,
      "end": 8.37,
      "duration": 8.37,
      "keyframes": [
        "keyframes/shot_0001.jpg",
        "keyframes/shot_0002.jpg",
        "keyframes/shot_0003.jpg"
      ],
      "description": "Opening sequence showing the Big Buck Bunny logo followed by establishing shots of a peaceful forest landscape with pink skies and lush vegetation.",
      "narrative_elements": {
        "setting": "Forest/Nature",
        "mood": "Peaceful, Serene",
        "visual_style": "Animated, Colorful"
      },
      "confidence": 0.92
    }
  ],
  "metadata": {
    "total_scenes": 42,
    "average_scene_duration": 15.1,
    "scene_detection_method": "llava_narrative"
  }
}
```

## Stage 3: Cinematic Analysis (Future Implementation)

### Purpose
Analyzes cinematographic techniques, camera movements, and visual storytelling elements.

### Planned Features
```json
{
  "cinematic_analysis": {
    "camera_techniques": {
      "movements": ["pan", "tilt", "zoom", "dolly"],
      "angles": ["low", "eye-level", "high", "dutch"],
      "shots": ["close-up", "medium", "wide", "establishing"]
    },
    "visual_composition": {
      "rule_of_thirds": 0.85,
      "symmetry": 0.45,
      "depth_layers": 3,
      "color_palette": ["warm", "cool", "neutral"]
    },
    "editing_rhythm": {
      "pacing": "moderate",
      "average_shot_length": 2.01,
      "rhythm_variance": 0.34
    }
  }
}
```

## Complete Output Schema

### Top-Level Structure
```json
{
  "metadata": {
    "filename": "video.mp4",
    "duration": 634.57,
    "fps": 30.0,
    "width": 1920,
    "height": 1080,
    "total_frames": 19037,
    "format": "mp4",
    "codec": "h264",
    "processing_timestamp": "2025-08-08T05:21:04.912Z",
    "pipeline_version": "0.1.0"
  },
  "processing_time": 321.55,
  "stages_completed": ["shot_detection", "scene_construction"],
  "analysis": {
    "shots": [...],           // Array of shot objects
    "scenes": [...],          // Array of scene objects
    "cinematic": {...},       // Cinematic analysis (when implemented)
    "summary": {
      "narrative_arc": "...", // Overall story structure
      "visual_style": "...",  // Dominant visual characteristics
      "key_moments": [...]    // Timestamp-indexed highlights
    }
  }
}
```

### Data Flow Example
```
Input: 10-minute video (634.57 seconds)
  ↓
Shot Detection: 315 shots detected
  ↓
Keyframe Extraction: 315 JPEG images
  ↓
Scene Construction: 42 scenes identified
  ↓
Output: 152KB JSON + 315 keyframes (≈50MB)
```

## Performance Characteristics

### Processing Speed
- **Shot Detection**: ~40 fps (TransNetV2 on GPU)
- **Scene Analysis**: ~1 shot/second (LLaVA-7B)
- **Total Pipeline**: ~5-6 minutes for 10-minute video

### Resource Requirements
- **GPU Memory**: 8-16GB VRAM (model dependent)
- **System Memory**: 16-32GB RAM
- **Storage**: 
  - Models: ~15GB (one-time download)
  - Per video: ~5MB/minute (keyframes + JSON)

### Scalability Features
- Batch processing support
- Resume from checkpoint
- Configurable model precision (FP32/FP16/INT8)
- Multi-GPU support (via device_map)
- Async pipeline stages

## Configuration System

### Key Parameters
```yaml
shot_detection:
  model_name: "transnetv2"      # Model selection
  confidence_threshold: 0.5      # Boundary confidence
  min_shot_duration: 0.5        # Seconds
  
scene_construction:
  model_name: "llava-hf/llava-1.5-7b-hf"
  max_frames_per_batch: 10      # GPU memory management
  temperature: 0.7              # Generation randomness
  
pipeline:
  batch_size: 32
  use_gpu: true
  device: "cuda:0"
```

## API Integration Points

### Pipeline Interface
```python
from hendrix import VideoAnalysisPipeline

# Initialize
pipeline = VideoAnalysisPipeline("config.yaml")

# Process video
results = pipeline.analyze_video("input.mp4")

# Access structured data
shots = results['analysis']['shots']
scenes = results['analysis']['scenes']

# Export formats
pipeline.export_json("output.json")
pipeline.export_timeline_html("timeline.html")
```

### Extensibility
- Custom shot detection models via plugin interface
- Alternative VLM models (BLIP-2, Flamingo, etc.)
- Post-processing hooks for custom analysis
- Export adapters for different formats

## Use Cases

1. **Content Analysis**: Automated video summarization and indexing
2. **Film Studies**: Cinematographic technique analysis
3. **Video Editing**: Automated rough cut generation
4. **Accessibility**: Scene descriptions for visually impaired
5. **Content Moderation**: Scene-level content classification
6. **Video Search**: Semantic search within video libraries

## Future Enhancements

1. **Real-time Processing**: Streaming video analysis
2. **Audio Integration**: Speech and music analysis
3. **Multi-modal Fusion**: Combined visual-audio understanding
4. **Action Recognition**: Detailed activity detection
5. **Character Tracking**: Person identification across scenes
6. **Emotion Analysis**: Mood and sentiment detection
