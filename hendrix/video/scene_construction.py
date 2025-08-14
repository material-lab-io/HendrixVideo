"""Sophisticated scene construction from detected shots with LLaVA integration."""

import logging
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

from hendrix.core.config import ConfigManager
from hendrix.core.exceptions import VideoProcessingError
from hendrix.captioning.models.model_factory import ModelFactory

logger = logging.getLogger(__name__)

# Prompt templates
SHOT_DESCRIPTION_PROMPT = """Describe this video frame in one sentence, including the action, setting, and mood."""

SCENE_CONSTRUCTION_PROMPT = """You are an expert film editor. I will provide you with a sequence of numbered keyframes from a video. Your task is to group these shots into coherent scenes. A scene is a continuous block of action that occurs in the same location at the same time. For each scene you identify, provide a concise one-sentence summary of the action, setting, and mood. Your output should be a JSON array with the following format:
[
  {
    "scene_id": 1,
    "summary": "A person walks through a bright hallway with a neutral mood",
    "contained_shots": [1, 2, 3],
    "setting": "hallway",
    "mood": "neutral"
  }
]

Here are the keyframes from shots {shot_range}:"""


class Shot:
    """Shot data structure compatible with legacy format"""
    def __init__(self, shot_dict: Dict[str, Any]):
        self.shot_id = shot_dict.get("shot_id", shot_dict.get("id", 0))
        self.start = shot_dict.get("start", shot_dict.get("start_time", 0.0))
        self.end = shot_dict.get("end", shot_dict.get("end_time", 0.0))
        self.duration = self.end - self.start
        self.keyframe_path = shot_dict.get("keyframe_path")
        self.confidence = shot_dict.get("confidence", 1.0)
        self.transition_type = shot_dict.get("transition_type")


class Scene:
    """Scene data structure"""
    def __init__(self, scene_id: int, summary: str, contained_shots: List[int], 
                 setting: str = None, mood: str = None, start_time: float = None, end_time: float = None):
        self.scene_id = scene_id
        self.summary = summary
        self.contained_shots = contained_shots
        self.setting = setting
        self.mood = mood
        self.start_time = start_time
        self.end_time = end_time
        self.duration = (end_time - start_time) if start_time is not None and end_time is not None else None
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.scene_id,
            "summary": self.summary,
            "contained_shots": self.contained_shots,
            "setting": self.setting,
            "mood": self.mood,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration if self.duration is not None else (self.end_time - self.start_time if self.start_time is not None and self.end_time is not None else 0),
            "shot_count": len(self.contained_shots),
            "description": f"Scene {self.scene_id}: {self.summary}",
            "confidence": 0.9
        }


