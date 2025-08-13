from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any


@dataclass
class Shot:
    """Represents a single shot in a video."""
    shot_id: int
    start: float  # Start time in seconds
    end: float    # End time in seconds
    duration: Optional[float] = None
    keyframe_path: Optional[str] = None
    confidence: Optional[float] = None
    transition_type: Optional[str] = None  # 'cut', 'dissolve', 'fade', etc.
    
    def __post_init__(self):
        if self.duration is None:
            self.duration = self.end - self.start
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert shot to dictionary representation."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Shot':
        """Create Shot instance from dictionary."""
        return cls(**data)
    
    def __repr__(self) -> str:
        return f"Shot(id={self.shot_id}, start={self.start:.2f}s, end={self.end:.2f}s)"