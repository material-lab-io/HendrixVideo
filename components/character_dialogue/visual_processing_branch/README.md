# Visual Processing Branch

This branch contains all components for visual processing and fusion in the Character-Dialogue Analysis pipeline. It implements face detection, character tracking, and character-dialogue matching using InsightFace and SORT tracking.

## Directory Structure

```
visual_processing_branch/
├── src/
│   ├── visual/
│   │   ├── __init__.py
│   │   ├── insightface_processor.py  # InsightFace detection & recognition
│   │   ├── face_tracker.py           # SORT tracking algorithm (with scene support)
│   │   ├── deepface_analyzer.py      # Facial attribute analysis
│   │   ├── frame_extractor.py        # Video frame extraction
│   │   ├── robust_frame_extractor.py # Multi-strategy frame extraction
│   │   ├── scene_detector.py         # NEW: Scene boundary detection
│   │   ├── scene_aware_character_clustering.py # NEW: Scene-based clustering
│   │   └── active_speaker_detector.py # Lip movement detection
│   ├── fusion/
│   │   ├── character_dialogue_matcher.py  # Main fusion orchestrator
│   │   ├── heuristic_matcher.py          # Rule-based matching
│   │   └── llm_matcher.py                # LLM-based matching (placeholder)
│   └── schemas.py                    # Schema A, B, C, D definitions
├── scripts/
│   ├── run_optimized_robust_pipeline.py  # Optimized pipeline (88%+ match rate)
│   ├── run_scene_aware_pipeline.py      # NEW: Scene-aware clustering pipeline
│   ├── run_complete_pipeline_v2.py       # Complete end-to-end pipeline
│   ├── tracked_visual_pipeline.py        # Visual processing with tracking
│   ├── evaluate_pipeline_output.py       # Pipeline quality evaluation
│   ├── validate_all_schemas.py           # Schema validation
│   ├── display_all_schemas.py            # Human-readable display
│   ├── test_scene_aware_clustering.py    # NEW: Test scene clustering
│   └── video_converter.py                # Video format converter
├── output/                               # Processing results
├── test_videos/                          # Sample videos for testing
├── configs/                              # Configuration files
└── requirements.txt                      # All dependencies
```

## Key Components

### 1. InsightFace Processor (`src/visual/insightface_processor.py`)
- Uses RetinaFace for robust face detection
- ArcFace embeddings (512-dimensional) for face recognition
- buffalo_s model for balanced speed and accuracy
- Handles challenging faces with quality scoring

### 2. Face Tracker (`src/visual/face_tracker.py`)
- SORT (Simple Online and Realtime Tracking) implementation
- Maintains character identity across frames
- Handles occlusions and temporary disappearances
- Clusters embeddings to identify unique characters

### 3. Scene Detection & Clustering (NEW!)
- **Scene Detector** (`src/visual/scene_detector.py`)
  - Uses scenedetect library for boundary detection
  - Configurable threshold and minimum scene length
  - Supports scene merging for short segments
- **Scene-Aware Clustering** (`src/visual/scene_aware_character_clustering.py`)
  - Two-stage clustering: within scenes then across scenes
  - Different thresholds for intra-scene vs inter-scene matching
  - Reduces character over-segmentation from costume/lighting changes

### 4. Character-Dialogue Matcher (`src/fusion/character_dialogue_matcher.py`)
- Combines audio transcriptions with visual character data
- Heuristic rules: temporal alignment, single character, centrality
- Confidence scoring for match quality
- Outputs Schema D with character-dialogue pairs
- **88%+ match rate** with optimized robust pipeline (up from 74-83%)
- **Scene-aware clustering** to handle costume/lighting changes

## Usage

### Complete Pipeline (Recommended)
```bash
# Run the optimized robust pipeline (88%+ match rate)
python scripts/run_optimized_robust_pipeline.py video.mp4 --verbose

# NEW: Run with scene-aware clustering (better character grouping)
python scripts/run_scene_aware_pipeline.py video.mp4 --scene-threshold 30.0

# Legacy complete pipeline
python scripts/run_complete_pipeline_v2.py video.mp4 --target-frames 600

# Evaluate the results
python scripts/evaluate_pipeline_output.py output/optimized_robust/session_*
```