class SceneConstructor:
    """Sophisticated scene construction using LLaVA for visual analysis"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.scene_config = config.get("scene_construction", {})
        self.max_frames_per_batch = self.scene_config.get('max_frames_per_batch', 10)
        self.individual_mode = self.scene_config.get('individual_mode', False)
        
        # Initialize model if available
        self.model = None
        try:
            # Check if scene construction should use LLaVA
            use_llava = self.scene_config.get('use_llava', False)
            if use_llava and config.get("captioning", {}).get("enabled", False):
                self.model_factory = ModelFactory(config)
                llava_model_name = self.scene_config.get('llava_model', 'llava_7b')
                self.model = self.model_factory.get_model(llava_model_name)
                logger.info(f"LLaVA model '{llava_model_name}' loaded for scene construction")
        except Exception as e:
            logger.warning(f"Could not load LLaVA model for scene construction: {e}")
            logger.info("Falling back to basic scene construction")
    
    def construct(self, video_path: Path, output_dir: Path, shots_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Construct scenes from detected shots using sophisticated algorithm
        
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
                    shots_json = json.load(f).get("shots", [])
            else:
                shots_json = []
            
            # Convert to Shot objects
            shots = [Shot(shot_dict) for shot_dict in shots_json]
            logger.info(f"Starting sophisticated scene construction for {len(shots)} shots")
            
            # Process shots with LLaVA if available, otherwise use basic grouping
            if self.model:
                scenes = self._process_shots_with_llava(shots)
            else:
                scenes = self._basic_scene_construction(shots)
            
            # Convert Scene objects to dictionaries
            scenes_dicts = [scene.to_dict() for scene in scenes]
            
            # Save results
            scenes_file = output_dir / "scenes.json"
            with open(scenes_file, 'w') as f:
                json.dump({"scenes": scenes_dicts}, f, indent=2)
            
            logger.info(f"Constructed {len(scenes)} scenes from {len(shots)} shots")
            return scenes_dicts
            
        except Exception as e:
            raise VideoProcessingError(f"Scene construction failed: {e}")
    
    def _process_shots_with_llava(self, shots: List[Shot]) -> List[Scene]:
        """Process shots using LLaVA for intelligent scene construction"""
        logger.info(f"Processing mode: {'Individual' if self.individual_mode else 'Batch'}")
        start_time = time.time()
        
        if self.individual_mode:
            scenes = self._process_shots_individually(shots)
        else:
            scenes = self._process_shots_in_batches(shots)
        
        # Post-process scenes to ensure consistency
        scenes = self._post_process_scenes(scenes, shots)
        
        processing_time = time.time() - start_time
        logger.info(f"Scene construction completed in {processing_time:.2f} seconds")
        logger.info(f"Constructed {len(scenes)} scenes from {len(shots)} shots")
        
        return scenes
    
    def _process_shots_individually(self, shots: List[Shot]) -> List[Scene]:
        """Process each shot individually to get detailed descriptions"""
        logger.info("Processing shots individually for detailed descriptions")
        scenes = []
        
        for i, shot in enumerate(shots):
            logger.info(f"Processing shot {shot.shot_id} ({i+1}/{len(shots)})")
            logger.info(f"Shot timing: {shot.start:.2f}s - {shot.end:.2f}s (duration: {shot.duration:.2f}s)")
            
            if not shot.keyframe_path or not Path(shot.keyframe_path).exists():
                logger.warning(f"No keyframe found for shot {shot.shot_id}")
                # Create fallback scene
                scene = Scene(
                    scene_id=shot.shot_id,
                    summary=f"Shot {shot.shot_id} - keyframe missing",
                    contained_shots=[shot.shot_id],
                    setting="Unknown",
                    mood="Unknown",
                    start_time=shot.start,
                    end_time=shot.end
                )
                scenes.append(scene)
                continue
            
            try:
                # Analyze the shot's keyframe
                logger.info(f"Analyzing keyframe: {shot.keyframe_path}")
                description = self.model.generate_caption_from_image(
                    shot.keyframe_path,
                    SHOT_DESCRIPTION_PROMPT
                )
                
                logger.info(f"LLaVA Response for shot {shot.shot_id}: {description}")
                
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
                # Create fallback scene
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
        
        return scenes
    
    def _process_shots_in_batches(self, shots: List[Shot]) -> List[Scene]:
        """Process shots in batches for efficiency"""
        # Verify keyframes exist
        missing_keyframes = [s for s in shots if not s.keyframe_path or not Path(s.keyframe_path).exists()]
        if missing_keyframes:
            logger.warning(f"{len(missing_keyframes)} shots missing keyframes")
        
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
                try:
                    # Analyze batch with LLaVA
                    batch_scenes = self._analyze_shot_sequence(keyframe_paths, shot_ids)
                    
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
                        
                except Exception as e:
                    logger.error(f"Error processing batch {batch_start}-{batch_end}: {e}")
                    # Fall back to basic grouping for this batch
                    fallback_scenes = self._basic_batch_grouping(batch_shots, len(scenes))
                    scenes.extend(fallback_scenes)
            
            batch_start = batch_end
        
        return scenes
    
    def _analyze_shot_sequence(self, keyframe_paths: List[str], shot_ids: List[int]) -> List[Dict[str, Any]]:
        """Analyze a sequence of keyframes and group into scenes"""
        # Create formatted prompt
        shot_range = f"{shot_ids[0]}-{shot_ids[-1]}" if len(shot_ids) > 1 else str(shot_ids[0])
        prompt = SCENE_CONSTRUCTION_PROMPT.format(shot_range=shot_range)
        
        # For now, use the first keyframe as representative
        # In a full implementation, this would analyze multiple images
        result = self.model.generate_caption_from_image(keyframe_paths[0], prompt)
        
        # Parse JSON result or create fallback
        try:
            import json
            scenes = json.loads(result)
            if not isinstance(scenes, list):
                raise ValueError("Expected list of scenes")
            return scenes
        except Exception as e:
            logger.warning(f"Could not parse LLaVA scene construction result: {e}")
            # Create single scene as fallback
            return [{
                "scene_id": 1,
                "summary": f"Scene containing shots {shot_range}",
                "contained_shots": shot_ids,
                "setting": "Unknown",
                "mood": "Unknown"
            }]
    
    def _basic_scene_construction(self, shots: List[Shot]) -> List[Scene]:
        """Fallback to basic scene construction when LLaVA is not available"""
        logger.info("Using basic scene construction (no LLaVA)")
        
        if not shots:
            return []
        
        scenes = []
        current_scene_shots = []
        
        # Simple grouping: combine 2-3 consecutive shots per scene
        shots_per_scene = self.scene_config.get('shots_per_scene', 2)
        
        for i, shot in enumerate(shots):
            current_scene_shots.append(shot)
            
            # Create scene when we have enough shots or reached the end
            if len(current_scene_shots) >= shots_per_scene or i == len(shots) - 1:
                scene = Scene(
                    scene_id=len(scenes) + 1,
                    summary=f"Scene {len(scenes) + 1} containing {len(current_scene_shots)} shots",
                    contained_shots=[s.shot_id for s in current_scene_shots],
                    setting="Basic grouping",
                    mood="Unknown",
                    start_time=current_scene_shots[0].start,
                    end_time=current_scene_shots[-1].end
                )
                scenes.append(scene)
                current_scene_shots = []
        
        return scenes
    
    def _basic_batch_grouping(self, shots: List[Shot], scene_offset: int) -> List[Scene]:
        """Create basic scenes from a batch of shots"""
        scenes = []
        
        # Group all shots in batch into a single scene
        if shots:
            scene = Scene(
                scene_id=scene_offset + 1,
                summary=f"Batch scene containing {len(shots)} shots",
                contained_shots=[s.shot_id for s in shots],
                setting="Batch processing",
                mood="Unknown",
                start_time=shots[0].start,
                end_time=shots[-1].end
            )
            scenes.append(scene)
        
        return scenes
    
    def _post_process_scenes(self, scenes: List[Scene], shots: List[Shot]) -> List[Scene]:
        """Post-process scenes to ensure consistency and completeness"""
        logger.info("Post-processing scenes for completeness")
        
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
            misc_scene_shots = [s for s in shots if s.shot_id in misc_shots]
            
            misc_scene = Scene(
                scene_id=len(scenes) + 1,
                summary="Miscellaneous unassigned shots",
                contained_shots=misc_shots,
                setting="Various",
                mood="Mixed",
                start_time=misc_scene_shots[0].start if misc_scene_shots else 0,
                end_time=misc_scene_shots[-1].end if misc_scene_shots else 0
            )
            scenes.append(misc_scene)
        
        # Sort scenes by start time
        scenes.sort(key=lambda s: s.start_time or 0)
        
        # Renumber scene IDs sequentially
        for i, scene in enumerate(scenes):
            scene.scene_id = i + 1
        
        logger.info(f"Post-processing complete: {len(scenes)} scenes, all {len(all_shot_ids)} shots assigned")
        return scenes
    
    def refine_scene(self, scene: Scene, shots: List[Shot], custom_prompt: Optional[str] = None) -> Scene:
        """
        Refine a single scene with additional LLaVA analysis
        
        Args:
            scene: Scene to refine
            shots: All shots in the video
            custom_prompt: Optional custom prompt for refinement
            
        Returns:
            Refined Scene object
        """
        if not self.model:
            logger.warning("Cannot refine scene - LLaVA model not available")
            return scene
            
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
        
        try:
            # Analyze with LLaVA using middle keyframe
            refined_summary = self.model.generate_caption_from_image(
                keyframe_paths[len(keyframe_paths) // 2],  # Use middle keyframe
                custom_prompt
            )
            
            # Update scene with refined information
            if refined_summary and refined_summary.strip():
                scene.summary = refined_summary
                logger.info(f"Refined scene {scene.scene_id}: {refined_summary[:100]}...")
            
        except Exception as e:
            logger.error(f"Error refining scene {scene.scene_id}: {e}")
        
        return scene