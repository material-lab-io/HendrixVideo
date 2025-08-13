"""
Character-Dialogue Matcher - Main Fusion Module

This module orchestrates the complete character-dialogue matching process,
combining heuristic rules and LLM analysis to produce Schema D.
"""

import logging
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
import numpy as np
from datetime import datetime
import uuid

from ..schemas import (
    SchemaA, SchemaB, SchemaC, SchemaD,
    TranscriptionSegment, CharacterDialogueMatch, MatchingScore
)
from .heuristic_matcher import HeuristicMatcher, HeuristicConfig
from .llm_matcher import LLMMatcher, LLMConfig

logger = logging.getLogger(__name__)


@dataclass
class FusionConfig:
    """Configuration for fusion matching"""
    heuristic_weight: float = 0.4
    llm_weight: float = 0.6
    min_confidence_threshold: float = 0.3
    use_speaker_diarization: bool = True
    use_llm: bool = True
    
    # Component configs
    heuristic_config: HeuristicConfig = None
    llm_config: LLMConfig = None
    
    def __post_init__(self):
        if self.heuristic_config is None:
            self.heuristic_config = HeuristicConfig()
        if self.llm_config is None:
            self.llm_config = LLMConfig()


class CharacterDialogueMatcher:
    """
    Main fusion module for character-dialogue matching
    
    Combines:
    1. Heuristic rules (single character, centrality, etc.)
    2. LLM analysis for visual context understanding
    3. Speaker diarization alignment (if available)
    """
    
    def __init__(self, config: FusionConfig = None):
        self.config = config or FusionConfig()
        self.heuristic_matcher = HeuristicMatcher(self.config.heuristic_config)
        self.llm_matcher = LLMMatcher(self.config.llm_config) if self.config.use_llm else None
        
    def match_schemas(self, 
                     schema_a: SchemaA,
                     schema_c: SchemaC,
                     schema_b: Optional[SchemaB] = None) -> SchemaD:
        """
        Perform complete character-dialogue matching
        
        Args:
            schema_a: Dialogue transcriptions
            schema_c: Character detections and database
            schema_b: Speaker diarization (optional)
            
        Returns:
            Schema D with matched character-dialogue pairs
        """
        logger.info(f"Starting character-dialogue matching for video: {schema_a.video_id}")
        logger.info(f"Dialogues: {len(schema_a.segments)}, Characters: {len(schema_c.characters)}")
        
        # Initialize Schema D
        schema_d = SchemaD(
            video_id=schema_a.video_id,
            duration=schema_a.duration,
            metadata={
                'fusion_config': {
                    'heuristic_weight': self.config.heuristic_weight,
                    'llm_weight': self.config.llm_weight,
                    'use_llm': self.config.use_llm
                },
                'source_schemas': {
                    'schema_a': f"{len(schema_a.segments)} segments",
                    'schema_b': f"{len(schema_b.segments) if schema_b else 0} speakers",
                    'schema_c': f"{len(schema_c.characters)} characters"
                }
            }
        )
        
        # Process each dialogue segment
        for dialogue in schema_a.segments:
            match = self._match_dialogue_to_character(
                dialogue, schema_c, schema_b
            )
            
            if match:
                schema_d.add_match(match)
            else:
                schema_d.unmatched_dialogues.append(dialogue)
        
        # Calculate summary statistics
        schema_d.calculate_summary_stats()
        
        logger.info(f"Matching complete: {len(schema_d.matches)} matched, "
                   f"{len(schema_d.unmatched_dialogues)} unmatched")
        
        return schema_d
    
    def _match_dialogue_to_character(self,
                                   dialogue: TranscriptionSegment,
                                   schema_c: SchemaC,
                                   schema_b: Optional[SchemaB]) -> Optional[CharacterDialogueMatch]:
        """Match a single dialogue to the most likely character"""
        
        # Find corresponding speaker segment if available
        speaker_segment = None
        if schema_b and self.config.use_speaker_diarization:
            speaker_segment = self._find_speaker_segment(dialogue, schema_b)
        
        # Score each character
        character_scores = {}
        
        for char_id, character in schema_c.characters.items():
            # Calculate heuristic scores
            heuristic_scores = self.heuristic_matcher.calculate_heuristic_scores(
                dialogue, char_id, schema_c, speaker_segment
            )
            
            best_heuristic = self.heuristic_matcher.get_best_heuristic_score(heuristic_scores)
            
            # Calculate LLM score if enabled
            llm_score = 0.0
            llm_reasoning = ""
            if self.config.use_llm and self.llm_matcher:
                visual_context = self._build_visual_context(dialogue, schema_c)
                llm_score, llm_reasoning = self.llm_matcher.analyze_match(
                    dialogue, char_id, schema_c, visual_context
                )
            
            # Calculate final fusion score
            if self.config.use_llm:
                final_score = (
                    self.config.heuristic_weight * best_heuristic +
                    self.config.llm_weight * llm_score
                )
            else:
                final_score = best_heuristic
            
            # Determine confidence level
            confidence_level = self._determine_confidence_level(final_score)
            
            character_scores[char_id] = {
                'heuristic_scores': heuristic_scores,
                'best_heuristic': best_heuristic,
                'llm_score': llm_score,
                'llm_reasoning': llm_reasoning,
                'final_score': final_score,
                'confidence_level': confidence_level
            }
        
        # Find best match
        if not character_scores:
            return None
            
        best_char_id = max(character_scores, key=lambda x: character_scores[x]['final_score'])
        best_scores = character_scores[best_char_id]
        
        # Check if score meets minimum threshold
        if best_scores['final_score'] < self.config.min_confidence_threshold:
            return None
        
        # Create matching score object
        matching_score = MatchingScore(
            heuristic_scores=best_scores['heuristic_scores'],
            llm_score=best_scores['llm_score'] if self.config.use_llm else None,
            final_score=best_scores['final_score'],
            confidence_level=best_scores['confidence_level'],
            reasoning=best_scores.get('llm_reasoning', 
                                     f"Best heuristic: {max(best_scores['heuristic_scores'], key=best_scores['heuristic_scores'].get)}")
        )
        
        # Calculate time overlap if speaker segment available
        time_overlap = 0.0
        if speaker_segment:
            overlap_start = max(dialogue.start_time, speaker_segment.start_time)
            overlap_end = min(dialogue.end_time, speaker_segment.end_time)
            if overlap_start < overlap_end:
                dialogue_duration = dialogue.end_time - dialogue.start_time
                time_overlap = (overlap_end - overlap_start) / dialogue_duration
        
        # Build visual context
        visual_context = self._build_visual_context(dialogue, schema_c)
        visual_context['character_id'] = best_char_id
        
        # Create match
        match = CharacterDialogueMatch(
            match_id=f"match_{uuid.uuid4().hex[:8]}",
            character_id=best_char_id,
            dialogue_segment=dialogue,
            speaker_segment=speaker_segment,
            time_overlap=time_overlap,
            matching_score=matching_score,
            visual_context=visual_context
        )
        
        return match
    
    def _find_speaker_segment(self, 
                            dialogue: TranscriptionSegment,
                            schema_b: SchemaB) -> Optional[Any]:
        """Find the speaker segment that best overlaps with dialogue"""
        best_overlap = 0.0
        best_segment = None
        
        for speaker_seg in schema_b.segments:
            # Calculate overlap
            overlap_start = max(dialogue.start_time, speaker_seg.start_time)
            overlap_end = min(dialogue.end_time, speaker_seg.end_time)
            
            if overlap_start < overlap_end:
                overlap_duration = overlap_end - overlap_start
                dialogue_duration = dialogue.end_time - dialogue.start_time
                overlap_ratio = overlap_duration / dialogue_duration
                
                if overlap_ratio > best_overlap:
                    best_overlap = overlap_ratio
                    best_segment = speaker_seg
        
        return best_segment
    
    def _build_visual_context(self, 
                            dialogue: TranscriptionSegment,
                            schema_c: SchemaC) -> Dict:
        """Build visual context for the dialogue timeframe"""
        # Get detections during dialogue
        detections = [d for d in schema_c.detections
                     if dialogue.start_time <= d.timestamp <= dialogue.end_time]
        
        # Count characters
        character_counts = {}
        face_positions = {}
        
        for det in detections:
            if det.character_id:
                if det.character_id not in character_counts:
                    character_counts[det.character_id] = 0
                    face_positions[det.character_id] = []
                
                character_counts[det.character_id] += 1
                face_positions[det.character_id].append({
                    'bbox': det.bbox,
                    'confidence': det.confidence,
                    'timestamp': det.timestamp
                })
        
        # Find dominant character
        dominant_character = None
        if character_counts:
            dominant_character = max(character_counts, key=character_counts.get)
        
        return {
            'dialogue_timeframe': {
                'start': dialogue.start_time,
                'end': dialogue.end_time
            },
            'characters_present': list(character_counts.keys()),
            'character_counts': character_counts,
            'dominant_character': dominant_character,
            'face_positions': face_positions,
            'num_detections': len(detections)
        }
    
    def _determine_confidence_level(self, score: float) -> str:
        """Determine confidence level from final score"""
        if score >= 0.8:
            return "high"
        elif score >= 0.5:
            return "medium"
        else:
            return "low"