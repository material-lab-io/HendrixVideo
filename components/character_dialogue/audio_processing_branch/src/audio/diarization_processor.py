"""
Pyannote Speaker Diarization Processor
Generates Schema B output with speaker segments
"""

import os
import torch
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path
import tempfile
from dataclasses import dataclass
from pyannote.audio import Pipeline
import warnings

from ..schemas import SchemaB, SpeakerSegment


@dataclass
class DiarizationConfig:
    """Configuration for Diarization processor"""
    model_name: str = "pyannote/speaker-diarization-3.1"
    device: Optional[str] = None  # None for auto-detect
    min_speakers: Optional[int] = None  # Auto-detect if None
    max_speakers: Optional[int] = None  # Auto-detect if None
    min_duration: float = 0.5  # Minimum segment duration in seconds
    use_auth_token: Optional[str] = None  # HuggingFace token from env


class DiarizationProcessor:
    """Pyannote speaker diarization processor"""
    
    def __init__(self, config: Optional[DiarizationConfig] = None):
        """Initialize Diarization processor
        
        Args:
            config: DiarizationConfig object or None for defaults
        """
        self.config = config or DiarizationConfig()
        self.logger = logging.getLogger(__name__)
        
        # Set device
        if self.config.device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(self.config.device)
        
        # Get auth token
        auth_token = self.config.use_auth_token or os.environ.get("HF_TOKEN")
        if not auth_token:
            raise ValueError(
                "HuggingFace token required for Pyannote. "
                "Set HF_TOKEN environment variable or pass use_auth_token parameter."
            )
        
        # Load pipeline
        self.logger.info(f"Loading Pyannote pipeline: {self.config.model_name}")
        try:
            self.pipeline = Pipeline.from_pretrained(
                self.config.model_name,
                use_auth_token=auth_token
            )
            
            # Move to device
            if self.device.type == "cuda":
                self.pipeline.to(self.device)
            
            self.logger.info(f"Pipeline loaded on device: {self.device}")
            
        except Exception as e:
            self.logger.error(f"Failed to load Pyannote pipeline: {e}")
            self.logger.error(
                "Make sure you have accepted the terms at: "
                "https://huggingface.co/pyannote/speaker-diarization-3.1"
            )
            raise
    
    def process_audio(self, audio_path: str, num_speakers: Optional[int] = None) -> Dict:
        """Process audio file for speaker diarization
        
        Args:
            audio_path: Path to audio file
            num_speakers: Number of speakers (auto-detect if None)
            
        Returns:
            Diarization output dictionary
        """
        self.logger.info(f"Processing audio for diarization: {audio_path}")
        
        # Prepare parameters
        params = {}
        
        if num_speakers is not None:
            params["num_speakers"] = num_speakers
        else:
            if self.config.min_speakers is not None:
                params["min_speakers"] = self.config.min_speakers
            if self.config.max_speakers is not None:
                params["max_speakers"] = self.config.max_speakers
        
        # Run diarization
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            diarization = self.pipeline(audio_path, **params)
        
        self.logger.info(f"Diarization complete: {len(diarization)} segments found")
        
        return diarization
    
    def diarization_to_schema_b(
        self, 
        diarization, 
        video_id: str, 
        duration: float
    ) -> SchemaB:
        """Convert Pyannote diarization output to Schema B
        
        Args:
            diarization: Pyannote diarization output
            video_id: Video identifier
            duration: Total duration in seconds
            
        Returns:
            SchemaB object
        """
        # Create Schema B
        schema_b = SchemaB(
            video_id=video_id,
            duration=duration,
            num_speakers=0,
            metadata={
                "processor": "pyannote",
                "model": self.config.model_name,
                "min_duration": self.config.min_duration
            }
        )
        
        # Track unique speakers
        speakers = set()
        segment_count = 0
        
        # Convert diarization segments
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            # Skip short segments
            if turn.duration < self.config.min_duration:
                continue
            
            # Add speaker to set
            speakers.add(speaker)
            
            # Create segment
            segment = SpeakerSegment(
                segment_id=f"SPK_SEG_{segment_count:04d}",
                speaker_id=speaker,
                start_time=turn.start,
                end_time=turn.end,
                confidence=1.0  # Pyannote doesn't provide confidence scores
            )
            
            schema_b.add_segment(segment)
            segment_count += 1
        
        # Update number of speakers
        schema_b.num_speakers = len(speakers)
        
        # Rename speakers to consistent format
        speaker_mapping = {}
        for i, speaker in enumerate(sorted(speakers)):
            speaker_mapping[speaker] = f"SPEAKER_{i:02d}"
        
        # Update speaker IDs in segments
        for segment in schema_b.segments:
            segment.speaker_id = speaker_mapping[segment.speaker_id]
        
        self.logger.info(
            f"Schema B created: {schema_b.num_speakers} speakers, "
            f"{len(schema_b.segments)} segments"
        )
        
        return schema_b
    
    def process_video(self, video_path: str, num_speakers: Optional[int] = None) -> SchemaB:
        """Process video file for speaker diarization
        
        Args:
            video_path: Path to video file
            num_speakers: Number of speakers (auto-detect if None)
            
        Returns:
            SchemaB object with speaker segments
        """
        self.logger.info(f"Processing video: {video_path}")
        
        # Extract video info
        video_path = Path(video_path)
        video_id = video_path.stem
        
        # Get video duration
        import subprocess
        import json as json_lib
        
        cmd = [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            str(video_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to get video info: {result.stderr}")
        
        info = json_lib.loads(result.stdout)
        duration = float(info["format"]["duration"])
        
        # Extract audio to temporary file
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
    
    def merge_overlapping_segments(self, schema_b: SchemaB, overlap_threshold: float = 0.1) -> SchemaB:
        """Merge overlapping segments from the same speaker
        
        Args:
            schema_b: Input Schema B
            overlap_threshold: Maximum gap between segments to merge (seconds)
            
        Returns:
            Schema B with merged segments
        """
        if not schema_b.segments:
            return schema_b
        
        # Sort segments by speaker and start time
        sorted_segments = sorted(
            schema_b.segments, 
            key=lambda s: (s.speaker_id, s.start_time)
        )
        
        # Merge segments
        merged_segments = []
        current_segment = None
        
        for segment in sorted_segments:
            if current_segment is None:
                current_segment = SpeakerSegment(
                    segment_id=segment.segment_id,
                    speaker_id=segment.speaker_id,
                    start_time=segment.start_time,
                    end_time=segment.end_time,
                    confidence=segment.confidence
                )
            elif (
                segment.speaker_id == current_segment.speaker_id and
                segment.start_time - current_segment.end_time <= overlap_threshold
            ):
                # Extend current segment
                current_segment.end_time = max(current_segment.end_time, segment.end_time)
            else:
                # Save current segment and start new one
                merged_segments.append(current_segment)
                current_segment = SpeakerSegment(
                    segment_id=segment.segment_id,
                    speaker_id=segment.speaker_id,
                    start_time=segment.start_time,
                    end_time=segment.end_time,
                    confidence=segment.confidence
                )
        
        # Add last segment
        if current_segment:
            merged_segments.append(current_segment)
        
        # Renumber segment IDs
        for i, segment in enumerate(merged_segments):
            segment.segment_id = f"SPK_SEG_{i:04d}"
        
        # Create new Schema B with merged segments
        merged_schema = SchemaB(
            video_id=schema_b.video_id,
            duration=schema_b.duration,
            num_speakers=schema_b.num_speakers,
            segments=merged_segments,
            metadata=schema_b.metadata
        )
        
        self.logger.info(
            f"Merged segments: {len(schema_b.segments)} -> {len(merged_segments)}"
        )
        
        return merged_schema