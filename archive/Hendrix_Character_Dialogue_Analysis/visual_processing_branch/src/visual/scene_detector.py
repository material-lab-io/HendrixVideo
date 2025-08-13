"""
Scene boundary detection using scenedetect library.
Detects scene changes in videos for scene-aware character clustering.
"""

import logging
from typing import List, Tuple, Optional, Dict
from pathlib import Path
import json

try:
    from scenedetect import VideoManager, SceneManager
    from scenedetect.detectors import ContentDetector, AdaptiveDetector
    from scenedetect.frame_timecode import FrameTimecode
except ImportError:
    logging.error("scenedetect not installed. Install with: pip install scenedetect[opencv]")
    raise

import numpy as np

logger = logging.getLogger(__name__)


class SceneInfo:
    """Information about a detected scene."""
    
    def __init__(self, scene_id: int, start_time: float, end_time: float, 
                 start_frame: int, end_frame: int):
        self.scene_id = scene_id
        self.start_time = start_time
        self.end_time = end_time
        self.start_frame = start_frame
        self.end_frame = end_frame
        self.duration = end_time - start_time
        
    def contains_time(self, time: float) -> bool:
        """Check if a given time falls within this scene."""
        return self.start_time <= time <= self.end_time
        
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'scene_id': self.scene_id,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'start_frame': self.start_frame,
            'end_frame': self.end_frame,
            'duration': self.duration
        }


