"""
Hendrix Video Analysis Pipeline

A modern, AI-powered video analysis system for:
- Shot boundary detection
- Scene construction 
- Audio transcription and speaker diarization
- Automated caption generation

Usage:
    >>> import hendrix
    >>> pipeline = hendrix.Pipeline()
    >>> results = pipeline.analyze("video.mp4")
"""

from .core.pipeline import Pipeline
from .core.config import ConfigManager
from .__version__ import __version__

__all__ = ["Pipeline", "ConfigManager", "__version__"]

# Package metadata
__author__ = "Material Lab"
__email__ = "info@material-lab.io"
__license__ = "MIT"