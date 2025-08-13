"""
Simple-Diarizer based Speaker Diarization Processor
Alternative to Pyannote that doesn't require HuggingFace authentication
"""

import os
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

from ..schemas import SchemaB, SpeakerSegment


@dataclass
class SimpleDiarizationConfig:
    """Configuration for Simple Diarization processor"""
    embed_model: str = 'xvec'  # 'xvec' or 'ecapa'
    cluster_method: str = 'sc'  # 'sc' (spectral) or 'ahc' (hierarchical)
    min_speakers: Optional[int] = None
    max_speakers: Optional[int] = None
    min_duration: float = 0.5


class SimpleDiarizationProcessor:
    """Simple-Diarizer based speaker diarization processor (no auth required)"""
    
    def __init__(self, config: Optional[SimpleDiarizationConfig] = None):
        """Initialize Simple Diarization processor
        
        Args:
            config: SimpleDiarizationConfig object or None for defaults
        """
        self.config = config or SimpleDiarizationConfig()
        self.logger = logging.getLogger(__name__)
        self.diarizer = None
        
        # Try to import simple_diarizer
        try:
            from simple_diarizer.diarizer import Diarizer
            self.diarizer_class = Diarizer
            self.available = True
        except ImportError:
            self.logger.warning("simple-diarizer not installed. Install with: pip install simple-diarizer")
            self.available = False
    
    def is_available(self) -> bool:
        """Check if Simple-Diarizer is available"""
        return self.available
    
    def process_audio(self, audio_path: str, num_speakers: Optional[int] = None) -> Dict:
        """Process audio file for speaker diarization
        
        Args:
            audio_path: Path to audio file
            num_speakers: Number of speakers (auto-detect if None)
            
        Returns:
            Diarization output dictionary
        """
        if not self.available:
            raise RuntimeError("simple-diarizer not installed")
        
        self.logger.info(f"Processing audio with Simple-Diarizer: {audio_path}")
        
        # Initialize diarizer if not done
        if self.diarizer is None:
            self.logger.info(f"Initializing Simple-Diarizer (embed: {self.config.embed_model}, cluster: {self.config.cluster_method})")
            self.diarizer = self.diarizer_class(
                embed_model=self.config.embed_model,
                cluster_method=self.config.cluster_method
            )
        
        # Determine number of speakers
        if num_speakers is None:
            # Simple-diarizer requires num_speakers, so estimate
            # Use min/max if provided, otherwise default to 2
            if self.config.min_speakers and self.config.max_speakers:
                num_speakers = (self.config.min_speakers + self.config.max_speakers) // 2
            else:
                num_speakers = self.config.min_speakers or 2
            self.logger.warning(f"Number of speakers not specified, using: {num_speakers}")
        
        # Run diarization
        try:
            segments = self.diarizer.diarize(audio_path, num_speakers=num_speakers)
            return segments
        except Exception as e:
            self.logger.error(f"Simple-diarizer failed: {e}")
            raise
    
    def diarization_to_schema_b(self, diarization_output: List, video_id: str, duration: float) -> SchemaB:
        """Convert Simple-Diarizer output to Schema B format
        
        Args:
            diarization_output: List of (start, end, speaker) tuples
            video_id: Video identifier
            duration: Video duration in seconds
            
        Returns:
            SchemaB object
        """
        # Create Schema B
        schema_b = SchemaB(
            video_id=video_id,
            duration=duration,
            metadata={
                'diarization_tool': 'simple-diarizer',
                'embed_model': self.config.embed_model,
                'cluster_method': self.config.cluster_method
            }
        )
        
        # Convert segments
        segment_id = 0
        for start, end, speaker_label in diarization_output:
            # Skip very short segments
            if end - start < self.config.min_duration:
                continue
            
            segment = SpeakerSegment(
                segment_id=f"SPKR_{segment_id:04d}",
                speaker_id=f"speaker_{speaker_label}",
                start_time=float(start),
                end_time=float(end),
                confidence=0.8  # Simple-diarizer doesn't provide confidence
            )
            
            schema_b.add_segment(segment)
            segment_id += 1
        
        return schema_b
    
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
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        # Generate video ID if not provided
        if video_id is None:
            video_id = video_path.stem
        
        self.logger.info(f"Processing video for diarization: {video_path}")
        
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
        if result.returncode != 0:
            raise RuntimeError(f"Failed to get video info: {result.stderr}")
        
        info = json.loads(result.stdout)
        duration = float(info["format"]["duration"])
        
        # Extract audio to temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_audio:
            tmp_audio_path = tmp_audio.name
        
        try:
            self.logger.info(f"Extracting audio to: {tmp_audio_path}")
            
            cmd = [
                "ffmpeg", "-i", str(video_path),
                "-vn",  # No video
                "-acodec", "pcm_s16le",  # PCM 16-bit
                "-ar", "16000",  # 16kHz sampling rate
                "-ac", "1",  # Mono
                "-y",  # Overwrite
                tmp_audio_path
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            
            # Process diarization
            diarization = self.process_audio(tmp_audio_path, num_speakers)
            
            # Convert to Schema B
            schema_b = self.diarization_to_schema_b(diarization, video_id, duration)
            
            return schema_b
            
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_audio_path):
                os.unlink(tmp_audio_path)