class SceneDetector:
    """Detects scene boundaries in videos using scenedetect library."""
    
    def __init__(self, threshold: float = 30.0, min_scene_len: int = 15,
                 use_adaptive: bool = False):
        """
        Initialize scene detector.
        
        Args:
            threshold: Threshold for scene detection (higher = less sensitive)
            min_scene_len: Minimum scene length in frames
            use_adaptive: Use adaptive detector instead of content detector
        """
        self.threshold = threshold
        self.min_scene_len = min_scene_len
        self.use_adaptive = use_adaptive
        self.scenes: List[SceneInfo] = []
        
    def detect_scenes(self, video_path: str) -> List[SceneInfo]:
        """
        Detect scene boundaries in a video.
        
        Args:
            video_path: Path to video file
            
        Returns:
            List of SceneInfo objects
        """
        logger.info(f"Detecting scenes in video: {video_path}")
        
        # Create video manager
        video_manager = VideoManager([video_path])
        
        # Create scene manager with appropriate detector
        scene_manager = SceneManager()
        
        if self.use_adaptive:
            scene_manager.add_detector(
                AdaptiveDetector(adaptive_threshold=self.threshold,
                                min_scene_len=self.min_scene_len)
            )
        else:
            scene_manager.add_detector(
                ContentDetector(threshold=self.threshold,
                               min_scene_len=self.min_scene_len)
            )
        
        # Start video manager
        video_manager.start()
        
        # Perform scene detection
        scene_manager.detect_scenes(frame_source=video_manager)
        
        # Get scene list
        scene_list = scene_manager.get_scene_list()
        
        # Get video framerate for time calculations
        framerate = video_manager.get_framerate()
        
        # Release video manager
        video_manager.release()
        
        # Convert to SceneInfo objects
        self.scenes = []
        for i, (start_time, end_time) in enumerate(scene_list):
            start_frame = int(start_time.get_frames())
            end_frame = int(end_time.get_frames())
            start_seconds = start_time.get_seconds()
            end_seconds = end_time.get_seconds()
            
            scene_info = SceneInfo(
                scene_id=i,
                start_time=start_seconds,
                end_time=end_seconds,
                start_frame=start_frame,
                end_frame=end_frame
            )
            self.scenes.append(scene_info)
            
        logger.info(f"Detected {len(self.scenes)} scenes")
        self._log_scene_summary()
        
        return self.scenes
    
    def get_scene_at_time(self, time: float) -> Optional[SceneInfo]:
        """
        Get the scene that contains a specific timestamp.
        
        Args:
            time: Time in seconds
            
        Returns:
            SceneInfo object or None if no scene contains the time
        """
        for scene in self.scenes:
            if scene.contains_time(time):
                return scene
        return None
    
    def get_scene_at_frame(self, frame_num: int, fps: float) -> Optional[SceneInfo]:
        """
        Get the scene that contains a specific frame number.
        
        Args:
            frame_num: Frame number
            fps: Video framerate
            
        Returns:
            SceneInfo object or None
        """
        time = frame_num / fps
        return self.get_scene_at_time(time)
    
    def save_scenes(self, output_path: str):
        """Save detected scenes to JSON file."""
        scenes_data = {
            'total_scenes': len(self.scenes),
            'detection_params': {
                'threshold': self.threshold,
                'min_scene_len': self.min_scene_len,
                'use_adaptive': self.use_adaptive
            },
            'scenes': [scene.to_dict() for scene in self.scenes]
        }
        
        with open(output_path, 'w') as f:
            json.dump(scenes_data, f, indent=2)
            
        logger.info(f"Saved scene data to {output_path}")
    
    def load_scenes(self, input_path: str):
        """Load previously detected scenes from JSON file."""
        with open(input_path, 'r') as f:
            data = json.load(f)
            
        self.scenes = []
        for scene_data in data['scenes']:
            scene = SceneInfo(
                scene_id=scene_data['scene_id'],
                start_time=scene_data['start_time'],
                end_time=scene_data['end_time'],
                start_frame=scene_data['start_frame'],
                end_frame=scene_data['end_frame']
            )
            self.scenes.append(scene)
            
        logger.info(f"Loaded {len(self.scenes)} scenes from {input_path}")
    
    def _log_scene_summary(self):
        """Log summary of detected scenes."""
        if not self.scenes:
            return
            
        durations = [scene.duration for scene in self.scenes]
        logger.info(f"Scene statistics:")
        logger.info(f"  - Number of scenes: {len(self.scenes)}")
        logger.info(f"  - Average scene duration: {np.mean(durations):.2f}s")
        logger.info(f"  - Min scene duration: {np.min(durations):.2f}s")
        logger.info(f"  - Max scene duration: {np.max(durations):.2f}s")
        
        # Log first few scenes
        for scene in self.scenes[:5]:
            logger.info(f"  - Scene {scene.scene_id}: "
                       f"{scene.start_time:.2f}s - {scene.end_time:.2f}s "
                       f"({scene.duration:.2f}s)")
        if len(self.scenes) > 5:
            logger.info(f"  - ... and {len(self.scenes) - 5} more scenes")
    
    def get_scene_transitions(self) -> List[float]:
        """Get list of scene transition timestamps."""
        transitions = []
        for i in range(1, len(self.scenes)):
            transitions.append(self.scenes[i].start_time)
        return transitions
    
    def merge_short_scenes(self, min_duration: float = 1.0):
        """
        Merge scenes shorter than min_duration with adjacent scenes.
        
        Args:
            min_duration: Minimum scene duration in seconds
        """
        if len(self.scenes) <= 1:
            return
            
        merged_scenes = []
        i = 0
        
        while i < len(self.scenes):
            current_scene = self.scenes[i]
            
            # If scene is too short and not the last scene
            if current_scene.duration < min_duration and i < len(self.scenes) - 1:
                # Merge with next scene
                next_scene = self.scenes[i + 1]
                merged_scene = SceneInfo(
                    scene_id=len(merged_scenes),
                    start_time=current_scene.start_time,
                    end_time=next_scene.end_time,
                    start_frame=current_scene.start_frame,
                    end_frame=next_scene.end_frame
                )
                merged_scenes.append(merged_scene)
                i += 2  # Skip next scene as it's merged
            else:
                # Keep scene as is but update scene_id
                current_scene.scene_id = len(merged_scenes)
                merged_scenes.append(current_scene)
                i += 1
        
        original_count = len(self.scenes)
        self.scenes = merged_scenes
        logger.info(f"Merged short scenes: {original_count} -> {len(self.scenes)} scenes")