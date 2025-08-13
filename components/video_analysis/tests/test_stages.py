import pytest
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pipeline.shot_detection import ShotDetectionPipeline
from pipeline.scene_construction import SceneConstructionPipeline
from pipeline.cinematic_analysis import CinematicAnalysisPipeline
from schemas.shot import Shot
from schemas.scene import Scene


class TestShotDetectionPipeline:
    """Test Stage 1: Shot Detection Pipeline."""
    
    @pytest.fixture
    def config(self, tmp_path):
        return {
            'shot_detection': {
                'confidence_threshold': 0.7,
                'min_shot_duration': 0.5,
                'detect_gradual_transitions': True
            },
            'pipeline': {
                'save_keyframes': True,
                'keyframes_directory': str(tmp_path / 'keyframes')
            },
            'output': {
                'shots_file': str(tmp_path / 'shots.json')
            }
        }
    
    @pytest.fixture
    def pipeline(self, config):
        return ShotDetectionPipeline(config)
    
    @patch('pipeline.shot_detection.VideoProcessor')
    def test_process_video(self, mock_vp_class, pipeline, config):
        """Test video processing for shot detection."""
        # Mock video processor
        mock_vp = Mock()
        mock_vp.duration = 10.0
        mock_vp.fps = 30.0
        mock_vp.get_video_metadata.return_value = {
            'filename': 'test.mp4',
            'duration': 10.0,
            'fps': 30.0,
            'width': 1920,
            'height': 1080,
            'total_frames': 300,
            'format': 'mp4',
            'codec': 'h264'
        }
        
        # Mock boundary detection
        mock_vp_class.return_value.__enter__.return_value = mock_vp
        
        # Mock detector to return some boundaries
        with patch.object(pipeline.detector, 'detect_boundaries') as mock_detect:
            mock_boundaries = [Mock(timestamp=0.0), Mock(timestamp=3.0), Mock(timestamp=7.0)]
            mock_detect.return_value = mock_boundaries
            
            with patch.object(pipeline.detector, 'boundaries_to_shots') as mock_convert:
                mock_convert.return_value = [
                    {'shot_id': 1, 'start': 0.0, 'end': 3.0},
                    {'shot_id': 2, 'start': 3.0, 'end': 7.0},
                    {'shot_id': 3, 'start': 7.0, 'end': 10.0}
                ]
                
                # Mock keyframe extraction
                mock_vp.extract_keyframe.return_value = np.zeros((100, 100, 3))
                mock_vp.save_frame.return_value = True
                
                shots = pipeline.process_video('test.mp4')
        
        assert len(shots) == 3
        assert all(isinstance(shot, Shot) for shot in shots)
        assert shots[0].shot_id == 1
        assert shots[0].start == 0.0
        assert shots[0].end == 3.0
    
    def test_save_and_load_shots(self, pipeline, tmp_path):
        """Test saving and loading shot detection results."""
        # Create test shots
        shots = [
            Shot(shot_id=1, start=0.0, end=3.0, confidence=0.9),
            Shot(shot_id=2, start=3.0, end=7.0, confidence=0.85),
            Shot(shot_id=3, start=7.0, end=10.0, confidence=0.95)
        ]
        
        # Save shots
        pipeline._save_shots(shots)
        
        # Verify file exists
        shots_file = Path(pipeline.output_config['shots_file'])
        assert shots_file.exists()
        
        # Load shots
        loaded_shots = pipeline.load_shots(str(shots_file))
        
        assert len(loaded_shots) == 3
        assert loaded_shots[0].shot_id == 1
        assert loaded_shots[1].start == 3.0
        assert loaded_shots[2].end == 10.0


