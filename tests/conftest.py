"""
Pytest configuration and fixtures for Hendrix tests
"""
import pytest
from pathlib import Path
import tempfile
import shutil
from typing import Generator

# Add project root to Python path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test outputs"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    # Cleanup
    if temp_path.exists():
        shutil.rmtree(temp_path)


@pytest.fixture
def sample_video_path() -> Path:
    """Path to sample test video"""
    # In a real setup, this would point to a small test video
    return Path("tests/fixtures/sample_video.mp4")


@pytest.fixture
def test_config() -> dict:
    """Test configuration"""
    return {
        "components": {
            "video_analysis": {
                "enabled": True,
                "shot_detection": {
                    "threshold": 0.5
                }
            },
            "character_dialogue": {
                "enabled": True,
                "whisper": {
                    "model_size": "tiny"  # Use tiny model for tests
                }
            },
            "captioning": {
                "enabled": True,
                "vision_language_model": {
                    "active_model": "mock_model"  # Mock for tests
                }
            }
        },
        "pipeline": {
            "device": "cpu",  # Use CPU for tests
            "batch_size": 2
        }
    }


@pytest.fixture
def mock_video_metadata() -> dict:
    """Mock video metadata for testing"""
    return {
        "filename": "test_video.mp4",
        "duration": 60.0,
        "fps": 30.0,
        "width": 1920,
        "height": 1080,
        "total_frames": 1800
    }


@pytest.fixture
def mock_scene_data() -> dict:
    """Mock scene analysis data"""
    return {
        "scenes": [
            {
                "scene_id": 1,
                "start_time": 0.0,
                "end_time": 10.0,
                "shots": [1, 2],
                "summary": "Opening scene"
            },
            {
                "scene_id": 2,
                "start_time": 10.0,
                "end_time": 20.0,
                "shots": [3, 4, 5],
                "summary": "Main dialogue"
            }
        ],
        "shots": [
            {"shot_id": 1, "start": 0.0, "end": 3.0},
            {"shot_id": 2, "start": 3.0, "end": 10.0},
            {"shot_id": 3, "start": 10.0, "end": 12.0},
            {"shot_id": 4, "start": 12.0, "end": 15.0},
            {"shot_id": 5, "start": 15.0, "end": 20.0}
        ]
    }


# Markers for test categorization
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "gpu: marks tests that require GPU")
    config.addinivalue_line("markers", "model: marks tests that require model downloads")