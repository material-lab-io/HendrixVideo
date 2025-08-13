"""
Data schemas for the video analysis pipeline
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import json
import numpy as np


class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles NumPy types"""
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (np.float32, np.float64)):
            return float(obj)
        if isinstance(obj, (np.int32, np.int64)):
            return int(obj)
        return super().default(obj)


@dataclass
class TranscriptionSegment:
    """Single transcription segment with timing and metadata"""
    segment_id: str
    start_time: float
    end_time: float
    text: str
    confidence: float = 1.0
    language: Optional[str] = None
    emotion: Optional[str] = None
    emotion_confidence: Optional[float] = None
    source: str = "whisper"  # whisper or ocr
    ocr_text: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "segment_id": self.segment_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "text": self.text,
            "confidence": self.confidence,
            "language": self.language,
            "emotion": self.emotion,
            "emotion_confidence": self.emotion_confidence,
            "source": self.source,
            "ocr_text": self.ocr_text
        }


@dataclass
class SchemaA:
    """Schema A: Dialogue Transcription from Whisper/OCR"""
    video_id: str
    duration: float
    segments: List[TranscriptionSegment] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def add_segment(self, segment: TranscriptionSegment):
        """Add a transcription segment"""
        self.segments.append(segment)
    
    def to_dict(self) -> Dict:
        return {
            "video_id": self.video_id,
            "duration": self.duration,
            "segments": [seg.to_dict() for seg in self.segments],
            "metadata": self.metadata,
            "created_at": self.created_at
        }
    
    def save_json(self, filepath: str):
        """Save schema to JSON file"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False, cls=NumpyEncoder)
    
    @classmethod
    def load_json(cls, filepath: str) -> 'SchemaA':
        """Load schema from JSON file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        schema = cls(
            video_id=data['video_id'],
            duration=data['duration'],
            metadata=data.get('metadata', {}),
            created_at=data.get('created_at', datetime.now().isoformat())
        )
        
        for seg_data in data['segments']:
            segment = TranscriptionSegment(**seg_data)
            schema.add_segment(segment)
        
        return schema


# Schema B: Speaker Diarization
@dataclass
class SpeakerSegment:
    """Single speaker segment with timing"""
    segment_id: str
    speaker_id: str  # SPEAKER_00, SPEAKER_01, etc.
    start_time: float
    end_time: float
    confidence: float = 1.0
    
    def to_dict(self) -> Dict:
        return {
            "segment_id": self.segment_id,
            "speaker_id": self.speaker_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "confidence": self.confidence
        }


@dataclass
class SchemaB:
    """Schema B: Speaker Diarization from Pyannote"""
    video_id: str
    duration: float
    num_speakers: int
    segments: List[SpeakerSegment] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def add_segment(self, segment: SpeakerSegment):
        """Add a speaker segment"""
        self.segments.append(segment)
    
    def to_dict(self) -> Dict:
        return {
            "video_id": self.video_id,
            "duration": self.duration,
            "num_speakers": self.num_speakers,
            "segments": [seg.to_dict() for seg in self.segments],
            "metadata": self.metadata,
            "created_at": self.created_at
        }
    
    def save_json(self, filepath: str):
        """Save schema to JSON file"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False, cls=NumpyEncoder)
    
    @classmethod
    def load_json(cls, filepath: str) -> 'SchemaB':
        """Load schema from JSON file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        schema = cls(
            video_id=data['video_id'],
            duration=data['duration'],
            num_speakers=data['num_speakers'],
            metadata=data.get('metadata', {}),
            created_at=data.get('created_at', datetime.now().isoformat())
        )
        
        for seg_data in data['segments']:
            segment = SpeakerSegment(**seg_data)
            schema.add_segment(segment)
        
        return schema
    
    def get_speaker_segments(self, speaker_id: str) -> List[SpeakerSegment]:
        """Get all segments for a specific speaker"""
        return [seg for seg in self.segments if seg.speaker_id == speaker_id]
    
    def get_speaker_stats(self) -> Dict[str, Dict[str, float]]:
        """Get speaking time statistics for each speaker"""
        stats = {}
        for speaker_id in [f"SPEAKER_{i:02d}" for i in range(self.num_speakers)]:
            segments = self.get_speaker_segments(speaker_id)
            if segments:
                total_time = sum(seg.end_time - seg.start_time for seg in segments)
                stats[speaker_id] = {
                    "total_time": total_time,
                    "percentage": (total_time / self.duration) * 100,
                    "num_segments": len(segments)
                }
        return stats


