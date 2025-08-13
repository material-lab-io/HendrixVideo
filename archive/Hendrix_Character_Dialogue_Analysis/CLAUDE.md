# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Multimodal video analysis system that performs character-dialogue matching by processing audio and visual streams in parallel, then fusing results using advanced heuristic techniques with confidence auto-calibration.

**Core Technologies**: Whisper ASR, InsightFace (RetinaFace + ArcFace), SORT tracking, wav2vec2, Pyannote, DeepFace

**Current Performance**: 74-83% dialogue-character match rate (achieved through optimized robust pipeline)

**Project Type**: Research/Analysis tool (MIT Licensed)
**Repository**: https://github.com/material-lab-io/Hendrix_Character_Dialogue_Analysis
**Language**: Python 3.8+
**Hardware**: GPU with CUDA recommended (5-10x speedup)

## Architecture

### Data Flow
```
Video Input
    ├── Audio Branch → Schema A (transcriptions + emotions)
    │                → Schema B (speaker diarization)
    └── Visual Branch → Schema C (character detection + tracking)
                     ↓
                     Fusion → Schema D (character-dialogue matches)
```

### Schema Definitions
- **Schema A**: Transcription segments with emotion enhancement (100% coverage)
- **Schema B**: Speaker diarization with temporal boundaries  
- **Schema C**: Character detection, embeddings, and appearance tracking
- **Schema D**: Final character-dialogue matches with confidence scoring

### Key Components
- **Audio**: `audio_processing_branch/src/audio/` - Whisper, emotion, diarization processors
- **Visual**: `visual_processing_branch/src/visual/` - InsightFace detection, SORT tracking, adaptive frame extraction
  - **Scene Detection**: `scene_detector.py` - Detects scene boundaries using scenedetect
  - **Scene Clustering**: `scene_aware_character_clustering.py` - Clusters characters within scenes
- **Fusion**: `visual_processing_branch/src/fusion/` - Advanced character matcher with continuity tracking

### Advanced Fusion Architecture
The fusion system (`advanced_character_matcher.py`) employs multiple scoring factors:
- **Temporal Alignment**: Matches characters visible during dialogue timing
- **Speaker Association**: Learns character-speaker mappings over time
- **Character Continuity**: Tracks characters across scene boundaries
- **Confidence Auto-Calibration**: Adjusts thresholds based on video characteristics
- **Multi-factor Scoring**: Combines temporal (0.4), spatial (0.2), continuity (0.3), speaker (0.1) weights

### Pipeline Execution Flow
1. **Audio Processing** (parallel):
   - Whisper transcription → Schema A segments
   - Emotion analysis enriches Schema A
   - Pyannote diarization → Schema B speakers
2. **Visual Processing**:
   - Frame extraction (adaptive/robust strategies)
   - Face detection with InsightFace
   - SORT tracking for temporal continuity
   - Character clustering → Schema C
3. **Fusion Stage**:
   - Loads all schemas (A, B, C)
   - Advanced matching with confidence calibration
   - Generates Schema D matches

### Key Design Patterns
- **Lazy Model Loading**: Models download/load on first use
- **Session-based Output**: Each run creates timestamped session directory
- **Schema Validation**: Built-in validation and repair tools
- **Fallback Strategies**: Multiple quality levels for robust processing
- **Parallel Processing**: ThreadPoolExecutor for frame quality checks

## Critical Setup

```bash
# Clone repository
git clone https://github.com/material-lab-io/Hendrix_Character_Dialogue_Analysis.git
cd Hendrix_Character_Dialogue_Analysis

# Environment setup (required)
export HF_TOKEN=your_huggingface_token  # Required for speaker diarization
export TF_USE_LEGACY_KERAS=1           # Required for DeepFace compatibility

# Virtual environment (from project root)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (includes both audio and visual)
cd visual_processing_branch
pip install -r requirements.txt

# Download models (optional - will auto-download on first use)
python scripts/setup_models.py

# Verify setup
cd ../audio_processing_branch
python scripts/test_setup.py
```

## Primary Commands

### Complete Pipeline (Recommended)
```bash
# OPTIMIZED ROBUST PIPELINE - Best performance (74-83% match rate) - RECOMMENDED
cd visual_processing_branch
python scripts/run_optimized_robust_pipeline.py video.mp4

# Legacy pipeline (older version)
python scripts/run_complete_pipeline_v2.py video.mp4 --target-frames 600

# EXPERIMENTAL: Scene-aware pipeline (still in development)
# python scripts/run_scene_aware_pipeline.py video.mp4 --scene-threshold 30.0

# Evaluate results
python scripts/evaluate_pipeline_output.py output/optimized_robust/session_*
```

