"""
Prompt Templates for MLLM Caption Generation

This module contains structured prompt templates for generating narrative captions
from scene context data.
"""

from typing import Dict, List, Optional
try:
    from .data_fusion_engine import SceneContextPacket, DialogueEntry
except ImportError:
    from data_fusion_engine import SceneContextPacket, DialogueEntry


class PromptTemplate:
    """Base class for prompt templates"""
    
    def format_dialogue_transcript(self, dialogue_entries: List[DialogueEntry]) -> str:
        """
        Format dialogue entries into a readable transcript
        
        Args:
            dialogue_entries: List of dialogue entries
            
        Returns:
            Formatted dialogue transcript
        """
        if not dialogue_entries:
            return "No dialogue in this scene."
        
        transcript_lines = []
        for entry in dialogue_entries:
            emotion_str = f" [{entry.emotion}]" if entry.emotion else ""
            line = f"{entry.speaker}: \"{entry.text}\"{emotion_str}"
            transcript_lines.append(line)
        
        return "\n".join(transcript_lines)
    
    def format_characters_list(self, characters: List[str]) -> str:
        """Format character list"""
        if not characters:
            return "No identified characters"
        return ", ".join(characters)


class NarrativeCaptionPrompt(PromptTemplate):
    """
    Prompt template for generating narrative-style captions
    """
    
    def __init__(self, include_emotions: bool = True, 
                 include_technical_details: bool = False):
        self.include_emotions = include_emotions
        self.include_technical_details = include_technical_details
    
    def generate_prompt(self, context: SceneContextPacket) -> str:
        """
        Generate the complete prompt for the MLLM
        
        Args:
            context: Scene context packet
            
        Returns:
            Formatted prompt string
        """
        dialogue_transcript = self.format_dialogue_transcript(context.dialogue_transcript)
        characters_list = self.format_characters_list(context.characters_present)
        
        prompt = f"""### ROLE ###
You are an expert film analyst and narrative writer. Your task is to write a concise, compelling, and narratively coherent summary for a single scene from a video.

### INSTRUCTIONS ###
- Write in the third-person, past-tense.
- Do NOT simply list the dialogue. Instead, synthesize the dialogue and visual information to describe the plot, character motivations, and interactions.
- Capture the subtext and the key developments in the scene.
- Your summary should flow logically from the summary of the previous scene.
- Keep the summary to 2-4 sentences.
- Focus on narrative progression and character development.
{self._get_additional_instructions()}

### CONTEXT FOR THE CURRENT SCENE ###

**Previous Scene Summary (What just happened):**
{context.prior_scene_summary}

**Scene Timestamp:**
{context.start_time:.1f}s to {context.end_time:.1f}s (Duration: {context.end_time - context.start_time:.1f}s)

**Visual Description (What the scene looks like):**
{context.visual_description}

**Scene Mood/Atmosphere:**
{context.mood or "Not specified"}

**Setting/Location:**
{context.setting or "Not specified"}

**Characters Present:**
{characters_list}

**Dialogue Transcript (What is being said):**
{dialogue_transcript}

### YOUR TASK ###
Based on all the provided context, write the narrative summary for the current scene now. Focus on what happens and why it matters to the story."""
        
        # Convert to LLaVA format
        return f"USER: {prompt}\n\nASSISTANT:"
    
    def _get_additional_instructions(self) -> str:
        """Get additional instructions based on configuration"""
        instructions = []
        
        if self.include_emotions:
            instructions.append("- Include emotional context when it's significant to the narrative.")
        
        if self.include_technical_details:
            instructions.append("- You may briefly mention significant cinematographic techniques if they enhance the narrative.")
        
        return "\n".join(instructions) if instructions else ""


class DescriptiveCaptionPrompt(PromptTemplate):
    """
    Prompt template for generating descriptive captions (for accessibility)
    """
    
    def generate_prompt(self, context: SceneContextPacket) -> str:
        """Generate descriptive caption prompt"""
        dialogue_transcript = self.format_dialogue_transcript(context.dialogue_transcript)
        characters_list = self.format_characters_list(context.characters_present)
        
        prompt = f"""### ROLE ###
You are an expert accessibility specialist creating descriptive video captions for visually impaired viewers.

### INSTRUCTIONS ###
- Describe both visual and audio elements clearly and concisely.
- Include important visual details that aren't apparent from dialogue alone.
- Mention character positions, movements, and expressions when relevant.
- Describe the setting and any significant visual changes.
- Keep descriptions objective and factual.
- Write in present tense for immediacy.
- Limit to 3-5 sentences.

### SCENE INFORMATION ###

**Timestamp:** {context.start_time:.1f}s to {context.end_time:.1f}s

**Visual Scene:**
{context.visual_description}

**Characters Visible:**
{characters_list}

**Dialogue and Sounds:**
{dialogue_transcript}

**Setting:**
{context.setting or "Not specified"}

**Mood/Atmosphere:**
{context.mood or "Not specified"}

### YOUR TASK ###
Write a descriptive caption that helps a visually impaired person understand what's happening in this scene, including both visual and audio elements."""
        
        # Convert to LLaVA format
        return f"USER: {prompt}\n\nASSISTANT:"


