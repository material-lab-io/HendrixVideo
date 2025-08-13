"""
Data schemas for the video analysis pipeline
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import json


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
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
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
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
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
class SchemaC:
    """Schema C: Character Detection"""
    pass


@dataclass
class SchemaD:
    """Schema D: Matched Character-Dialogue"""
    pass