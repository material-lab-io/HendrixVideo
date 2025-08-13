import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import time

from models.autoshot import AutoShotDetector
from models.transnetv2 import TransNetV2Detector
from schemas.shot import Shot
from utils.video_utils import VideoProcessor

logger = logging.getLogger(__name__)


class ShotDetectionPipeline:
    """Stage 1: High-Precision Shot Boundary Detection."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.shot_config = config.get('shot_detection', {})
        self.output_config = config.get('output', {})
        
        # Initialize appropriate detector based on config
        model_name = self.shot_config.get('model_name', 'autoshot').lower()
        if model_name == 'transnetv2':
            self.detector = TransNetV2Detector(self.shot_config)
        else:
            self.detector = AutoShotDetector(self.shot_config)
    
    def process_video(self, video_path: str, save_intermediate: bool = True) -> List[Shot]:
        """
        Process a video file to detect shot boundaries.
        
        Args:
            video_path: Path to the input video file
            save_intermediate: Whether to save intermediate results
            
        Returns:
            List of Shot objects
        """
        logger.info(f"Starting shot detection for: {video_path}")
        start_time = time.time()
        
        # Initialize video processor
        with VideoProcessor(video_path) as video_processor:
            # Get video metadata
            metadata = video_processor.get_video_metadata()
            logger.info(f"Video metadata: {metadata}")
            
            # Detect shots based on detector type
            if hasattr(self.detector, 'detect_shots'):
                # TransNetV2 returns shots directly
                shot_dicts = self.detector.detect_shots(video_processor)
            else:
                # AutoShot uses boundaries
                boundaries = self.detector.detect_boundaries(video_processor)
                shot_dicts = self.detector.boundaries_to_shots(
                    boundaries, video_processor.duration
                )
            
            # Create Shot objects
            shots = []
            for shot_dict in shot_dicts:
                shot = Shot(
                    shot_id=shot_dict['shot_id'],
                    start=shot_dict['start'],
                    end=shot_dict['end'],
                    confidence=shot_dict.get('confidence'),
                    transition_type=shot_dict.get('transition_type')
                )
                shots.append(shot)
            
            # Extract and save keyframes if configured
            if self.config.get('pipeline', {}).get('save_keyframes', True):
                self._extract_keyframes(video_processor, shots)
        
        processing_time = time.time() - start_time
        logger.info(f"Shot detection completed in {processing_time:.2f} seconds")
        logger.info(f"Detected {len(shots)} shots")
        
        # Save intermediate results if requested
        if save_intermediate:
            self._save_shots(shots)
        
        return shots
    
    def _extract_keyframes(self, video_processor: VideoProcessor, shots: List[Shot]) -> None:
        """Extract and save keyframes for each shot."""
        keyframes_dir = Path(self.config.get('pipeline', {}).get('keyframes_directory', './keyframes'))
        keyframes_dir.mkdir(parents=True, exist_ok=True)
        
        method = self.config.get('scene_construction', {}).get('keyframe_extraction_method', 'middle')
        
        logger.info(f"Extracting keyframes using '{method}' method")
        
        for shot in shots:
            try:
                # Extract keyframe
                keyframe = video_processor.extract_keyframe(shot.start, shot.end, method)
                
                if keyframe is not None:
                    # Save keyframe
                    filename = f"shot_{shot.shot_id:04d}.jpg"
                    filepath = keyframes_dir / filename
                    
                    if video_processor.save_frame(keyframe, str(filepath)):
                        shot.keyframe_path = str(filepath)
                        logger.debug(f"Saved keyframe for shot {shot.shot_id}")
                    else:
                        logger.warning(f"Failed to save keyframe for shot {shot.shot_id}")
                else:
                    logger.warning(f"Failed to extract keyframe for shot {shot.shot_id}")
                    
            except Exception as e:
                logger.error(f"Error processing keyframe for shot {shot.shot_id}: {e}")
    
    def _save_shots(self, shots: List[Shot]) -> None:
        """Save shot detection results to file."""
        output_file = Path(self.output_config.get('shots_file', 'shots.json'))
        
        try:
            shots_data = {
                'total_shots': len(shots),
                'shots': [shot.to_dict() for shot in shots]
            }
            
            with open(output_file, 'w') as f:
                json.dump(shots_data, f, indent=2)
            
            logger.info(f"Saved shot detection results to: {output_file}")
            
        except Exception as e:
            logger.error(f"Failed to save shot detection results: {e}")
    
    def load_shots(self, shots_file: str) -> List[Shot]:
        """Load previously saved shot detection results."""
        try:
            with open(shots_file, 'r') as f:
                data = json.load(f)
            
            shots = [Shot.from_dict(shot_dict) for shot_dict in data['shots']]
            logger.info(f"Loaded {len(shots)} shots from: {shots_file}")
            
            return shots
            
        except Exception as e:
            logger.error(f"Failed to load shots from file: {e}")
            raise