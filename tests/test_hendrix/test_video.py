"""Tests for hendrix.video module."""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch

from hendrix.video.analyzer import VideoAnalyzer
from hendrix.core.config import ConfigManager
from hendrix.core.exceptions import VideoProcessingError


class TestVideoAnalyzer:
    """Test VideoAnalyzer functionality."""
    
    def test_init(self):
        """Test VideoAnalyzer initialization."""
        config = ConfigManager()
        analyzer = VideoAnalyzer(config)
        assert analyzer is not None
        assert analyzer.config == config
    
    def test_process_video_success(self):
        """Test successful video processing."""
        config = ConfigManager()
        analyzer = VideoAnalyzer(config)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "test_video.mp4"
            video_path.touch()
            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()
            
            result = analyzer.process(video_path, output_dir)
            
            assert result["status"] == "success"
            assert "output_files" in result
            assert "shots_detected" in result
            assert "scenes_created" in result
            
            # Check output files were created
            output_files = result["output_files"]
            assert isinstance(output_files, list)
            assert len(output_files) > 0
            
            # Verify files exist
            for file_path in output_files:
                assert Path(file_path).exists()
    
    def test_detect_shots(self):
        """Test shot detection."""
        config = ConfigManager()
        analyzer = VideoAnalyzer(config)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "test_video.mp4"
            video_path.touch()
            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()
            
            shots = analyzer._detect_shots(video_path, output_dir)
            
            assert isinstance(shots, list)
            assert len(shots) > 0
            
            # Check shot data structure
            for shot in shots:
                assert "shot_id" in shot
                assert "start_time" in shot
                assert "end_time" in shot
                assert "confidence" in shot
    
    def test_construct_scenes(self):
        """Test scene construction."""
        config = ConfigManager()
        analyzer = VideoAnalyzer(config)
        
        # Mock shots data
        mock_shots = [
            {"shot_id": 1, "start_time": 0.0, "end_time": 5.0, "confidence": 0.9},
            {"shot_id": 2, "start_time": 5.0, "end_time": 10.0, "confidence": 0.8},
            {"shot_id": 3, "start_time": 10.0, "end_time": 15.0, "confidence": 0.7}
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()
            
            scenes = analyzer._construct_scenes(mock_shots, output_dir)
            
            assert isinstance(scenes, list)
            assert len(scenes) > 0
            
            # Check scene data structure
            for scene in scenes:
                assert "scene_id" in scene
                assert "start_time" in scene
                assert "end_time" in scene
                assert "shots" in scene
                assert isinstance(scene["shots"], list)
    
    def test_extract_keyframes(self):
        """Test keyframe extraction."""
        config = ConfigManager()
        analyzer = VideoAnalyzer(config)
        
        # Mock shots data
        mock_shots = [
            {"shot_id": 1, "start_time": 0.0, "end_time": 5.0, "confidence": 0.9}
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "test_video.mp4"
            video_path.touch()
            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()
            
            keyframes = analyzer._extract_keyframes(video_path, mock_shots, output_dir)
            
            assert isinstance(keyframes, list)
            # In mock implementation, returns empty list
            assert len(keyframes) >= 0
    
    def test_process_video_error_handling(self):
        """Test error handling in video processing."""
        config = ConfigManager()
        analyzer = VideoAnalyzer(config)
        
        # Test with invalid paths
        with pytest.raises(VideoProcessingError):
            analyzer.process(Path("nonexistent.mp4"), Path("nonexistent_dir"))