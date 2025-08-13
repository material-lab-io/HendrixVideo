from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Optional
from datetime import datetime

from .shot import Shot
from .scene import Scene


@dataclass
class VideoMetadata:
    """Metadata about the analyzed video."""
    filename: str
    duration: float  # Total duration in seconds
    fps: float
    width: int
    height: int
    total_frames: int
    format: Optional[str] = None
    codec: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AnalysisResult:
    """Complete analysis result containing all stages of processing."""
    video_metadata: VideoMetadata
    shots: List[Shot]
    scenes: List[Scene]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    processing_time: Optional[float] = None
    cinematic_analysis: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert complete analysis to dictionary representation."""
        return {
            "metadata": self.video_metadata.to_dict(),
            "timestamp": self.timestamp,
            "processing_time": self.processing_time,
            "analysis": {
                "total_shots": len(self.shots),
                "total_scenes": len(self.scenes),
                "shots": [shot.to_dict() for shot in self.shots],
                "scenes": [scene.to_dict() for scene in self.scenes],
                "cinematic_analysis": self.cinematic_analysis
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisResult':
        """Create AnalysisResult from dictionary."""
        video_metadata = VideoMetadata(**data["metadata"])
        shots = [Shot.from_dict(s) for s in data["analysis"]["shots"]]
        scenes = [Scene.from_dict(s) for s in data["analysis"]["scenes"]]
        
        return cls(
            video_metadata=video_metadata,
            shots=shots,
            scenes=scenes,
            timestamp=data.get("timestamp"),
            processing_time=data.get("processing_time"),
            cinematic_analysis=data["analysis"].get("cinematic_analysis")
        )
    
    def get_scene_by_shot(self, shot_id: int) -> Optional[Scene]:
        """Find which scene contains a specific shot."""
        for scene in self.scenes:
            if shot_id in scene.contained_shots:
                return scene
        return None
    
    def get_shots_in_scene(self, scene_id: int) -> List[Shot]:
        """Get all shots belonging to a specific scene."""
        scene = next((s for s in self.scenes if s.scene_id == scene_id), None)
        if scene:
            return [shot for shot in self.shots if shot.shot_id in scene.contained_shots]
        return []