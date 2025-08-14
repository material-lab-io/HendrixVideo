"""Tests for hendrix.captioning module."""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch

from hendrix.captioning.generator import CaptionGenerator
from hendrix.core.config import ConfigManager
from hendrix.core.exceptions import CaptioningError


class TestCaptionGenerator:
    """Test CaptionGenerator functionality."""
    
    def test_init(self):
        """Test CaptionGenerator initialization."""
        config = ConfigManager()
        generator = CaptionGenerator(config)
        assert generator is not None
        assert generator.config == config
    
    def test_process_captions_success(self):
        """Test successful caption generation."""
        config = ConfigManager()
        generator = CaptionGenerator(config)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "test_video.mp4"
            video_path.touch()
            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()
            
            # Mock video and audio data
            video_data = {
                "shots": [{"shot_id": 1, "start_time": 0.0, "end_time": 5.0}],
                "scenes": [{"scene_id": 1, "start_time": 0.0, "end_time": 10.0}]
            }
            audio_data = {
                "transcription": "[00:00:00] Test transcription",
                "speakers": [{"speaker_id": "SPEAKER_00", "start_time": 0.0}]
            }
            
            result = generator.process(video_path, output_dir, video_data, audio_data)
            
            assert result["status"] == "success"
            assert "caption_files" in result
            
            # Check caption files were created
            caption_files = result["caption_files"]
            assert isinstance(caption_files, list)
            assert len(caption_files) > 0
            
            # Verify files exist and have correct extensions
            extensions = [Path(f).suffix for f in caption_files]
            assert ".srt" in extensions
            assert ".vtt" in extensions
            assert ".json" in extensions
    
    def test_generate_srt_captions(self):
        """Test SRT caption generation."""
        config = ConfigManager()
        generator = CaptionGenerator(config)
        
        # Mock caption data
        mock_captions = [
            {
                "start_time": 0.0,
                "end_time": 5.0, 
                "text": "Welcome to this video demonstration.",
                "speaker": "SPEAKER_00"
            },
            {
                "start_time": 5.0,
                "end_time": 10.0,
                "text": "In this section, we'll explore the features.",
                "speaker": "SPEAKER_01"
            }
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "test_video.mp4"
            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()
            
            srt_file = generator._generate_srt_captions(mock_captions, video_path, output_dir)
            
            assert srt_file.exists()
            assert srt_file.suffix == ".srt"
            
            # Check SRT content
            content = srt_file.read_text()
            assert "00:00:00,000 --> 00:00:05,000" in content
            assert "Welcome to this video" in content
    
    def test_generate_vtt_captions(self):
        """Test VTT caption generation."""
        config = ConfigManager()
        generator = CaptionGenerator(config)
        
        # Mock caption data
        mock_captions = [
            {
                "start_time": 0.0,
                "end_time": 5.0,
                "text": "Welcome to this video demonstration.",
                "speaker": "SPEAKER_00"
            }
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "test_video.mp4"
            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()
            
            vtt_file = generator._generate_vtt_captions(mock_captions, video_path, output_dir)
            
            assert vtt_file.exists()
            assert vtt_file.suffix == ".vtt"
            
            # Check VTT content
            content = vtt_file.read_text()
            assert "WEBVTT" in content
            assert "00:00:00.000 --> 00:00:05.000" in content
            assert "Welcome to this video" in content
    
    def test_generate_json_captions(self):
        """Test JSON caption generation."""
        config = ConfigManager()
        generator = CaptionGenerator(config)
        
        # Mock caption data
        mock_captions = [
            {
                "start_time": 0.0,
                "end_time": 5.0,
                "text": "Welcome to this video demonstration.",
                "speaker": "SPEAKER_00"
            }
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "test_video.mp4"
            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()
            
            json_file = generator._generate_json_captions(mock_captions, video_path, output_dir)
            
            assert json_file.exists()
            assert json_file.suffix == ".json"
            
            # Check JSON content
            with open(json_file) as f:
                data = json.load(f)
            
            assert "captions" in data
            assert isinstance(data["captions"], list)
            assert len(data["captions"]) > 0
    
    def test_process_captions_error_handling(self):
        """Test error handling in caption processing."""
        config = ConfigManager()
        generator = CaptionGenerator(config)
        
        # Test with invalid paths
        with pytest.raises(CaptioningError):
            generator.process(Path("nonexistent.mp4"), Path("nonexistent_dir"), {}, {})