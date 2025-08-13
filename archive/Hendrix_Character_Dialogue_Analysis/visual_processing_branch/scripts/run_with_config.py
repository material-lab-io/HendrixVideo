#!/usr/bin/env python3
"""
Run visual pipeline with production configurations

This script provides an easy way to run the pipeline with optimized
settings for different content types.
"""

import argparse
import sys
from pathlib import Path
import logging
from typing import Optional

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from configs.production_configs import (
    get_config, list_configs, suggest_config,
    ProductionPresets
)
from scripts.tracked_visual_pipeline import TrackedVisualPipeline


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def analyze_video_properties(video_path: str) -> dict:
    """Quick analysis of video properties for config suggestion"""
    # This is a placeholder - in production, you'd implement actual analysis
    # For now, return default properties
    return {
        "avg_brightness": 0.5,
        "motion_score": 0.5,
        "scene_changes_per_minute": 10,
        "detected_faces_sample": 2,
        "duration": 600
    }


def main():
    parser = argparse.ArgumentParser(
        description="Run visual pipeline with production configurations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available configurations:
  default      - Balanced settings for general content
  dialogue     - Optimized for dialogue scenes
  action       - Optimized for action scenes  
  dark_scenes  - Optimized for poorly lit content
  crowd_scenes - Optimized for multiple people
  surveillance - Optimized for security footage

Presets:
  --preset netflix    - Netflix-style TV series
  --preset youtube    - YouTube content
  --preset trailer    - Movie trailers
        """
    )
    
    parser.add_argument('video_path', nargs='?', help='Path to input video')
    parser.add_argument('--config', '-c', default='default',
                       help='Configuration name (default: default)')
    parser.add_argument('--preset', '-p', 
                       choices=['netflix', 'youtube', 'trailer'],
                       help='Use production preset')
    parser.add_argument('--suggest', action='store_true',
                       help='Suggest best configuration based on video')
    parser.add_argument('--list-configs', action='store_true',
                       help='List all available configurations')
    parser.add_argument('--output', '-o', default='output',
                       help='Output directory')
    parser.add_argument('--device', choices=['cpu', 'cuda'], default='cpu',
                       help='Processing device')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')
    
    args = parser.parse_args()
    
    # Handle list configs
    if args.list_configs:
        print("\nAvailable configurations:")
        print("-" * 50)
        for name, desc in list_configs().items():
            print(f"{name:15} - {desc}")
        return
    
    # Validate video exists
    if not args.video_path:
        logger.error("Video path required")
        return 1
    
    if not Path(args.video_path).exists():
        logger.error(f"Video not found: {args.video_path}")
        return 1
    
    # Get configuration
    if args.preset:
        # Use preset
        if args.preset == 'netflix':
            config = ProductionPresets.netflix_series()
        elif args.preset == 'youtube':
            config = ProductionPresets.youtube_content()
        elif args.preset == 'trailer':
            config = ProductionPresets.movie_trailer()
        logger.info(f"Using preset: {args.preset}")
    elif args.suggest:
        # Analyze and suggest
        logger.info("Analyzing video properties...")
        properties = analyze_video_properties(args.video_path)
        suggested = suggest_config(properties)
        logger.info(f"Suggested configuration: {suggested}")
        config = get_config(suggested)
    else:
        # Use specified config
        try:
            config = get_config(args.config)
            logger.info(f"Using configuration: {args.config}")
        except ValueError as e:
            logger.error(str(e))
            return 1
    
    # Log configuration details
    logger.info(f"Configuration: {config.description}")
    logger.info(f"Min appearances: {config.face_tracker_config.min_character_appearances}")
    logger.info(f"Frame extraction: {config.frame_extraction['mode']} mode, "
               f"{config.frame_extraction['target_frames']} frames")
    
    # Create output directory
    output_dir = Path(args.output) / f"{config.name}_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize pipeline with configuration
    logger.info("Initializing pipeline...")
    pipeline = TrackedVisualPipeline(
        output_dir=str(output_dir),
        device=args.device,
        min_appearances=config.face_tracker_config.min_character_appearances
    )
    
    # Override tracker config
    pipeline.face_tracker.config = config.face_tracker_config
    
    # Process video
    logger.info(f"Processing video: {args.video_path}")
    
    try:
        schema_c = pipeline.process_video(
            video_path=args.video_path,
            extraction_mode=config.frame_extraction['mode'],
            target_frames=config.frame_extraction['target_frames']
        )
        
        # Summary
        print(f"\nProcessing complete!")
        print(f"Results saved to: {output_dir}")
        print(f"Characters detected: {len(schema_c.characters)}")
        print(f"Total detections: {len(schema_c.detections)}")
        
        # Character summary
        if schema_c.characters:
            print("\nCharacter Summary:")
            for char_id, char in schema_c.characters.items():
                print(f"  Character {char_id}: {char['num_appearances']} appearances, "
                     f"{char['total_screen_time']:.1f}s screen time")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=args.debug)
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())