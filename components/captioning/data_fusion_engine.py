"""
Data Fusion Engine for Comprehensive Captioning

This module aggregates data from both audio_analysis and Hendrix_Video_Analysis
pipelines to create rich context packets for each scene.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class DialogueEntry:
    """Represents a single dialogue entry with speaker and metadata"""
    speaker: str
    character_id: str
    text: str
    start_time: float
    end_time: float
    emotion: Optional[str] = None
    emotion_confidence: Optional[float] = None
    confidence: Optional[float] = None


@dataclass
class SceneContextPacket:
    """
    Contains all relevant data for a single scene to be captioned
    """
    scene_id: int
    start_time: float
    end_time: float
    visual_description: str
    characters_present: List[str] = field(default_factory=list)
    dialogue_transcript: List[DialogueEntry] = field(default_factory=list)
    prior_scene_summary: str = ""
    
    # Additional metadata
    shot_ids: List[int] = field(default_factory=list)
    mood: Optional[str] = None
    setting: Optional[str] = None
    key_actions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "scene_id": self.scene_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "visual_description": self.visual_description,
            "characters_present": self.characters_present,
            "dialogue_transcript": [
                {
                    "speaker": d.speaker,
                    "character_id": d.character_id,
                    "text": d.text,
                    "start_time": d.start_time,
                    "end_time": d.end_time,
                    "emotion": d.emotion,
                    "emotion_confidence": d.emotion_confidence,
                    "confidence": d.confidence
                }
                for d in self.dialogue_transcript
            ],
            "prior_scene_summary": self.prior_scene_summary,
            "shot_ids": self.shot_ids,
            "mood": self.mood,
            "setting": self.setting,
            "key_actions": self.key_actions
        }


class DataFusionEngine:
    """
    Fuses data from audio_analysis and scene analysis pipelines
    """
    
    def __init__(self, 
                 audio_analysis_path: str,
                 scene_analysis_path: str,
                 include_emotions: bool = True,
                 min_dialogue_confidence: float = 0.5):
        """
        Initialize the data fusion engine
        
        Args:
            audio_analysis_path: Path to audio_analysis output directory
            scene_analysis_path: Path to scenes.json from Hendrix_Video_Analysis
            include_emotions: Whether to include emotion data in dialogue
            min_dialogue_confidence: Minimum confidence threshold for dialogue
        """
        self.audio_analysis_path = Path(audio_analysis_path)
        self.scene_analysis_path = Path(scene_analysis_path)
        self.include_emotions = include_emotions
        self.min_dialogue_confidence = min_dialogue_confidence
        
        # Data containers
        self.schema_a_data = None  # Transcriptions
        self.schema_b_data = None  # Speaker diarization
        self.schema_c_data = None  # Character detections
        self.schema_d_data = None  # Character-dialogue matches
        self.scene_data = None     # Scene boundaries and descriptions
        
        # Character ID to name mapping
        self.character_names = {}
        
    def load_audio_analysis_data(self) -> None:
        """Load all schemas from audio_analysis output"""
        logger.info(f"Loading audio analysis data from {self.audio_analysis_path}")
        
        # Find the session directory
        if self.audio_analysis_path.name.startswith("session_"):
            session_dir = self.audio_analysis_path
        else:
            # Find the most recent session
            sessions = sorted(self.audio_analysis_path.glob("session_*"))
            if not sessions:
                raise FileNotFoundError(f"No session directories found in {self.audio_analysis_path}")
            session_dir = sessions[-1]
            
        logger.info(f"Using session: {session_dir.name}")
        
        # Load Schema A (transcriptions)
        schema_a_path = list(session_dir.glob("audio_output/*/schemas/schema_a_transcription.json"))
        if schema_a_path:
            with open(schema_a_path[0], 'r', encoding='utf-8') as f:
                self.schema_a_data = json.load(f)
            logger.info(f"Loaded Schema A with {len(self.schema_a_data.get('segments', []))} segments")
        
        # Load Schema B (speaker diarization)
        schema_b_path = list(session_dir.glob("audio_output/*/schemas/schema_b_speakers.json"))
        if schema_b_path:
            with open(schema_b_path[0], 'r', encoding='utf-8') as f:
                self.schema_b_data = json.load(f)
            logger.info(f"Loaded Schema B with {len(self.schema_b_data.get('segments', []))} speaker segments")
        
        # Load Schema C (character detections)
        schema_c_path = session_dir / "visual_output" / "character_data_schemaC.json"
        if schema_c_path.exists():
            with open(schema_c_path, 'r', encoding='utf-8') as f:
                self.schema_c_data = json.load(f)
            logger.info(f"Loaded Schema C with {len(self.schema_c_data.get('characters', {}))} characters")
            
            # Build character name mapping
            characters = self.schema_c_data.get('characters', {})
            if isinstance(characters, dict):
                # Handle dictionary format
                for char_id, char_data in characters.items():
                    self.character_names[char_id] = f"Character_{char_id}"
            else:
                # Handle list format
                for char in characters:
                    char_id = char.get('character_id', '')
                    self.character_names[char_id] = f"Character_{char_id}"
        
        # Load Schema D (character-dialogue matches)
        schema_d_path = session_dir / "fusion_output" / "schema_d_matches.json"
        if schema_d_path.exists():
            with open(schema_d_path, 'r', encoding='utf-8') as f:
                self.schema_d_data = json.load(f)
            logger.info(f"Loaded Schema D with {len(self.schema_d_data.get('matches', []))} matches")
    
    def load_scene_boundaries(self) -> None:
        """Load scene data from Hendrix_Video_Analysis"""
        logger.info(f"Loading scene data from {self.scene_analysis_path}")
        
        if not self.scene_analysis_path.exists():
            raise FileNotFoundError(f"Scene analysis file not found: {self.scene_analysis_path}")
            
        with open(self.scene_analysis_path, 'r', encoding='utf-8') as f:
            self.scene_data = json.load(f)
            
        logger.info(f"Loaded {self.scene_data.get('total_scenes', 0)} scenes")
    
    def get_dialogue_in_timeframe(self, start_time: float, end_time: float) -> List[DialogueEntry]:
        """
        Get all dialogue entries within a given timeframe
        
        Args:
            start_time: Start time in seconds
            end_time: End time in seconds
            
        Returns:
            List of DialogueEntry objects
        """
        dialogue_entries = []
        
        if not self.schema_d_data:
            return dialogue_entries
            
        # Iterate through character-dialogue matches
        for match in self.schema_d_data.get('matches', []):
            dialogue = match.get('dialogue', {})
            dialogue_start = dialogue.get('start_time', 0)
            dialogue_end = dialogue.get('end_time', 0)
            
            # Check if dialogue falls within scene timeframe
            if dialogue_start >= start_time and dialogue_start < end_time:
                # Check confidence threshold
                confidence = match.get('matching_score', {}).get('final_score', 0)
                if confidence >= self.min_dialogue_confidence:
                    char_id = match.get('character_id', 'unknown')
                    char_name = self.character_names.get(char_id, f"Character_{char_id}")
                    
                    entry = DialogueEntry(
                        speaker=char_name,
                        character_id=char_id,
                        text=dialogue.get('text', ''),
                        start_time=dialogue_start,
                        end_time=dialogue_end,
                        emotion=dialogue.get('emotion') if self.include_emotions else None,
                        emotion_confidence=dialogue.get('emotion_confidence') if self.include_emotions else None,
                        confidence=confidence
                    )
                    dialogue_entries.append(entry)
        
        # Sort by start time
        dialogue_entries.sort(key=lambda x: x.start_time)
        
        return dialogue_entries
    
    def get_characters_in_scene(self, start_time: float, end_time: float, 
                               dialogue_entries: List[DialogueEntry]) -> List[str]:
        """
        Get all characters present in a scene (both speaking and non-speaking)
        
        Args:
            start_time: Scene start time
            end_time: Scene end time
            dialogue_entries: Dialogue entries already collected
            
        Returns:
            List of character names
        """
        characters = set()
        
        # Add speaking characters
        for entry in dialogue_entries:
            characters.add(entry.speaker)
        
        # Add visually detected characters from Schema C
        if self.schema_c_data:
            for detection in self.schema_c_data.get('detections', []):
                det_time = detection.get('timestamp', 0)
                if start_time <= det_time <= end_time:
                    char_id = detection.get('character_id', '')
                    char_name = self.character_names.get(char_id, f"Character_{char_id}")
                    characters.add(char_name)
        
        return sorted(list(characters))
    
    def create_scene_context_packet(self, scene: Dict[str, Any], 
                                   prior_summary: str = "") -> SceneContextPacket:
        """
        Create a complete context packet for a single scene
        
        Args:
            scene: Scene data from scene analysis
            prior_summary: Summary of the previous scene
            
        Returns:
            SceneContextPacket with all relevant data
        """
        scene_id = scene.get('scene_id', 0)
        start_time = scene.get('start_time', 0)
        end_time = scene.get('end_time', 0)
        
        # Get dialogue entries
        dialogue_entries = self.get_dialogue_in_timeframe(start_time, end_time)
        
        # Get characters present
        characters = self.get_characters_in_scene(start_time, end_time, dialogue_entries)
        
        # Create the context packet
        packet = SceneContextPacket(
            scene_id=scene_id,
            start_time=start_time,
            end_time=end_time,
            visual_description=scene.get('summary', ''),
            characters_present=characters,
            dialogue_transcript=dialogue_entries,
            prior_scene_summary=prior_summary,
            shot_ids=scene.get('contained_shots', []),
            mood=scene.get('mood', ''),
            setting=scene.get('setting', ''),
            key_actions=scene.get('key_actions', [])
        )
        
        return packet
    
    def process_all_scenes(self) -> List[SceneContextPacket]:
        """
        Process all scenes and create context packets
        
        Returns:
            List of SceneContextPacket objects
        """
        # Load all data
        self.load_audio_analysis_data()
        self.load_scene_boundaries()
        
        context_packets = []
        prior_summary = "The story begins."
        
        # Process each scene
        for scene in self.scene_data.get('scenes', []):
            packet = self.create_scene_context_packet(scene, prior_summary)
            context_packets.append(packet)
            
            # Update prior summary (will be updated by caption generator)
            prior_summary = f"Scene {packet.scene_id}: {packet.visual_description[:100]}..."
        
        logger.info(f"Created {len(context_packets)} scene context packets")
        
        return context_packets


def main():
    """Test the data fusion engine"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test data fusion engine")
    parser.add_argument("--audio-analysis", required=True, help="Path to audio analysis output")
    parser.add_argument("--scene-analysis", required=True, help="Path to scenes.json")
    parser.add_argument("--output", default="context_packets.json", help="Output file")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Create engine and process
    engine = DataFusionEngine(args.audio_analysis, args.scene_analysis)
    packets = engine.process_all_scenes()
    
    # Save to file
    output_data = {
        "total_scenes": len(packets),
        "context_packets": [p.to_dict() for p in packets]
    }
    
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"Saved {len(packets)} context packets to {args.output}")


if __name__ == "__main__":
    main()