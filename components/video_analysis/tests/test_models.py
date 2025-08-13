import pytest
import sys
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from models.autoshot import AutoShotDetector, ShotBoundary
from models.llava import LLaVAAnalyzer
from models.cinematic_vlm import CinematicVLM


class TestAutoShotDetector:
    """Test AutoShot model functionality."""
    
    @pytest.fixture
    def detector_config(self):
        return {
            'confidence_threshold': 0.7,
            'min_shot_duration': 0.5,
            'detect_gradual_transitions': True,
            'use_gpu': False
        }
    
    @pytest.fixture
    def detector(self, detector_config):
        return AutoShotDetector(detector_config)
    
    def test_initialization(self, detector, detector_config):
        """Test AutoShot detector initialization."""
        assert detector.confidence_threshold == detector_config['confidence_threshold']
        assert detector.min_shot_duration == detector_config['min_shot_duration']
        assert detector.detect_gradual == detector_config['detect_gradual_transitions']
    
    def test_frame_difference_calculation(self, detector):
        """Test frame difference calculation."""
        # Create two identical frames
        frame1 = np.ones((100, 100, 3), dtype=np.uint8) * 128
        frame2 = np.ones((100, 100, 3), dtype=np.uint8) * 128
        
        # Identical frames should have zero difference
        diff = detector._calculate_frame_difference(frame1, frame2)
        assert diff == 0.0
        
        # Completely different frames
        frame2 = np.zeros((100, 100, 3), dtype=np.uint8)
        diff = detector._calculate_frame_difference(frame1, frame2)
        assert diff > 0.5  # Should be significant
        
        # Partially different frames
        frame2 = np.ones((100, 100, 3), dtype=np.uint8) * 128
        frame2[:50, :50, :] = 255
        diff = detector._calculate_frame_difference(frame1, frame2)
        assert 0 < diff < 1.0
    
    def test_boundary_filtering(self, detector):
        """Test boundary filtering by minimum duration."""
        boundaries = [
            ShotBoundary(0, 0.0, 0.9, 'cut'),
            ShotBoundary(10, 0.3, 0.8, 'cut'),  # Too close to previous
            ShotBoundary(30, 1.0, 0.85, 'cut'),
            ShotBoundary(45, 1.4, 0.7, 'cut'),  # Too close to previous
            ShotBoundary(60, 2.0, 0.9, 'cut')
        ]
        
        filtered = detector._filter_boundaries_by_duration(boundaries, fps=30.0)
        
        # Should filter out boundaries too close together
        assert len(filtered) == 3
        assert filtered[0].frame_index == 0
        assert filtered[1].frame_index == 30
        assert filtered[2].frame_index == 60
    
    def test_boundaries_to_shots(self, detector):
        """Test conversion of boundaries to shot list."""
        boundaries = [
            ShotBoundary(0, 0.0, 1.0, 'start'),
            ShotBoundary(30, 1.0, 0.9, 'cut'),
            ShotBoundary(60, 2.0, 0.85, 'cut')
        ]
        
        shots = detector.boundaries_to_shots(boundaries, video_duration=3.0)
        
        assert len(shots) == 3
        assert shots[0]['shot_id'] == 1
        assert shots[0]['start'] == 0.0
        assert shots[0]['end'] == 1.0
        assert shots[1]['shot_id'] == 2
        assert shots[1]['start'] == 1.0
        assert shots[1]['end'] == 2.0
        assert shots[2]['shot_id'] == 3
        assert shots[2]['start'] == 2.0
        assert shots[2]['end'] == 3.0
    
    @patch('models.autoshot.logger')
    def test_detect_boundaries(self, mock_logger, detector):
        """Test boundary detection with mock video processor."""
        mock_vp = Mock()
        mock_vp.fps = 30.0
        mock_vp.frame_count = 90
        
        # Mock frame generator
        frames = []
        for i in range(3):
            # Create 30 similar frames for each shot
            base_color = i * 85  # 0, 85, 170
            for j in range(30):
                frame = np.ones((100, 100, 3), dtype=np.uint8) * base_color
                frames.append((i * 30 + j, frame))
        
        mock_vp.frames_generator.return_value = iter(frames)
        
        boundaries = detector.detect_boundaries(mock_vp)
        
        # Should detect boundaries between different colored sections
        assert len(boundaries) >= 2  # At least 2 transitions
        mock_logger.info.assert_called()


