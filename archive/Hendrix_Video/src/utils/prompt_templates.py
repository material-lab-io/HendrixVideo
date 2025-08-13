"""Prompt templates for LLM/VLM models."""

# For individual shot description
SHOT_DESCRIPTION_PROMPT = """Describe this video frame in one sentence, including the action, setting, and mood."""

# For scene construction from multiple shots
SCENE_CONSTRUCTION_PROMPT = """You are an expert film editor. I will provide you with a sequence of numbered keyframes from a video. Your task is to group these shots into coherent scenes. A scene is a continuous block of action that occurs in the same location at the same time. For each scene you identify, provide a concise one-sentence summary of the action, setting, and mood. Your output should be a JSON array with the following format:
[
  {{
    "scene_id": 1,
    "summary": "A person walks through a bright hallway with a neutral mood",
    "contained_shots": [1, 2, 3]
  }}
]

Here are the keyframes from shots {shot_range}:"""


CINEMATIC_ANALYSIS_PROMPT = """You are an expert cinematographer and film analyst. Analyze the following video scenes and provide insights on:

1. **Visual Style**: Camera work, framing, composition
2. **Cinematographic Techniques**: Use of lighting, color grading, camera movements
3. **Narrative Structure**: How shots and scenes build the story
4. **Emotional Impact**: How visual choices support the narrative mood
5. **Technical Quality**: Overall production value and craftsmanship

Provide your analysis in a structured format focusing on actionable insights."""


SHOT_TRANSITION_ANALYSIS_PROMPT = """Analyze the transition between these two consecutive frames and classify the type of transition:

Types of transitions:
- Cut: Instant change from one shot to another
- Dissolve: Gradual blend between shots
- Fade: Fade to/from black or white
- Wipe: One shot pushes another off screen
- Match cut: Visually similar elements connect two different shots

Describe what you observe and classify the transition type."""