### Individual Components
```bash
# Audio only
cd audio_processing_branch
python scripts/complete_audio_pipeline.py video.mp4 --whisper-model base

# Visual only  
cd visual_processing_branch
python scripts/tracked_visual_pipeline.py video.mp4 --target-frames 300
```

### Testing & Utilities
```bash
# Verify setup
cd audio_processing_branch && python scripts/test_setup.py

# Convert problematic video formats
cd visual_processing_branch && python scripts/video_converter.py input.mp4 output_h264.mp4

# Test performance
python scripts/test_tracking_performance.py video.mp4

# Download test videos
cd visual_processing_branch && python scripts/download_test_videos.py

# Download required models
cd visual_processing_branch && python scripts/setup_models.py

# Validate schemas
python scripts/validate_all_schemas.py output/optimized_robust/session_*

# Display schemas in human-readable format
python scripts/display_all_schemas.py output/optimized_robust/session_*

# Fix schema issues in existing files
python scripts/fix_schema_issues.py output/optimized_robust/session_*

# Test long video simulation
python scripts/test_long_video_simulation.py

# Test scene-aware clustering
python scripts/test_scene_aware_clustering.py --video video.mp4
```

### Component Testing
```bash
# Audio testing
cd audio_processing_branch
python scripts/test_whisper_component.py video.mp4
python scripts/test_emotion_component.py video.mp4
python scripts/test_diarization_component.py video.mp4

# Visual testing
cd visual_processing_branch
python scripts/test_insightface_detection.py video.mp4
python scripts/test_complete_fusion.py video.mp4
python scripts/test_heuristic_matching.py video.mp4
python scripts/test_pipeline_performance.py video.mp4
```

### Additional Development Commands
```bash
# Use production configurations
cd visual_processing_branch
python scripts/run_with_config.py video.mp4 --config default

# Analyze multiple videos
python scripts/test_multiple_videos.py test_videos/       # Process directory

# Preprocess videos
python scripts/video_preprocessor.py input.mp4 output/    # Extract frames/audio
```

## Fixed Issues & Solutions

### High Match Rate Achieved (74-83% → 88%+)
- **Solution**: Adaptive frame extraction focusing on dialogue segments
- **Key**: Multi-level fallback strategies (medium_quality → low_quality → force_extract)
- **Result**: Excellent temporal coverage during speech segments

### Emotion Processing Fixed ✓
- **File**: `audio_processing_branch/src/audio/emotion_processor.py`
- **Fix**: Added minimum duration checks (0.025s) and padding for short segments
- **Status**: 100% emotion coverage on all dialogues

### Early Character Detection ✓
- **Solution**: Process frames uniformly including early segments
- **Result**: Characters detected throughout video timeline

### Whisper Hallucination Prevention ✓
- **Solution**: Use base model instead of large-v3 for better stability
- **Fix**: Added validation to skip segments with 0 duration or empty text

### Scene-Aware Character Clustering (EXPERIMENTAL)
- **Problem**: Over-segmentation (e.g., 25+ characters for 10-character movie)
- **Solution**: Detect scene boundaries and cluster characters within/across scenes
- **Implementation**: 
  - `scene_detector.py` - Uses scenedetect library for boundary detection
  - `scene_aware_character_clustering.py` - Two-stage clustering (intra-scene then inter-scene)
  - Enhanced schemas with scene_id and scene statistics
- **Status**: Still experimental - use optimized robust pipeline for production

## Output Structure

```
output/optimized_robust/session_YYYYMMDD_HHMMSS/
├── audio_output/
│   └── {video_name}_YYYYMMDD_HHMMSS/
│       └── schemas/
│           ├── schema_a_transcription.json    # Transcriptions with emotions
│           └── schema_b_speakers.json         # Speaker diarization
├── visual_output/
│   ├── character_data_schemaC.json           # Character detections with embeddings
│   ├── tracking_data.json                    # SORT tracking data
│   ├── visual_pipeline_report.txt            # Processing summary
│   ├── extraction_stats.json                 # Frame extraction statistics
│   └── lip_movement_data.pkl                 # Lip sync data
└── fusion_output/
    ├── schema_d_matches.json                 # Character-dialogue matches
    ├── optimized_matching_report.md          # Human-readable summary
    └── character_profiles.json               # Enhanced character profiles

# Scene-aware pipeline adds:
output/scene_aware/scene_aware_session_YYYYMMDD_HHMMSS/
├── scene_data/
│   └── detected_scenes.json                  # Scene boundaries
├── visual_output/
│   ├── scene_clustering_results.json         # Scene-based clustering
│   └── character_data_schemaC_scenes.json    # Enhanced with scene info
└── fusion_output/
    └── scene_aware_matching_report.md        # Scene-aware analysis
```

