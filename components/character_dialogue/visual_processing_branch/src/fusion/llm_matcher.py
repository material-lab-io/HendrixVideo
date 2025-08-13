"""
LLM-based Matcher for Character-Dialogue Matching

This module uses language models to analyze visual context and make
intelligent character-dialogue matching decisions.

Note: This is a simplified implementation. In production, you would:
1. Use LLaVA or similar multimodal models
2. Pass actual video frames with character bounding boxes
3. Get visual understanding directly from the model
"""

import logging
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
import numpy as np

from ..schemas import (
    SchemaA, SchemaB, SchemaC,
    TranscriptionSegment, CharacterInfo, FaceDetection
)

logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """Configuration for LLM matching"""
    model_name: str = "gpt-4"  # In production, would use LLaVA
    temperature: float = 0.3
    max_tokens: int = 150
    use_visual_context: bool = True
    confidence_weight: float = 0.6  # Weight for LLM score in final fusion


class LLMMatcher:
    """
    LLM-based matcher for character-dialogue matching
    
    In a real implementation, this would:
    1. Use LLaVA or similar multimodal LLM
    2. Pass video frames directly to the model
    3. Get visual understanding of who is speaking
    
    For now, we simulate this with structured prompts based on our schema data.
    """
    
    def __init__(self, config: LLMConfig = None):
        self.config = config or LLMConfig()
        
    def analyze_match(self,
                     dialogue: TranscriptionSegment,
                     character_id: str,
                     schema_c: SchemaC,
                     visual_context: Dict[str, Any]) -> Tuple[float, str]:
        """
        Analyze a potential character-dialogue match using LLM
        
        Args:
            dialogue: The dialogue segment
            character_id: The character to evaluate
            schema_c: Complete visual schema
            visual_context: Additional visual context (frame info, positions, etc.)
            
        Returns:
            Tuple of (score, reasoning)
        """
        # Get character info
        character = schema_c.characters.get(character_id)
        if not character:
            return 0.0, "Character not found"
        
        # Build context for LLM
        prompt = self._build_analysis_prompt(
            dialogue, character, schema_c, visual_context
        )
        
        # Simulate LLM analysis (in production, would call actual LLM API)
        score, reasoning = self._simulate_llm_analysis(
            dialogue, character, schema_c, visual_context
        )
        
        return score, reasoning
    
    def _build_analysis_prompt(self,
                             dialogue: TranscriptionSegment,
                             character: CharacterInfo,
                             schema_c: SchemaC,
                             visual_context: Dict[str, Any]) -> str:
        """Build prompt for LLM analysis"""
        
        # Get detections during dialogue
        detections_during = [d for d in schema_c.detections
                           if dialogue.start_time <= d.timestamp <= dialogue.end_time]
        
        # Count characters present
        characters_present = set()
        for det in detections_during:
            if det.character_id:
                characters_present.add(det.character_id)
        
        prompt = f"""
Analyze if Character {character.character_id} is speaking the following dialogue:

DIALOGUE:
Text: "{dialogue.text}"
Time: {dialogue.start_time:.2f}s - {dialogue.end_time:.2f}s
Emotion: {dialogue.emotion or 'neutral'}

CHARACTER INFO:
- ID: {character.character_id}
- Total appearances: {character.num_appearances}
- Screen time: {character.total_screen_time:.1f}s
- Demographics: {self._format_demographics(character.attributes)}

VISUAL CONTEXT:
- Characters on screen during dialogue: {len(characters_present)}
- Character {character.character_id} visible: {'Yes' if character.character_id in characters_present else 'No'}
- Face positions: {self._format_face_positions(detections_during, character.character_id)}

Based on this information, how likely is it that Character {character.character_id} 
is speaking this dialogue? Consider:
1. Character presence during dialogue
2. Face position and size (central/large faces more likely to be speaking)
3. Number of other characters present
4. Dialogue content and character demographics

Provide a confidence score (0-1) and brief reasoning.
"""
        return prompt
    
    def _simulate_llm_analysis(self,
                             dialogue: TranscriptionSegment,
                             character: CharacterInfo,
                             schema_c: SchemaC,
                             visual_context: Dict[str, Any]) -> Tuple[float, str]:
        """
        Simulate LLM analysis based on visual context
        
        In production, this would call actual LLM API.
        Here we implement rule-based simulation.
        """
        score = 0.0
        reasons = []
        
        # Get detections during dialogue
        detections_during = [d for d in schema_c.detections
                           if dialogue.start_time <= d.timestamp <= dialogue.end_time]
        
        # Check if character is present
        char_detections = [d for d in detections_during 
                          if d.character_id == character.character_id]
        
        if not char_detections:
            # Character not visible
            score = 0.1
            reasons.append("Character not visible during dialogue")
        else:
            # Character is visible
            score = 0.5
            reasons.append("Character visible during dialogue")
            
            # Analyze face positions
            avg_size, centrality = self._analyze_face_metrics(char_detections)
            
            if avg_size > 0.15:  # Large face
                score += 0.2
                reasons.append("Large face size suggests prominence")
            
            if centrality > 0.7:  # Central position
                score += 0.2
                reasons.append("Central position indicates speaker")
            
            # Check for single character
            unique_chars = set(d.character_id for d in detections_during 
                             if d.character_id is not None)
            if len(unique_chars) == 1:
                score += 0.1
                reasons.append("Only character on screen")
            
            # Emotion alignment (if available)
            if dialogue.emotion and character.attributes:
                char_emotion = character.attributes.get('dominant_emotion')
                if char_emotion and self._emotions_align(dialogue.emotion, char_emotion):
                    score += 0.1
                    reasons.append(f"Emotion alignment: {dialogue.emotion}")
        
        # Cap score at 1.0
        score = min(score, 1.0)
        
        # Determine reasoning
        if score >= 0.8:
            reasoning = f"High confidence: {', '.join(reasons)}"
        elif score >= 0.5:
            reasoning = f"Medium confidence: {', '.join(reasons)}"
        else:
            reasoning = f"Low confidence: {', '.join(reasons)}"
        
        return score, reasoning
    
    def _format_demographics(self, attributes: Optional[Dict]) -> str:
        """Format character demographics for prompt"""
        if not attributes:
            return "Unknown"
        
        parts = []
        if 'dominant_gender' in attributes:
            parts.append(attributes['dominant_gender'])
        if 'age' in attributes and isinstance(attributes['age'], dict):
            parts.append(f"Age ~{attributes['age'].get('median', 'unknown')}")
        elif 'age' in attributes:
            parts.append(f"Age ~{attributes['age']}")
        
        return ", ".join(parts) if parts else "Unknown"
    
    def _format_face_positions(self, detections: List[FaceDetection], 
                             target_char_id: str) -> str:
        """Format face position information"""
        positions = []
        
        for det in detections:
            if det.character_id == target_char_id:
                bbox = det.bbox
                center_x = (bbox[0] + bbox[2]) / 2
                center_y = (bbox[1] + bbox[3]) / 2
                size = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
                
                # Determine position
                if center_x < 213:
                    h_pos = "left"
                elif center_x > 427:
                    h_pos = "right"
                else:
                    h_pos = "center"
                
                positions.append(f"{h_pos} ({size:.1%} of frame)")
        
        return ", ".join(positions) if positions else "Not visible"
    
    def _analyze_face_metrics(self, detections: List[FaceDetection]) -> Tuple[float, float]:
        """Analyze face size and centrality"""
        if not detections:
            return 0.0, 0.0
        
        sizes = []
        centralities = []
        
        for det in detections:
            bbox = det.bbox
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
            size = (width * height) / (640 * 480)  # Normalized by frame size
            
            center_x = (bbox[0] + bbox[2]) / 2
            center_y = (bbox[1] + bbox[3]) / 2
            
            # Distance from center (normalized)
            dist_from_center = np.sqrt(
                ((center_x - 320) / 320) ** 2 + 
                ((center_y - 240) / 240) ** 2
            )
            centrality = 1.0 - min(dist_from_center, 1.0)
            
            sizes.append(size)
            centralities.append(centrality)
        
        return np.mean(sizes), np.mean(centralities)
    
    def _emotions_align(self, dialogue_emotion: str, char_emotion: str) -> bool:
        """Check if emotions align reasonably"""
        # Simple emotion grouping
        positive = {'happy', 'surprise'}
        negative = {'sad', 'angry', 'fear', 'disgust'}
        neutral = {'neutral'}
        
        # Get emotion groups
        dialogue_group = None
        char_group = None
        
        for group, emotions in [(positive, positive), 
                               (negative, negative), 
                               (neutral, neutral)]:
            if dialogue_emotion in emotions:
                dialogue_group = group
            if char_emotion in emotions:
                char_group = group
        
        # Emotions align if in same group
        return dialogue_group == char_group