"""
Production Configuration Templates for Visual Pipeline

This module provides pre-configured settings optimized for different
video content types and production scenarios.
"""

from dataclasses import dataclass, field
from typing import Dict, Any

from src.visual.face_tracker import FaceTrackerConfig
from src.visual.insightface_processor import InsightFaceConfig


@dataclass
class PipelineConfig:
    """Complete pipeline configuration"""
    name: str
    description: str
    face_tracker_config: FaceTrackerConfig
    frame_extraction: Dict[str, Any]
    
    
# Production Configurations

def get_default_config() -> PipelineConfig:
    """Default balanced configuration for general content"""
    
    tracker_config = FaceTrackerConfig(
        insightface_config=InsightFaceConfig(
            model_name='buffalo_s',
            det_thresh=0.5,
            det_size=(640, 640),
            min_face_size=20,
            enable_attributes=True
        ),
        max_age=30,
        min_hits=3,
        iou_threshold=0.3,
        use_embeddings=True,
        embedding_threshold=0.6,
        character_similarity_threshold=0.7,
        min_character_appearances=5
    )
    
    return PipelineConfig(
        name="default",
        description="Balanced configuration for general video content",
        face_tracker_config=tracker_config,
        frame_extraction={
            "mode": "intelligent",
            "target_frames": 500,
            "min_scene_length": 1.0
        }
    )


def get_dialogue_config() -> PipelineConfig:
    """Optimized for dialogue-heavy scenes with stable shots"""
    
    tracker_config = FaceTrackerConfig(
        insightface_config=InsightFaceConfig(
            model_name='buffalo_s',
            det_thresh=0.4,  # Lower threshold for better detection
            det_size=(640, 640),
            min_face_size=20,  # Less padding needed
            enable_attributes=True
        ),
        max_age=60,  # Keep tracks longer
        min_hits=5,  # More confirmations
        iou_threshold=0.4,
        use_embeddings=True,
        embedding_threshold=0.7,  # Stricter matching
        character_similarity_threshold=0.75,
        min_character_appearances=10  # Higher threshold
    )
    
    return PipelineConfig(
        name="dialogue",
        description="Optimized for dialogue scenes with stable camera work",
        face_tracker_config=tracker_config,
        frame_extraction={
            "mode": "scene",
            "target_frames": 300,
            "min_scene_length": 2.0,
            "sample_rate": 3  # Every 3rd frame in scenes
        }
    )


def get_action_config() -> PipelineConfig:
    """Optimized for action scenes with fast motion"""
    
    tracker_config = FaceTrackerConfig(
        insightface_config=InsightFaceConfig(
            model_name='buffalo_s',
            det_thresh=0.5,
            det_size=(640, 640),
            min_face_size=15,  # More padding for motion
            enable_attributes=False  # Skip for speed
        ),
        max_age=15,  # Shorter tracking window
        min_hits=2,  # Quick confirmation
        iou_threshold=0.2,  # Looser spatial matching
        use_embeddings=True,
        embedding_threshold=0.5,  # More flexible
        character_similarity_threshold=0.65,
        min_character_appearances=3  # Lower threshold
    )
    
    return PipelineConfig(
        name="action",
        description="Optimized for action scenes with quick cuts and motion",
        face_tracker_config=tracker_config,
        frame_extraction={
            "mode": "uniform",
            "target_frames": 800,
            "sample_rate": 1  # Every frame in sampled set
        }
    )


def get_dark_scenes_config() -> PipelineConfig:
    """Optimized for dark or artistically lit content"""
    
    tracker_config = FaceTrackerConfig(
        insightface_config=InsightFaceConfig(
            model_name='buffalo_s',
            det_thresh=0.3,  # Much lower threshold
            det_size=(640, 640),
            min_face_size=15,  # Larger search area
            enable_attributes=True
        ),
        max_age=45,
        min_hits=2,
        iou_threshold=0.25,
        use_embeddings=True,
        embedding_threshold=0.55,
        character_similarity_threshold=0.65,
        min_character_appearances=4
    )
    
    return PipelineConfig(
        name="dark_scenes",
        description="Optimized for poorly lit or artistic cinematography",
        face_tracker_config=tracker_config,
        frame_extraction={
            "mode": "intelligent",
            "target_frames": 600,
            "brightness_threshold": 0.2,
            "contrast_enhancement": True
        }
    )