## Key Output Files for Manual Review

1. **`fusion_output/optimized_matching_report.md`** - Start here! Human-readable summary
2. **`fusion_output/schema_d_matches.json`** - Detailed character-dialogue matches
3. **`visual_output/visual_pipeline_report.txt`** - Character detection summary

See `OUTPUT_FILES_GUIDE.md` for detailed instructions on viewing results.

## Performance Optimization

### Model Selection
- **Whisper**: base (recommended), large-v3 (accurate but may hallucinate), tiny (fast)
- **InsightFace**: buffalo_s (balanced), buffalo_l (accurate but slower)

### Processing Options
- `--target-frames`: More frames = better matching (default: 600)
- `--extraction-mode`: adaptive (recommended), uniform, intelligent
- `--min-appearances`: Filter noise by requiring multiple detections

### Configuration System
The project uses predefined configurations in `configs/production_configs.py`:
- **default**: Balanced settings for general videos
- **dialogue**: Optimized for dialogue-heavy content
- **action**: High frame rates for action scenes
- **dark_scenes**: Enhanced detection for low-light videos
- **crowd_scenes**: Handles multiple faces per frame
- **surveillance**: Low-quality video optimization

### Hardware
- GPU: 5-10x speedup with CUDA
- Memory: Typical usage 4-8GB VRAM
- Storage: Models cache to ~/.cache/ (~20GB total)

### Long Video Performance
- **30-minute video**: ~9.5 minutes processing
- **1-hour video**: ~19 minutes
- **2-hour movie**: ~38 minutes
- Linear scaling with duration, constant memory usage

## Development Patterns

1. **Branch Navigation**: Always cd to correct branch before running scripts
2. **Failure Resilience**: Pipeline continues on component failures
3. **Progressive Enhancement**: Each stage adds to existing data
4. **Lazy Loading**: Models download on first use only
5. **Environment Variables**: Auto-loaded from .env file in project root

## Critical Files for Architecture Understanding

1. **Schemas**: `visual_processing_branch/src/schemas.py` - All data structures (now with scene support)
2. **Fusion Logic**: `visual_processing_branch/src/fusion/advanced_character_matcher.py` - Character continuity tracking
3. **Adaptive Extraction**: `visual_processing_branch/src/visual/adaptive_frame_extractor.py` - Dialogue-aware sampling
4. **Robust Extraction**: `visual_processing_branch/src/visual/robust_frame_extractor.py` - Multi-level fallback
5. **Scene Detection**: `visual_processing_branch/src/visual/scene_detector.py` - Scene boundary detection
6. **Scene Clustering**: `visual_processing_branch/src/visual/scene_aware_character_clustering.py` - Scene-aware character grouping
7. **Pipelines**: 
   - `visual_processing_branch/scripts/run_optimized_robust_pipeline.py` - Best performance (74-83% match rate)
   - `visual_processing_branch/scripts/run_scene_aware_pipeline.py` - Experimental scene clustering

### Schema Data Structures
Each schema uses Pydantic models with built-in validation:
- **TranscriptionSegment**: `segment_id`, `text`, `start_time`, `end_time`, `emotion`, `emotion_confidence`
- **SpeakerSegment**: `segment_id`, `speaker_id`, `start_time`, `end_time`, `confidence`
- **CharacterInfo**: `character_id`, `num_appearances`, `representative_embeddings`, `appearance_segments`
- **CharacterDialogueMatch**: `match_id`, `character_id`, `dialogue`, `matching_score`, `metadata`

## Common Troubleshooting

### Environment Issues
```bash
# Missing HF_TOKEN error
echo "HF_TOKEN=your_token" >> .env

# DeepFace Keras error
export TF_USE_LEGACY_KERAS=1

# CUDA not detected
python -c "import torch; print(torch.cuda.is_available())"

# Model download failures
rm -rf ~/.cache/huggingface/hub/models--*  # Clear cache and retry
```

### Processing Failures
- **Low match rate**: Use optimized_robust_pipeline.py instead of v2
- **Memory errors**: Reduce batch_size in config, process shorter videos
- **Codec errors**: Use video_converter.py to convert to H.264
- **Schema validation errors**: Run fix_schema_issues.py

## Quick Reference Commands

### Most Common Tasks
```bash
# Best quality analysis (recommended)
cd visual_processing_branch && python scripts/run_optimized_robust_pipeline.py video.mp4

# Quick analysis with parameters
python scripts/run_optimized_robust_pipeline.py video.mp4 --whisper-model tiny

# Batch processing
for video in test_videos/*.mp4; do
    python scripts/run_optimized_robust_pipeline.py "$video"
done

# Check results
python scripts/display_all_schemas.py output/optimized_robust/session_* | less

# Validate schemas
python scripts/validate_all_schemas.py output/optimized_robust/session_*
```

