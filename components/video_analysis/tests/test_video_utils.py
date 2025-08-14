import pytest
import sys
import numpy as np
import cv2
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ..src.utils.video_utils import VideoProcessor, calculate_frame_difference, resize_frame_aspect_ratio


class TestVideoProcessor:
    """Test VideoProcessor class functionality."""
    
    @pytest.fixture
    def mock_video_cap(self):
        """Create a mock video capture object."""
        mock = Mock()
        mock.isOpened.return_value = True
        mock.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FPS: 30.0,
            cv2.CAP_PROP_FRAME_COUNT: 300,
            cv2.CAP_PROP_FRAME_WIDTH: 1920,
            cv2.CAP_PROP_FRAME_HEIGHT: 1080,
            cv2.CAP_PROP_FOURCC: cv2.VideoWriter_fourcc(*'mp4v')
        }.get(prop, 0)
        return mock
    
    @patch('cv2.VideoCapture')
    def test_initialization(self, mock_cv2_cap, mock_video_cap):
        """Test VideoProcessor initialization."""
        mock_cv2_cap.return_value = mock_video_cap
        
        processor = VideoProcessor('test_video.mp4')
        
        assert processor.video_path == 'test_video.mp4'
        assert processor.fps == 30.0
        assert processor.frame_count == 300
        assert processor.width == 1920
        assert processor.height == 1080
        assert processor.duration == 10.0  # 300 frames / 30 fps
        
        mock_cv2_cap.assert_called_once_with('test_video.mp4')
    
    @patch('cv2.VideoCapture')
    def test_initialization_failure(self, mock_cv2_cap):
        """Test VideoProcessor initialization with invalid video."""
        mock_cap = Mock()
        mock_cap.isOpened.return_value = False
        mock_cv2_cap.return_value = mock_cap
        
        with pytest.raises(ValueError, match="Failed to open video"):
            VideoProcessor('invalid_video.mp4')
    
    @patch('cv2.VideoCapture')
    def test_context_manager(self, mock_cv2_cap, mock_video_cap):
        """Test VideoProcessor as context manager."""
        mock_cv2_cap.return_value = mock_video_cap
        
        with VideoProcessor('test_video.mp4') as processor:
            assert processor.cap is not None
        
        # Verify release was called
        mock_video_cap.release.assert_called_once()
    
    @patch('cv2.VideoCapture')
    def test_get_frame_at_time(self, mock_cv2_cap, mock_video_cap):
        """Test frame extraction at specific time."""
        mock_cv2_cap.return_value = mock_video_cap
        
        # Mock frame reading
        test_frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        mock_video_cap.read.return_value = (True, test_frame)
        
        processor = VideoProcessor('test_video.mp4')
        
        # Get frame at 5 seconds
        frame = processor.get_frame_at_time(5.0)
        
        assert frame is not None
        assert frame.shape == (1080, 1920, 3)
        
        # Verify seek to correct frame (5s * 30fps = frame 150)
        mock_video_cap.set.assert_called_with(cv2.CAP_PROP_POS_FRAMES, 150)
    
    @patch('cv2.VideoCapture')
    def test_get_frame_at_index(self, mock_cv2_cap, mock_video_cap):
        """Test frame extraction at specific index."""
        mock_cv2_cap.return_value = mock_video_cap
        
        # Mock frame reading
        test_frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        mock_video_cap.read.return_value = (True, test_frame)
        
        processor = VideoProcessor('test_video.mp4')
        
        # Get frame at index 100
        frame = processor.get_frame_at_index(100)
        
        assert frame is not None
        mock_video_cap.set.assert_called_with(cv2.CAP_PROP_POS_FRAMES, 100)
        
        # Test out of bounds
        frame = processor.get_frame_at_index(-1)
        assert frame is None
        
        frame = processor.get_frame_at_index(500)  # Beyond frame count
        assert frame is None
    
    @patch('cv2.VideoCapture')
    def test_extract_keyframe(self, mock_cv2_cap, mock_video_cap):
        """Test keyframe extraction methods."""
        mock_cv2_cap.return_value = mock_video_cap
        
        test_frame = np.ones((1080, 1920, 3), dtype=np.uint8) * 128
        mock_video_cap.read.return_value = (True, test_frame)
        
        processor = VideoProcessor('test_video.mp4')
        
        # Test middle extraction
        frame = processor.extract_keyframe(2.0, 8.0, method='middle')
        assert frame is not None
        # Should seek to middle time (5.0s = frame 150)
        mock_video_cap.set.assert_called_with(cv2.CAP_PROP_POS_FRAMES, 150)
        
        # Test first extraction
        frame = processor.extract_keyframe(2.0, 8.0, method='first')
        # Should seek to start + 0.1s
        expected_frame = int((2.0 + 0.1) * 30)
        mock_video_cap.set.assert_called_with(cv2.CAP_PROP_POS_FRAMES, expected_frame)
        
        # Test last extraction
        frame = processor.extract_keyframe(2.0, 8.0, method='last')
        # Should seek to end - 0.1s
        expected_frame = int((8.0 - 0.1) * 30)
        mock_video_cap.set.assert_called_with(cv2.CAP_PROP_POS_FRAMES, expected_frame)
        
        # Test invalid method
        with pytest.raises(ValueError):
            processor.extract_keyframe(2.0, 8.0, method='invalid')
    
    @patch('cv2.imwrite')
    @patch('cv2.VideoCapture')
    def test_save_frame(self, mock_cv2_cap, mock_imwrite, mock_video_cap):
        """Test frame saving functionality."""
        mock_cv2_cap.return_value = mock_video_cap
        mock_imwrite.return_value = True
        
        processor = VideoProcessor('test_video.mp4')
        test_frame = np.zeros((100, 100, 3), dtype=np.uint8)
        
        # Test JPEG save
        success = processor.save_frame(test_frame, 'test.jpg', quality=90)
        assert success
        mock_imwrite.assert_called_once()
        args = mock_imwrite.call_args[0]
        assert args[0] == 'test.jpg'
        assert args[2] == [cv2.IMWRITE_JPEG_QUALITY, 90]
        
        # Test PNG save
        mock_imwrite.reset_mock()
        success = processor.save_frame(test_frame, 'test.png')
        assert success
        mock_imwrite.assert_called_once_with('test.png', test_frame)
        
        # Test save failure
        mock_imwrite.return_value = False
        success = processor.save_frame(test_frame, 'test.jpg')
        assert not success
    
    @patch('cv2.VideoCapture')
    def test_frames_generator(self, mock_cv2_cap, mock_video_cap):
        """Test frame generator functionality."""
        mock_cv2_cap.return_value = mock_video_cap
        
        # Mock sequential frame reading
        frames = [np.ones((100, 100, 3), dtype=np.uint8) * i for i in range(10)]
        read_returns = [(True, frame) for frame in frames] + [(False, None)]
        mock_video_cap.read.side_effect = read_returns
        
        processor = VideoProcessor('test_video.mp4')
        
        # Test basic generation
        generated_frames = list(processor.frames_generator(0, 5, 1))
        assert len(generated_frames) == 5
        assert all(idx == i for i, (idx, _) in enumerate(generated_frames))
        
        # Reset mock
        mock_video_cap.read.side_effect = read_returns
        mock_video_cap.set.reset_mock()
        
        # Test with step
        generated_frames = list(processor.frames_generator(0, 10, 2))
        # Should read every other frame
        assert len(generated_frames) == 5
        assert all(idx == i*2 for i, (idx, _) in enumerate(generated_frames))
    
    @patch('cv2.VideoCapture')
    def test_get_video_metadata(self, mock_cv2_cap, mock_video_cap):
        """Test video metadata extraction."""
        mock_cv2_cap.return_value = mock_video_cap
        
        processor = VideoProcessor('test_video.mp4')
        metadata = processor.get_video_metadata()
        
        assert metadata['filename'] == 'test_video.mp4'
        assert metadata['duration'] == 10.0
        assert metadata['fps'] == 30.0
        assert metadata['width'] == 1920
        assert metadata['height'] == 1080
        assert metadata['total_frames'] == 300
        assert metadata['format'] == 'mp4'
        assert 'codec' in metadata


