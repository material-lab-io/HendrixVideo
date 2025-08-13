"""
Improved Prompt Templates for MLLM Caption Generation

This module contains enhanced prompt templates that address:
- Repetitive phrasing issues
- Better dialogue integration
- More concise output
- Improved context management
"""

from typing import Dict, List, Optional
from .data_fusion_engine import SceneContextPacket, DialogueEntry


class ImprovedPromptTemplate:
    """Base class for improved prompt templates"""
    
    def format_dialogue_with_context(self, dialogue_entries: List[DialogueEntry], max_entries: int = 3) -> str:
        """
        Format dialogue entries with emotional context and speaker identification
        
        Args:
            dialogue_entries: List of dialogue entries
            max_entries: Maximum number of dialogue entries to include
            
        Returns:
            Formatted dialogue with context
        """
        if not dialogue_entries:
            return ""
        
        # Select most important dialogue (prioritize by emotion confidence)
        sorted_dialogue = sorted(dialogue_entries, 
                               key=lambda x: x.emotion_confidence if x.emotion_confidence else 0, 
                               reverse=True)[:max_entries]
        
        # Re-sort by time for natural flow
        sorted_dialogue.sort(key=lambda x: x.start_time)
        
        dialogue_parts = []
        for entry in sorted_dialogue:
            if entry.emotion and entry.emotion != "neutral":
                dialogue_parts.append(f"{entry.speaker} ({entry.emotion}): \"{entry.text}\"")
            else:
                dialogue_parts.append(f"{entry.speaker}: \"{entry.text}\"")
        
        return " ".join(dialogue_parts)
    
    def get_character_description(self, characters: List[str]) -> str:
        """Get natural character description"""
        if not characters:
            return ""
        elif len(characters) == 1:
            return characters[0]
        elif len(characters) == 2:
            return f"{characters[0]} and {characters[1]}"
        else:
            return f"{', '.join(characters[:-1])}, and {characters[-1]}"
    
    def should_include_prior_context(self, prior_summary: str, visual_description: str) -> bool:
        """Determine if prior context should be included to avoid redundancy"""
        # Avoid including prior context if it's too similar to current scene
        if not prior_summary or prior_summary == "The story begins.":
            return False
        
        # Simple similarity check (could be enhanced with better NLP)
        prior_words = set(prior_summary.lower().split())
        current_words = set(visual_description.lower().split())
        overlap = len(prior_words & current_words) / max(len(prior_words), len(current_words))
        
        return overlap < 0.5  # Include if less than 50% overlap


class EnhancedNarrativePrompt(ImprovedPromptTemplate):
    """
    Enhanced narrative prompt that generates more natural, concise captions
    """
    
    def generate_prompt(self, context: SceneContextPacket) -> str:
        """Generate improved narrative prompt"""
        
        # Format dialogue with emotional context
        dialogue_context = self.format_dialogue_with_context(context.dialogue_transcript)
        
        # Get natural character description
        character_desc = self.get_character_description(context.characters_present)
        
        # Determine if we need prior context
        include_prior = self.should_include_prior_context(
            context.prior_scene_summary, 
            context.visual_description
        )
        
        # Build the prompt with better structure
        prompt_parts = [
            "Generate a concise narrative caption for this video scene.",
            "",
            "GUIDELINES:",
            "- Write 2-3 sentences maximum",
            "- Focus on action and emotion, not technical descriptions",
            "- Include actual dialogue only if it's crucial to the story",
            "- Use natural, flowing language",
            "- Avoid phrases like 'the scene shows' or 'frame analysis'",
            "",
            "SCENE DETAILS:",
            f"Visual: {context.visual_description}",
        ]
        
        if include_prior and context.prior_scene_summary != "The story begins.":
            prompt_parts.append(f"Context: Following {context.prior_scene_summary.lower()}")
        
        if character_desc:
            prompt_parts.append(f"Characters: {character_desc}")
        
        if dialogue_context:
            prompt_parts.append(f"Key dialogue: {dialogue_context}")
        
        prompt_parts.extend([
            "",
            "Write the caption now, focusing on what happens and why it matters:"
        ])
        
        prompt = "\n".join(prompt_parts)
        return f"USER: {prompt}\n\nASSISTANT:"


class ConciseDescriptivePrompt(ImprovedPromptTemplate):
    """
    Concise descriptive prompt for accessibility
    """
    
    def generate_prompt(self, context: SceneContextPacket) -> str:
        """Generate concise descriptive prompt"""
        
        dialogue_summary = self._summarize_dialogue(context.dialogue_transcript)
        character_desc = self.get_character_description(context.characters_present)
        
        prompt = f"""Create an accessibility caption for this scene in 2 sentences.

SCENE: {context.visual_description}
{f'CHARACTERS: {character_desc}' if character_desc else ''}
{f'DIALOGUE: {dialogue_summary}' if dialogue_summary else 'DIALOGUE: None'}

Write a clear, factual description of what viewers see and hear:"""
        
        return f"USER: {prompt}\n\nASSISTANT:"
    
    def _summarize_dialogue(self, dialogue_entries: List[DialogueEntry]) -> str:
        """Summarize dialogue content briefly"""
        if not dialogue_entries:
            return ""
        
        speakers = list(set(entry.speaker for entry in dialogue_entries))
        
        if len(dialogue_entries) == 1:
            entry = dialogue_entries[0]
            return f"{entry.speaker} says \"{entry.text}\""
        else:
            return f"{', '.join(speakers)} are speaking"