class SummaryCaptionPrompt(PromptTemplate):
    """
    Prompt template for generating brief summary captions
    """
    
    def generate_prompt(self, context: SceneContextPacket) -> str:
        """Generate summary caption prompt"""
        dialogue_transcript = self.format_dialogue_transcript(context.dialogue_transcript)
        
        prompt = f"""### ROLE ###
You are creating brief, informative video summaries.

### INSTRUCTIONS ###
- Summarize the key action or event in this scene in ONE sentence.
- Focus on what happens, not how it looks.
- Include character names when relevant.
- Be specific but concise.

### SCENE CONTENT ###

**Visual:** {context.visual_description}

**Dialogue:**
{dialogue_transcript}

**Previous Scene:** {context.prior_scene_summary}

### YOUR TASK ###
Write a one-sentence summary of what happens in this scene."""
        
        # Convert to LLaVA format
        return f"USER: {prompt}\n\nASSISTANT:"


class CustomPromptTemplate(PromptTemplate):
    """
    Custom prompt template that can be configured with a template string
    """
    
    def __init__(self, template: str):
        """
        Initialize with a custom template string
        
        The template can use the following placeholders:
        - {prior_summary}
        - {start_time}
        - {end_time}
        - {duration}
        - {visual_description}
        - {mood}
        - {setting}
        - {characters}
        - {dialogue}
        """
        self.template = template
    
    def generate_prompt(self, context: SceneContextPacket) -> str:
        """Generate prompt from custom template"""
        dialogue_transcript = self.format_dialogue_transcript(context.dialogue_transcript)
        characters_list = self.format_characters_list(context.characters_present)
        
        return self.template.format(
            prior_summary=context.prior_scene_summary,
            start_time=context.start_time,
            end_time=context.end_time,
            duration=context.end_time - context.start_time,
            visual_description=context.visual_description,
            mood=context.mood or "Not specified",
            setting=context.setting or "Not specified",
            characters=characters_list,
            dialogue=dialogue_transcript
        )


# Preset prompt templates
PROMPT_TEMPLATES = {
    "narrative": NarrativeCaptionPrompt(),
    "narrative_with_emotions": NarrativeCaptionPrompt(include_emotions=True),
    "narrative_technical": NarrativeCaptionPrompt(include_emotions=True, include_technical_details=True),
    "descriptive": DescriptiveCaptionPrompt(),
    "summary": SummaryCaptionPrompt()
}


def get_prompt_template(template_name: str, **kwargs) -> PromptTemplate:
    """
    Get a prompt template by name or create a custom one
    
    Args:
        template_name: Name of the template or "custom"
        **kwargs: Additional arguments for template initialization
        
    Returns:
        PromptTemplate instance
    """
    if template_name == "custom":
        if "template" not in kwargs:
            raise ValueError("Custom template requires 'template' parameter")
        return CustomPromptTemplate(kwargs["template"])
    
    if template_name in PROMPT_TEMPLATES:
        return PROMPT_TEMPLATES[template_name]
    
    # Try to create a template with the given name
    template_classes = {
        "narrative": NarrativeCaptionPrompt,
        "descriptive": DescriptiveCaptionPrompt,
        "summary": SummaryCaptionPrompt
    }
    
    base_name = template_name.split("_")[0]
    if base_name in template_classes:
        return template_classes[base_name](**kwargs)
    
    raise ValueError(f"Unknown template name: {template_name}")


if __name__ == "__main__":
    # Test the prompt templates
    try:
        from .data_fusion_engine import SceneContextPacket, DialogueEntry
    except ImportError:
        from data_fusion_engine import SceneContextPacket, DialogueEntry
    
    # Create a sample context packet
    sample_dialogue = [
        DialogueEntry(
            speaker="John",
            character_id="1",
            text="I can't believe you did that!",
            start_time=10.5,
            end_time=12.3,
            emotion="angry",
            emotion_confidence=0.85
        ),
        DialogueEntry(
            speaker="Sarah",
            character_id="2", 
            text="I had no choice. You have to understand.",
            start_time=12.5,
            end_time=14.8,
            emotion="sad",
            emotion_confidence=0.92
        )
    ]
    
    sample_context = SceneContextPacket(
        scene_id=5,
        start_time=10.0,
        end_time=15.0,
        visual_description="Two people arguing in a dimly lit room. John stands by the window while Sarah sits on the couch.",
        characters_present=["John", "Sarah"],
        dialogue_transcript=sample_dialogue,
        prior_scene_summary="John discovered that Sarah had been keeping a secret from him.",
        mood="tense",
        setting="living room"
    )
    
    # Test different prompt templates
    print("=== NARRATIVE PROMPT ===")
    narrative_prompt = NarrativeCaptionPrompt(include_emotions=True)
    print(narrative_prompt.generate_prompt(sample_context))
    
    print("\n\n=== DESCRIPTIVE PROMPT ===")
    descriptive_prompt = DescriptiveCaptionPrompt()
    print(descriptive_prompt.generate_prompt(sample_context))
    
    print("\n\n=== SUMMARY PROMPT ===")
    summary_prompt = SummaryCaptionPrompt()
    print(summary_prompt.generate_prompt(sample_context))