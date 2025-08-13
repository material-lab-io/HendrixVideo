"""
Comprehensive Captioning System

This package combines outputs from audio_analysis (character-dialogue matching)
and Hendrix_Video_Analysis (scene boundaries) to generate rich narrative captions
using MLLMs like Gemini 1.5 Pro.
"""

__version__ = "0.1.0"
__author__ = "Hendrix Team"

from .data_fusion_engine import DataFusionEngine, SceneContextPacket
from .caption_generator import CaptionGenerator, MLLMInterface
from .pipeline import ComprehensiveCaptioningPipeline
from .output_formats import OutputFormatter

__all__ = [
    "DataFusionEngine",
    "SceneContextPacket",
    "CaptionGenerator",
    "MLLMInterface",
    "ComprehensiveCaptioningPipeline",
    "OutputFormatter"
]