def get_crowd_scenes_config() -> PipelineConfig:
    """Optimized for scenes with multiple people"""
    
    tracker_config = FaceTrackerConfig(
        insightface_config=InsightFaceConfig(
            model_name='buffalo_s',
            det_thresh=0.6,  # Higher to reduce false positives
            det_size=(960, 960),  # Larger detection size
            min_face_size=20,
            enable_attributes=False
        ),
        max_age=20,
        min_hits=4,
        iou_threshold=0.35,
        use_embeddings=True,
        embedding_threshold=0.7,  # Stricter to avoid mixing
        character_similarity_threshold=0.8,  # Very strict
        min_character_appearances=8
    )
    
    return PipelineConfig(
        name="crowd_scenes",
        description="Optimized for scenes with multiple characters",
        face_tracker_config=tracker_config,
        frame_extraction={
            "mode": "uniform",
            "target_frames": 400,
            "max_faces_per_frame": 10
        }
    )


def get_surveillance_config() -> PipelineConfig:
    """Optimized for surveillance or security footage"""
    
    tracker_config = FaceTrackerConfig(
        insightface_config=InsightFaceConfig(
            model_name='buffalo_s',
            det_thresh=0.4,
            det_size=(480, 480),  # Smaller for speed
            min_face_size=20,
            enable_attributes=True
        ),
        max_age=120,  # Very long tracking
        min_hits=3,
        iou_threshold=0.3,
        use_embeddings=True,
        embedding_threshold=0.65,
        character_similarity_threshold=0.7,
        min_character_appearances=15  # Many appearances expected
    )
    
    return PipelineConfig(
        name="surveillance",
        description="Optimized for continuous surveillance footage",
        face_tracker_config=tracker_config,
        frame_extraction={
            "mode": "uniform",
            "target_frames": 1000,
            "sample_rate": 5  # Every 5th frame
        }
    )


# Configuration registry
CONFIGS = {
    "default": get_default_config,
    "dialogue": get_dialogue_config,
    "action": get_action_config,
    "dark_scenes": get_dark_scenes_config,
    "crowd_scenes": get_crowd_scenes_config,
    "surveillance": get_surveillance_config
}


def get_config(name: str = "default") -> PipelineConfig:
    """Get a configuration by name
    
    Args:
        name: Configuration name (default, dialogue, action, etc.)
        
    Returns:
        PipelineConfig instance
        
    Raises:
        ValueError: If configuration name not found
    """
    if name not in CONFIGS:
        available = ", ".join(CONFIGS.keys())
        raise ValueError(f"Unknown config '{name}'. Available: {available}")
    
    return CONFIGS[name]()


def list_configs() -> Dict[str, str]:
    """List all available configurations
    
    Returns:
        Dictionary of config_name -> description
    """
    return {
        name: func().description 
        for name, func in CONFIGS.items()
    }


# Adaptive configuration based on video analysis
def suggest_config(video_properties: Dict[str, Any]) -> str:
    """Suggest best configuration based on video properties
    
    Args:
        video_properties: Dict containing:
            - avg_brightness: float (0-1)
            - motion_score: float (0-1)
            - scene_changes_per_minute: float
            - detected_faces_sample: int
            - duration: float (seconds)
            
    Returns:
        Suggested configuration name
    """
    brightness = video_properties.get("avg_brightness", 0.5)
    motion = video_properties.get("motion_score", 0.5)
    scene_changes = video_properties.get("scene_changes_per_minute", 10)
    
    # Decision logic
    if brightness < 0.3:
        return "dark_scenes"
    elif motion > 0.7 or scene_changes > 30:
        return "action"
    elif scene_changes < 5:
        return "dialogue"
    elif video_properties.get("detected_faces_sample", 0) > 5:
        return "crowd_scenes"
    else:
        return "default"


# Production presets for specific use cases
class ProductionPresets:
    """Pre-configured settings for common production scenarios"""
    
    @staticmethod
    def netflix_series() -> PipelineConfig:
        """Configuration for Netflix-style TV series"""
        config = get_dialogue_config()
        config.name = "netflix_series"
        config.description = "Optimized for high-quality TV series content"
        config.face_tracker_config.min_character_appearances = 8
        return config
    
    @staticmethod
    def youtube_content() -> PipelineConfig:
        """Configuration for YouTube videos"""
        config = get_default_config()
        config.name = "youtube"
        config.description = "Balanced settings for varied YouTube content"
        config.frame_extraction["target_frames"] = 300
        return config
    
    @staticmethod
    def movie_trailer() -> PipelineConfig:
        """Configuration for movie trailers"""
        config = get_action_config()
        config.name = "movie_trailer"
        config.description = "Fast processing for trailer analysis"
        config.frame_extraction["target_frames"] = 200
        return config


if __name__ == "__main__":
    # Example usage
    print("Available configurations:")
    for name, desc in list_configs().items():
        print(f"  {name}: {desc}")
    
    # Get specific config
    config = get_config("dialogue")
    print(f"\nDialogue config: {config.face_tracker_config.min_character_appearances} min appearances")