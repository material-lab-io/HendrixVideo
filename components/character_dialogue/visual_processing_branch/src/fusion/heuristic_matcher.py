"""
Heuristic Rules for Character-Dialogue Matching

This module implements various heuristic rules to score character-dialogue matches
based on visual and temporal features.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import logging

from ..schemas import (
    SchemaA, SchemaB, SchemaC, SchemaD,
    TranscriptionSegment, SpeakerSegment, FaceDetection, CharacterInfo,
    CharacterDialogueMatch, MatchingScore
)
from ..visual.active_speaker_detector import ActiveSpeakerDetector, LipMovementData

logger = logging.getLogger(__name__)


@dataclass
class HeuristicConfig:
    """Configuration for heuristic matching"""
    single_character_weight: float = 0.8
    lip_sync_weight: float = 0.9
    character_centrality_weight: float = 0.6
    speaker_alignment_weight: float = 0.7
    temporal_proximity_weight: float = 0.5
    
    # Thresholds
    single_character_threshold: int = 1  # Max characters on screen for single character rule
    centrality_threshold: float = 0.3  # Min fraction of frame for centrality
    temporal_window: float = 0.5  # Seconds for temporal proximity
    window_extension: float = 30.0  # Seconds to extend search window before/after dialogue


class HeuristicMatcher:
    """Implements heuristic rules for character-dialogue matching"""
    
    def __init__(self, config: HeuristicConfig = None):
        self.config = config or HeuristicConfig()
        self.active_speaker_detector = ActiveSpeakerDetector()
        
    def calculate_heuristic_scores(self, 
                                 dialogue: TranscriptionSegment,
                                 character_id: str,
                                 schema_c: SchemaC,
                                 speaker_segment: Optional[SpeakerSegment] = None,
                                 lip_movement_data: Optional[Dict[str, List[LipMovementData]]] = None,
                                 audio_amplitude: Optional[np.ndarray] = None) -> Dict[str, float]:
        """Calculate all heuristic scores for a character-dialogue pair
        
        Returns:
            Dictionary of heuristic_name -> score
        """
        scores = {}
        
        # Get character info and detections during dialogue time
        character_info = schema_c.characters.get(character_id)
        if not character_info:
            return scores
            
        detections_during_dialogue = self._get_detections_in_timerange(
            schema_c, dialogue.start_time, dialogue.end_time
        )
        
        # Heuristic 1: Single on-screen character
        scores['single_character'] = self._calculate_single_character_score(
            detections_during_dialogue, character_id, dialogue
        )
        
        # Heuristic 2: Lip-sync detection with active speaker analysis
        scores['lip_sync'] = self._calculate_lip_sync_score(
            dialogue, character_id, detections_during_dialogue,
            lip_movement_data, audio_amplitude
        )
        
        # Heuristic 3: Character centrality/bbox size
        scores['character_centrality'] = self._calculate_centrality_score(
            detections_during_dialogue, character_id, schema_c, dialogue
        )
        
        # Heuristic 4: Speaker turn alignment
        if speaker_segment:
            scores['speaker_alignment'] = self._calculate_speaker_alignment_score(
                dialogue, speaker_segment, character_info
            )
        
        # Additional heuristic: Temporal proximity
        scores['temporal_proximity'] = self._calculate_temporal_proximity_score(
            dialogue, character_info
        )
        
        return scores
    
    def _get_detections_in_timerange(self, schema_c: SchemaC, 
                                   start_time: float, end_time: float, 
                                   window_extension: Optional[float] = None) -> List[FaceDetection]:
        """Get all face detections within a time range
        
        Args:
            schema_c: Schema C containing detections
            start_time: Start of dialogue
            end_time: End of dialogue
            window_extension: Optional extension to search window (uses config value if None)
        """
        if window_extension is None:
            window_extension = self.config.window_extension
            
        # Expand search window
        search_start = max(0, start_time - window_extension)
        search_end = end_time + window_extension
        
        return [det for det in schema_c.detections
                if search_start <= det.timestamp <= search_end]
    
    def _calculate_single_character_score(self, detections: List[FaceDetection], 
                                        character_id: str, dialogue: TranscriptionSegment) -> float:
        """Heuristic 1: Single on-screen character → 0.8 confidence
        
        If only one character appears during the dialogue, they're likely the speaker
        """
        if not detections:
            return 0.0
            
        # Separate detections into those during dialogue and those in extended window
        during_dialogue = [d for d in detections if dialogue.start_time <= d.timestamp <= dialogue.end_time]
        extended_window = [d for d in detections if d not in during_dialogue]
        
        # First check detections during dialogue
        if during_dialogue:
            unique_characters = set(d.character_id for d in during_dialogue if d.character_id is not None)
            
            # If only one character on screen and it's our target character
            if len(unique_characters) == 1 and character_id in unique_characters:
                return self.config.single_character_weight
            
            # Partial score if character is present but not alone
            if character_id in unique_characters:
                char_detections = sum(1 for d in during_dialogue if d.character_id == character_id)
                dominance_ratio = char_detections / len(during_dialogue)
                return self.config.single_character_weight * dominance_ratio * 0.5
        
        # If no detections during dialogue, check extended window with decay
        if extended_window:
            unique_characters = set(d.character_id for d in extended_window if d.character_id is not None)
            
            if character_id in unique_characters:
                # Apply temporal decay based on distance from dialogue
                min_distance = float('inf')
                for d in extended_window:
                    if d.character_id == character_id:
                        dist = min(abs(d.timestamp - dialogue.start_time), 
                                 abs(d.timestamp - dialogue.end_time))
                        min_distance = min(min_distance, dist)
                
                # Decay factor: closer detections get higher scores
                decay_factor = max(0.2, 1.0 - (min_distance / self.config.window_extension))
                
                # Check if character is dominant in extended window
                char_detections = sum(1 for d in extended_window if d.character_id == character_id)
                dominance_ratio = char_detections / len(extended_window)
                
                if len(unique_characters) == 1:
                    return self.config.single_character_weight * decay_factor * 0.7
                else:
                    return self.config.single_character_weight * dominance_ratio * decay_factor * 0.4
        
        return 0.0
    
    def _calculate_lip_sync_score(self, dialogue: TranscriptionSegment,
                                character_id: str, 
                                detections: List[FaceDetection],
                                lip_movement_data: Optional[Dict[str, List[LipMovementData]]] = None,
                                audio_amplitude: Optional[np.ndarray] = None) -> float:
        """Heuristic 2: Lip-sync detection → 0.9 confidence
        
        Uses active speaker detection to analyze lip movements and correlation with audio
        """
        # Check if we have lip movement data
        if not lip_movement_data or str(character_id) not in lip_movement_data:
            # Fallback to presence-based scoring
            char_detections = [d for d in detections if d.character_id == character_id]
            if char_detections:
                return 0.1  # Low score for presence without lip data
            return 0.0
        
        # Get lip movements for this character during dialogue time
        character_movements = lip_movement_data.get(str(character_id), [])
        dialogue_movements = [
            m for m in character_movements
            if dialogue.start_time <= m.timestamp <= dialogue.end_time
        ]
        
        if not dialogue_movements:
            return 0.0
        
        # Update active speaker detector with movement history
        for movement in dialogue_movements:
            self.active_speaker_detector.update_character_frame(
                int(character_id),
                movement.lip_landmarks,
                movement.frame_number,
                movement.timestamp
            )
        
        # Detect if character is speaking
        is_speaking, confidence = self.active_speaker_detector.detect_speaking(
            int(character_id),
            audio_amplitude
        )
        
        if is_speaking:
            # Apply full weight for active speakers
            return self.config.lip_sync_weight * confidence
        else:
            # Small score if character is present but not speaking
            return 0.05
    
    def _calculate_centrality_score(self, detections: List[FaceDetection],
                                  character_id: str, schema_c: SchemaC, 
                                  dialogue: Optional[TranscriptionSegment] = None) -> float:
        """Heuristic 3: Character centrality/bbox size → 0.6 confidence
        
        Larger, more central faces are more likely to be speaking
        """
        char_detections = [d for d in detections if d.character_id == character_id]
        if not char_detections:
            return 0.0
        
        scores = []
        for det in char_detections:
            # Calculate bbox area (normalized)
            bbox = det.bbox
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
            
            # Normalize by frame dimensions (assuming 640x480 default)
            # In production, would get actual frame dimensions
            area = (width * height) / (640 * 480)
            
            # Calculate centrality (distance from center)
            center_x = (bbox[0] + bbox[2]) / 2
            center_y = (bbox[1] + bbox[3]) / 2
            
            # Distance from frame center (normalized)
            dist_from_center = np.sqrt(
                ((center_x - 320) / 320) ** 2 + 
                ((center_y - 240) / 240) ** 2
            )
            centrality = 1.0 - min(dist_from_center, 1.0)
            
            # Combine area and centrality
            score = (area + centrality) / 2
            scores.append(score)
        
        # Average score across all detections
        avg_score = np.mean(scores)
        
        # Apply weight if score exceeds threshold
        if avg_score >= self.config.centrality_threshold:
            return self.config.character_centrality_weight * avg_score
        
        return avg_score * self.config.character_centrality_weight * 0.5
    
    def _calculate_speaker_alignment_score(self, dialogue: TranscriptionSegment,
                                         speaker_segment: SpeakerSegment,
                                         character_info: CharacterInfo) -> float:
        """Heuristic 4: Speaker turn alignment → 0.7 confidence
        
        If character appearances align with speaker diarization segments
        """
        # Check temporal overlap between speaker segment and character appearances
        overlap = 0.0
        
        for appearance in character_info.appearance_segments:
            # Calculate overlap between speaker segment and character appearance
            overlap_start = max(speaker_segment.start_time, appearance['start'])
            overlap_end = min(speaker_segment.end_time, appearance['end'])
            
            if overlap_start < overlap_end:
                overlap += overlap_end - overlap_start
        
        # Calculate overlap ratio
        speaker_duration = speaker_segment.end_time - speaker_segment.start_time
        overlap_ratio = overlap / speaker_duration if speaker_duration > 0 else 0
        
        # Apply weight based on overlap
        if overlap_ratio > 0.8:
            return self.config.speaker_alignment_weight
        elif overlap_ratio > 0.5:
            return self.config.speaker_alignment_weight * overlap_ratio
        else:
            return overlap_ratio * self.config.speaker_alignment_weight * 0.5
    
    def _calculate_temporal_proximity_score(self, dialogue: TranscriptionSegment,
                                          character_info: CharacterInfo) -> float:
        """Additional heuristic: Temporal proximity
        
        Characters appearing close to dialogue time are more likely speakers
        """
        min_distance = float('inf')
        
        # Find minimum distance between dialogue and character appearances
        for appearance in character_info.appearance_segments:
            # Distance to start of dialogue
            dist_to_start = abs(appearance['end'] - dialogue.start_time)
            # Distance to end of dialogue  
            dist_to_end = abs(appearance['start'] - dialogue.end_time)
            
            min_distance = min(min_distance, dist_to_start, dist_to_end)
            
            # If character appears during dialogue, distance is 0
            if (appearance['start'] <= dialogue.start_time <= appearance['end'] or
                appearance['start'] <= dialogue.end_time <= appearance['end']):
                min_distance = 0
                break
        
        # Convert distance to score
        if min_distance == 0:
            return self.config.temporal_proximity_weight
        elif min_distance <= self.config.temporal_window:
            # Linear decay within temporal window
            score = 1.0 - (min_distance / self.config.temporal_window)
            return score * self.config.temporal_proximity_weight
        else:
            # Exponential decay beyond window
            score = np.exp(-min_distance / self.config.temporal_window)
            return score * self.config.temporal_proximity_weight * 0.3
    
    def get_best_heuristic_score(self, scores: Dict[str, float]) -> float:
        """Get the maximum heuristic score"""
        return max(scores.values()) if scores else 0.0
    
    def determine_confidence_level(self, final_score: float) -> str:
        """Determine confidence level based on final score"""
        if final_score >= 0.8:
            return "high"
        elif final_score >= 0.5:
            return "medium"
        else:
            return "low"