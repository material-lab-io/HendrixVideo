"""
Flexible Diarization Processor that can use multiple backends
Automatically selects the best available option
"""

import os
import logging
from typing import Optional
from pathlib import Path

from ..schemas import SchemaB


class FlexibleDiarizationProcessor:
    """Flexible diarization processor that auto-selects backend"""
    
    def __init__(self, prefer_backend: Optional[str] = None):
        """Initialize flexible diarization processor
        
        Args:
            prefer_backend: Preferred backend ('pyannote', 'simple', or None for auto)
        """
        self.logger = logging.getLogger(__name__)
        self.backend = None
        self.processor = None
        
        # Try to initialize backends in order of preference
        backends_to_try = []
        
        if prefer_backend:
            backends_to_try.append(prefer_backend)
        
        # Default order: pyannote (if token available), then simple-diarizer
        if os.environ.get("HF_TOKEN"):
            backends_to_try.append("pyannote")
        backends_to_try.append("simple")
        
        # Remove duplicates while preserving order
        backends_to_try = list(dict.fromkeys(backends_to_try))
        
        # Try each backend
        for backend in backends_to_try:
            if self._init_backend(backend):
                break
        
        if not self.backend:
            self.logger.warning("No diarization backend available")
    
    def _init_backend(self, backend: str) -> bool:
        """Try to initialize a specific backend
        
        Args:
            backend: Backend name ('pyannote' or 'simple')
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if backend == "pyannote":
                if not os.environ.get("HF_TOKEN"):
                    self.logger.info("Pyannote requires HF_TOKEN, skipping")
                    return False
                
                from .diarization_processor import DiarizationProcessor, DiarizationConfig
                self.processor = DiarizationProcessor(DiarizationConfig())
                self.backend = "pyannote"
                self.logger.info("Using Pyannote diarization backend")
                return True
                
            elif backend == "simple":
                from .simple_diarization_processor import SimpleDiarizationProcessor, SimpleDiarizationConfig
                processor = SimpleDiarizationProcessor(SimpleDiarizationConfig())
                
                if not processor.is_available():
                    self.logger.info("Simple-diarizer not installed")
                    return False
                
                self.processor = processor
                self.backend = "simple"
                self.logger.info("Using Simple-Diarizer backend")
                return True
                
        except Exception as e:
            self.logger.warning(f"Failed to initialize {backend} backend: {e}")
            return False
        
        return False
    
    def is_available(self) -> bool:
        """Check if any diarization backend is available"""
        return self.processor is not None
    
    def get_backend(self) -> str:
        """Get the name of the active backend"""
        return self.backend or "none"
    
    def process_video(self, video_path: str, video_id: Optional[str] = None, 
                     num_speakers: Optional[int] = None) -> SchemaB:
        """Process video file for speaker diarization
        
        Args:
            video_path: Path to video file
            video_id: Optional video ID
            num_speakers: Number of speakers (auto-detect if None)
            
        Returns:
            SchemaB object with speaker segments
        """
        if not self.processor:
            # Return empty Schema B if no backend available
            video_path = Path(video_path)
            if video_id is None:
                video_id = video_path.stem
            
            # Get video duration
            import subprocess
            import json
            
            cmd = [
                "ffprobe", "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                str(video_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            info = json.loads(result.stdout)
            duration = float(info["format"]["duration"])
            
            return SchemaB(
                video_id=video_id,
                duration=duration,
                num_speakers=0,  # No speakers detected
                metadata={
                    'status': 'no_backend',
                    'message': 'No diarization backend available'
                }
            )
        
        # Use the available processor
        return self.processor.process_video(video_path, video_id, num_speakers)
    
    def merge_overlapping_segments(self, schema_b: SchemaB, overlap_threshold: float = 0.5) -> SchemaB:
        """Merge overlapping speaker segments
        
        Args:
            schema_b: Input SchemaB
            overlap_threshold: Overlap threshold in seconds
            
        Returns:
            SchemaB with merged segments
        """
        if hasattr(self.processor, 'merge_overlapping_segments'):
            return self.processor.merge_overlapping_segments(schema_b, overlap_threshold)
        else:
            # Simple implementation if backend doesn't provide it
            return schema_b