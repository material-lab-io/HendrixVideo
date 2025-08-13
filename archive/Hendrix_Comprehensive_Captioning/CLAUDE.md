# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## System Overview

The Comprehensive Captioning System generates rich narrative captions by fusing outputs from two video analysis pipelines:
- **audio_analysis**: Provides character-dialogue matching with emotion detection (Schema A, B, C, D)
- **Hendrix_Video_Analysis**: Provides scene boundaries and visual descriptions (scenes.json)

The system uses **LLaVA-NeXT (LLaVA 1.6)** as the MLLM to generate contextually aware captions that maintain narrative continuity across scenes.

## Key Commands

### Running the Pipeline

```bash
# Standard execution with keyframes
python scripts/generate_comprehensive_captions.py \
  --audio-analysis /dev-work/audio_analysis/visual_processing_branch/output/optimized_robust/session_* \
  --scene-analysis /dev-work/Hendrix_Video_Analysis/output/scenes.json \
  --keyframes /dev-work/Hendrix_Video_Analysis/keyframes/ \
  --output-dir /dev-work/comprehensive_captioning/output/

# Dry run to test data loading
python scripts/generate_comprehensive_captions.py \
  --audio-analysis <path> --scene-analysis <path> --output-dir <path> --dry-run

# With custom config
python scripts/generate_comprehensive_captions.py \
  --audio-analysis <path> --scene-analysis <path> --output-dir <path> \
  --config config/custom_config.yaml
```

### Testing Components

```bash
# Test data fusion independently
python -m comprehensive_captioning.data_fusion_engine \
  --audio-analysis <path> --scene-analysis <path> --output context_packets.json

# Test prompt templates
python -m comprehensive_captioning.prompt_templates

# Test output formatters
python -m comprehensive_captioning.output_formats
```

### Installation

```bash
cd /dev-work/comprehensive_captioning
pip install -r requirements.txt
```

### Code Quality Checks

```bash
# Format code with Black
black .

# Check code formatting without modifying
black --check .

# Lint code with flake8
flake8 . --max-line-length=120 --extend-ignore=E203,W503

# Run built-in module tests
python -m comprehensive_captioning.utils
python -m comprehensive_captioning.output_formats
python -m comprehensive_captioning.prompt_templates
python -m comprehensive_captioning.caption_generator
```

## Architecture & Data Flow

### 1. Data Fusion Stage
The `DataFusionEngine` combines data from both pipelines:
- Loads Schema A (transcriptions + emotions), B (speakers), C (characters), D (matches) from audio_analysis
- Loads scene boundaries and visual descriptions from Hendrix_Video_Analysis
- Creates `SceneContextPacket` objects containing:
  - Dialogue entries with speaker identification and emotions
  - Character presence information
  - Visual scene descriptions
  - Prior scene summary for continuity

### 2. Caption Generation Stage
The `CaptionGenerator` uses LLaVA-NeXT to generate captions:
- Accepts text prompts AND optional keyframe images
- Implements the `LLaVAInterface` which loads the model locally (no API key needed)
- Falls back to text-only generation if keyframes unavailable
- Maintains scene-to-scene narrative continuity

### 3. Output Generation
The `OutputFormatter` creates multiple formats:
- JSON: Structured data with full metadata
- SRT/WebVTT: Standard subtitle formats with character annotations
- HTML: Interactive viewer with styling
- TXT: Human-readable report format

## Critical Design Decisions

### LLaVA-NeXT Integration
- Uses `transformers` library with `LlavaNextProcessor` and `LlavaNextForConditionalGeneration`
- Automatically detects and uses GPU if available
- Supports both text-only and image+text inputs
- Model path: `llava-hf/llava-v1.6-vicuna-7b-hf`

### Scene Context Continuity
- Each scene's `prior_scene_summary` is updated with the generated caption from the previous scene
- This creates narrative flow and prevents repetitive descriptions
- Configurable via `pipeline.update_context` setting

### Time Alignment
- The fusion engine matches dialogue to scenes based on temporal overlap
- Uses `min_dialogue_confidence` threshold (default: 0.5) to filter low-quality matches
- Handles missing or incomplete data gracefully

## Configuration Structure

The `config/captioning_config.yaml` controls:
- **mllm**: Provider (llava), model name, generation parameters
- **fusion**: Emotion inclusion, confidence thresholds
- **prompt**: Template selection (narrative, descriptive, summary)
- **output**: Format selection, metadata inclusion
- **pipeline**: Retry settings, keyframe usage

