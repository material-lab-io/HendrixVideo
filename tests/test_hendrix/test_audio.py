"""Tests for hendrix.audio module."""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch

from hendrix.audio.processor import AudioProcessor
from hendrix.core.config import ConfigManager
from hendrix.core.exceptions import AudioProcessingError


class TestAudioProcessor:
    """Test AudioProcessor functionality."""
    
    def test_init(self):
        """Test AudioProcessor initialization."""
        config = ConfigManager()
        processor = AudioProcessor(config)
        assert processor is not None
        assert processor.config == config
    
    def test_process_audio_success(self):
        """Test successful audio processing."""
        config = ConfigManager()
        processor = AudioProcessor(config)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "test_video.mp4"
            video_path.touch()
            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()
            
            result = processor.process(video_path, output_dir)
            
            assert result["status"] == "success"
            assert "transcription_file" in result
            assert "speakers_count" in result
            assert "transcript_length" in result
            
            # Check transcript file was created
            transcript_file = Path(result["transcription_file"])
            assert transcript_file.exists()
            
            # Check transcript content
            with open(transcript_file) as f:
                transcript_data = json.load(f)
            
            assert "transcription" in transcript_data
            assert "speakers" in transcript_data
            assert isinstance(transcript_data["speakers"], list)
    
    def test_extract_audio(self):
        """Test audio extraction."""
        config = ConfigManager()
        processor = AudioProcessor(config)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "test_video.mp4"
            video_path.touch()
            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()
            
            audio_path = processor._extract_audio(video_path, output_dir)
            
            assert audio_path.exists()
            assert audio_path.suffix == ".wav"
    
    def test_transcribe_audio(self):
        """Test audio transcription."""
        config = ConfigManager()
        processor = AudioProcessor(config)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            audio_path = Path(temp_dir) / "test_audio.wav" 
            audio_path.touch()
            
            transcription = processor._transcribe_audio(audio_path)
            
            assert isinstance(transcription, str)
            assert len(transcription) > 0
            assert "Welcome to this video" in transcription
    
    def test_diarize_speakers(self):
        """Test speaker diarization."""
        config = ConfigManager()
        processor = AudioProcessor(config)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            audio_path = Path(temp_dir) / "test_audio.wav"
            audio_path.touch()
            
            speakers = processor._diarize_speakers(audio_path)
            
            assert isinstance(speakers, list)
            assert len(speakers) > 0
            
            # Check speaker data structure
            for speaker in speakers:
                assert "speaker_id" in speaker
                assert "start_time" in speaker
                assert "end_time" in speaker
                assert "confidence" in speaker
    
    def test_process_audio_error_handling(self):
        """Test error handling in audio processing."""
        config = ConfigManager()
        processor = AudioProcessor(config)
        
        # Test with invalid paths
        with pytest.raises(AudioProcessingError):
            processor.process(Path("nonexistent.mp4"), Path("nonexistent_dir"))