class TestLLaVAAnalyzer:
    """Test LLaVA model functionality."""
    
    @pytest.fixture
    def llava_config(self):
        return {
            'model_name': 'llava-test',
            'temperature': 0.7,
            'max_tokens': 1024,
            'use_gpu': False
        }
    
    @pytest.fixture
    def analyzer(self, llava_config):
        return LLaVAAnalyzer(llava_config)
    
    def test_initialization(self, analyzer, llava_config):
        """Test LLaVA analyzer initialization."""
        assert analyzer.model_name == llava_config['model_name']
        assert analyzer.temperature == llava_config['temperature']
        assert analyzer.max_tokens == llava_config['max_tokens']
    
    def test_json_extraction(self, analyzer):
        """Test JSON extraction from model response."""
        # Test valid JSON
        response = '''The scenes are as follows:
        [
            {
                "scene_id": 1,
                "summary": "Opening scene in a city",
                "setting": "Urban street",
                "mood": "Busy",
                "contained_shots": [1, 2, 3]
            }
        ]
        Additional text here.'''
        
        scenes = analyzer._extract_json_from_response(response)
        assert len(scenes) == 1
        assert scenes[0]['scene_id'] == 1
        assert scenes[0]['summary'] == "Opening scene in a city"
        
        # Test invalid JSON
        response = "No JSON here"
        scenes = analyzer._extract_json_from_response(response)
        assert scenes == []
        
        # Test malformed JSON
        response = "[{invalid json}]"
        scenes = analyzer._extract_json_from_response(response)
        assert scenes == []
    
    def test_demo_scene_generation(self, analyzer):
        """Test demo scene generation."""
        shot_ids = list(range(1, 11))  # 10 shots
        
        scenes = analyzer._generate_demo_scenes(shot_ids)
        
        assert len(scenes) > 0
        assert all('scene_id' in s for s in scenes)
        assert all('summary' in s for s in scenes)
        assert all('contained_shots' in s for s in scenes)
        
        # Check all shots are assigned
        all_assigned = []
        for scene in scenes:
            all_assigned.extend(scene['contained_shots'])
        assert set(all_assigned) == set(shot_ids)
    
    @patch('models.llava.Image')
    def test_analyze_shot_sequence(self, mock_image, analyzer):
        """Test shot sequence analysis in demo mode."""
        keyframe_paths = ['frame1.jpg', 'frame2.jpg', 'frame3.jpg']
        shot_ids = [1, 2, 3]
        prompt = "Analyze these frames"
        
        scenes = analyzer.analyze_shot_sequence(keyframe_paths, shot_ids, prompt)
        
        # In demo mode, should return demo scenes
        assert len(scenes) > 0
        assert all(isinstance(s, dict) for s in scenes)


class TestCinematicVLM:
    """Test Cinematic VLM functionality."""
    
    @pytest.fixture
    def cinematic_config(self):
        return {
            'enabled': True,
            'model_name': 'cinematic-test'
        }
    
    @pytest.fixture
    def analyzer(self, cinematic_config):
        return CinematicVLM(cinematic_config)
    
    def test_initialization(self, analyzer, cinematic_config):
        """Test Cinematic VLM initialization."""
        assert analyzer.enabled == cinematic_config['enabled']
        assert analyzer.config == cinematic_config
    
    def test_disabled_analysis(self):
        """Test analysis when disabled."""
        config = {'enabled': False}
        analyzer = CinematicVLM(config)
        
        result = analyzer.analyze_cinematography([], [])
        
        assert result['status'] == 'disabled'
        assert 'message' in result
    
    def test_placeholder_analysis(self, analyzer):
        """Test placeholder analysis output."""
        scenes = [
            {'scene_id': 1, 'summary': 'Test scene'},
            {'scene_id': 2, 'summary': 'Another scene'}
        ]
        keyframes = ['frame1.jpg', 'frame2.jpg']
        
        result = analyzer.analyze_cinematography(scenes, keyframes)
        
        assert 'visual_style' in result
        assert 'cinematographic_techniques' in result
        assert 'narrative_structure' in result
        assert 'technical_quality' in result
        assert 'recommendations' in result
        
        # Check structure
        assert 'overall_aesthetic' in result['visual_style']
        assert 'camera_movements' in result['cinematographic_techniques']
        assert 'pacing' in result['narrative_structure']
        assert 'production_value' in result['technical_quality']