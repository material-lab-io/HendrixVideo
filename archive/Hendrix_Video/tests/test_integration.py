import pytest
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from main import VideoAnalysisPipeline
from schemas.shot import Shot
from schemas.scene import Scene
from schemas.analysis import AnalysisResult, VideoMetadata


class TestIntegration:
    """Integration tests for the complete video analysis pipeline."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test outputs."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_config(self, temp_dir):
        """Create a test configuration."""
        return {
            'general': {
                'output_format': 'json',
                'save_intermediate_results': True,
                'temp_directory': temp_dir,
                'log_level': 'INFO'
            },
            'shot_detection': {
                'confidence_threshold': 0.7,
                'min_shot_duration': 0.5,
                'detect_gradual_transitions': True,
                'use_gpu': False
            },
            'scene_construction': {
                'model_name': 'llava-test',
                'keyframe_extraction_method': 'middle',
                'max_frames_per_batch': 5,
                'temperature': 0.7,
                'max_tokens': 1024,
                'use_gpu': False
            },
            'cinematic_analysis': {
                'enabled': False
            },
            'pipeline': {
                'batch_size': 16,
                'use_gpu': False,
                'progress_tracking': True,
                'save_keyframes': True,
                'keyframes_directory': str(Path(temp_dir) / 'keyframes')
            },
            'output': {
                'shots_file': str(Path(temp_dir) / 'shots.json'),
                'scenes_file': str(Path(temp_dir) / 'scenes.json'),
                'analysis_file': str(Path(temp_dir) / 'analysis.json'),
                'combined_output': str(Path(temp_dir) / 'complete.json')
            }
        }
    
    @pytest.fixture
    def mock_video_processor(self):
        """Mock VideoProcessor for testing."""
        mock = Mock()
        mock.fps = 30.0
        mock.frame_count = 300
        mock.width = 1920
        mock.height = 1080
        mock.duration = 10.0
        mock.get_video_metadata.return_value = {
            'filename': 'test_video.mp4',
            'duration': 10.0,
            'fps': 30.0,
            'width': 1920,
            'height': 1080,
            'total_frames': 300,
            'format': 'mp4',
            'codec': 'h264'
        }
        
        # Mock frame generator
        def frame_generator(start_frame=0, end_frame=None, step=1):
            import numpy as np
            if end_frame is None:
                end_frame = mock.frame_count
            for i in range(start_frame, end_frame, step):
                yield i, np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
        
        mock.frames_generator = frame_generator
        return mock
    
    def test_pipeline_initialization(self, mock_config, temp_dir):
        """Test pipeline initialization with custom config."""
        config_path = Path(temp_dir) / "test_config.yaml"
        
        # Save config to file
        import yaml
        with open(config_path, 'w') as f:
            yaml.dump(mock_config, f)
        
        # Initialize pipeline
        pipeline = VideoAnalysisPipeline(str(config_path))
        
        assert pipeline.config == mock_config
        assert pipeline.shot_detector is not None
        assert pipeline.scene_constructor is not None
        assert pipeline.cinematic_analyzer is not None
    
    @patch('src.pipeline.shot_detection.VideoProcessor')
    def test_complete_pipeline(self, mock_vp_class, mock_config, temp_dir, mock_video_processor):
        """Test the complete pipeline execution."""
        # Setup mocks
        mock_vp_class.return_value.__enter__.return_value = mock_video_processor
        
        # Create test config file
        config_path = Path(temp_dir) / "test_config.yaml"
        import yaml
        with open(config_path, 'w') as f:
            yaml.dump(mock_config, f)
        
        # Initialize and run pipeline
        pipeline = VideoAnalysisPipeline(str(config_path))
        
        # Mock video path
        video_path = "test_video.mp4"
        
        # Run analysis
        result = pipeline.analyze_video(video_path)
        
        # Verify result structure
        assert isinstance(result, AnalysisResult)
        assert isinstance(result.video_metadata, VideoMetadata)
        assert isinstance(result.shots, list)
        assert isinstance(result.scenes, list)
        assert result.processing_time > 0
        
        # Check if intermediate files were saved
        assert Path(mock_config['output']['shots_file']).exists()
        assert Path(mock_config['output']['scenes_file']).exists()
        assert Path(mock_config['output']['combined_output']).exists()
    
    def test_resume_functionality(self, mock_config, temp_dir):
        """Test resuming from saved intermediate results."""
        # Create mock saved data
        shots_data = {
            'total_shots': 3,
            'shots': [
                {'shot_id': 1, 'start': 0.0, 'end': 3.0},
                {'shot_id': 2, 'start': 3.0, 'end': 6.0},
                {'shot_id': 3, 'start': 6.0, 'end': 10.0}
            ]
        }
        
        scenes_data = {
            'total_scenes': 2,
            'scenes': [
                {
                    'scene_id': 1,
                    'summary': 'Test scene 1',
                    'contained_shots': [1, 2],
                    'setting': 'Indoor',
                    'mood': 'Calm'
                },
                {
                    'scene_id': 2,
                    'summary': 'Test scene 2',
                    'contained_shots': [3],
                    'setting': 'Outdoor',
                    'mood': 'Energetic'
                }
            ]
        }
        
        # Save mock data
        with open(mock_config['output']['shots_file'], 'w') as f:
            json.dump(shots_data, f)
        
        with open(mock_config['output']['scenes_file'], 'w') as f:
            json.dump(scenes_data, f)
        
        # Create config file
        config_path = Path(temp_dir) / "test_config.yaml"
        import yaml
        with open(config_path, 'w') as f:
            yaml.dump(mock_config, f)
        
        # Initialize pipeline
        pipeline = VideoAnalysisPipeline(str(config_path))
        
        # Test loading shots
        shots = pipeline.shot_detector.load_shots(mock_config['output']['shots_file'])
        assert len(shots) == 3
        assert all(isinstance(shot, Shot) for shot in shots)
        
        # Test loading scenes
        scenes = pipeline.scene_constructor.load_scenes(mock_config['output']['scenes_file'])
        assert len(scenes) == 2
        assert all(isinstance(scene, Scene) for scene in scenes)
    
    def test_error_handling(self, mock_config, temp_dir):
        """Test error handling in the pipeline."""
        config_path = Path(temp_dir) / "test_config.yaml"
        import yaml
        with open(config_path, 'w') as f:
            yaml.dump(mock_config, f)
        
        pipeline = VideoAnalysisPipeline(str(config_path))
        
        # Test with non-existent video file
        with pytest.raises(Exception):
            pipeline.analyze_video("non_existent_video.mp4")
    
    def test_output_format_validation(self, mock_config, temp_dir):
        """Test that output matches expected schema."""
        # Create mock complete analysis
        analysis_data = {
            "metadata": {
                "filename": "test.mp4",
                "duration": 10.0,
                "fps": 30.0,
                "width": 1920,
                "height": 1080,
                "total_frames": 300,
                "format": "mp4",
                "codec": "h264"
            },
            "timestamp": "2024-01-01T00:00:00",
            "processing_time": 5.5,
            "analysis": {
                "total_shots": 3,
                "total_scenes": 2,
                "shots": [
                    {
                        "shot_id": 1,
                        "start": 0.0,
                        "end": 3.0,
                        "duration": 3.0,
                        "confidence": 0.95,
                        "transition_type": "cut"
                    }
                ],
                "scenes": [
                    {
                        "scene_id": 1,
                        "summary": "Opening scene",
                        "contained_shots": [1],
                        "setting": "Indoor",
                        "mood": "Calm",
                        "characters": [],
                        "key_actions": [],
                        "start_time": 0.0,
                        "end_time": 3.0,
                        "duration": 3.0
                    }
                ],
                "cinematic_analysis": {
                    "status": "disabled"
                }
            }
        }
        
        # Validate structure
        assert "metadata" in analysis_data
        assert "analysis" in analysis_data
        assert "shots" in analysis_data["analysis"]
        assert "scenes" in analysis_data["analysis"]
        
        # Test loading from dict
        result = AnalysisResult.from_dict(analysis_data)
        assert isinstance(result, AnalysisResult)
        assert len(result.shots) == 1
        assert len(result.scenes) == 1
        
        # Test conversion back to dict
        result_dict = result.to_dict()
        assert result_dict["metadata"]["filename"] == "test.mp4"
        assert result_dict["analysis"]["total_shots"] == 1
        assert result_dict["analysis"]["total_scenes"] == 1