class TestUtilityFunctions:
    """Test standalone utility functions."""
    
    def test_calculate_frame_difference_mse(self):
        """Test MSE frame difference calculation."""
        # Identical frames
        frame1 = np.ones((100, 100, 3), dtype=np.uint8) * 128
        frame2 = np.ones((100, 100, 3), dtype=np.uint8) * 128
        diff = calculate_frame_difference(frame1, frame2, method='mse')
        assert diff == 0.0
        
        # Completely different frames
        frame1 = np.zeros((100, 100, 3), dtype=np.uint8)
        frame2 = np.ones((100, 100, 3), dtype=np.uint8) * 255
        diff = calculate_frame_difference(frame1, frame2, method='mse')
        assert diff == 255.0 ** 2  # Maximum MSE
        
        # Partially different frames
        frame1 = np.zeros((100, 100, 3), dtype=np.uint8)
        frame2 = np.zeros((100, 100, 3), dtype=np.uint8)
        frame2[:50, :50, :] = 255  # Top-left quadrant different
        diff = calculate_frame_difference(frame1, frame2, method='mse')
        assert 0 < diff < 255.0 ** 2
    
    @patch('cv2.compareHist')
    @patch('cv2.calcHist')
    def test_calculate_frame_difference_histogram(self, mock_calc_hist, mock_compare_hist):
        """Test histogram-based frame difference calculation."""
        frame1 = np.zeros((100, 100, 3), dtype=np.uint8)
        frame2 = np.ones((100, 100, 3), dtype=np.uint8) * 128
        
        # Mock histogram calculation and comparison
        mock_calc_hist.side_effect = [np.array([1]), np.array([2])]
        mock_compare_hist.return_value = 0.5
        
        diff = calculate_frame_difference(frame1, frame2, method='histogram')
        
        assert diff == 0.5
        assert mock_calc_hist.call_count == 2
        mock_compare_hist.assert_called_once()
    
    def test_calculate_frame_difference_invalid_method(self):
        """Test frame difference with invalid method."""
        frame1 = np.zeros((100, 100, 3), dtype=np.uint8)
        frame2 = np.zeros((100, 100, 3), dtype=np.uint8)
        
        with pytest.raises(ValueError, match="Unknown difference method"):
            calculate_frame_difference(frame1, frame2, method='invalid')
    
    def test_calculate_frame_difference_shape_mismatch(self):
        """Test frame difference with mismatched shapes."""
        frame1 = np.zeros((100, 100, 3), dtype=np.uint8)
        frame2 = np.zeros((200, 200, 3), dtype=np.uint8)
        
        with pytest.raises(ValueError, match="same dimensions"):
            calculate_frame_difference(frame1, frame2)
    
    def test_resize_frame_aspect_ratio(self):
        """Test aspect ratio preserving resize."""
        # Test downscaling
        frame = np.ones((1080, 1920, 3), dtype=np.uint8)
        resized = resize_frame_aspect_ratio(frame, 960, 540)
        assert resized.shape == (540, 960, 3)
        
        # Test when one dimension is limiting
        frame = np.ones((1080, 1920, 3), dtype=np.uint8)
        resized = resize_frame_aspect_ratio(frame, 1920, 540)
        assert resized.shape == (540, 960, 3)  # Height limited
        
        frame = np.ones((1080, 1920, 3), dtype=np.uint8)
        resized = resize_frame_aspect_ratio(frame, 480, 1080)
        assert resized.shape == (270, 480, 3)  # Width limited
        
        # Test when no resizing needed
        frame = np.ones((360, 640, 3), dtype=np.uint8)
        resized = resize_frame_aspect_ratio(frame, 1920, 1080)
        assert resized.shape == frame.shape  # No change