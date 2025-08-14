# Hendrix Video Analysis Pipeline - Style Guide

## Import Style

### Relative Imports for Internal Modules

When importing modules within the same package, use relative imports:

```python
# Good - within components/video_analysis/src/pipeline/shot_detection.py
from ..models.autoshot import AutoShotDetector
from ..schemas.shot import Shot
from ..utils.video_utils import VideoProcessor

# Bad - absolute imports that won't work when package is installed
from models.autoshot import AutoShotDetector
from schemas.shot import Shot
```

### Import Order

Follow the standard Python import order:

1. Standard library imports
2. Third-party imports
3. Local application/library specific imports

```python
# Standard library
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

# Third-party
import numpy as np
import torch
from transformers import AutoModel

# Local imports (using relative imports)
from ..models.llava import LLaVAAnalyzer
from ..schemas.scene import Scene
from ..utils.prompt_templates import SCENE_CONSTRUCTION_PROMPT
```

### Import Formatting

- One import per line for clarity
- Group imports by category with blank lines
- Sort alphabetically within each group
- Use `from __future__ import annotations` when needed for type hints

## Code Style

### General Guidelines

- Line length: 120 characters maximum
- Use Black formatter with `--line-length 120`
- Follow PEP 8 with the exceptions noted here
- Use type hints for function parameters and return values

### Naming Conventions

- Classes: `PascalCase` (e.g., `VideoAnalysisPipeline`)
- Functions/methods: `snake_case` (e.g., `process_video`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_BATCH_SIZE`)
- Private methods: Leading underscore (e.g., `_validate_input`)

### Documentation

- Use docstrings for all public classes and functions
- Follow Google-style docstrings format
- Include type information in docstrings when not using type hints

```python
def analyze_video(self, video_path: str, config: Optional[Dict] = None) -> AnalysisResult:
    """Analyze a video file and return structured results.
    
    Args:
        video_path: Path to the video file to analyze
        config: Optional configuration override
        
    Returns:
        AnalysisResult containing shots, scenes, and metadata
        
    Raises:
        FileNotFoundError: If video file doesn't exist
        ProcessingError: If analysis fails
    """
```

## Testing

- Test files should mirror the source structure
- Use pytest for all tests
- Mock external dependencies and API calls
- Aim for 80%+ code coverage

## Git Commit Messages

Follow conventional commits format:

- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `style:` Code style changes (formatting, imports, etc.)
- `refactor:` Code refactoring
- `test:` Test additions/changes
- `chore:` Maintenance tasks

Example: `fix: update relative imports in video analysis components`