### Key Command-Line Parameters
```bash
# Audio pipeline parameters
--whisper-model {tiny,base,small,medium,large,large-v2,large-v3}
--emotion-model MODEL_NAME
--num-speakers N         # Force N speakers for diarization
--min-speakers N        # Minimum speakers to detect
--max-speakers N        # Maximum speakers to detect

# Visual pipeline parameters  
--target-frames N       # Number of frames to extract
--min-appearances N     # Minimum detections for character
--extraction-mode {adaptive,uniform,intelligent}
--config {default,dialogue,action,dark_scenes,crowd_scenes}

# General parameters
--output OUTPUT_DIR     # Custom output directory
--verbose              # Enable detailed logging
```

## Recent Improvements (v2 → Optimized Robust)

1. **Adaptive Frame Extraction** - Process more frames during dialogue segments
2. **Emotion Processing Fixed** - 100% coverage with proper short segment handling
3. **Multi-Level Fallback** - Ensures frames extracted even from difficult videos
4. **Character Continuity** - Tracks characters across scene changes
5. **Confidence Auto-Calibration** - Adjusts thresholds based on video characteristics
6. **Schema Validation** - Automatic detection and fixing of data issues
7. **Production Ready** - Comprehensive logging and error handling

## Testing Framework

- **Unit Tests**: Standalone test scripts in `scripts/test_*.py`
- **Integration Tests**: `test_multiple_videos.py`, `test_long_video_simulation.py`
- **Validation**: `validate_all_schemas.py` ensures data integrity
- **Performance**: Achieved 74-83% match rate on test videos

## Project Structure Notes

### Key Directories
- `audio_processing_branch/` - Audio analysis pipeline
- `visual_processing_branch/` - Visual processing and fusion
- `visual_processing_branch/src/visual/` - Adaptive and robust frame extractors
- `visual_processing_branch/src/fusion/` - Advanced character matching
- `visual_processing_branch/test_videos/` - Sample videos for testing
- `output/` - All pipeline outputs organized by session

### Test Files Pattern
- `test_*.py` scripts are for testing individual components
- `run_*.py` scripts are for running full pipelines
- `evaluate_*.py` scripts are for analyzing results
- `validate_*.py` scripts are for data validation
- `display_*.py` scripts are for human-readable output

## Testing Guidelines

### No Formal Linting/Formatting
- No linting tools configured (black, flake8, pylint, mypy, ruff)
- No pre-commit hooks or CI/CD workflows
- Project uses manual testing and validation scripts

### Running Tests
```bash
# Use pytest for any unit tests (if created)
pytest tests/

# Most testing is done via standalone scripts
python scripts/test_*.py  # Component-specific tests
```

## Pending Improvements

1. **Scene-aware character clustering** - Better handling of costume changes (experimental)
2. **Real LLM integration** - Replace mock implementation for visual context
3. **GUI interface** - Web-based visualization of results
4. **Real-time processing** - Stream processing for live video
5. **Multi-language support** - Extend beyond English transcription
6. **Formal testing framework** - Add pytest unit tests and CI/CD

## Performance Metrics

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Match Rate | 74-83% | 80%+ | ✓ Achieved |
| Character Count | ~22 | <15 | In progress |
| Processing Speed | 3x realtime | 5x realtime | In progress |
| Memory Usage | 4-8GB | <4GB | Optimized |
| GPU Utilization | 60-80% | 90%+ | Good |
| Schema Validity | 100% | 100% | ✓ Achieved |

## Contributing

When contributing to this project:
1. Create feature branches from `master`
2. Follow existing code patterns and conventions
3. Add unit tests for new functionality (`test_*.py` in scripts/)
4. Ensure all tests pass before submitting PR
5. Update documentation if changing APIs or adding features

## Important Notes for Development

### Model Download Locations
- Models auto-download to `~/.cache/huggingface/` (~20GB total)
- InsightFace models: `~/.insightface/models/`
- First run will be slower due to model downloads

### Environment Variable Loading
- `.env` file in project root is auto-loaded
- Required: `HF_TOKEN` for Pyannote diarization
- Required: `TF_USE_LEGACY_KERAS=1` for DeepFace

### Common Issues and Solutions
1. **"No module named 'audio'"** - Run from correct directory (use cd commands)
2. **GPU not detected** - Check CUDA installation with `nvidia-smi`
3. **Low match rate** - Use `run_optimized_robust_pipeline.py` not v2
4. **Codec errors** - Convert video to H.264 with `video_converter.py`

---

For detailed output file documentation, see `OUTPUT_FILES_GUIDE.md`
For long video performance analysis, see `LONG_VIDEO_ANALYSIS.md`