@dataclass
class FaceDetection:
    """Single face detection with bounding box and metadata"""
    detection_id: str
    frame_number: int
    timestamp: float
    bbox: List[float]  # [x1, y1, x2, y2] normalized to [0, 1]
    confidence: float
    character_id: Optional[str] = None  # Will be assigned after clustering
    embedding: Optional[List[float]] = None  # Face embedding vector
    quality_score: Optional[float] = None  # Face quality assessment
    pose: Optional[Dict[str, float]] = None  # Pitch, yaw, roll
    attributes: Optional[Dict[str, Any]] = None  # DeepFace attributes (age, gender, emotion, etc.)
    scene_id: Optional[int] = None  # Scene this detection belongs to
    
    def to_dict(self) -> Dict:
        return {
            "detection_id": self.detection_id,
            "frame_number": self.frame_number,
            "timestamp": self.timestamp,
            "bbox": self.bbox,
            "confidence": self.confidence,
            "character_id": self.character_id,
            "embedding": self.embedding,
            "quality_score": self.quality_score,
            "pose": self.pose,
            "attributes": self.attributes,
            "scene_id": self.scene_id
        }


@dataclass
class CharacterInfo:
    """Information about a detected character"""
    character_id: str
    num_appearances: int
    first_appearance: float
    last_appearance: float
    total_screen_time: float
    average_confidence: float
    representative_embeddings: List[List[float]] = field(default_factory=list)
    appearance_segments: List[Dict[str, float]] = field(default_factory=list)  # [{start, end}]
    attributes: Optional[Dict[str, Any]] = None  # Aggregated attributes from DeepFace
    description: Optional[str] = None  # Human-readable character description
    scene_appearances: Dict[int, int] = field(default_factory=dict)  # scene_id -> appearance count
    scene_embeddings: Dict[int, List[float]] = field(default_factory=dict)  # scene_id -> representative embedding
    cross_scene_similarity: Optional[float] = None  # Average similarity across scenes
    temporal_consistency: Optional[float] = None  # How consistently character appears
    
    def to_dict(self) -> Dict:
        return {
            "character_id": self.character_id,
            "num_appearances": self.num_appearances,
            "first_appearance": self.first_appearance,
            "last_appearance": self.last_appearance,
            "total_screen_time": self.total_screen_time,
            "average_confidence": self.average_confidence,
            "representative_embeddings": self.representative_embeddings,
            "appearance_segments": self.appearance_segments,
            "attributes": self.attributes,
            "description": self.description,
            "scene_appearances": self.scene_appearances,
            "scene_embeddings": self.scene_embeddings,
            "cross_scene_similarity": self.cross_scene_similarity,
            "temporal_consistency": self.temporal_consistency
        }


@dataclass
class SchemaC:
    """Schema C: Character Detection from InsightFace (RetinaFace + ArcFace)"""
    video_id: str
    duration: float
    fps: float
    total_frames: int
    detections: List[FaceDetection] = field(default_factory=list)
    characters: Dict[str, CharacterInfo] = field(default_factory=dict)  # character_id -> info
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def add_detection(self, detection: FaceDetection):
        """Add a face detection"""
        self.detections.append(detection)
    
    def add_character(self, character: CharacterInfo):
        """Add or update character information"""
        self.characters[character.character_id] = character
    
    def get_character_detections(self, character_id: str) -> List[FaceDetection]:
        """Get all detections for a specific character"""
        return [det for det in self.detections if det.character_id == character_id]
    
    def get_detections_at_time(self, timestamp: float, tolerance: float = 0.5) -> List[FaceDetection]:
        """Get detections near a specific timestamp"""
        return [det for det in self.detections 
                if abs(det.timestamp - timestamp) <= tolerance]
    
    def to_dict(self) -> Dict:
        return {
            "video_id": self.video_id,
            "duration": self.duration,
            "fps": self.fps,
            "total_frames": self.total_frames,
            "detections": [det.to_dict() for det in self.detections],
            "characters": {cid: char.to_dict() for cid, char in self.characters.items()},
            "metadata": self.metadata,
            "created_at": self.created_at
        }


@dataclass
class MatchingScore:
    """Detailed scoring for character-dialogue matching"""
    heuristic_scores: Dict[str, float] = field(default_factory=dict)
    llm_score: Optional[float] = None
    final_score: float = 0.0
    confidence_level: str = "low"  # low, medium, high
    reasoning: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "heuristic_scores": self.heuristic_scores,
            "llm_score": self.llm_score,
            "final_score": self.final_score,
            "confidence_level": self.confidence_level,
            "reasoning": self.reasoning
        }


@dataclass
class CharacterDialogueMatch:
    """A matched character-dialogue segment"""
    match_id: str
    character_id: str
    dialogue_segment: TranscriptionSegment  # From Schema A
    speaker_segment: Optional[SpeakerSegment] = None  # From Schema B
    time_overlap: float = 0.0  # Percentage of time overlap
    matching_score: Optional[MatchingScore] = None
    visual_context: Optional[Dict[str, Any]] = None  # Frame info, character position, etc.
    
    def to_dict(self) -> Dict:
        return {
            "match_id": self.match_id,
            "character_id": self.character_id,
            "dialogue": self.dialogue_segment.to_dict(),
            "speaker": self.speaker_segment.to_dict() if self.speaker_segment else None,
            "time_overlap": self.time_overlap,
            "matching_score": self.matching_score.to_dict() if self.matching_score else None,
            "visual_context": self.visual_context
        }


