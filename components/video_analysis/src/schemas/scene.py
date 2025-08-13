from dataclasses import dataclass, asdict, field
from typing import List, Optional, Dict, Any


@dataclass
class Scene:
    """Represents a semantic scene composed of multiple shots."""
    scene_id: int
    summary: str
    contained_shots: List[int]
    setting: Optional[str] = None
    mood: Optional[str] = None
    characters: List[str] = field(default_factory=list)
    key_actions: List[str] = field(default_factory=list)
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    duration: Optional[float] = None
    
    def __post_init__(self):
        if self.start_time is not None and self.end_time is not None and self.duration is None:
            self.duration = self.end_time - self.start_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert scene to dictionary representation."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Scene':
        """Create Scene instance from dictionary."""
        return cls(**data)
    
    def add_shot(self, shot_id: int) -> None:
        """Add a shot to this scene."""
        if shot_id not in self.contained_shots:
            self.contained_shots.append(shot_id)
    
    def __repr__(self) -> str:
        return f"Scene(id={self.scene_id}, shots={len(self.contained_shots)}, summary='{self.summary[:50]}...')"