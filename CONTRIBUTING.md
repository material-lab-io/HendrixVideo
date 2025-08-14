# Contributing to Hendrix Video Analysis Pipeline

Thank you for your interest in contributing to Hendrix! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Reporting Issues](#reporting-issues)

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct:

- **Be respectful**: Treat everyone with respect. No harassment, discrimination, or inappropriate behavior.
- **Be collaborative**: Work together to resolve conflicts and assume good intentions.
- **Be professional**: Focus on what is best for the community and the project.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Set up the development environment** (see below)
4. **Create a new branch** for your contribution
5. **Make your changes** following our guidelines
6. **Submit a pull request**

## How to Contribute

### Types of Contributions

- **Bug Fixes**: Fix issues reported in GitHub Issues
- **New Features**: Add new capabilities to the pipeline
- **Documentation**: Improve or add documentation
- **Tests**: Add or improve test coverage
- **Performance**: Optimize code for better performance
- **Models**: Add support for new AI models

### Before Contributing

1. Check existing [issues](https://github.com/yourusername/hendrix_12aug/issues) and [pull requests](https://github.com/yourusername/hendrix_12aug/pulls)
2. Open an issue to discuss major changes
3. For small fixes, you can directly create a pull request

## Development Setup

### Prerequisites

```bash
# System requirements
- Python 3.8 or higher
- Git
- FFmpeg
- CUDA (optional, for GPU support)
```

### Environment Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/hendrix_12aug.git
   cd hendrix_12aug
   git remote add upstream https://github.com/ORIGINAL_OWNER/hendrix_12aug.git
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv hendrix_dev
   source hendrix_dev/bin/activate  # On Windows: hendrix_dev\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements/all.txt
   pip install -r requirements/dev.txt
   pip install -r requirements/test.txt
   ```

4. **Install pre-commit hooks**
   ```bash
   pre-commit install
   ```

5. **Download test models** (optional)
   ```bash
   bash scripts/setup/download_models.sh --test-models
   ```

## Coding Standards

Please refer to our [Style Guide](STYLE_GUIDE.md) for detailed coding conventions, including:
- Import style and organization
- Code formatting standards
- Documentation requirements
- Git commit message format

### Python Style Guide

We follow PEP 8 with some modifications:

- **Line length**: 120 characters maximum
- **Formatting**: Use Black formatter
- **Import sorting**: Use isort
- **Type hints**: Required for public APIs
- **Imports**: Use relative imports for internal modules (see [Style Guide](STYLE_GUIDE.md#import-style))

### Code Formatting

Before committing, run:

```bash
# Format code
black components/ scripts/ tests/ --line-length 120

# Sort imports
isort components/ scripts/ tests/ --profile black --line-length 120

# Lint code
flake8 components/ scripts/ tests/ --max-line-length 120
```

Or use pre-commit:

```bash
pre-commit run --all-files
```

### Documentation

- Use Google-style docstrings
- Document all public functions and classes
- Include type hints
- Add usage examples for complex functions

Example:

```python
def process_video(
    video_path: Path,
    output_dir: Path,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """Process a video file through the analysis pipeline.
    
    Args:
        video_path: Path to the input video file
        output_dir: Directory for output files
        config: Configuration dictionary
        
    Returns:
        Dictionary containing analysis results
        
    Raises:
        ValueError: If video_path doesn't exist
        RuntimeError: If processing fails
        
    Example:
        >>> results = process_video(
        ...     Path("input.mp4"),
        ...     Path("outputs/"),
        ...     {"profile": "fast"}
        ... )
    """
```

## Testing Guidelines

### Writing Tests

1. **Location**: Place tests in the `tests/` directory
2. **Naming**: Use `test_` prefix for test files and functions
3. **Structure**: Mirror the source code structure

### Test Categories

- **Unit tests**: Test individual functions/classes
- **Integration tests**: Test component interactions
- **End-to-end tests**: Test complete pipeline

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_config_manager.py

# Run with coverage
pytest --cov=components --cov-report=html

# Run only fast tests
pytest -m "not slow"
```

### Test Requirements

- All new features must include tests
- Bug fixes should include regression tests
- Maintain or improve code coverage
- Tests must pass on all supported Python versions

## Pull Request Process

### Before Submitting

1. **Update your fork**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run tests**
   ```bash
   pytest
   pre-commit run --all-files
   ```

3. **Update documentation** if needed

### PR Guidelines

1. **Title**: Use conventional commit format
   - `feat: add new feature`
   - `fix: resolve issue with X`
   - `docs: update installation guide`
   - `test: add tests for Y`
   - `refactor: improve Z performance`

2. **Description**: Use the PR template
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

3. **Size**: Keep PRs focused and reasonably sized

### Review Process

1. Maintainers will review your PR
2. Address feedback promptly
3. Once approved, maintainers will merge

## Reporting Issues

### Bug Reports

When reporting bugs, include:

1. **Environment details**
   - OS and version
   - Python version
   - CUDA version (if applicable)
   - Package versions (`pip freeze`)

2. **Steps to reproduce**
   - Minimal code example
   - Input files (if applicable)
   - Expected vs actual behavior

3. **Error messages**
   - Complete error traceback
   - Log files if available

### Feature Requests

For feature requests, provide:

1. **Use case**: Why is this feature needed?
2. **Proposed solution**: How should it work?
3. **Alternatives**: Other approaches considered
4. **Additional context**: Examples, mockups, etc.

### Issue Template

```markdown
**Describe the issue**
A clear description of the problem

**To Reproduce**
Steps to reproduce the behavior:
1. Run command '...'
2. See error

**Expected behavior**
What you expected to happen

**Screenshots/Logs**
If applicable, add screenshots or logs

**Environment:**
- OS: [e.g., Ubuntu 22.04]
- Python: [e.g., 3.10.6]
- CUDA: [e.g., 11.8]
- Hendrix version: [e.g., 2.0.0]

**Additional context**
Any other relevant information
```

## Community

- **Discussions**: Use GitHub Discussions for questions
- **Discord**: Join our [Discord server](https://discord.gg/hendrix)
- **Email**: contact@hendrix-project.org

## Recognition

Contributors will be recognized in:
- The project README
- Release notes
- Our website

Thank you for contributing to Hendrix!