#!/usr/bin/env python3
"""
Example of using custom prompts for video analysis.

Usage:
    python examples/custom_prompts.py video.mp4
"""

import sys
import argparse
from pathlib import Path
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.main import VideoAnalysisPipeline


# Example custom prompts for different genres
GENRE_PROMPTS = {
    'action': {
        'shot_description': """Analyze this action scene frame. Describe:
1. The primary action or movement
2. Camera angle and motion (if apparent)
3. Energy level and pacing
4. Any visual effects or stunts visible""",
        
        'scene_construction': """Group these action shots into coherent sequences.
For each sequence, identify:
- Type of action (fight, chase, explosion, etc.)
- Intensity level (low/medium/high)
- Key participants
- Overall dramatic purpose
Format as JSON with clear scene boundaries."""
    },
    
    'documentary': {
        'shot_description': """Analyze this documentary frame. Note:
1. Subject matter and content
2. Interview setup (if applicable)
3. B-roll or archival footage characteristics
4. Information being conveyed""",
        
        'scene_construction': """Organize these documentary shots into thematic segments.
For each segment:
- Main topic or theme
- Type of footage (interview, B-roll, archival)
- Narrative purpose
- Key information presented
Structure as JSON with logical segment divisions."""
    },
    
    'cinematic': {
        'shot_description': """Analyze the cinematography in this frame:
1. Composition and framing
2. Lighting setup and mood
3. Color palette and grading
4. Depth of field and focus
5. Camera angle and perspective""",
        
        'scene_construction': """Group shots by visual style and narrative purpose.
For each scene:
- Visual style and aesthetic
- Emotional tone
- Narrative function
- Cinematographic techniques used
Provide detailed JSON with artistic analysis."""
    }
}


def create_custom_config(base_config_path, genre, output_path):
    """Create a custom configuration with genre-specific prompts."""
    
    # Load base configuration
    with open(base_config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Update prompts
    if genre in GENRE_PROMPTS:
        config['scene_construction']['prompts'] = GENRE_PROMPTS[genre]
        print(f"Using {genre} genre prompts")
    else:
        print(f"Warning: Unknown genre '{genre}', using default prompts")
    
    # Save custom config
    with open(output_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Video analysis with custom prompts")
    parser.add_argument("video", help="Path to video file")
    parser.add_argument("--genre", choices=['action', 'documentary', 'cinematic'], 
                       default='cinematic', help="Video genre for specialized prompts")
    parser.add_argument("--custom-prompt", help="Custom prompt string for shot description")
    parser.add_argument("--prompt-file", help="File containing custom prompts")
    parser.add_argument("--output-dir", default="output_custom", help="Output directory")
    parser.add_argument("--config", default="config.yaml", help="Base configuration file")
    args = parser.parse_args()
    
    # Check video exists
    if not Path(args.video).exists():
        print(f"Error: Video file not found: {args.video}")
        sys.exit(1)
    
    print(f"Analyzing video: {args.video}")
    print(f"Genre: {args.genre}")
    print("=" * 50)
    
    try:
        # Create custom configuration
        custom_config_path = "config_custom_temp.yaml"
        
        if args.prompt_file:
            # Load prompts from file
            with open(args.prompt_file, 'r') as f:
                custom_prompts = yaml.safe_load(f)
            
            with open(args.config, 'r') as f:
                config = yaml.safe_load(f)
            
            config['scene_construction']['prompts'] = custom_prompts
            
            with open(custom_config_path, 'w') as f:
                yaml.dump(config, f)
        else:
            # Use genre-based prompts
            custom_config_path = create_custom_config(
                args.config, 
                args.genre, 
                custom_config_path
            )
        
        # Override with command-line prompt if provided
        if args.custom_prompt:
            with open(custom_config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            config['scene_construction']['prompts']['shot_description'] = args.custom_prompt
            
            with open(custom_config_path, 'w') as f:
                yaml.dump(config, f)
            
            print(f"Using custom prompt: {args.custom_prompt[:50]}...")
        
        # Initialize pipeline with custom config
        pipeline = VideoAnalysisPipeline(custom_config_path)
        
        # Analyze video
        results = pipeline.analyze_video(
            args.video,
            output_dir=args.output_dir
        )
        
        # Display specialized results based on genre
        print("\nAnalysis Complete!")
        print("=" * 50)
        
        scenes = results.get('scenes', [])
        
        if args.genre == 'action':
            print("\nAction Sequence Analysis:")
            high_intensity = [s for s in scenes if 'high' in s.summary.lower()]
            print(f"  High intensity sequences: {len(high_intensity)}")
            
        elif args.genre == 'documentary':
            print("\nDocumentary Segment Analysis:")
            interviews = [s for s in scenes if 'interview' in s.summary.lower()]
            print(f"  Interview segments: {len(interviews)}")
            
        elif args.genre == 'cinematic':
            print("\nCinematographic Analysis:")
            
        # Show sample results
        print(f"\nTotal scenes identified: {len(scenes)}")
        print("\nSample scene descriptions:")
        for i, scene in enumerate(scenes[:3]):
            print(f"\nScene {scene.scene_id}:")
            print(f"  {scene.summary}")
            if scene.mood:
                print(f"  Mood: {scene.mood}")
            if scene.setting:
                print(f"  Setting: {scene.setting}")
        
        print(f"\nFull results saved to: {args.output_dir}/")
        
        # Clean up temporary config
        Path(custom_config_path).unlink(missing_ok=True)
        
    except Exception as e:
        print(f"\nError during analysis: {e}")
        # Clean up on error
        Path(custom_config_path).unlink(missing_ok=True)
        sys.exit(1)


if __name__ == "__main__":
    main()