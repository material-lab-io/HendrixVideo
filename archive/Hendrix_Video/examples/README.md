# Hendrix Video Analysis Examples

This directory contains example scripts demonstrating various use cases of the Hendrix Video Analysis Pipeline.

## Available Examples

### 1. Basic Analysis (`basic_analysis.py`)
Simple video analysis with default settings.

```bash
python examples/basic_analysis.py path/to/video.mp4
```

### 2. Batch Processing (`batch_processing.py`)
Process multiple videos in parallel.

```bash
python examples/batch_processing.py path/to/video/directory/
```

### 3. Custom Configuration (`custom_config_example.py`)
Using custom configuration for specific needs.

```bash
python examples/custom_config_example.py video.mp4 --config custom.yaml
```

### 4. Performance Benchmarking (`benchmark.py`)
Benchmark pipeline performance on your hardware.

```bash
python examples/benchmark.py
```

### 5. Model Comparison (`compare_models.py`)
Compare different model configurations.

```bash
python examples/compare_models.py video.mp4
```

### 6. Resume Processing (`resume_example.py`)
Resume interrupted processing from checkpoints.

```bash
python examples/resume_example.py video.mp4 --resume-from scene_construction
```

### 7. Custom Prompts (`custom_prompts.py`)
Using custom prompts for scene analysis.

```bash
python examples/custom_prompts.py video.mp4
```

### 8. Export Results (`export_results.py`)
Export analysis results to different formats.

```bash
python examples/export_results.py results.json --format csv
```

## Sample Outputs

The `sample_outputs/` directory contains example output files:
- `shots.json` - Shot detection results
- `scenes.json` - Scene construction results
- `analysis_report.html` - HTML visualization
- `performance_metrics.txt` - Benchmark results

## Quick Start

1. Ensure the pipeline is installed:
   ```bash
   pip install -e .
   ```

2. Run a basic example:
   ```bash
   python examples/basic_analysis.py tests/sample_video.mp4
   ```

3. Check the output in `output/` directory

## Creating Your Own Examples

Use these examples as templates for your own scripts. Key patterns:

```python
from src.main import VideoAnalysisPipeline

# Initialize pipeline
pipeline = VideoAnalysisPipeline("config.yaml")

# Analyze video
results = pipeline.analyze_video("video.mp4")

# Process results
for shot in results['shots']:
    print(f"Shot {shot.shot_id}: {shot.start:.2f}s - {shot.end:.2f}s")
```