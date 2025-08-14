"""Tests for hendrix.core module."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from hendrix.core.config import ConfigManager
from hendrix.core.pipeline import Pipeline
from hendrix.core.exceptions import HendrixError, PipelineError


class TestConfigManager:
    """Test ConfigManager functionality."""
    
    def test_init_default_config(self):
        """Test ConfigManager initializes with default config."""
        config = ConfigManager()
        assert config is not None
        assert isinstance(config.get_config(), dict)
    
    def test_get_config_key(self):
        """Test getting specific config values."""
        config = ConfigManager()
        # Test accessing nested config
        models = config.get("models", {})
        assert isinstance(models, dict)
    
    def test_set_config_value(self):
        """Test setting config values."""
        config = ConfigManager()
        config.set("test_key", "test_value")
        assert config.get("test_key") == "test_value"
    
    def test_profile_loading(self):
        """Test loading different profiles."""
        config = ConfigManager(profile="test")
        assert config.active_profile == "test"
    
    def test_config_property_backward_compatibility(self):
        """Test backward compatibility property."""
        config = ConfigManager()
        # Should have .config property for backward compatibility
        assert hasattr(config, 'config')
        assert isinstance(config.config, dict)


class TestPipeline:
    """Test Pipeline functionality."""
    
    def test_pipeline_init(self):
        """Test Pipeline initialization."""
        pipeline = Pipeline()
        assert pipeline is not None
        assert hasattr(pipeline, 'config')
    
    def test_pipeline_init_with_config(self):
        """Test Pipeline initialization with custom config."""
        config = ConfigManager(profile="test")
        pipeline = Pipeline(config=config)
        assert pipeline.config == config
    
    @patch('hendrix.video.analyzer.VideoAnalyzer')
    @patch('hendrix.audio.processor.AudioProcessor') 
    @patch('hendrix.captioning.generator.CaptionGenerator')
    def test_analyze_video(self, mock_caption, mock_audio, mock_video):
        """Test video analysis pipeline."""
        # Setup mocks
        mock_video.return_value.process.return_value = {
            "status": "success",
            "shots_detected": 4,
            "scenes_created": 2
        }
        mock_audio.return_value.process.return_value = {
            "status": "success", 
            "speakers_count": 2
        }
        mock_caption.return_value.process.return_value = {
            "status": "success",
            "captions_generated": True
        }
        
        pipeline = Pipeline()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "test_video.mp4"
            video_path.touch()  # Create empty file
            
            results = pipeline.analyze(str(video_path))
            
            assert results is not None
            assert "video" in results
            assert "audio" in results
            assert "caption" in results
    
    def test_analyze_nonexistent_video(self):
        """Test pipeline with nonexistent video file."""
        pipeline = Pipeline()
        
        with pytest.raises((FileNotFoundError, PipelineError)):
            pipeline.analyze("nonexistent_video.mp4")


class TestExceptions:
    """Test custom exceptions."""
    
    def test_hendrix_error(self):
        """Test base HendrixError."""
        error = HendrixError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)
    
    def test_pipeline_error(self):
        """Test PipelineError inherits from HendrixError."""
        error = PipelineError("Pipeline failed")
        assert str(error) == "Pipeline failed"
        assert isinstance(error, HendrixError)
        assert isinstance(error, Exception)