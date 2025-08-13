"""
Whisper ASR Processor for transcription with timestamps
Generates Schema A output
"""

import os
import whisper
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path
import tempfile
import subprocess
from dataclasses import dataclass

from ..schemas import SchemaA, TranscriptionSegment


@dataclass
class WhisperConfig:
    """Configuration for Whisper processor"""
    model_name: str = "large-v3"  # Production model
    device: Optional[str] = None  # None for auto-detect
    language: Optional[str] = None  # None for auto-detect
    task: str = "transcribe"  # transcribe or translate
    temperature: float = 0.0  # 0 for deterministic
    compression_ratio_threshold: float = 2.4
    logprob_threshold: float = -1.0
    no_speech_threshold: float = 0.6
    condition_on_previous_text: bool = True
    initial_prompt: Optional[str] = None
    word_timestamps: bool = True  # Enable word-level timestamps
    prepend_punctuations: str = '"\'"¿([{-'
    append_punctuations: str = '"\'.。,，!！?？:：")]}、'
    

class WhisperProcessor:
    """Whisper ASR processor for video transcription"""
    
    def __init__(self, config: Optional[WhisperConfig] = None):
        """Initialize Whisper processor
        
        Args:
            config: WhisperConfig object or None for defaults
        """
        self.config = config or WhisperConfig()
        self.logger = logging.getLogger(__name__)
        
        # Load model
        self.logger.info(f"Loading Whisper model: {self.config.model_name}")
        self.model = whisper.load_model(
            self.config.model_name,
            device=self.config.device
        )
        self.logger.info(f"Model loaded successfully on {self.model.device}")
        
    def extract_audio(self, video_path: str) -> str:
        """Extract audio from video file
        
        Args:
            video_path: Path to video file
            
        Returns:
            Path to extracted audio file
        """
        self.logger.info(f"Extracting audio from: {video_path}")
        
        # Create temporary audio file
        temp_audio = tempfile.NamedTemporaryFile(
            suffix='.wav',
            delete=False
        ).name
        
        # Use ffmpeg to extract audio
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-ar', '16000',  # Whisper expects 16kHz
            '-ac', '1',      # Mono
            '-c:a', 'pcm_s16le',  # 16-bit PCM
            '-y',  # Overwrite
            temp_audio
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            self.logger.info(f"Audio extracted to: {temp_audio}")
            return temp_audio
        except subprocess.CalledProcessError as e:
            self.logger.error(f"FFmpeg error: {e.stderr.decode()}")
            raise
    
    def process_audio(self, audio_path: str) -> Dict:
        """Process audio file with Whisper
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Whisper transcription result
        """
        self.logger.info(f"Processing audio with Whisper: {audio_path}")
        
        # Transcribe with word timestamps
        result = self.model.transcribe(
            audio_path,
            language=self.config.language,
            task=self.config.task,
            temperature=self.config.temperature,
            compression_ratio_threshold=self.config.compression_ratio_threshold,
            logprob_threshold=self.config.logprob_threshold,
            no_speech_threshold=self.config.no_speech_threshold,
            condition_on_previous_text=self.config.condition_on_previous_text,
            initial_prompt=self.config.initial_prompt,
            word_timestamps=self.config.word_timestamps,
            prepend_punctuations=self.config.prepend_punctuations,
            append_punctuations=self.config.append_punctuations,
            verbose=False
        )
        
        return result
    
    def create_segments(self, whisper_result: Dict) -> List[TranscriptionSegment]:
        """Convert Whisper result to TranscriptionSegment objects
        
        Args:
            whisper_result: Result from Whisper transcribe
            
        Returns:
            List of TranscriptionSegment objects
        """
        segments = []
        segment_counter = 0
        
        for idx, segment in enumerate(whisper_result['segments']):
            # Skip segments with invalid duration or empty text
            duration = segment['end'] - segment['start']
            text = segment['text'].strip()
            
            if duration <= 0:
                self.logger.warning(f"Skipping segment {idx} with zero/negative duration: {duration}")
                continue
                
            if not text:
                self.logger.warning(f"Skipping segment {idx} with empty text")
                continue
            
            # Create segment ID
            segment_id = f"SEG_{segment_counter:04d}"
            segment_counter += 1
            
            # Extract segment data
            seg = TranscriptionSegment(
                segment_id=segment_id,
                start_time=segment['start'],
                end_time=segment['end'],
                text=text,
                confidence=1.0 - segment.get('no_speech_prob', 0.0),
                language=whisper_result.get('language', None),
                source='whisper'
            )
            
            segments.append(seg)
            
        return segments
    
    def process_video(self, video_path: str, video_id: Optional[str] = None) -> SchemaA:
        """Process video file and generate Schema A
        
        Args:
            video_path: Path to video file
            video_id: Optional video ID (uses filename if not provided)
            
        Returns:
            SchemaA object with transcription data
        """
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        # Generate video ID if not provided
        if video_id is None:
            video_id = video_path.stem
        
        self.logger.info(f"Processing video: {video_path} (ID: {video_id})")
        
        # Extract audio
        audio_path = None
        try:
            audio_path = self.extract_audio(str(video_path))
            
            # Process with Whisper
            whisper_result = self.process_audio(audio_path)
            
            # Create segments
            segments = self.create_segments(whisper_result)
            
            # Get video duration from last segment
            duration = segments[-1].end_time if segments else 0.0
            
            # Create Schema A
            schema_a = SchemaA(
                video_id=video_id,
                duration=duration,
                metadata={
                    'whisper_model': self.config.model_name,
                    'language': whisper_result.get('language', 'unknown'),
                    'source_video': str(video_path),
                    'total_segments': len(segments)
                }
            )
            
            # Add segments
            for segment in segments:
                schema_a.add_segment(segment)
            
            self.logger.info(f"Transcription complete: {len(segments)} segments")
            
            return schema_a
            
        finally:
            # Clean up temporary audio file
            if audio_path and os.path.exists(audio_path):
                os.unlink(audio_path)
                self.logger.debug(f"Cleaned up temp audio: {audio_path}")
    
    def process_audio_file(self, audio_path: str, video_id: str, duration: float) -> SchemaA:
        """Process audio file directly (no video extraction)
        
        Args:
            audio_path: Path to audio file
            video_id: ID for the content
            duration: Duration of the audio
            
        Returns:
            SchemaA object with transcription data
        """
        self.logger.info(f"Processing audio file: {audio_path}")
        
        # Process with Whisper
        whisper_result = self.process_audio(audio_path)
        
        # Create segments
        segments = self.create_segments(whisper_result)
        
        # Create Schema A
        schema_a = SchemaA(
            video_id=video_id,
            duration=duration,
            metadata={
                'whisper_model': self.config.model_name,
                'language': whisper_result.get('language', 'unknown'),
                'source_audio': audio_path,
                'total_segments': len(segments)
            }
        )
        
        # Add segments
        for segment in segments:
            schema_a.add_segment(segment)
        
        self.logger.info(f"Transcription complete: {len(segments)} segments")
        
        return schema_a