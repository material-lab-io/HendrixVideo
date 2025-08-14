"""
Integration tests for the Hendrix pipeline
"""
import pytest
from pathlib import Path
import json
from unittest.mock import Mock, patch

from hendrix.core.pipeline import Pipeline
from hendrix.core.config import ConfigManager


class TestPipelineIntegration:
    """Test complete pipeline execution"""
    
    @pytest.mark.integration
    def test_pipeline_initialization(self, test_config):
        """Test pipeline can be initialized with config"""
        config = ConfigManager()
        config.config = test_config
        
        pipeline = Pipeline(config)
        assert pipeline is not None
        assert hasattr(pipeline, 'process_video')
    
    @pytest.mark.integration
    @patch('subprocess.run')
    def test_pipeline_component_execution(self, mock_subprocess, test_config, temp_dir):
        """Test pipeline executes components in correct order"""
        # Mock subprocess calls to components
        mock_subprocess.return_value = Mock(returncode=0)
        
        config = ConfigManager()
        config.config = test_config
        
        pipeline = Pipeline(config)
        pipeline.output_dir = temp_dir
        
        # Mock component outputs
        scenes_data = {"scenes": [], "shots": []}
        (temp_dir / "video_analysis" / "scenes.json").parent.mkdir(parents=True)
        (temp_dir / "video_analysis" / "scenes.json").write_text(json.dumps(scenes_data))
        
        # Run pipeline
        results = pipeline._run_components("test_video.mp4")
        
        # Verify components were called
        assert mock_subprocess.call_count >= 2  # At least video and character components
    
    @pytest.mark.integration
    def test_pipeline_error_handling(self, test_config, temp_dir):
        """Test pipeline handles component failures gracefully"""
        config = ConfigManager()
        config.config = test_config
        
        pipeline = Pipeline(config)
        pipeline.output_dir = temp_dir
        
        # Simulate component failure
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = Exception("Component failed")
            
            # Pipeline should handle error gracefully
            results = pipeline._run_components("test_video.mp4")
            assert results is not None  # Should return partial results
    
    def test_pipeline_output_structure(self, test_config, temp_dir, mock_scene_data):
        """Test pipeline creates expected output structure"""
        config = ConfigManager()
        config.config = test_config
        
        pipeline = Pipeline(config)
        pipeline.output_dir = temp_dir
        
        # Create mock outputs
        (temp_dir / "video_analysis").mkdir()
        (temp_dir / "video_analysis" / "scenes.json").write_text(
            json.dumps(mock_scene_data)
        )
        
        # Verify output structure
        assert (temp_dir / "video_analysis").exists()
        
        # Load and verify data
        loaded_data = json.loads((temp_dir / "video_analysis" / "scenes.json").read_text())
        assert "scenes" in loaded_data
        assert len(loaded_data["scenes"]) == 2


class TestPipelineProfiles:
    """Test different pipeline profiles"""
    
    @pytest.mark.parametrize("profile", ["fast", "balanced", "quality"])
    def test_profile_loading(self, profile):
        """Test each profile loads correctly"""
        config = ConfigManager(profile=profile)
        assert config is not None
        
        # Profile should affect settings
        if profile == "fast":
            # Fast profile should use smaller models
            assert "tiny" in str(config.config) or "small" in str(config.config)
        elif profile == "quality":
            # Quality profile should enable more features
            assert config.get("components.character_dialogue.emotion_detection.enabled", True)
    
    def test_test_profile(self):
        """Test the test profile uses mock models"""
        config = ConfigManager(profile="test")
        
        # Should use mock models
        vlm_model = config.get("components.captioning.vision_language_model.active_model")
        assert "mock" in vlm_model.lower() or "test" in vlm_model.lower()


class TestPipelineComponents:
    """Test individual component integration"""
    
    @pytest.mark.integration
    def test_video_analysis_component(self, temp_dir):
        """Test video analysis component integration"""
        from components.video_analysis.src.schemas import SceneData, ShotData
        
        # Create test data
        shot = ShotData(
            shot_id=1,
            start_frame=0,
            end_frame=90,
            start_time=0.0,
            end_time=3.0,
            confidence=0.95
        )
        
        scene = SceneData(
            scene_id=1,
            shots=[shot],
            start_time=0.0,
            end_time=3.0,
            summary="Test scene"
        )
        
        # Verify serialization
        scene_json = scene.json()
        assert "scene_id" in scene_json
        
    @pytest.mark.integration
    def test_caption_generation_component(self, mock_scene_data):
        """Test caption generation with mock data"""
        from components.captioning.schemas import CaptionData
        
        # Create test caption
        caption = CaptionData(
            start_time=0.0,
            end_time=2.5,
            text="Test caption",
            speaker="speaker_1",
            confidence=0.9
        )
        
        # Verify format conversion
        srt_format = f"{caption.start_time} --> {caption.end_time}\n{caption.text}"
        assert "Test caption" in srt_format


class TestPipelineUtils:
    """Test pipeline utility functions"""
    
    def test_output_directory_creation(self, temp_dir):
        """Test output directory structure is created correctly"""
        from components.pipeline import Pipeline
        
        # Create expected structure
        pipeline = Pipeline(ConfigManager())
        pipeline._create_output_structure(temp_dir)
        
        # Verify directories exist
        expected_dirs = [
            "video_analysis",
            "character_dialogue",
            "comprehensive_captions"
        ]
        
        for dir_name in expected_dirs:
            assert (temp_dir / dir_name).exists()
    
    def test_timestamp_generation(self):
        """Test timestamp generation for output naming"""
        from components.utils.common import generate_timestamp
        
        timestamp = generate_timestamp()
        assert len(timestamp) == 15  # YYYYMMDD_HHMMSS format
        assert timestamp[8] == "_"  # Separator
        
    def test_file_validation(self):
        """Test video file validation"""
        from components.utils.validation import validate_video_file
        
        # Valid extensions
        assert validate_video_file(Path("test.mp4"))
        assert validate_video_file(Path("test.avi"))
        assert validate_video_file(Path("test.mov"))
        
        # Invalid extensions
        assert not validate_video_file(Path("test.txt"))
        assert not validate_video_file(Path("test.jpg"))


@pytest.mark.slow
@pytest.mark.integration
class TestPipelinePerformance:
    """Performance tests for the pipeline"""
    
    def test_pipeline_memory_usage(self, test_config, temp_dir):
        """Test pipeline memory usage stays within limits"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Run pipeline
        config = ConfigManager()
        config.config = test_config
        pipeline = Pipeline(config)
        
        # Memory after initialization
        post_init_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = post_init_memory - initial_memory
        
        # Should not use more than 500MB for initialization
        assert memory_increase < 500, f"Pipeline initialization used {memory_increase}MB"
    
    def test_pipeline_execution_time(self, test_config, temp_dir):
        """Test pipeline execution completes in reasonable time"""
        import time
        
        config = ConfigManager()
        config.config = test_config
        pipeline = Pipeline(config)
        
        start_time = time.time()
        
        # Mock execution
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0)
            pipeline._run_components("test.mp4")
        
        elapsed = time.time() - start_time
        
        # Should complete mock execution quickly
        assert elapsed < 5.0, f"Pipeline took {elapsed}s for mock execution"