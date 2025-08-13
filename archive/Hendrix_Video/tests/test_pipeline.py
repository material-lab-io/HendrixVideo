import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from schemas.shot import Shot
from schemas.scene import Scene
from schemas.analysis import VideoMetadata, AnalysisResult


class TestSchemas:
    """Test data schemas."""
    
    def test_shot_creation(self):
        """Test Shot object creation and methods."""
        shot = Shot(
            shot_id=1,
            start=0.0,
            end=5.0,
            confidence=0.95,
            transition_type="cut"
        )
        
        assert shot.shot_id == 1
        assert shot.start == 0.0
        assert shot.end == 5.0
        assert shot.duration == 5.0
        assert shot.confidence == 0.95
        assert shot.transition_type == "cut"
        
        # Test dict conversion
        shot_dict = shot.to_dict()
        assert isinstance(shot_dict, dict)
        assert shot_dict['shot_id'] == 1
        
        # Test from_dict
        shot2 = Shot.from_dict(shot_dict)
        assert shot2.shot_id == shot.shot_id
        assert shot2.duration == shot.duration
    
    def test_scene_creation(self):
        """Test Scene object creation and methods."""
        scene = Scene(
            scene_id=1,
            summary="Opening scene in a city",
            contained_shots=[1, 2, 3],
            setting="Urban street",
            mood="Energetic"
        )
        
        assert scene.scene_id == 1
        assert scene.summary == "Opening scene in a city"
        assert len(scene.contained_shots) == 3
        assert scene.setting == "Urban street"
        assert scene.mood == "Energetic"
        
        # Test add_shot
        scene.add_shot(4)
        assert 4 in scene.contained_shots
        assert len(scene.contained_shots) == 4
        
        # Test duplicate prevention
        scene.add_shot(4)
        assert len(scene.contained_shots) == 4
    
    def test_video_metadata(self):
        """Test VideoMetadata object."""
        metadata = VideoMetadata(
            filename="test_video.mp4",
            duration=120.5,
            fps=24.0,
            width=1920,
            height=1080,
            total_frames=2892,
            format="mp4",
            codec="h264"
        )
        
        assert metadata.filename == "test_video.mp4"
        assert metadata.duration == 120.5
        assert metadata.fps == 24.0
        assert metadata.width == 1920
        assert metadata.height == 1080
    
    def test_analysis_result(self):
        """Test AnalysisResult object."""
        metadata = VideoMetadata(
            filename="test.mp4",
            duration=60.0,
            fps=30.0,
            width=1280,
            height=720,
            total_frames=1800
        )
        
        shots = [
            Shot(shot_id=1, start=0.0, end=5.0),
            Shot(shot_id=2, start=5.0, end=10.0),
            Shot(shot_id=3, start=10.0, end=15.0)
        ]
        
        scenes = [
            Scene(scene_id=1, summary="Scene 1", contained_shots=[1, 2]),
            Scene(scene_id=2, summary="Scene 2", contained_shots=[3])
        ]
        
        result = AnalysisResult(
            video_metadata=metadata,
            shots=shots,
            scenes=scenes,
            processing_time=10.5
        )
        
        assert len(result.shots) == 3
        assert len(result.scenes) == 2
        assert result.processing_time == 10.5
        
        # Test get_scene_by_shot
        scene = result.get_scene_by_shot(2)
        assert scene is not None
        assert scene.scene_id == 1
        
        # Test get_shots_in_scene
        scene_shots = result.get_shots_in_scene(1)
        assert len(scene_shots) == 2
        assert scene_shots[0].shot_id == 1
        assert scene_shots[1].shot_id == 2
        
        # Test to_dict
        result_dict = result.to_dict()
        assert isinstance(result_dict, dict)
        assert 'metadata' in result_dict
        assert 'analysis' in result_dict
        assert result_dict['analysis']['total_shots'] == 3
        assert result_dict['analysis']['total_scenes'] == 2


class TestVideoUtils:
    """Test video utility functions."""
    
    def test_frame_difference_calculation(self):
        """Test frame difference calculation."""
        import numpy as np
        from utils.video_utils import calculate_frame_difference
        
        # Create two identical frames
        frame1 = np.ones((100, 100, 3), dtype=np.uint8) * 128
        frame2 = np.ones((100, 100, 3), dtype=np.uint8) * 128
        
        # Identical frames should have zero difference
        diff = calculate_frame_difference(frame1, frame2, method="mse")
        assert diff == 0.0
        
        # Different frames should have non-zero difference
        frame2[:50, :50, :] = 255
        diff = calculate_frame_difference(frame1, frame2, method="mse")
        assert diff > 0.0
    
    def test_resize_aspect_ratio(self):
        """Test aspect ratio preserving resize."""
        import numpy as np
        from utils.video_utils import resize_frame_aspect_ratio
        
        # Create a test frame
        frame = np.ones((1080, 1920, 3), dtype=np.uint8)
        
        # Test downscaling
        resized = resize_frame_aspect_ratio(frame, 960, 540)
        assert resized.shape[0] == 540
        assert resized.shape[1] == 960
        
        # Test when frame is already smaller
        small_frame = np.ones((360, 640, 3), dtype=np.uint8)
        resized = resize_frame_aspect_ratio(small_frame, 1920, 1080)
        assert resized.shape == small_frame.shape


if __name__ == "__main__":
    pytest.main([__file__, "-v"])