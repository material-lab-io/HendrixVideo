import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import time

from models.llava import LLaVAAnalyzer
from schemas.shot import Shot
from schemas.scene import Scene
from utils.prompt_templates import SCENE_CONSTRUCTION_PROMPT, SHOT_DESCRIPTION_PROMPT

logger = logging.getLogger(__name__)


class SceneConstructionPipeline:
    """Stage 2: Semantic Scene Construction & Narrative Generation using LLaVA."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.scene_config = config.get('scene_construction', {})
        self.output_config = config.get('output', {})
        self.analyzer = LLaVAAnalyzer(self.scene_config)
        self.max_frames_per_batch = self.scene_config.get('max_frames_per_batch', 10)
    
    def process_shots(self, shots: List[Shot], save_intermediate: bool = True, individual_mode: bool = True) -> List[Scene]:
        """
        Process shots to construct semantic scenes.
        
        Args:
            shots: List of Shot objects from Stage 1
            save_intermediate: Whether to save intermediate results
            individual_mode: Whether to process each shot individually
            
        Returns:
            List of Scene objects
        """
        logger.info(f"Starting scene construction for {len(shots)} shots")
        logger.info(f"Processing mode: {'Individual' if individual_mode else 'Batch'}")
        start_time = time.time()
        
        if individual_mode:
            return self._process_shots_individually(shots, save_intermediate)
        
        # Verify keyframes exist
        missing_keyframes = [s for s in shots if not s.keyframe_path or not Path(s.keyframe_path).exists()]
        if missing_keyframes:
            logger.warning(f"{len(missing_keyframes)} shots missing keyframes")
        
        # Process shots in batches
        scenes = []
        batch_start = 0
        
        while batch_start < len(shots):
            batch_end = min(batch_start + self.max_frames_per_batch, len(shots))
            batch_shots = shots[batch_start:batch_end]
            
            logger.info(f"Processing batch: shots {batch_start + 1} to {batch_end}")
            
            # Extract keyframe paths and shot IDs
            keyframe_paths = []
            shot_ids = []
            
            for shot in batch_shots:
                if shot.keyframe_path and Path(shot.keyframe_path).exists():
                    keyframe_paths.append(shot.keyframe_path)
                    shot_ids.append(shot.shot_id)
            
            if keyframe_paths:
                # Analyze batch with LLaVA
                batch_scenes = self.analyzer.analyze_shot_sequence(
                    keyframe_paths,
                    shot_ids,
                    SCENE_CONSTRUCTION_PROMPT
                )
                
                # Convert to Scene objects and adjust IDs
                for scene_dict in batch_scenes:
                    # Adjust scene ID to be globally unique
                    scene_dict['scene_id'] = len(scenes) + 1
                    
                    # Calculate temporal information
                    contained_shot_ids = scene_dict['contained_shots']
                    contained_shots = [s for s in shots if s.shot_id in contained_shot_ids]
                    
                    if contained_shots:
                        start_time = contained_shots[0].start
                        end_time = contained_shots[-1].end
                    else:
                        start_time = end_time = 0.0
                    
                    # Create Scene object
                    scene = Scene(
                        scene_id=scene_dict['scene_id'],
                        summary=scene_dict['summary'],
                        contained_shots=scene_dict['contained_shots'],
                        setting=scene_dict.get('setting'),
                        mood=scene_dict.get('mood'),
                        start_time=start_time,
                        end_time=end_time
                    )
                    
                    scenes.append(scene)
            
            batch_start = batch_end
        
        # Post-process scenes
        scenes = self._post_process_scenes(scenes, shots)
        
        processing_time = time.time() - start_time
        logger.info(f"Scene construction completed in {processing_time:.2f} seconds")
        logger.info(f"Constructed {len(scenes)} scenes from {len(shots)} shots")
        
        # Save intermediate results if requested
        if save_intermediate:
            self._save_scenes(scenes)
        
        return scenes
    
    def _post_process_scenes(self, scenes: List[Scene], shots: List[Shot]) -> List[Scene]:
        """Post-process scenes to ensure consistency and completeness."""
        # Ensure all shots are assigned to a scene
        all_shot_ids = {shot.shot_id for shot in shots}
        assigned_shot_ids = set()
        
        for scene in scenes:
            assigned_shot_ids.update(scene.contained_shots)
        
        unassigned_shot_ids = all_shot_ids - assigned_shot_ids
        
        if unassigned_shot_ids:
            logger.warning(f"{len(unassigned_shot_ids)} shots not assigned to any scene")
            
            # Create a miscellaneous scene for unassigned shots
            misc_shots = sorted(list(unassigned_shot_ids))
            misc_scene = Scene(
                scene_id=len(scenes) + 1,
                summary="Miscellaneous shots",
                contained_shots=misc_shots,
                setting="Various",
                mood="Mixed"
            )
            
            # Calculate temporal information
            contained_shots = [s for s in shots if s.shot_id in misc_shots]
            if contained_shots:
                misc_scene.start_time = contained_shots[0].start
                misc_scene.end_time = contained_shots[-1].end
            
            scenes.append(misc_scene)
        
        # Sort scenes by start time
        scenes.sort(key=lambda s: s.start_time or 0)
        
        # Renumber scene IDs sequentially
        for i, scene in enumerate(scenes):
            scene.scene_id = i + 1
        
        return scenes
    
    def _save_scenes(self, scenes: List[Scene]) -> None:
        """Save scene construction results to file."""
        output_file = Path(self.output_config.get('scenes_file', 'scenes.json'))
        
        try:
            scenes_data = {
                'total_scenes': len(scenes),
                'scenes': [scene.to_dict() for scene in scenes]
            }
            
            with open(output_file, 'w') as f:
                json.dump(scenes_data, f, indent=2)
            
            logger.info(f"Saved scene construction results to: {output_file}")
            
        except Exception as e:
            logger.error(f"Failed to save scene construction results: {e}")
    
    def load_scenes(self, scenes_file: str) -> List[Scene]:
        """Load previously saved scene construction results."""
        try:
            with open(scenes_file, 'r') as f:
                data = json.load(f)
            
            scenes = [Scene.from_dict(scene_dict) for scene_dict in data['scenes']]
            logger.info(f"Loaded {len(scenes)} scenes from: {scenes_file}")
            
            return scenes
            
        except Exception as e:
            logger.error(f"Failed to load scenes from file: {e}")
            raise
    
    def refine_scene(self, scene: Scene, shots: List[Shot], 
                    custom_prompt: Optional[str] = None) -> Scene:
        """
        Refine a single scene with additional analysis.
        
        Args:
            scene: Scene to refine
            shots: All shots in the video
            custom_prompt: Optional custom prompt for refinement
            
        Returns:
            Refined Scene object
        """
        # Get shots in this scene
        scene_shots = [s for s in shots if s.shot_id in scene.contained_shots]
        
        if not scene_shots:
            logger.warning(f"No shots found for scene {scene.scene_id}")
            return scene
        
        # Get keyframe paths
        keyframe_paths = [s.keyframe_path for s in scene_shots 
                         if s.keyframe_path and Path(s.keyframe_path).exists()]
        
        if not keyframe_paths:
            logger.warning(f"No keyframes found for scene {scene.scene_id}")
            return scene
        
        # Use custom prompt or default refinement prompt
        if not custom_prompt:
            custom_prompt = f"Analyze these frames from scene {scene.scene_id} and provide a more detailed description including characters, actions, and cinematographic elements."
        
        # Analyze with LLaVA
        refined_summary = self.analyzer.analyze_single_image(
            keyframe_paths[len(keyframe_paths) // 2],  # Use middle keyframe
            custom_prompt
        )
        
        # Update scene with refined information
        if refined_summary and refined_summary != "Model not loaded - demo mode":
            scene.summary = refined_summary
        
        return scene
    
    def _process_shots_individually(self, shots: List[Shot], save_intermediate: bool = True) -> List[Scene]:
        """Process each shot individually to get detailed descriptions."""
        logger.info("Processing shots individually for detailed descriptions")
        start_time = time.time()
        
        scenes = []
        
        for i, shot in enumerate(shots):
            logger.info("="*60)
            logger.info(f"Processing shot {shot.shot_id} ({i+1}/{len(shots)})")
            logger.info(f"Shot timing: {shot.start:.2f}s - {shot.end:.2f}s (duration: {shot.duration:.2f}s)")
            
            if not shot.keyframe_path or not Path(shot.keyframe_path).exists():
                logger.warning(f"No keyframe found for shot {shot.shot_id}")
                continue
            
            # Analyze the shot's keyframe
            logger.info(f"Analyzing keyframe: {shot.keyframe_path}")
            
            try:
                # Get description for this single shot
                description = self.analyzer.analyze_single_image(
                    shot.keyframe_path,
                    SHOT_DESCRIPTION_PROMPT
                )
                
                logger.info(f"LLaVA Response for shot {shot.shot_id}:")
                logger.info("-" * 40)
                logger.info(description)
                logger.info("-" * 40)
                
                # Create a scene for this single shot
                scene = Scene(
                    scene_id=shot.shot_id,
                    summary=description if description else f"Shot {shot.shot_id}",
                    contained_shots=[shot.shot_id],
                    setting="From frame analysis",
                    mood="From frame analysis",
                    start_time=shot.start,
                    end_time=shot.end
                )
                
                scenes.append(scene)
                
            except Exception as e:
                logger.error(f"Error processing shot {shot.shot_id}: {e}")
                # Create a fallback scene
                scene = Scene(
                    scene_id=shot.shot_id,
                    summary=f"Error processing shot {shot.shot_id}",
                    contained_shots=[shot.shot_id],
                    setting="Unknown",
                    mood="Unknown",
                    start_time=shot.start,
                    end_time=shot.end
                )
                scenes.append(scene)
        
        processing_time = time.time() - start_time
        logger.info("="*60)
        logger.info(f"Individual shot processing completed in {processing_time:.2f} seconds")
        logger.info(f"Processed {len(scenes)} shots into {len(scenes)} scenes")
        
        # Save intermediate results if requested
        if save_intermediate:
            self._save_scenes(scenes)
        
        return scenes