class TestSceneConstructionPipeline:
    """Test Stage 2: Scene Construction Pipeline."""
    
    @pytest.fixture
    def config(self, tmp_path):
        return {
            'scene_construction': {
                'model_name': 'llava-test',
                'keyframe_extraction_method': 'middle',
                'max_frames_per_batch': 5,
                'temperature': 0.7,
                'max_tokens': 1024
            },
            'output': {
                'scenes_file': str(tmp_path / 'scenes.json')
            }
        }
    
    @pytest.fixture
    def pipeline(self, config):
        return SceneConstructionPipeline(config)
    
    @pytest.fixture
    def test_shots(self, tmp_path):
        """Create test shots with keyframe paths."""
        shots = []
        for i in range(6):
            keyframe_path = tmp_path / f'shot_{i+1}.jpg'
            keyframe_path.touch()  # Create empty file
            
            shot = Shot(
                shot_id=i+1,
                start=i*2.0,
                end=(i+1)*2.0,
                keyframe_path=str(keyframe_path)
            )
            shots.append(shot)
        return shots
    
    def test_process_shots(self, pipeline, test_shots):
        """Test processing shots to construct scenes."""
        # Mock analyzer to return demo scenes
        with patch.object(pipeline.analyzer, 'analyze_shot_sequence') as mock_analyze:
            # Return scenes for two batches
            mock_analyze.side_effect = [
                [
                    {
                        'scene_id': 1,
                        'summary': 'Opening scene',
                        'contained_shots': [1, 2, 3],
                        'setting': 'Indoor',
                        'mood': 'Calm'
                    }
                ],
                [
                    {
                        'scene_id': 2,
                        'summary': 'Action scene',
                        'contained_shots': [4, 5, 6],
                        'setting': 'Outdoor',
                        'mood': 'Intense'
                    }
                ]
            ]
            
            scenes = pipeline.process_shots(test_shots, save_intermediate=False)
        
        assert len(scenes) == 2
        assert all(isinstance(scene, Scene) for scene in scenes)
        assert scenes[0].summary == 'Opening scene'
        assert scenes[0].contained_shots == [1, 2, 3]
        assert scenes[1].summary == 'Action scene'
        assert scenes[1].contained_shots == [4, 5, 6]
        
        # Check temporal information
        assert scenes[0].start_time == 0.0
        assert scenes[0].end_time == 6.0
        assert scenes[1].start_time == 6.0
        assert scenes[1].end_time == 12.0
    
    def test_post_process_scenes(self, pipeline, test_shots):
        """Test scene post-processing."""
        # Create scenes with some unassigned shots
        scenes = [
            Scene(
                scene_id=1,
                summary='Scene 1',
                contained_shots=[1, 2],
                start_time=0.0,
                end_time=4.0
            ),
            Scene(
                scene_id=2,
                summary='Scene 2',
                contained_shots=[4, 5],
                start_time=6.0,
                end_time=10.0
            )
        ]
        
        # Process scenes (shots 3 and 6 are unassigned)
        processed = pipeline._post_process_scenes(scenes, test_shots)
        
        # Should have added a miscellaneous scene
        assert len(processed) == 3
        assert processed[-1].summary == 'Miscellaneous shots'
        assert 3 in processed[-1].contained_shots
        assert 6 in processed[-1].contained_shots
        
        # Check renumbering
        assert processed[0].scene_id == 1
        assert processed[1].scene_id == 2
        assert processed[2].scene_id == 3
    
    def test_save_and_load_scenes(self, pipeline, tmp_path):
        """Test saving and loading scene construction results."""
        scenes = [
            Scene(
                scene_id=1,
                summary='Test scene 1',
                contained_shots=[1, 2, 3],
                setting='Indoor',
                mood='Calm'
            ),
            Scene(
                scene_id=2,
                summary='Test scene 2',
                contained_shots=[4, 5],
                setting='Outdoor',
                mood='Energetic'
            )
        ]
        
        # Save scenes
        pipeline._save_scenes(scenes)
        
        # Verify file exists
        scenes_file = Path(pipeline.output_config['scenes_file'])
        assert scenes_file.exists()
        
        # Load scenes
        loaded_scenes = pipeline.load_scenes(str(scenes_file))
        
        assert len(loaded_scenes) == 2
        assert loaded_scenes[0].summary == 'Test scene 1'
        assert loaded_scenes[1].contained_shots == [4, 5]


class TestCinematicAnalysisPipeline:
    """Test Stage 3: Cinematic Analysis Pipeline."""
    
    @pytest.fixture
    def config(self):
        return {
            'cinematic_analysis': {
                'enabled': True,
                'model_name': 'cinematic-test'
            }
        }
    
    @pytest.fixture
    def pipeline(self, config):
        return CinematicAnalysisPipeline(config)
    
    @pytest.fixture
    def test_data(self, tmp_path):
        """Create test shots and scenes."""
        shots = []
        for i in range(6):
            keyframe_path = tmp_path / f'shot_{i+1}.jpg'
            keyframe_path.touch()
            
            shot = Shot(
                shot_id=i+1,
                start=i*2.0,
                end=(i+1)*2.0,
                keyframe_path=str(keyframe_path)
            )
            shots.append(shot)
        
        scenes = [
            Scene(
                scene_id=1,
                summary='Opening scene',
                contained_shots=[1, 2, 3],
                setting='Indoor',
                mood='Calm'
            ),
            Scene(
                scene_id=2,
                summary='Action scene',
                contained_shots=[4, 5, 6],
                setting='Outdoor',
                mood='Intense'
            )
        ]
        
        return shots, scenes
    
    def test_analyze_video(self, pipeline, test_data):
        """Test cinematic analysis."""
        shots, scenes = test_data
        
        result = pipeline.analyze_video(shots, scenes)
        
        assert 'metadata' in result
        assert result['metadata']['total_shots_analyzed'] == 6
        assert result['metadata']['total_scenes_analyzed'] == 2
        assert result['metadata']['processing_time'] > 0
        
        # Check placeholder analysis results
        assert 'visual_style' in result
        assert 'cinematographic_techniques' in result
        assert 'narrative_structure' in result
        assert 'technical_quality' in result
        assert 'recommendations' in result
    
    def test_disabled_analysis(self):
        """Test analysis when disabled."""
        config = {
            'cinematic_analysis': {
                'enabled': False
            }
        }
        pipeline = CinematicAnalysisPipeline(config)
        
        result = pipeline.analyze_video([], [])
        
        assert result['status'] == 'disabled'
        assert 'message' in result