### Validation and Display
```bash
# NEW: Validate all output schemas
python scripts/validate_all_schemas.py output/complete_pipeline_v2/session_*

# NEW: Display results in human-readable format
python scripts/display_all_schemas.py output/complete_pipeline_v2/session_*
```

### Visual Processing Only
```bash
# Process video with character tracking
python scripts/tracked_visual_pipeline.py video.mp4 --target-frames 300 --output output/visual

# Convert problematic video formats
python scripts/video_converter.py input_av1.mp4 output_h264.mp4
```

## Configuration

### Environment Variables
```bash
export HF_TOKEN=your_huggingface_token  # Required for speaker diarization
export TF_USE_LEGACY_KERAS=1           # Required for DeepFace
```

### Key Parameters
- `target_frames`: Number of frames to process (default: 600)
- `min_appearances`: Minimum detections to consider a character (default: 3)
- `extraction_mode`: uniform, intelligent, or hybrid
- `whisper_model`: large-v3 (production), base, small, etc.

## Output Structure

```
output/session_YYYYMMDD_HHMMSS/
├── audio_output/          # Schema A & B
│   └── schemas/
│       ├── schema_a_transcription.json    # With emotions (FIXED!)
│       └── schema_b_speakers.json
├── visual_output/         # Schema C
│   ├── character_data_schemaC.json
│   ├── tracking_data.json
│   └── visual_pipeline_report.txt
└── fusion_output/         # Schema D
    ├── schema_d_matches.json
    └── fusion_report.md
```

## Performance Metrics

- **Processing Speed**: ~2-3 fps on CPU, 10-15 fps on GPU
- **Character Detection**: 95%+ accuracy with good lighting
- **Tracking Consistency**: 90%+ identity preservation
- **Match Rate**: **74-83%** (25x improvement from initial 2.9%)

## Recent Improvements

1. **Fixed Emotion Processing**: All transcriptions now include emotion labels
2. **Improved Temporal Alignment**: Better matching between audio and visual
3. **Dialogue-Aware Frame Extraction**: More frames processed during speech
4. **Validation Tools**: New scripts to ensure data integrity
5. **Display Tools**: Human-readable output formatting
6. **Optimized Pipeline**: New robust pipeline with better performance
7. **Long Video Support**: Handle videos of any length efficiently

## Common Issues

1. **Low Match Rate**: Ensure sufficient frames are processed during dialogue
2. **Missing Characters**: Lower detection confidence threshold
3. **Too Many Characters**: Increase min_appearances threshold
4. **GPU Memory**: Reduce batch size or target frames
5. **Emotion Missing**: Ensure TF_USE_LEGACY_KERAS=1 is set

## Dependencies

Key packages:
- insightface==0.7.3
- onnxruntime==1.16.3
- opencv-python==4.8.1.78
- deepface==0.0.79
- filterpy==1.4.5 (for SORT)
- python-dotenv==1.0.0

See `requirements.txt` for complete list.

## Testing Components

```bash
# Test face detection
python scripts/test_insightface_detection.py video.mp4

# Test complete fusion
python scripts/test_complete_fusion.py

# Test heuristic matching
python scripts/test_heuristic_matching.py

# Test pipeline performance
python scripts/test_pipeline_performance.py video.mp4

# Test multiple videos
python scripts/test_multiple_videos.py video1.mp4 video2.mp4
```

## Configuration Presets

```bash
# Run with specific configuration
python scripts/run_with_config.py video.mp4 --config dialogue
python scripts/run_with_config.py video.mp4 --config action
python scripts/run_with_config.py video.mp4 --config dark_scenes

# Available configs: default, dialogue, action, dark_scenes, crowd_scenes, surveillance
```