@dataclass
class SchemaD:
    """Schema D: Final Character-Dialogue Matching Results"""
    video_id: str
    duration: float
    matches: List[CharacterDialogueMatch] = field(default_factory=list)
    unmatched_dialogues: List[TranscriptionSegment] = field(default_factory=list)
    matching_summary: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def add_match(self, match: CharacterDialogueMatch):
        """Add a character-dialogue match"""
        self.matches.append(match)
    
    def get_character_dialogues(self, character_id: str) -> List[CharacterDialogueMatch]:
        """Get all dialogues for a specific character"""
        return [m for m in self.matches if m.character_id == character_id]
    
    def get_matches_by_confidence(self, min_confidence: float) -> List[CharacterDialogueMatch]:
        """Get matches above a confidence threshold"""
        return [m for m in self.matches 
                if m.matching_score and m.matching_score.final_score >= min_confidence]
    
    def calculate_summary_stats(self):
        """Calculate matching summary statistics"""
        total_dialogues = len(self.matches) + len(self.unmatched_dialogues)
        matched_dialogues = len(self.matches)
        
        confidence_distribution = {"high": 0, "medium": 0, "low": 0}
        for match in self.matches:
            if match.matching_score:
                confidence_distribution[match.matching_score.confidence_level] += 1
        
        character_dialogue_counts = {}
        for match in self.matches:
            if match.character_id not in character_dialogue_counts:
                character_dialogue_counts[match.character_id] = 0
            character_dialogue_counts[match.character_id] += 1
        
        self.matching_summary = {
            "total_dialogues": total_dialogues,
            "matched_dialogues": matched_dialogues,
            "unmatched_dialogues": len(self.unmatched_dialogues),
            "matching_rate": matched_dialogues / total_dialogues if total_dialogues > 0 else 0,
            "confidence_distribution": confidence_distribution,
            "character_dialogue_counts": character_dialogue_counts,
            "average_confidence": np.mean([m.matching_score.final_score 
                                         for m in self.matches if m.matching_score]) 
                                         if self.matches else 0
        }
    
    def to_dict(self) -> Dict:
        return {
            "video_id": self.video_id,
            "duration": self.duration,
            "matches": [m.to_dict() for m in self.matches],
            "unmatched_dialogues": [d.to_dict() for d in self.unmatched_dialogues],
            "matching_summary": self.matching_summary,
            "metadata": self.metadata,
            "created_at": self.created_at
        }
    
    def save_json(self, filepath: str):
        """Save schema to JSON file"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False, cls=NumpyEncoder)
    
    @classmethod
    def load_json(cls, filepath: str) -> 'SchemaC':
        """Load schema from JSON file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        schema = cls(
            video_id=data['video_id'],
            duration=data['duration'],
            fps=data['fps'],
            total_frames=data['total_frames'],
            metadata=data.get('metadata', {}),
            created_at=data.get('created_at', datetime.now().isoformat())
        )
        
        # Load detections
        for det_data in data.get('detections', []):
            detection = FaceDetection(**det_data)
            schema.add_detection(detection)
        
        # Load characters
        for char_id, char_data in data.get('characters', {}).items():
            character = CharacterInfo(**char_data)
            schema.add_character(character)
        
        return schema


@dataclass
class CharacterDialogue:
    """Single dialogue entry matched to a character"""
    dialogue_id: str
    character_id: str
    character_confidence: float
    transcript_segment_id: str  # Reference to Schema A segment
    text: str
    start_time: float
    end_time: float
    speaker_id: Optional[str] = None  # Reference to Schema B speaker
    emotion: Optional[str] = None
    emotion_confidence: Optional[float] = None
    matching_method: str = "visual"  # visual, speaker, hybrid
    
    def to_dict(self) -> Dict:
        return {
            "dialogue_id": self.dialogue_id,
            "character_id": self.character_id,
            "character_confidence": self.character_confidence,
            "transcript_segment_id": self.transcript_segment_id,
            "speaker_id": self.speaker_id,
            "text": self.text,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "emotion": self.emotion,
            "emotion_confidence": self.emotion_confidence,
            "matching_method": self.matching_method
        }


@dataclass
class Character:
    """Complete character profile with dialogues"""
    character_id: str
    name: Optional[str] = None  # Can be assigned manually
    total_dialogues: int = 0
    total_speaking_time: float = 0.0
    first_appearance: float = 0.0
    last_appearance: float = 0.0
    screen_time: float = 0.0
    emotion_distribution: Dict[str, int] = field(default_factory=dict)
    dialogues: List[str] = field(default_factory=list)  # List of dialogue_ids
    
    def to_dict(self) -> Dict:
        return {
            "character_id": self.character_id,
            "name": self.name,
            "total_dialogues": self.total_dialogues,
            "total_speaking_time": self.total_speaking_time,
            "first_appearance": self.first_appearance,
            "last_appearance": self.last_appearance,
            "screen_time": self.screen_time,
            "emotion_distribution": self.emotion_distribution,
            "dialogues": self.dialogues
        }


# SchemaD is defined above for character-dialogue matching