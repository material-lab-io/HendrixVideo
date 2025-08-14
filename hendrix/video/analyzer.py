"""
Video Analysis Main Orchestrator
Coordinates shot detection and scene construction
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

from hendrix.core.config import ConfigManager
from hendrix.core.exceptions import VideoProcessingError

logger = logging.getLogger(__name__)


class VideoAnalyzer:
    """Main video analysis orchestrator"""
    
    def __init__(self, config: ConfigManager):
        """Initialize video analyzer with configuration"""
        self.config = config
        self.video_config = config.get("video_analysis", {})
        
    def process(self, video_path: Path, output_dir: Path) -> Dict[str, Any]:
        """
        Process video through shot detection and scene construction
        
        Args:
            video_path: Path to input video
            output_dir: Directory to save results
            
        Returns:
            Dictionary with processing results
        """
        try:
            # Validate input
            if not video_path.exists():
                raise VideoProcessingError(f"Video file not found: {video_path}")
            
            # Create output directory
            output_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Processing video: {video_path}")
            
            # Step 1: Shot detection
            shots_results = self._detect_shots(video_path, output_dir)
            
            # Step 2: Scene construction (if shots were detected)
            scenes_results = {}
            if shots_results.get("shots_count", 0) > 0:
                scenes_results = self._construct_scenes(video_path, output_dir, shots_results)
            
            # Combine results
            results = {
                "status": "success",
                "video_path": str(video_path),
                "output_dir": str(output_dir),
                **shots_results,
                **scenes_results,
                "output_files": self._list_output_files(output_dir)
            }
            
            logger.info("Video analysis completed successfully")
            return results
            
        except Exception as e:
            logger.error(f"Video analysis failed: {e}")
            raise VideoProcessingError(f"Video analysis failed: {e}")
    
    def _detect_shots(self, video_path: Path, output_dir: Path) -> Dict[str, Any]:
        """Detect shot boundaries in the video"""
        try:
            from .shot_detection import ShotDetector
            
            detector = ShotDetector(self.config)
            shots = detector.detect(video_path, output_dir)
            
            return {
                "shots_count": len(shots),
                "shots_file": str(output_dir / "shots.json")
            }
            
        except ImportError:
            logger.warning("Shot detection module not available, using mock results")
            return self._mock_shot_detection(video_path, output_dir)
        
        except Exception as e:
            logger.error(f"Shot detection failed: {e}")
            return {
                "shots_count": 0,
                "shots_file": None,
                "error": str(e)
            }
    
    def _construct_scenes(self, video_path: Path, output_dir: Path, shots_data: Dict[str, Any]) -> Dict[str, Any]:
        """Construct scenes from detected shots"""
        try:
            from .scene_construction import SceneConstructor
            
            constructor = SceneConstructor(self.config)
            scenes = constructor.construct(video_path, output_dir, shots_data)
            
            return {
                "scenes_count": len(scenes),
                "scenes_file": str(output_dir / "scenes.json")
            }
            
        except ImportError:
            logger.warning("Scene construction module not available, using mock results")
            return self._mock_scene_construction(shots_data)
            
        except Exception as e:
            logger.error(f"Scene construction failed: {e}")
            return {
                "scenes_count": 0,
                "scenes_file": None,
                "error": str(e)
            }
    
    def _mock_shot_detection(self, video_path: Path, output_dir: Path) -> Dict[str, Any]:
        """Mock shot detection for testing/fallback"""
        import json
        
        # Create mock shots data
        mock_shots = [
            {
                "id": 1,
                "start_time": 0.0,
                "end_time": 30.0,
                "confidence": 0.9,
                "transition_type": "cut"
            },
            {
                "id": 2, 
                "start_time": 30.0,
                "end_time": 60.0,
                "confidence": 0.8,
                "transition_type": "cut"
            }
        ]
        
        shots_file = output_dir / "shots.json"
        with open(shots_file, 'w') as f:
            json.dump({"shots": mock_shots}, f, indent=2)
        
        return {
            "shots_count": len(mock_shots),
            "shots_file": str(shots_file),
            "method": "mock"
        }
    
    def _mock_scene_construction(self, shots_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock scene construction for testing/fallback"""
        shots_count = shots_data.get("shots_count", 0)
        
        # Group shots into scenes (roughly 2 shots per scene)
        scenes_count = max(1, shots_count // 2)
        
        return {
            "scenes_count": scenes_count,
            "scenes_file": None,
            "method": "mock"
        }
    
    def _list_output_files(self, output_dir: Path) -> List[str]:
        """List generated output files"""
        output_files = []
        
        for pattern in ["*.json", "*.srt", "*.vtt", "*.html"]:
            output_files.extend(str(f) for f in output_dir.glob(pattern))
        
        return output_files