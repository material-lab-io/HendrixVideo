"""
Advanced Character-Dialogue Matcher with Multi-Modal Fusion

This module implements sophisticated matching strategies including:
- Character continuity tracking across scenes
- Speaker diarization integration
- Confidence auto-calibration
- Progressive matching with feedback
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Any, Set
from dataclasses import dataclass, field
import logging
from collections import defaultdict
import json
import uuid

from ..schemas import (
    SchemaA, SchemaB, SchemaC, SchemaD,
    TranscriptionSegment, CharacterInfo, FaceDetection,
    CharacterDialogueMatch, MatchingScore
)

logger = logging.getLogger(__name__)


@dataclass
class CharacterProfile:
    """Extended character profile for continuity tracking"""
    character_id: str
    embeddings: List[np.ndarray] = field(default_factory=list)
    appearance_segments: List[Tuple[float, float]] = field(default_factory=list)
    dialogue_history: List[str] = field(default_factory=list)
    speaker_associations: Dict[str, float] = field(default_factory=dict)  # speaker_id -> confidence
    visual_attributes: Dict[str, Any] = field(default_factory=dict)
    scene_appearances: Set[int] = field(default_factory=set)
    avg_screen_position: Tuple[float, float] = (0.5, 0.5)  # Normalized x, y
    
    def update_speaker_association(self, speaker_id: str, confidence: float):
        """Update speaker association with weighted average"""
        if speaker_id in self.speaker_associations:
            # Weighted update
            old_conf = self.speaker_associations[speaker_id]
            self.speaker_associations[speaker_id] = (old_conf + confidence) / 2
        else:
            self.speaker_associations[speaker_id] = confidence
    
    def get_best_speaker(self) -> Optional[Tuple[str, float]]:
        """Get most likely speaker for this character"""
        if not self.speaker_associations:
            return None
        best_speaker = max(self.speaker_associations.items(), key=lambda x: x[1])
        return best_speaker


@dataclass
class MatchingContext:
    """Context information for matching decisions"""
    video_duration: float
    total_dialogues: int
    total_characters: int
    avg_dialogue_duration: float
    character_density: float  # Characters per minute
    dialogue_density: float  # Dialogues per minute
    video_type: str = "unknown"  # movie, interview, documentary, etc.
    
    @classmethod
    def from_schemas(cls, schema_a: SchemaA, schema_c: SchemaC) -> 'MatchingContext':
        """Create context from schemas"""
        avg_dialogue_duration = np.mean([
            seg.end_time - seg.start_time 
            for seg in schema_a.segments
        ]) if schema_a.segments else 0
        
        return cls(
            video_duration=schema_a.duration,
            total_dialogues=len(schema_a.segments),
            total_characters=len(schema_c.characters),
            avg_dialogue_duration=avg_dialogue_duration,
            character_density=len(schema_c.characters) / (schema_a.duration / 60) if schema_a.duration > 0 else 0,
            dialogue_density=len(schema_a.segments) / (schema_a.duration / 60) if schema_a.duration > 0 else 0
        )


class AdvancedCharacterMatcher:
    """Advanced character-dialogue matching with multiple strategies"""
    
    def __init__(self, enable_learning: bool = True):
        """
        Args:
            enable_learning: Enable progressive learning from matches
        """
        self.enable_learning = enable_learning
        self.character_profiles: Dict[str, CharacterProfile] = {}
        self.matching_history: List[Dict] = []
        self.confidence_calibration = None
        
    def match_with_continuity(self,
                            schema_a: SchemaA,
                            schema_c: SchemaC,
                            schema_b: Optional[SchemaB] = None) -> SchemaD:
        """Perform advanced matching with character continuity
        
        Args:
            schema_a: Transcription segments
            schema_c: Character detections
            schema_b: Optional speaker diarization
            
        Returns:
            SchemaD with character-dialogue matches
        """
        logger.info("Starting advanced character-dialogue matching")
        
        # Build context
        context = MatchingContext.from_schemas(schema_a, schema_c)
        logger.info(f"Context: {context.total_dialogues} dialogues, "
                   f"{context.total_characters} characters")
        
        # Auto-calibrate confidence thresholds
        self._calibrate_confidence_thresholds(context)
        
        # Build character profiles with continuity
        self._build_character_profiles(schema_c)
        
        # Integrate speaker diarization if available
        if schema_b:
            self._integrate_speaker_information(schema_b, schema_a)
        
        # Perform multi-stage matching
        matches = []
        unmatched = []
        
        for dialogue in schema_a.segments:
            match = self._match_dialogue_advanced(dialogue, schema_c, context)
            
            if match:
                matches.append(match)
                
                # Learn from match if enabled
                if self.enable_learning:
                    self._update_from_match(match)
            else:
                unmatched.append(dialogue)
        
        # Post-processing: resolve conflicts and improve matches
        matches = self._post_process_matches(matches, unmatched, context)
        
        # Create SchemaD
        schema_d = SchemaD(
            video_id=schema_a.video_id,
            duration=schema_a.duration,
            matches=matches,
            unmatched_dialogues=[d for d in schema_a.segments if d not in [m.dialogue_segment for m in matches]],
            metadata={
                'matching_method': 'advanced_continuity',
                'context': context.__dict__,
                'character_profiles': len(self.character_profiles),
                'confidence_calibration': self.confidence_calibration
            }
        )
        
        logger.info(f"Matching complete: {len(matches)}/{len(schema_a.segments)} "
                   f"({len(matches)/len(schema_a.segments)*100:.1f}%)")
        
        return schema_d
    
    def _calibrate_confidence_thresholds(self, context: MatchingContext):
        """Auto-calibrate confidence thresholds based on video characteristics"""
        # Base thresholds
        base_confidence = 0.3
        
        # Adjust based on character density
        if context.character_density < 1:  # Few characters
            confidence_modifier = 0.9
        elif context.character_density > 10:  # Many characters
            confidence_modifier = 1.2
        else:
            confidence_modifier = 1.0
        
        # Adjust based on dialogue density
        if context.dialogue_density > 20:  # Fast-paced dialogue
            temporal_window = 10.0
        elif context.dialogue_density < 5:  # Sparse dialogue
            temporal_window = 60.0
        else:
            temporal_window = 30.0
        
        self.confidence_calibration = {
            'min_confidence': base_confidence * confidence_modifier,
            'temporal_window': temporal_window,
            'require_visible': context.character_density > 5,  # Stricter for crowded videos
            'use_speaker_info': True,
            'continuity_weight': 0.3 if context.video_duration > 600 else 0.1
        }
        
        logger.info(f"Calibrated thresholds: {self.confidence_calibration}")
    
    def _build_character_profiles(self, schema_c: SchemaC):
        """Build comprehensive character profiles"""
        for char_id, char_info in schema_c.characters.items():
            profile = CharacterProfile(character_id=char_id)
            
            # Extract embeddings
            if hasattr(char_info, 'representative_embeddings'):
                profile.embeddings = [
                    np.array(emb) for emb in char_info.representative_embeddings
                ]
            
            # Extract appearance segments
            profile.appearance_segments = [
                (seg['start'], seg['end']) 
                for seg in char_info.appearance_segments
            ]
            
            # Extract visual attributes
            if hasattr(char_info, 'attributes') and char_info.attributes:
                profile.visual_attributes = char_info.attributes
            
            # Calculate average screen position
            positions = []
            for detection in schema_c.detections:
                if detection.character_id == char_id:
                    bbox = detection.bbox
                    center_x = (bbox[0] + bbox[2]) / 2
                    center_y = (bbox[1] + bbox[3]) / 2
                    positions.append((center_x, center_y))
            
            if positions:
                profile.avg_screen_position = (
                    np.mean([p[0] for p in positions]),
                    np.mean([p[1] for p in positions])
                )
            
            self.character_profiles[char_id] = profile
    
    def _integrate_speaker_information(self, schema_b: SchemaB, schema_a: SchemaA):
        """Integrate speaker diarization with character profiles"""
        logger.info("Integrating speaker diarization information")
        
        # Map dialogues to speakers
        dialogue_speakers = {}
        
        for dialogue in schema_a.segments:
            # Find overlapping speaker segment
            best_overlap = 0
            best_speaker = None
            
            for speaker_seg in schema_b.segments:
                overlap = self._calculate_overlap(
                    (dialogue.start_time, dialogue.end_time),
                    (speaker_seg.start_time, speaker_seg.end_time)
                )
                
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_speaker = speaker_seg.speaker_id
            
            if best_speaker and best_overlap > 0.5:
                dialogue_speakers[dialogue.segment_id] = best_speaker
        
        logger.info(f"Mapped {len(dialogue_speakers)} dialogues to speakers")
        
        # Store for later use
        self.dialogue_speakers = dialogue_speakers
    
    def _match_dialogue_advanced(self, 
                               dialogue: TranscriptionSegment,
                               schema_c: SchemaC,
                               context: MatchingContext) -> Optional[CharacterDialogueMatch]:
        """Advanced matching for a single dialogue"""
        
        candidates = []
        
        # Get temporal window based on calibration
        window = self.confidence_calibration['temporal_window']
        
        # Find characters in temporal proximity
        for char_id, profile in self.character_profiles.items():
            # Check temporal proximity
            min_distance = float('inf')
            
            for start, end in profile.appearance_segments:
                # Distance to dialogue
                if start <= dialogue.end_time and end >= dialogue.start_time:
                    min_distance = 0  # Character visible during dialogue
                    break
                else:
                    # Calculate minimum distance
                    dist_to_start = abs(start - dialogue.end_time)
                    dist_to_end = abs(end - dialogue.start_time)
                    min_distance = min(min_distance, dist_to_start, dist_to_end)
            
            if min_distance <= window:
                # Calculate comprehensive score
                score = self._calculate_comprehensive_score(
                    dialogue, char_id, profile, min_distance, context
                )
                
                if score > self.confidence_calibration['min_confidence']:
                    candidates.append((char_id, score))
        
        # Select best candidate
        if candidates:
            candidates.sort(key=lambda x: x[1], reverse=True)
            best_char_id, best_score = candidates[0]
            
            # Create match
            match = CharacterDialogueMatch(
                match_id=f"match_{dialogue.segment_id}_{best_char_id}",
                character_id=best_char_id,
                dialogue_segment=dialogue,
                matching_score=MatchingScore(
                    heuristic_scores={
                        'temporal': 1.0 - min(1.0, min_distance / window),
                        'speaker': self._get_speaker_score(dialogue, best_char_id),
                        'continuity': self._get_continuity_score(dialogue, best_char_id),
                        'position': self._get_position_score(best_char_id)
                    },
                    llm_score=0.0,
                    final_score=best_score,
                    confidence_level='high' if best_score > 0.7 else 'medium'
                )
            )
            
            return match
        
        return None
    
    def _calculate_comprehensive_score(self,
                                     dialogue: TranscriptionSegment,
                                     char_id: str,
                                     profile: CharacterProfile,
                                     temporal_distance: float,
                                     context: MatchingContext) -> float:
        """Calculate comprehensive matching score"""
        scores = []
        weights = []
        
        # 1. Temporal score
        window = self.confidence_calibration['temporal_window']
        temporal_score = 1.0 - min(1.0, temporal_distance / window)
        scores.append(temporal_score)
        weights.append(0.3)
        
        # 2. Speaker association score
        speaker_score = self._get_speaker_score(dialogue, char_id)
        if speaker_score > 0:
            scores.append(speaker_score)
            weights.append(0.3)
        
        # 3. Continuity score (based on recent dialogue history)
        continuity_score = self._get_continuity_score(dialogue, char_id)
        scores.append(continuity_score)
        weights.append(self.confidence_calibration.get('continuity_weight', 0.2))
        
        # 4. Position score (characters in center more likely to speak)
        position_score = self._get_position_score(char_id)
        scores.append(position_score)
        weights.append(0.1)
        
        # 5. Emotion correlation (if available)
        if hasattr(dialogue, 'emotion') and dialogue.emotion:
            emotion_score = self._get_emotion_correlation_score(dialogue, profile)
            scores.append(emotion_score)
            weights.append(0.1)
        
        # Normalize weights
        total_weight = sum(weights)
        if total_weight > 0:
            weights = [w / total_weight for w in weights]
        
        # Calculate weighted score
        final_score = sum(s * w for s, w in zip(scores, weights))
        
        return final_score
    
    def _get_speaker_score(self, dialogue: TranscriptionSegment, char_id: str) -> float:
        """Get speaker-character association score"""
        if not hasattr(self, 'dialogue_speakers'):
            return 0.0
        
        speaker_id = self.dialogue_speakers.get(dialogue.segment_id)
        if not speaker_id:
            return 0.0
        
        profile = self.character_profiles[char_id]
        return profile.speaker_associations.get(speaker_id, 0.0)
    
    def _get_continuity_score(self, dialogue: TranscriptionSegment, char_id: str) -> float:
        """Get continuity score based on recent matches"""
        if not self.matching_history:
            return 0.5  # Neutral score
        
        # Look at recent matches
        recent_matches = self.matching_history[-10:]
        
        # Count how often this character spoke recently
        char_count = sum(1 for m in recent_matches if m['character_id'] == char_id)
        
        # Also consider temporal proximity of last match
        last_char_match = None
        for match in reversed(recent_matches):
            if match['character_id'] == char_id:
                last_char_match = match
                break
        
        if last_char_match:
            time_since_last = dialogue.start_time - last_char_match['end_time']
            
            # Characters tend to have continuous dialogue
            if time_since_last < 5.0:  # Within 5 seconds
                return 0.9
            elif time_since_last < 30.0:  # Within 30 seconds
                return 0.7
        
        # Base score on frequency
        frequency_score = char_count / len(recent_matches) if recent_matches else 0
        return 0.5 + frequency_score * 0.3
    
    def _get_position_score(self, char_id: str) -> float:
        """Get position-based score (central characters more likely to speak)"""
        profile = self.character_profiles[char_id]
        x, y = profile.avg_screen_position
        
        # Distance from center (normalized)
        center_dist = np.sqrt((x - 0.5)**2 + (y - 0.5)**2)
        
        # Convert to score (closer to center = higher score)
        position_score = 1.0 - min(1.0, center_dist * 2)
        
        return position_score
    
    def _get_emotion_correlation_score(self, 
                                     dialogue: TranscriptionSegment,
                                     profile: CharacterProfile) -> float:
        """Correlate dialogue emotion with character's visual appearance"""
        # This is a placeholder - could be enhanced with actual emotion detection
        # from facial expressions
        
        emotion = dialogue.emotion
        
        # Simple heuristic: certain emotions correlate with screen position
        if emotion in ['angry', 'fear']:
            # Angry/fearful characters might be off-center
            return 1.0 - self._get_position_score(profile.character_id)
        elif emotion in ['happy', 'surprise']:
            # Happy characters might be centered
            return self._get_position_score(profile.character_id)
        
        return 0.5  # Neutral
    
    def _update_from_match(self, match: CharacterDialogueMatch):
        """Update character profiles from successful match"""
        char_id = match.character_id
        dialogue = match.dialogue_segment
        
        # Update dialogue history
        profile = self.character_profiles[char_id]
        profile.dialogue_history.append(dialogue.text)
        
        # Update speaker association if available
        if hasattr(self, 'dialogue_speakers'):
            speaker_id = self.dialogue_speakers.get(dialogue.segment_id)
            if speaker_id:
                profile.update_speaker_association(speaker_id, match.matching_score.final_score)
        
        # Update matching history
        self.matching_history.append({
            'character_id': char_id,
            'start_time': dialogue.start_time,
            'end_time': dialogue.end_time,
            'confidence': match.matching_score.final_score
        })
    
    def _post_process_matches(self, 
                            matches: List[CharacterDialogueMatch],
                            unmatched: List[TranscriptionSegment],
                            context: MatchingContext) -> List[CharacterDialogueMatch]:
        """Post-process matches to resolve conflicts and improve quality"""
        
        # 1. Resolve temporal conflicts (same character speaking simultaneously)
        matches = self._resolve_temporal_conflicts(matches)
        
        # 2. Try to match remaining dialogues using learned associations
        if self.enable_learning and unmatched:
            additional_matches = self._match_using_learned_associations(unmatched, context)
            matches.extend(additional_matches)
        
        # 3. Smooth confidence scores
        matches = self._smooth_confidence_scores(matches)
        
        return matches
    
    def _resolve_temporal_conflicts(self, 
                                  matches: List[CharacterDialogueMatch]) -> List[CharacterDialogueMatch]:
        """Resolve cases where same character has overlapping dialogues"""
        # Group by character
        char_matches = defaultdict(list)
        for match in matches:
            char_matches[match.character_id].append(match)
        
        resolved_matches = []
        
        for char_id, char_match_list in char_matches.items():
            # Sort by time
            char_match_list.sort(key=lambda m: m.dialogue_segment.start_time)
            
            # Check for overlaps
            for i, match in enumerate(char_match_list):
                if i == 0:
                    resolved_matches.append(match)
                    continue
                
                prev_match = char_match_list[i-1]
                
                # If overlapping, keep the one with higher confidence
                if match.dialogue_segment.start_time < prev_match.dialogue_segment.end_time:
                    if match.matching_score.final_score > prev_match.matching_score.final_score:
                        # Remove previous, add current
                        resolved_matches = [m for m in resolved_matches if m != prev_match]
                        resolved_matches.append(match)
                    # Otherwise, skip current (previous already added)
                else:
                    resolved_matches.append(match)
        
        return resolved_matches
    
    def _match_using_learned_associations(self,
                                        unmatched: List[TranscriptionSegment],
                                        context: MatchingContext) -> List[CharacterDialogueMatch]:
        """Try to match unmatched dialogues using learned speaker associations"""
        additional_matches = []
        
        for dialogue in unmatched:
            if hasattr(self, 'dialogue_speakers'):
                speaker_id = self.dialogue_speakers.get(dialogue.segment_id)
                if speaker_id:
                    # Find character with strongest association to this speaker
                    best_char = None
                    best_conf = 0.0
                    
                    for char_id, profile in self.character_profiles.items():
                        conf = profile.speaker_associations.get(speaker_id, 0.0)
                        if conf > best_conf and conf > 0.5:  # Minimum threshold
                            best_char = char_id
                            best_conf = conf
                    
                    if best_char:
                        match = CharacterDialogueMatch(
                            match_id=f"match_{dialogue.segment_id}_{best_char}_speaker",
                            character_id=best_char,
                            dialogue_segment=dialogue,
                            matching_score=MatchingScore(
                                heuristic_scores={'speaker_association': best_conf},
                                llm_score=0.0,
                                final_score=best_conf * 0.8,  # Slightly reduce confidence
                                confidence_level='medium'
                            )
                        )
                        additional_matches.append(match)
        
        return additional_matches
    
    def _smooth_confidence_scores(self, 
                                matches: List[CharacterDialogueMatch]) -> List[CharacterDialogueMatch]:
        """Smooth confidence scores using temporal context"""
        # Sort by time
        matches.sort(key=lambda m: m.dialogue_segment.start_time)
        
        # Apply smoothing
        window_size = 3
        for i, match in enumerate(matches):
            # Get nearby matches
            start_idx = max(0, i - window_size)
            end_idx = min(len(matches), i + window_size + 1)
            
            nearby_matches = matches[start_idx:end_idx]
            
            # If same character appears nearby with high confidence, boost current
            same_char_matches = [
                m for m in nearby_matches 
                if m.character_id == match.character_id and m != match
            ]
            
            if same_char_matches:
                avg_nearby_conf = np.mean([
                    m.matching_score.final_score for m in same_char_matches
                ])
                
                # Weighted average with nearby confidence
                smoothed_score = (
                    match.matching_score.final_score * 0.7 + 
                    avg_nearby_conf * 0.3
                )
                
                match.matching_score.final_score = smoothed_score
        
        return matches
    
    def _calculate_overlap(self, seg1: Tuple[float, float], seg2: Tuple[float, float]) -> float:
        """Calculate overlap ratio between two time segments"""
        start = max(seg1[0], seg2[0])
        end = min(seg1[1], seg2[1])
        
        if start >= end:
            return 0.0
        
        overlap = end - start
        duration = min(seg1[1] - seg1[0], seg2[1] - seg2[0])
        
        return overlap / duration if duration > 0 else 0.0