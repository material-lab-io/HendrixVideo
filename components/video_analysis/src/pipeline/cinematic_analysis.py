import logging
from typing import List, Dict, Any
import time

from ..models.cinematic_vlm import CinematicVLM
from ..schemas.scene import Scene
from ..schemas.shot import Shot

logger = logging.getLogger(__name__)


class CinematicAnalysisPipeline:
    """Stage 3: Expert Cinematic Analysis using specialized VLM."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.cinematic_config = config.get('cinematic_analysis', {})
        self.analyzer = CinematicVLM(self.cinematic_config)
    
    def analyze_video(self, shots: List[Shot], scenes: List[Scene]) -> Dict[str, Any]:
        """
        Perform cinematic analysis on the video.
        
        Args:
            shots: List of Shot objects
            scenes: List of Scene objects
            
        Returns:
            Dictionary containing cinematic analysis results
        """
        if not self.analyzer.enabled:
            logger.info("Cinematic analysis is disabled")
            return {
                "status": "disabled",
                "message": "Stage 3 cinematic analysis is not enabled"
            }
        
        logger.info("Starting cinematic analysis")
        start_time = time.time()
        
        # Prepare data for analysis
        scenes_data = [scene.to_dict() for scene in scenes]
        
        # Collect representative keyframes
        keyframes = []
        for scene in scenes:
            # Get middle shot from each scene
            if scene.contained_shots:
                middle_shot_id = scene.contained_shots[len(scene.contained_shots) // 2]
                shot = next((s for s in shots if s.shot_id == middle_shot_id), None)
                if shot and shot.keyframe_path:
                    keyframes.append(shot.keyframe_path)
        
        # Perform analysis
        analysis_result = self.analyzer.analyze_cinematography(scenes_data, keyframes)
        
        # Add metadata
        analysis_result['metadata'] = {
            'total_shots_analyzed': len(shots),
            'total_scenes_analyzed': len(scenes),
            'processing_time': time.time() - start_time
        }
        
        logger.info(f"Cinematic analysis completed in {analysis_result['metadata']['processing_time']:.2f} seconds")
        
        return analysis_result