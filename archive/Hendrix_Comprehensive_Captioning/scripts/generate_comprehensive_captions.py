#!/usr/bin/env python3
"""
Generate Comprehensive Captions

Main script to run the comprehensive captioning pipeline that combines
audio_analysis (character-dialogue matching) with Hendrix_Video_Analysis
(scene boundaries) to create rich narrative captions.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add parent directory to path for imports
parent_dir = str(Path(__file__).parent.parent)
sys.path.insert(0, parent_dir)

# Import directly from modules
from pipeline import ComprehensiveCaptioningPipeline


def setup_logging(log_level: str, log_file: Optional[str] = None):
    """Setup logging configuration"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    handlers = [logging.StreamHandler(sys.stdout)]
    
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=handlers
    )


def validate_paths(args):
    """Validate input paths exist"""
    errors = []
    
    # Check audio analysis path
    audio_path = Path(args.audio_analysis)
    if not audio_path.exists():
        errors.append(f"Audio analysis path not found: {audio_path}")
    
    # Check scene analysis path
    scene_path = Path(args.scene_analysis)
    if not scene_path.exists():
        errors.append(f"Scene analysis file not found: {scene_path}")
    
    # Check keyframes directory if provided
    if args.keyframes:
        keyframes_path = Path(args.keyframes)
        if not keyframes_path.exists():
            errors.append(f"Keyframes directory not found: {keyframes_path}")
    
    # Check config file if provided
    if args.config:
        config_path = Path(args.config)
        if not config_path.exists():
            errors.append(f"Config file not found: {config_path}")
    
    if errors:
        for error in errors:
            logging.error(error)
        sys.exit(1)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Generate comprehensive video captions by combining character-dialogue "
                    "matching with scene analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with default settings
  python generate_comprehensive_captions.py \\
    --audio-analysis audio_analysis/output/optimized_robust/session_20250805_145254 \\
    --scene-analysis Hendrix_Video_Analysis/output/scenes.json \\
    --output-dir output/captions/

  # With keyframes for visual context
  python generate_comprehensive_captions.py \\
    --audio-analysis audio_analysis/output/optimized_robust/session_20250805_145254 \\
    --scene-analysis Hendrix_Video_Analysis/output/scenes.json \\
    --keyframes Hendrix_Video_Analysis/keyframes/ \\
    --output-dir output/captions/

  # With custom configuration
  python generate_comprehensive_captions.py \\
    --audio-analysis audio_analysis/output/optimized_robust/session_20250805_145254 \\
    --scene-analysis Hendrix_Video_Analysis/output/scenes.json \\
    --config config/custom_captioning.yaml \\
    --output-dir output/captions/
        """
    )
    
    # Required arguments
    parser.add_argument(
        "--audio-analysis", 
        required=True,
        help="Path to audio analysis output directory (from optimized_robust pipeline)"
    )
    
    parser.add_argument(
        "--scene-analysis", 
        required=True,
        help="Path to scenes.json from Hendrix_Video_Analysis"
    )
    
    parser.add_argument(
        "--output-dir", 
        required=True,
        help="Directory to save generated captions"
    )
    
    # Optional arguments
    parser.add_argument(
        "--keyframes",
        help="Directory containing keyframe images for visual context"
    )
    
    parser.add_argument(
        "--config",
        help="Path to configuration file (default: config/captioning_config.yaml)"
    )
    
    parser.add_argument(
        "--api-key",
        help="API key for MLLM provider (not needed for LLaVA)"
    )
    
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--log-file",
        help="Save logs to file"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Process scenes but don't generate captions (for testing)"
    )
    
    parser.add_argument(
        "--max-scenes",
        type=int,
        help="Maximum number of scenes to process (for testing)"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level, args.log_file)
    
    # Log startup
    logging.info("=" * 80)
    logging.info("Comprehensive Captioning Pipeline")
    logging.info("=" * 80)
    logging.info(f"Audio Analysis: {args.audio_analysis}")
    logging.info(f"Scene Analysis: {args.scene_analysis}")
    logging.info(f"Output Directory: {args.output_dir}")
    if args.keyframes:
        logging.info(f"Keyframes: {args.keyframes}")
    logging.info("=" * 80)
    
    # Validate paths
    validate_paths(args)
    
    try:
        # Create pipeline
        config_path = args.config
        if not config_path:
            # Use default config
            default_config = Path(__file__).parent.parent / "config" / "captioning_config.yaml"
            if default_config.exists():
                config_path = str(default_config)
                logging.info(f"Using default config: {config_path}")
        
        pipeline = ComprehensiveCaptioningPipeline(config_path)
        
        # Dry run mode - just process scenes
        if args.dry_run:
            logging.info("DRY RUN MODE - Processing scenes only")
            
            # Initialize components
            pipeline.initialize_components(
                args.audio_analysis,
                args.scene_analysis,
                args.api_key
            )
            
            # Process scenes
            context_packets = pipeline.process_scenes()
            
            # Limit scenes if requested
            if args.max_scenes:
                context_packets = context_packets[:args.max_scenes]
                logging.info(f"Limited to {args.max_scenes} scenes")
            
            # Print summary
            print(f"\nProcessed {len(context_packets)} scenes:")
            for packet in context_packets[:5]:  # Show first 5
                print(f"  Scene {packet.scene_id}: {packet.start_time:.1f}s - {packet.end_time:.1f}s")
                print(f"    Characters: {', '.join(packet.characters_present) or 'None'}")
                print(f"    Dialogue segments: {len(packet.dialogue_transcript)}")
            
            if len(context_packets) > 5:
                print(f"  ... and {len(context_packets) - 5} more scenes")
            
            return
        
        # Run full pipeline
        results = pipeline.run(
            audio_analysis_path=args.audio_analysis,
            scene_analysis_path=args.scene_analysis,
            output_dir=args.output_dir,
            keyframes_dir=args.keyframes,
            mllm_api_key=args.api_key
        )
        
        # Print results summary
        print("\n" + "=" * 80)
        print("CAPTIONING COMPLETE")
        print("=" * 80)
        print(f"Status: {results['status']}")
        print(f"Processing Time: {results['processing_time']:.2f} seconds")
        print(f"Total Scenes: {results['total_scenes']}")
        print(f"Successful Captions: {results['successful_captions']}")
        print(f"Failed Captions: {results['failed_captions']}")
        print("\nOutput Files:")
        for format_name, filepath in results['saved_files'].items():
            print(f"  {format_name}: {filepath}")
        print("=" * 80)
        
    except KeyboardInterrupt:
        logging.info("Pipeline interrupted by user")
        sys.exit(130)
    except Exception as e:
        logging.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()