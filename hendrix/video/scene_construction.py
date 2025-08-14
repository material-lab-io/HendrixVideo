"""Scene construction from detected shots."""

import logging
import json
from pathlib import Path
from typing import List, Dict, Any

from hendrix.core.config import ConfigManager
from hendrix.core.exceptions import VideoProcessingError

logger = logging.getLogger(__name__)


class SceneConstructor:
    """Scene construction from detected shots"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.scene_config = config.get("scene_construction", {})
    
    def construct(self, video_path: Path, output_dir: Path, shots_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Construct scenes from detected shots
        
        Args:
            video_path: Path to input video
            output_dir: Directory to save results
            shots_data: Results from shot detection
            
        Returns:
            List of scene dictionaries
        """
        try:
            # Load shots data
            shots_file = shots_data.get("shots_file")
            if shots_file and Path(shots_file).exists():
                with open(shots_file) as f:
                    shots = json.load(f).get("shots", [])
            else:
                shots = []
            
            # Group shots into scenes
            scenes = self._group_shots_into_scenes(shots)
            
            # Save results
            scenes_file = output_dir / "scenes.json"
            with open(scenes_file, 'w') as f:
                json.dump({"scenes": scenes}, f, indent=2)
            
            logger.info(f"Constructed {len(scenes)} scenes from {len(shots)} shots")
            return scenes
            
        except Exception as e:
            raise VideoProcessingError(f"Scene construction failed: {e}")
    
    def _group_shots_into_scenes(self, shots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Group shots into scenes using simple heuristics"""
        
        if not shots:
            return []
        
        scenes = []
        current_scene_shots = []
        
        # Simple grouping: combine 2-3 consecutive shots per scene
        shots_per_scene = 2
        
        for i, shot in enumerate(shots):
            current_scene_shots.append(shot)
            
            # Create scene when we have enough shots or reached the end
            if len(current_scene_shots) >= shots_per_scene or i == len(shots) - 1:
                scene = self._create_scene_from_shots(current_scene_shots, len(scenes) + 1)
                scenes.append(scene)
                current_scene_shots = []
        
        return scenes
    
    def _create_scene_from_shots(self, shots: List[Dict[str, Any]], scene_id: int) -> Dict[str, Any]:
        """Create a scene dictionary from a list of shots"""
        
        if not shots:
            return {}
        
        start_time = shots[0]["start_time"]
        end_time = shots[-1]["end_time"]
        duration = end_time - start_time
        
        return {
            "id": scene_id,
            "start_time": start_time,
            "end_time": end_time,
            "duration": duration,
            "shots": [shot["id"] for shot in shots],
            "shot_count": len(shots),
            "description": f"Scene {scene_id} containing {len(shots)} shots",
            "confidence": 0.8
        }