class ActionFocusedPrompt(ImprovedPromptTemplate):
    """
    Action-focused prompt that emphasizes what happens
    """
    
    def generate_prompt(self, context: SceneContextPacket) -> str:
        """Generate action-focused prompt"""
        
        # Extract key action words from visual description
        action_context = self._extract_action_context(context)
        
        prompt = f"""In one sentence, describe the key action in this scene.

Visual: {context.visual_description}
{f'Action: {action_context}' if action_context else ''}

Focus on WHAT happens, not how it looks:"""
        
        return f"USER: {prompt}\n\nASSISTANT:"
    
    def _extract_action_context(self, context: SceneContextPacket) -> str:
        """Extract action-related information"""
        if context.dialogue_transcript:
            # Get the most emotional or important line
            most_important = max(context.dialogue_transcript, 
                               key=lambda x: x.emotion_confidence if x.emotion_confidence else 0)
            return f"{most_important.speaker} {most_important.emotion}ly says \"{most_important.text}\""
        return ""


class ImprovedNarrativeWithEmotions(ImprovedPromptTemplate):
    """
    Improved narrative prompt that better integrates emotions and dialogue
    """
    
    def generate_prompt(self, context: SceneContextPacket) -> str:
        """Generate emotion-aware narrative prompt"""
        
        # Build emotion map
        emotion_context = self._build_emotion_context(context.dialogue_transcript)
        
        # Get dialogue highlights
        dialogue_highlights = self._get_dialogue_highlights(context.dialogue_transcript)
        
        # Character context
        character_desc = self.get_character_description(context.characters_present)
        
        prompt_parts = [
            "Write a 2-3 sentence narrative caption that captures both action and emotion.",
            "",
            f"SCENE: {context.visual_description}",
        ]
        
        if character_desc:
            prompt_parts.append(f"CHARACTERS: {character_desc}")
        
        if emotion_context:
            prompt_parts.append(f"EMOTIONAL TONE: {emotion_context}")
        
        if dialogue_highlights:
            prompt_parts.append(f"KEY MOMENTS: {dialogue_highlights}")
        
        prompt_parts.extend([
            "",
            "Craft a caption that weaves together the visual, emotional, and dialogue elements:"
        ])
        
        prompt = "\n".join(prompt_parts)
        return f"USER: {prompt}\n\nASSISTANT:"
    
    def _build_emotion_context(self, dialogue_entries: List[DialogueEntry]) -> str:
        """Build emotional context summary"""
        if not dialogue_entries:
            return ""
        
        emotions = [entry.emotion for entry in dialogue_entries if entry.emotion and entry.emotion != "neutral"]
        if not emotions:
            return "conversational"
        
        # Get dominant emotion
        emotion_counts = {}
        for emotion in emotions:
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        dominant_emotion = max(emotion_counts.items(), key=lambda x: x[1])[0]
        
        if len(set(emotions)) == 1:
            return dominant_emotion
        else:
            return f"shifting from {emotions[0]} to {emotions[-1]}"
    
    def _get_dialogue_highlights(self, dialogue_entries: List[DialogueEntry]) -> str:
        """Get the most impactful dialogue moments"""
        if not dialogue_entries:
            return ""
        
        # Find most emotional moment
        highlights = []
        
        # Get highest emotion confidence entry
        if any(entry.emotion_confidence for entry in dialogue_entries):
            most_emotional = max(dialogue_entries, 
                               key=lambda x: x.emotion_confidence if x.emotion_confidence else 0)
            if most_emotional.emotion != "neutral":
                highlights.append(f"{most_emotional.speaker} {most_emotional.emotion}ly: \"{most_emotional.text}\"")
        
        # Get first and last if different
        if len(dialogue_entries) > 2:
            if dialogue_entries[0].text not in [h for h in highlights]:
                highlights.append(f"{dialogue_entries[0].speaker}: \"{dialogue_entries[0].text}\"")
        
        return " → ".join(highlights[:2])  # Limit to 2 highlights


# Create preset templates
IMPROVED_TEMPLATES = {
    "enhanced_narrative": EnhancedNarrativePrompt(),
    "concise_descriptive": ConciseDescriptivePrompt(),
    "action_focused": ActionFocusedPrompt(),
    "narrative_emotions": ImprovedNarrativeWithEmotions(),
}


def get_improved_template(template_name: str) -> ImprovedPromptTemplate:
    """Get an improved prompt template by name"""
    if template_name not in IMPROVED_TEMPLATES:
        # Default to enhanced narrative
        return IMPROVED_TEMPLATES["enhanced_narrative"]
    return IMPROVED_TEMPLATES[template_name]