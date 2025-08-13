# Contributing to Hendrix Video Analysis

We welcome contributions to the Hendrix Video Analysis Pipeline! This document provides guidelines for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Submitting Changes](#submitting-changes)

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct:

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive criticism
- Respect differing viewpoints and experiences

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/yourusername/Hendrix_Video_Analysis.git
   cd Hendrix_Video_Analysis
   ```
3. Add the upstream repository:
   ```bash
   git remote add upstream https://github.com/originalowner/Hendrix_Video_Analysis.git
   ```
4. Create a virtual environment and install dependencies:
   ```bash
   ./setup_env.sh
   ```

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/originalowner/Hendrix_Video_Analysis/issues)
2. If not, create a new issue with:
   - Clear, descriptive title
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - System information (OS, Python version, GPU)
   - Relevant logs or error messages

### Suggesting Enhancements

1. Check if the enhancement has been suggested
2. Create an issue with:
   - Clear description of the enhancement
   - Use cases and benefits
   - Possible implementation approach

### Code Contributions

1. Find an issue to work on or create one
2. Comment on the issue to claim it
3. Create a feature branch
4. Make your changes
5. Write tests
6. Update documentation
7. Submit a pull request

## Development Setup

### Prerequisites

- Python 3.8+
- CUDA-capable GPU (optional)
- FFmpeg
- Git

### Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/Hendrix_Video_Analysis.git
cd Hendrix_Video_Analysis

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

## Coding Standards

### Python Style Guide

We follow PEP 8 with some modifications:

- Line length: 100 characters
- Use type hints for function signatures
- Use docstrings for all public functions and classes

### Code Formatting

We use Black for code formatting:

```bash
# Format code
black src/ tests/

# Check formatting
black --check src/ tests/
```

### Linting

We use Flake8 and MyPy:

```bash
# Run linting
flake8 src/ tests/

# Type checking
mypy src/
```

### Example Code Style

```python
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class VideoAnalyzer:
    """Analyze video content using computer vision models.
    
    Args:
        config: Configuration dictionary
        device: Device to run models on ('cuda' or 'cpu')
    """
    
    def __init__(self, config: Dict[str, Any], device: str = "cuda"):
        self.config = config
        self.device = device
        
    def analyze(
        self, 
        video_path: str, 
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze a video file.
        
        Args:
            video_path: Path to video file
            output_dir: Optional output directory
            
        Returns:
            Dictionary containing analysis results
            
        Raises:
            FileNotFoundError: If video file not found
            RuntimeError: If analysis fails
        """
        logger.info(f"Analyzing video: {video_path}")
        # Implementation here
        return {}
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_shot_detection.py

# Run with verbose output
pytest -v
```

### Writing Tests

Create tests in the `tests/` directory:

```python
# tests/test_my_feature.py
import pytest
from src.models.my_model import MyModel


class TestMyModel:
    """Test cases for MyModel."""
    
    @pytest.fixture
    def model(self):
        """Create model instance for testing."""
        config = {"device": "cpu"}
        return MyModel(config)
    
    def test_model_initialization(self, model):
        """Test model initializes correctly."""
        assert model is not None
        assert model.device == "cpu"
    
    def test_model_processing(self, model, sample_data):
        """Test model processes data correctly."""
        result = model.process(sample_data)
        assert result is not None
        assert "output" in result
```

## Documentation

### Docstring Format

Use Google-style docstrings:

```python
def process_video(video_path: str, config: dict) -> dict:
    """Process a video file through the analysis pipeline.
    
    Args:
        video_path: Path to the input video file
        config: Configuration dictionary with processing parameters
        
    Returns:
        Dictionary containing:
            - shots: List of detected shots
            - scenes: List of constructed scenes
            - metadata: Video metadata
            
    Raises:
        FileNotFoundError: If video file doesn't exist
        ValueError: If configuration is invalid
        
    Example:
        >>> config = {"batch_size": 32}
        >>> results = process_video("video.mp4", config)
        >>> print(f"Found {len(results['shots'])} shots")
    """
```

### Updating Documentation

- Update relevant `.md` files in `docs/`
- Update docstrings in code
- Update README.md if needed
- Add examples for new features

## Submitting Changes

### Pull Request Process

1. Update your fork:
   ```bash
   git fetch upstream
   git checkout main
   git merge upstream/main
   ```

2. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. Make your changes and commit:
   ```bash
   git add .
   git commit -m "Add: Brief description of changes"
   ```

4. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

5. Create a Pull Request on GitHub

### Pull Request Guidelines

- Title should be clear and descriptive
- Description should include:
  - What changes were made
  - Why the changes were made
  - Related issue numbers
  - Screenshots/examples if applicable
- Ensure all tests pass
- Update documentation
- Add yourself to CONTRIBUTORS.md

### Commit Message Format

Use conventional commits:

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

Example:
```
feat(models): Add CLIP model integration

- Implement CLIP model wrapper
- Add configuration options
- Update documentation

Closes #123
```

## Review Process

1. Maintainers will review your PR
2. Address any requested changes
3. Once approved, your PR will be merged

## Release Process

We use semantic versioning (MAJOR.MINOR.PATCH):

- MAJOR: Breaking changes
- MINOR: New features (backwards compatible)
- PATCH: Bug fixes

## Getting Help

- Check the [documentation](docs/)
- Search existing [issues](https://github.com/originalowner/Hendrix_Video_Analysis/issues)
- Ask in [discussions](https://github.com/originalowner/Hendrix_Video_Analysis/discussions)
- Contact maintainers

## Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project documentation

Thank you for contributing to Hendrix Video Analysis!