## Expected Input Structure

### Audio Analysis Output
```
session_*/
├── audio_output/
│   └── */schemas/
│       ├── schema_a_transcription.json  # Dialogue with emotions
│       └── schema_b_speakers.json       # Speaker diarization
├── visual_output/
│   └── character_data_schemaC.json      # Character detections
└── fusion_output/
    └── schema_d_matches.json            # Character-dialogue matches
```

### Scene Analysis Output
```
scenes.json with structure:
{
  "total_scenes": N,
  "scenes": [{
    "scene_id": 1,
    "start_time": 0.0,
    "end_time": 10.0,
    "summary": "Visual description",
    "contained_shots": [1, 2, 3]
  }]
}
```

## Common Issues & Solutions

### GPU Memory
- If OOM errors occur, the model automatically falls back to CPU
- Can force CPU mode by setting `CUDA_VISIBLE_DEVICES=""`

### Missing Dependencies
- LLaVA requires: `transformers`, `torch`, `pillow`, `accelerate`
- Install with: `pip install -r requirements.txt`

### Data Alignment
- If scene times don't align with dialogue, check `time_alignment_tolerance` in config
- Use `--dry-run` to debug data loading issues

## Extension Points

### Adding New MLLM Providers
1. Inherit from `MLLMInterface` in `caption_generator.py`
2. Implement `generate_caption()` and `is_available()`
3. Register in `create_mllm_interface()` factory

### Custom Prompt Templates
1. Create new class inheriting from `PromptTemplate` in `prompt_templates.py`
2. Implement `generate_prompt()` method
3. Register in `PROMPT_TEMPLATES` dict

### New Output Formats
1. Add handler method to `OutputFormatter` in `output_formats.py`
2. Register in `self.format_handlers` dict
3. Add format name to config options

## Common Development Workflows

### Debugging Caption Generation
1. Use `--dry-run` to verify data loading without running the MLLM
2. Check `context_packets.json` for the fused data structure
3. Set `logging.level: DEBUG` in config for detailed logs
4. Use `--max-scenes` to limit processing during testing

### Testing Individual Components
```bash
# Test fusion engine with specific data
python -m comprehensive_captioning.data_fusion_engine \
  --audio-analysis <path> --scene-analysis <path>

# Generate a single caption manually
python -c "
from comprehensive_captioning.caption_generator import create_mllm_interface
from comprehensive_captioning.data_fusion_engine import SceneContextPacket
mllm = create_mllm_interface('llava', {})
packet = SceneContextPacket(...)  # Create test packet
caption = mllm.generate_caption(packet, 'narrative')
print(caption)
"
```

### Memory Management
- For GPU OOM errors: Set `CUDA_VISIBLE_DEVICES=""` to force CPU mode
- Reduce `generation.max_new_tokens` in config
- Enable `advanced.clear_cuda_cache` in config for long videos

## Project Structure

```
comprehensive_captioning/
├── scripts/
│   └── generate_comprehensive_captions.py  # Main entry point
├── comprehensive_captioning/              # Core package (modules at root level)
│   ├── __init__.py
│   ├── data_fusion_engine.py           # Fuses audio/video analysis data
│   ├── caption_generator.py            # MLLM interface and LLaVA implementation
│   ├── pipeline.py                     # Orchestrates the complete pipeline
│   ├── prompt_templates.py             # Narrative/descriptive/summary templates
│   ├── output_formats.py               # JSON/SRT/WebVTT/HTML/TXT formatters
│   └── utils.py                        # Helper functions and validators
├── config/
│   └── captioning_config.yaml          # Main configuration file
├── test_llava.py                       # Standalone LLaVA testing
└── requirements.txt                    # Python dependencies

Note: Core modules are directly in the root directory, not in a subdirectory.
```

## Quick Debugging Tips

### Verify LLaVA Installation
```bash
# Test if LLaVA loads correctly
python test_llava.py

# Check GPU availability
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

### Common CLI Arguments
```bash
# Process only first N scenes (for testing)
--max-scenes 5

# Enable debug logging
--log-level DEBUG

# Save logs to file
--log-file debug.log

# Skip MLLM generation (only test data loading)
--dry-run

# Force specific prompt template
--prompt-template narrative  # or 'descriptive', 'summary'
```

### File Path Resolution
The codebase uses absolute paths internally. When debugging path issues:
```python
# Scripts automatically resolve to absolute paths
# But for manual testing, use:
from pathlib import Path
audio_path = Path("/dev-work/audio_analysis/...").resolve()
```